"""VRAM helpers for the staged load/unload lifecycle on a 24 GB card.

torch is imported lazily so `import geogrounder.utils` stays dep-free.
"""

from contextlib import contextmanager


def _torch():
    import torch
    return torch


def reset_peak(device=None):
    torch = _torch()
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats(device)


def peak_gb(device=None):
    torch = _torch()
    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.max_memory_allocated(device) / 1e9


def empty_cache():
    torch = _torch()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


@contextmanager
def track_vram(label='', device=None):
    """with track_vram('qwen load'): ...  -> prints peak GB on exit."""
    reset_peak(device)
    try:
        yield
    finally:
        print(f'[vram] {label}: peak {peak_gb(device):.2f} GB')
