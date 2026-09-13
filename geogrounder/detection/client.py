"""Main-env client that invokes LAE-DINO in its isolated conda env via subprocess.

Design rule (from the doc): grounding is reached ONLY through this client. Nothing in the
main package imports LAE-DINO / mmdet. The isolated env runs as a child process and frees
its VRAM on exit.

Throughput: prefer `detect_batch(...)` for eval — ONE child process loads LAE-DINO once and
serves all images. `detect(...)` (single image) is a convenience wrapper for the interactive
pipeline. Transport: temp JSON files (robust for bbox arrays / large batches).
"""

import os
import re
import subprocess
import sys
import tempfile
import threading

from .protocol import (DetectionRequest, DetectionResponse,
                       requests_to_json, responses_from_json)

try:
    from tqdm import tqdm
    _HAS_TQDM = True
except Exception:  # optional dep -> fall back to streaming the text progress markers
    _HAS_TQDM = False

# Child emits progress on stderr prefixed with this; MUST match serve_detect.py PROGRESS_MARKER.
PROGRESS_MARKER = '[[LAEDINO_PROGRESS]]'
_PROGRESS_RE = re.compile(r'detected (\d+)/(\d+)')


class LaeDinoClient:
    def __init__(self, serve_script, conda_env='laedino', python_bin=None,
                 extra_env=None, timeout=3600):
        """
        serve_script : path to laedino_env/serve_detect.py
        conda_env    : isolated env name (used with `conda run -n`)
        python_bin   : explicit path to the isolated env's python (alt to conda run)
        extra_env    : extra env vars for the child (e.g. LAEDINO_CONFIG, LAEDINO_WEIGHTS)
        """
        self.serve_script = os.path.abspath(serve_script)
        self.conda_env = conda_env
        self.python_bin = python_bin
        self.extra_env = extra_env or {}
        self.timeout = timeout

    def _base_cmd(self):
        if self.python_bin:
            return [self.python_bin, self.serve_script]
        return ['conda', 'run', '--no-capture-output', '-n', self.conda_env,
                'python', self.serve_script]

    def detect_batch(self, requests, stream_progress=True):
        """Run a list of DetectionRequest in ONE child process. -> list[DetectionResponse].

        Streams the child's progress lines (PROGRESS_MARKER on stderr) to our stdout live so the
        long detection phase isn't silent; full stdout+stderr are still captured for error reports.
        Drains both pipes on threads to avoid a pipe-buffer deadlock on verbose mmdet output.
        """
        tmpdir = tempfile.mkdtemp(prefix='laedino_')
        req_path = os.path.join(tmpdir, 'requests.json')
        resp_path = os.path.join(tmpdir, 'responses.json')
        with open(req_path, 'w') as f:
            f.write(requests_to_json(requests))

        cmd = self._base_cmd() + ['--requests', req_path, '--responses', resp_path]
        env = {**os.environ, **self.extra_env}
        # The LAE-DINO env's (older) torch rejects PYTORCH_CUDA_ALLOC_CONF=expandable_segments with
        # "Unrecognized CachingAllocator option" and the detector crashes -> empty detections. The
        # main process may legitimately set it (for the parser/SAM), so strip it from the SUBPROCESS
        # env only, unless the caller explicitly re-supplied it via extra_env.
        if 'PYTORCH_CUDA_ALLOC_CONF' not in self.extra_env:
            env.pop('PYTORCH_CUDA_ALLOC_CONF', None)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, bufsize=1, env=env)

        out_buf, err_buf = [], []
        bar = tqdm(total=len(requests), desc='[2] LAE-DINO detect', unit='img') \
            if (stream_progress and _HAS_TQDM) else None

        def _drain(pipe, buf, handle_progress):
            for line in iter(pipe.readline, ''):
                buf.append(line)
                if handle_progress and line.startswith(PROGRESS_MARKER):
                    rest = line[len(PROGRESS_MARKER):]
                    m = _PROGRESS_RE.search(rest)
                    if bar is not None and m:
                        bar.n = int(m.group(1))   # 'detected i/total' -> advance bar to i
                        bar.refresh()
                    elif bar is not None:
                        tqdm.write(rest.rstrip())  # non-progress marker (e.g. build error) above the bar
                    else:
                        sys.stdout.write(rest)     # no tqdm -> stream the text marker (old behavior)
                        sys.stdout.flush()
            pipe.close()

        t_out = threading.Thread(target=_drain, args=(proc.stdout, out_buf, False))
        t_err = threading.Thread(target=_drain, args=(proc.stderr, err_buf, stream_progress))
        t_out.start()
        t_err.start()
        try:
            proc.wait(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            proc.kill()  # kill first so the child closes its pipes and the drain threads can exit
            raise
        finally:
            t_out.join()
            t_err.join()
            if bar is not None:
                bar.close()

        if proc.returncode != 0 or not os.path.exists(resp_path):
            raise RuntimeError(
                f'LAE-DINO subprocess failed (code {proc.returncode}).\n'
                f'CMD: {" ".join(cmd)}\nSTDERR:\n{"".join(err_buf)}\nSTDOUT:\n{"".join(out_buf)}')
        with open(resp_path) as f:
            return responses_from_json(f.read())

    def detect(self, request: DetectionRequest) -> DetectionResponse:
        """Single image (loads the model once for this one call)."""
        resp = self.detect_batch([request], stream_progress=False)[0]
        if resp.error:
            raise RuntimeError(f'LAE-DINO reported error: {resp.error}')
        return resp
