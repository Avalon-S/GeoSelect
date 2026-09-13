/* GeoSelect execution inspector.
 *
 * Three panes over one state: the image (candidates + field), the program (the control surface),
 * and the scored candidate set (what every operator transforms). Editing a token re-executes the
 * program in the browser; stepping walks the executor's post-order trace.
 *
 * Candidates arrive per detector phrase ({phrase: [box...]}), because Select queries one noun
 * phrase at a time -- that is what lets an anchor of a different class resolve at all.
 */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var TRACES = window.TRACES || [];
  var G = window.GeoExec;

  /* Image paths in traces.js are relative to this directory. Embedded in a page one level up,
     the host sets window.INSPECTOR_BASE = "inspector/" so both entry points keep working. */
  var BASE = window.INSPECTOR_BASE || "";

  /* Type-legal edit vocabularies. AREA is deliberately absent: comparative-size operators are a
     dropped ablation in the paper, not part of the frozen pipeline. */
  var PREDS = ["LEFT", "RIGHT", "TOP", "BOTTOM", "UL", "UR", "LL", "LR", "CENTER", "NEAR"];
  var AXES = ["X", "Y", "DIAG_UL_LR", "DIAG_UR_LL"];
  var EXTREMA = ["argmax", "argmin"];

  var state = {
    caseId: null,
    program: null,     // possibly edited copy
    pristine: null,    // the synthesised original
    steps: [],
    step: 0,
    hover: -1,
    showField: false,
    showMask: false,
    filter: "all",
  };

  function curCase() {
    return TRACES.find(function (c) { return c.id === state.caseId; });
  }
  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  /* The pipeline fell back for this expression. That is NOT the same as "no program": the
     synthesiser may well have produced one, and the checker or the executor then rejected it.
     Either way the program never ran, so the page must not act it out as though it had. */
  function fellBack(c) { return !!c && (c.mode === "fallback" || !c.program); }
  function edited() {
    return state.pristine && JSON.stringify(state.program) !== JSON.stringify(state.pristine);
  }

  /* The numbered candidate set: the boxes of the program's outermost Select phrase. */
  function cands(c) {
    if (!c) return [];
    var d = c.detections || {};
    return (c.phrase && d[c.phrase]) || d[Object.keys(d)[0]] || [];
  }

  /* Boxes of every other detected class -- anchors the program may reference. */
  function anchorBoxes(c) {
    if (!c || !c.detections) return [];
    var out = [];
    Object.keys(c.detections).forEach(function (k) {
      if (k !== c.phrase) out = out.concat(c.detections[k]);
    });
    return out;
  }

  /* ---------- case picker ---------- */

  function opLabel(c) {
    if (c.mode === "fallback") return "fallback";
    var o = (c.ops || []).filter(function (x) { return x !== "select"; });
    return o.length ? o.join("+") : "select";
  }

  /* 120 cases do not browse well as one strip. Filter by the two axes that matter here -- which
     benchmark, and which operator the program actually uses. */
  var FILTERS = [
    { key: "all", label: "All" },
    { key: "RRSIS-D", label: "RRSIS-D" },
    { key: "RISBench", label: "RISBench" },
    { key: "filter", label: "Filter" },
    { key: "extremum", label: "Argmax / Argmin" },
    { key: "nth", label: "Nth" },
    { key: "relate", label: "Relate" },
    { key: "fallback", label: "Fallback" },
  ];

  function matchesFilter(c, key) {
    if (key === "all") return true;
    if (key === "RRSIS-D" || key === "RISBench") return c.dataset === key;
    if (key === "fallback") return c.mode === "fallback";
    if (key === "extremum") {
      return (c.ops || []).indexOf("argmax") >= 0 || (c.ops || []).indexOf("argmin") >= 0;
    }
    return (c.ops || []).indexOf(key) >= 0;
  }

  function filtered() {
    return TRACES.filter(function (c) { return matchesFilter(c, state.filter); });
  }

  function renderFilters() {
    var host = $("inspFilters");
    if (!host) return;
    host.innerHTML = FILTERS.map(function (f) {
      var n = TRACES.filter(function (c) { return matchesFilter(c, f.key); }).length;
      if (!n) return "";
      return '<button class="filter-tab' + (state.filter === f.key ? " active" : "") +
        '" data-filter="' + f.key + '">' + f.label +
        ' <span class="ft-n">' + n + "</span></button>";
    }).join("");
    Array.prototype.forEach.call(host.querySelectorAll(".filter-tab"), function (b) {
      b.onclick = function () {
        state.filter = b.dataset.filter;
        var list = filtered();
        // keep the open case if it survives the filter, else open the first that does
        if (!list.some(function (c) { return c.id === state.caseId; }) && list.length) {
          loadCase(list[0].id);
        } else {
          renderAll();
        }
      };
    });
  }

  function renderCases() {
    var list = filtered();
    $("cases").innerHTML = list.map(function (c) {
      var idx = c.id.slice(c.id.lastIndexOf("_") + 1);
      return '<button class="case-pill' + (c.id === state.caseId ? " sel" : "") +
        (c.mode === "fallback" ? " fb" : "") + '" data-id="' + c.id + '"' +
        ' title="' + c.dataset + " — " + c.sentence.replace(/"/g, "&quot;") + '">' +
        '<span class="op">' + opLabel(c) + "</span>" +
        c.stratum + ' <span class="idx">#' + idx + "</span></button>";
    }).join("");
    Array.prototype.forEach.call($("cases").querySelectorAll(".case-pill"), function (b) {
      b.onclick = function () { loadCase(b.dataset.id); };
    });
  }

  /* ---------- expression ---------- */

  function renderExpression(c) {
    var s = c.sentence, ph = c.phrase;
    var html = s;
    if (ph) {
      var i = s.toLowerCase().indexOf(ph.toLowerCase());
      if (i >= 0) {
        html = s.slice(0, i) + '<span class="hl">' + s.slice(i, i + ph.length) + "</span>" +
          s.slice(i + ph.length);
      }
    }
    $("sentence").innerHTML = "&ldquo;" + html + "&rdquo;";
    var n = cands(c).length, extra = anchorBoxes(c).length;
    $("meta").innerHTML = c.dataset + " &middot; " + c.stratum + " &middot; " +
      n + " candidate" + (n === 1 ? "" : "s") +
      (extra ? " + " + extra + " anchor box" + (extra === 1 ? "" : "es") : "") +
      " &middot; pipeline IoU <code>" + c.iou + "</code>" +
      (c.mode === "fallback" ? ' &middot; <code>fallback</code>' : "") +
      (c.source === "recovered" ? ' &middot; <code>boxes recovered from overlays</code>' : "");
  }

  /* ---------- program tree ---------- */

  function sel(value, options, onchange, changed) {
    var s = document.createElement("select");
    s.className = "tok tok-select" + (changed ? " changed" : "");
    options.forEach(function (o) {
      var op = document.createElement("option");
      op.value = o; op.textContent = o; op.selected = o === value;
      s.appendChild(op);
    });
    s.onchange = function () { onchange(s.value); };
    return s;
  }

  /* `orig` is the same node in the synthesised program, so an edited token can be marked. Edits
     never change the tree's shape -- only an operator, predicate, axis or index -- so the two
     trees stay in step. */
  function nodeLabel(node, orig, activeNode, doneNodes) {
    var wrap = document.createElement("div");
    var line = document.createElement("span");
    var isDone = !!doneNodes && doneNodes.indexOf(node) >= 0 && node !== activeNode;
    line.className = "node" + (node === activeNode ? " active" : (isDone ? " done" : ""));

    var name = document.createElement("span");
    name.className = "op-name";

    if (node.op === "select") {
      name.textContent = "Select";
      line.appendChild(name);
      line.appendChild(document.createTextNode('("'));
      var lit = document.createElement("span");
      lit.className = "lit";
      lit.textContent = node.type;
      line.appendChild(lit);
      line.appendChild(document.createTextNode('")'));
    } else if (node.op === "filter") {
      name.textContent = "Filter";
      line.appendChild(name);
      line.appendChild(document.createTextNode("( "));
      line.appendChild(sel(node.pred, PREDS, function (v) { node.pred = v; reexecute(); },
        orig && orig.pred !== node.pred));
      line.appendChild(document.createTextNode(
        node.anchor && node.anchor !== "image" ? " , anchor ↓ )" : " , IMAGE )"));
    } else if (node.op === "argmax" || node.op === "argmin") {
      var opSel = sel(node.op, EXTREMA, function (v) { node.op = v; reexecute(); },
        orig && orig.op !== node.op);
      line.appendChild(opSel);
      line.appendChild(document.createTextNode("( "));
      line.appendChild(sel(node.axis, AXES, function (v) { node.axis = v; reexecute(); },
        orig && orig.axis !== node.axis));
      line.appendChild(document.createTextNode(" )"));
    } else if (node.op === "nth") {
      name.textContent = "Nth";
      line.appendChild(name);
      line.appendChild(document.createTextNode("( n="));
      // Offer 0..nCand, so one index is always past the end: an out-of-range Nth is type-legal,
      // returns nothing, and is exactly the empty result the reliability ladder catches.
      var ns = [];
      var nCand = cands(curCase()).length;
      for (var i = 0, top = Math.max(3, nCand); i <= top; i++) ns.push(String(i));
      line.appendChild(sel(String(node.n), ns, function (v) { node.n = +v; reexecute(); },
        orig && orig.n !== node.n));
      line.appendChild(document.createTextNode(" , "));
      line.appendChild(sel(node.axis, AXES, function (v) { node.axis = v; reexecute(); },
        orig && orig.axis !== node.axis));
      line.appendChild(document.createTextNode(" )"));
    } else if (node.op === "relate") {
      name.textContent = "Relate";
      line.appendChild(name);
      line.appendChild(document.createTextNode("( " + node.rel + " , anchor ↓ )"));
    } else {
      name.textContent = node.op;
      line.appendChild(name);
    }

    wrap.appendChild(line);

    var kids = [];
    if (node.child) kids.push([node.child, orig && orig.child]);
    if (node.anchor && typeof node.anchor === "object") kids.push([node.anchor, orig && orig.anchor]);
    if (node.anchor2 && typeof node.anchor2 === "object") kids.push([node.anchor2, orig && orig.anchor2]);
    if (kids.length) {
      var box = document.createElement("div");
      box.className = "kids";
      kids.forEach(function (kv) {
        box.appendChild(nodeLabel(kv[0], kv[1], activeNode, doneNodes));
      });
      wrap.appendChild(box);
    }
    return wrap;
  }

  function renderAst() {
    var host = $("ast");
    host.innerHTML = "";
    var c = curCase();
    if (fellBack(c)) {
      var hasField = !!(c && c.fallbackPrior);
      host.innerHTML = '<div class="fallback-box"><b>' +
        (c.program ? "Program rejected." : "No legal program.") + "</b> " +
        (c.program
          ? "The synthesiser produced this program, but the pipeline did not execute it — the " +
            "well-formedness checker or the executor turned it down, so it is shown read-only " +
            "rather than acted out here."
          : "The synthesiser did not produce a well-formed program for this expression, so the " +
            "checker rejected it before execution.") +
        ' The pipeline fell back to the field-only selector on the same candidates; the mask ' +
        'shown is that fallback’s real output (IoU ' + c.iou + ').' +
        (hasField ? ' Tick <b>field</b> to see the dense field that selector actually used.' : "") +
        "</div>" +
        (c.program ? '<code class="prog">' + G.programString(c.program) + "</code>" : "");
      return;
    }
    var active = state.steps[state.step - 1] ? state.steps[state.step - 1].node : null;
    // nodes already evaluated at this point in the trace -- how far execution has got
    var done = [];
    for (var i = 0; i < state.step && i < state.steps.length; i++) done.push(state.steps[i].node);
    host.appendChild(nodeLabel(state.program, state.pristine, active, done));

    var note = $("editedNote");
    if (edited()) {
      note.classList.remove("hidden");
      note.innerHTML = "Program edited. The selection below is recomputed live; the mask overlay " +
        "still shows the original run’s output.";
    } else {
      note.classList.add("hidden");
    }
  }

  /* ---------- execution ---------- */

  function reexecute(keepStep) {
    var c = curCase();
    if (!c || !state.program || fellBack(c)) {
      state.steps = []; state.step = 0; renderAll(); return;
    }
    var res = G.runTrace(state.program, c.detections);
    state.steps = res.steps;
    state.step = keepStep ? Math.min(state.step, state.steps.length) : state.steps.length;
    renderAll();
  }

  /* The scored set as of the current step. Null at step 0: no operator has run yet, so what
     stands is the raw detector output, not the result of the first node. */
  function currentScored() {
    if (!state.steps.length || state.step <= 0) return null;
    return state.steps[Math.min(state.step - 1, state.steps.length - 1)];
  }

  /* The single selected box, by the same rule the executor's terminal step uses: the first
     strict maximum. Ties therefore resolve to one winner rather than lighting up several. */
  function winnerBox(scored) {
    var win = null;
    for (var i = 0; i < scored.length; i++) {
      if (!win || scored[i].score > win.score) win = scored[i];
    }
    // No score>0 gate: the executor's terminal step takes the top of the ranked set even when an
    // unsatisfiable constraint zeroed every candidate, and the page must name the same box the
    // pipeline named rather than claim there was no answer.
    return win ? win.box : null;
  }

  /* ---------- canvas ---------- */

  var img = new Image();
  var maskImg = new Image();
  var imgReady = false, maskReady = false;

  function draw() {
    var c = curCase();
    var cv = $("canvas");
    if (!c || !imgReady) return;
    var W = img.naturalWidth, H = img.naturalHeight;
    var dpr = window.devicePixelRatio || 1;
    cv.width = W * dpr; cv.height = H * dpr;
    cv.style.aspectRatio = W + " / " + H;
    var g = cv.getContext("2d");
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);
    g.drawImage(img, 0, 0, W, H);

    if (state.showMask && maskReady) {
      g.globalAlpha = 0.9;
      g.drawImage(maskImg, 0, 0, W, H);
      g.globalAlpha = 1;
    }

    var step = currentScored();

    if (state.showField) {
      if (step && step.op === "filter") {
        drawField(g, step.node, W, H);
      } else if (fellBack(c) && c.fallbackPrior) {
        drawPrior(g, c.fallbackPrior, W, H);      // the V1 field-only selector's real field
      }
    }

    var boxes = cands(c);
    var live = step ? step.scored : boxes.map(function (b) { return { box: b, score: 1 }; });
    var maxScore = live.reduce(function (m, r) { return Math.max(m, r.score); }, 0) || 1;
    var isFinal = state.step >= state.steps.length && state.steps.length > 0;
    var winBox = isFinal ? winnerBox(live) : null;

    // anchor-class detections first, muted: they are context, not the candidate set
    anchorBoxes(c).forEach(function (b) {
      g.lineWidth = 1.5;
      g.setLineDash([4, 3]);
      g.strokeStyle = "rgba(120,130,150,0.55)";
      g.strokeRect(b[0] * W, b[1] * H, (b[2] - b[0]) * W, (b[3] - b[1]) * H);
      g.setLineDash([]);
    });

    // every detected candidate, dimmed if the current step dropped it
    boxes.forEach(function (b, i) {
      var rec = live.find(function (r) { return r.box === b; });
      var px = [b[0] * W, b[1] * H, b[2] * W, b[3] * H];
      var alive = !!rec && rec.score > 0;
      var rel = rec ? rec.score / maxScore : 0;
      var isWin = !!winBox && !!rec && rec.box === winBox;
      g.lineWidth = state.hover === i ? 4 : (isWin ? 3.5 : 2);
      g.strokeStyle = isWin ? "#12B886"
        : alive ? "rgba(232,98,74," + (0.35 + 0.65 * rel).toFixed(3) + ")"
        : "rgba(160,160,170,0.45)";
      g.strokeRect(px[0], px[1], px[2] - px[0], px[3] - px[1]);

      if (alive || state.hover === i) {
        var tag = String(i);
        g.font = "600 13px 'Fira Code', monospace";
        var tw = g.measureText(tag).width + 8;
        g.fillStyle = isWin ? "#12B886" : "rgba(232,98,74,0.92)";
        g.fillRect(px[0], Math.max(px[1] - 17, 0), tw, 17);
        g.fillStyle = "#fff";
        g.fillText(tag, px[0] + 4, Math.max(px[1] - 4, 13));
      }
    });
  }

  /* Deep teal -> teal -> amber, on the page's own accent ramp. A single translucent tint washed
     out against dark aerial imagery, so this lifts the mid-tones (gamma) and keeps a visible
     floor, letting the field's shape read rather than just its peak. */
  function fieldColour(v) {
    var x = Math.max(0, Math.min(1, v));
    var t = Math.pow(x, 0.55);              // lift the mid-tones hard: the field's SHAPE has to read
    var r, g, b, u;
    if (t < 0.5) {                          // page teal -> the bright cyan the teaser legend uses
      u = t / 0.5;
      r = 12 + (25 - 12) * u;
      g = 124 + (195 - 124) * u;
      b = 140 + (214 - 140) * u;
    } else {                                // -> amber, this page's other accent
      u = (t - 0.5) / 0.5;
      r = 25 + (240 - 25) * u;
      g = 195 + (185 - 195) * u;
      b = 214 + (42 - 214) * u;
    }
    // Exactly zero stays nearly clear, so the wrong side of a half-plane keeps its detail and the
    // field's boundary reads as an edge. The peak is deliberately NOT opaque: a directional field
    // is strongest exactly where its referent sits, and burying the box the program is about to
    // select would defeat the panel. Hue carries the strength; alpha only has to make it legible.
    var a = x <= 0.001 ? 0.10 : 0.26 + 0.46 * t;
    return [r, g, b, 255 * a];
  }

  function paintGrid(g, values, n, W, H) {
    var off = document.createElement("canvas");
    off.width = n; off.height = n;
    var og = off.getContext("2d");
    var im = og.createImageData(n, n);
    for (var k = 0; k < n * n; k++) {
      var c = fieldColour(values[k]);
      im.data[k * 4] = c[0];
      im.data[k * 4 + 1] = c[1];
      im.data[k * 4 + 2] = c[2];
      im.data[k * 4 + 3] = c[3];
    }
    og.putImageData(im, 0, 0);
    g.imageSmoothingEnabled = true;
    g.drawImage(off, 0, 0, W, H);
  }

  /* Geometric field for the active filter, sampled on a coarse grid and stretched. */
  function drawField(g, node, W, H) {
    var c = curCase();
    var pred = G.PRED_VALUE[node.pred];
    if (!pred) return;
    var anchors = G.resolveAnchor(node.anchor, c.detections);
    if (!anchors.length) anchors = [G.IMAGE_BOX];
    var N = 96, vals = new Array(N * N);
    for (var y = 0; y < N; y++) {
      for (var x = 0; x < N; x++) {
        var fx = (x + 0.5) / N, fy = (y + 0.5) / N, v = 0;
        for (var a = 0; a < anchors.length; a++) {
          v = Math.max(v, G.fieldAt(pred, anchors[a], fx, fy));
        }
        vals[y * N + x] = v;
      }
    }
    // Normalise to the field's own maximum before colouring. A directional ramp against the image
    // frame tops out at 0.5 (the boundary is the centre, the ramp is divided by the full width),
    // so painting absolute values turns half the frame into one flat wash with no gradient to
    // read. The fallback prior arrives from the server normalised the same way.
    var mx = 0;
    for (var i = 0; i < vals.length; i++) if (vals[i] > mx) mx = vals[i];
    if (mx > 0) for (var j = 0; j < vals.length; j++) vals[j] /= mx;
    paintGrid(g, vals, N, W, H);
  }

  /* The V1 fallback's dense field, dumped from the pipeline itself (not recomputed here). */
  function drawPrior(g, prior, W, H) {
    paintGrid(g, prior.grid, prior.n, W, H);
  }

  /* ---------- candidate inspector ---------- */

  function renderCands() {
    var c = curCase();
    var host = $("cands");
    var step = currentScored();
    var boxes = cands(c);

    if (fellBack(c)) {
      host.innerHTML = '<div class="fallback-box">The field-only fallback selected the referent ' +
        'without an executable program, so there is no trace to step through. ' +
        (c.fallbackPrior
          ? 'The dense field it scored these candidates with is dumped from the pipeline and drawn ' +
            'on the image when <b>field</b> is ticked.'
          : 'That selector does score these candidates with a dense field, but the field is driven ' +
            'by the V1 relation schema, which this case does not carry — so none is drawn ' +
            'here rather than a guessed one.') +
        ' The mask is the fallback’s real output.</div>';
      $("stepLabel").innerHTML = "";
      $("candHint").textContent = "";
      return;
    }

    // At step 0 the detector output stands unscored -- nothing has been dropped yet.
    var live = step ? step.scored : boxes.map(function (b) { return { box: b, score: 1 }; });
    var maxScore = live.reduce(function (m, r) { return Math.max(m, r.score); }, 0) || 1;
    var isFinal = state.step >= state.steps.length;
    var winBox = isFinal ? winnerBox(live) : null;

    var rows = boxes.map(function (b, i) {
      var rec = live.find(function (r) { return r.box === b; });
      return { i: i, box: b, score: rec ? rec.score : null };
    });
    rows.sort(function (a, b) {
      if (a.score === null && b.score === null) return a.i - b.i;
      if (a.score === null) return 1;
      if (b.score === null) return -1;
      return b.score - a.score || a.i - b.i;
    });

    // An edit can make the program return nothing -- an out-of-range Nth, say. That is a legal
    // program with an empty result, which is exactly what the reliability ladder catches.
    // Every candidate scored 0: the constraint was unsatisfiable (an anchor class the detector
    // never found, say). The executor still returns a referent, so say why it looks arbitrary.
    var zeroNote = (isFinal && live.length && maxScore === 0)
      ? '<div class="fallback-box note-zero" style="margin-bottom:.7rem"><b>Constraint unsatisfiable.</b> ' +
        'Every candidate scored zero — the anchor this program refers to was never detected — so ' +
        'the selection below is the executor returning the head of an unranked set rather than a ' +
        'geometric decision.</div>'
      : "";

    // Several candidates share the top score. Nothing in the program separated them, so the
    // winner is just the head of the set -- which is the detector's own order, most confident
    // first. Without saying so, picking #0 over #1 looks arbitrary.
    var tiedCount = live.filter(function (r) { return r.score === maxScore; }).length;
    var tieNote = (isFinal && maxScore > 0 && tiedCount > 1)
      ? '<div class="fallback-box note-tie" style="margin-bottom:.7rem"><b>Tie at the top.</b> ' +
        tiedCount + ' candidates share the highest score' +
        (state.program && state.program.op === "select"
          ? ' — a bare Select scores every detection 1.0, with no operator to separate them'
          : '') +
        '. The executor returns the head of the set, which is the detector’s ranking: the ' +
        'detector confidence on each row is what actually breaks this tie.</div>'
      : "";

    var emptyNote = (isFinal && !live.length)
      ? '<div class="fallback-box note-empty" style="margin-bottom:.7rem"><b>Empty result.</b> This program ' +
        'is well-formed but selects nothing, so the pipeline would fall back to the field-only ' +
        'selector on these same candidates rather than forfeit an answer.</div>'
      : "";

    // Two numbers per row, and without saying which is which the reader cannot tell why a
    // candidate won -- detector confidence and the executor's score often disagree.
    var legend = rows.length
      ? '<div class="cand-legend"><span>det</span> = detector confidence &middot; ' +
        "<span>score</span> = candidate score after this step</div>"
      : "";

    host.innerHTML = zeroNote + tieNote + emptyNote + legend + rows.map(function (r) {
      var dropped = r.score === null;
      var isWin = !!winBox && r.box === winBox;
      var pct = dropped ? 0 : Math.max(2, (r.score / maxScore) * 100);
      var det = typeof r.box[4] === "number" ? r.box[4].toFixed(2) : null;
      return '<div class="cand' + (isWin ? " win" : "") + (dropped ? " out" : "") +
        (state.hover === r.i ? " hover" : "") + '" data-i="' + r.i + '">' +
        '<div class="row"><span class="tag">' + r.i + "</span>" +
        "<span>" + (dropped ? "dropped by this operator" : (isWin ? "selected" : "candidate")) + "</span>" +
        (det ? '<span class="det" title="detector confidence">det ' + det + "</span>" : "") +
        '<span class="val">' + (dropped ? "&mdash;" : r.score.toFixed(4)) + "</span></div>" +
        '<div class="track"><div class="fill" style="width:' + pct + '%"></div></div></div>';
    }).join("");

    Array.prototype.forEach.call(host.querySelectorAll(".cand"), function (el) {
      el.onmouseenter = function () { state.hover = +el.dataset.i; renderCands(); draw(); };
      el.onmouseleave = function () { state.hover = -1; renderCands(); draw(); };
    });

    var n = state.steps.length;
    var opName = step ? step.op : "—";
    $("stepLabel").innerHTML = "step <b>" + state.step + " / " + n + "</b> &nbsp; " +
      (step ? "after <b>" + opName + "</b> &rarr; " + step.scored.length + " live" : "not started") +
      (step && step.note ? '<br><span class="passthrough">' + step.note + "</span>" : "");
    $("candHint").textContent = isFinal ? "final" : "mid-execution";
  }

  /* ---------- wiring ---------- */

  function renderAll() {
    var c = curCase();
    if (!c) return;
    renderFilters();
    renderCases();
    renderExpression(c);
    renderAst();
    renderCands();
    draw();
    var ran = !!state.program && !fellBack(c);
    $("btnBack").disabled = state.step <= 0 || !ran;
    $("btnStep").disabled = !ran || state.step >= state.steps.length;
    $("btnRun").disabled = !ran || state.step >= state.steps.length;

    // A field belongs to a filter node. Name the actual reason none is drawn rather than
    // borrowing another operator's mechanism.
    var stepNow = currentScored();
    var hasFilter = state.steps.some(function (s) { return s.op === "filter"; });
    var hint;
    if (fellBack(c)) {
      hint = !state.showField ? "detector candidates"
        : c.fallbackPrior ? "field-only fallback — the selector's real field"
        : "field-only fallback — field not exported";
    } else if (state.showField && stepNow && stepNow.op === "filter") {
      hint = "geometric field";
    } else if (state.showField) {
      hint = hasFilter ? "no field at this step" : "no dense field here — extremal softmax";
    } else {
      hint = "scored candidate set";
    }
    $("stageHint").textContent = hint;
  }

  function loadCase(id) {
    var c = TRACES.find(function (x) { return x.id === id; });
    if (!c) return;
    state.caseId = id;
    state.pristine = c.program ? clone(c.program) : null;
    state.program = c.program ? clone(c.program) : null;
    state.hover = -1;
    state.step = 0;
    imgReady = false; maskReady = false;
    img.onload = function () { imgReady = true; draw(); };
    img.src = BASE + c.img.input;
    maskImg.onload = function () { maskReady = true; draw(); };
    maskImg.src = BASE + c.img.mask;
    if (state.program && !fellBack(c)) {
      var res = G.runTrace(state.program, c.detections);
      state.steps = res.steps;
      // Open before the first operator: the detector output, with the answer not yet given away.
      state.step = 0;
    } else {
      state.steps = [];      // the pipeline never executed this one; nothing to step through
    }
    renderAll();
  }

  $("btnStep").onclick = function () {
    if (state.step < state.steps.length) { state.step++; renderAll(); }
  };
  $("btnBack").onclick = function () {
    if (state.step > 0) { state.step--; renderAll(); }
  };
  $("btnRun").onclick = function () { state.step = state.steps.length; renderAll(); };
  $("btnReset").onclick = function () {
    var c = curCase();
    state.program = c.program ? clone(c.program) : null;
    state.step = 0;
    reexecute(true);
  };
  $("toggleField").onchange = function (e) {
    state.showField = e.target.checked;
    // The field is drawn for the filter being executed, so jump to the first filter rather than
    // leaving the reader on a step that has no field to show.
    var here = currentScored();
    if (state.showField && state.program && !(here && here.op === "filter")) {
      for (var k = 0; k < state.steps.length; k++) {
        if (state.steps[k].op === "filter") { state.step = k + 1; break; }
      }
    }
    renderAll();
  };
  $("toggleMask").onchange = function (e) { state.showMask = e.target.checked; draw(); };

  document.addEventListener("keydown", function (e) {
    if (e.key === "ArrowRight") $("btnStep").click();
    if (e.key === "ArrowLeft") $("btnBack").click();
  });

  /* The Program Library on the project page is an index into this panel, so it needs a way in. */
  window.GeoInspector = {
    open: function (id) {
      if (!TRACES.some(function (c) { return c.id === id; })) return false;
      state.filter = "all";          // the card may name a case the current filter hides
      loadCase(id);
      return true;
    },
  };

  if (TRACES.length) loadCase(TRACES[0].id);
})();
