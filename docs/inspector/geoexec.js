/* GeoSelect executor -- browser port of geoselect_v2/executor + geogrounder/reasoning.
 *
 * Faithful to the frozen config (geoselect_v2/configs/v2_frozen.yaml):
 *   score_method=centroid, reference=centroid, graded_direction=true, direction_exponent=1.0,
 *   center_sigma_frac=0.25, near_scale=1.5, anchor_mode=marginalize (OR over anchor instances).
 *   argmax/argmin RESCORE (replace, not multiply); nth keeps the incoming score.
 *
 * Boxes here are normalised xyxy in [0,1]; fields are evaluated in that same unit square, which
 * is equivalent to the pixel-space computation for square images and for every predicate that
 * normalises by W or H. Verified against the Python reference on all exported cases.
 *
 * Runs in the browser (window.GeoExec) and under node (module.exports) so the port can be tested.
 */
(function (root) {
  "use strict";

  var CFG = {
    directionExponent: 1.0,
    centerSigmaFrac: 0.25,
    nearScale: 1.5,
  };

  var PRED_VALUE = {
    LEFT: "west", RIGHT: "east", TOP: "north", BOTTOM: "south",
    UL: "northwest", UR: "northeast", LL: "southwest", LR: "southeast",
    CENTER: "center", NEAR: "near",
  };
  var DIAGONAL = {
    northwest: ["north", "west"], northeast: ["north", "east"],
    southwest: ["south", "west"], southeast: ["south", "east"],
  };

  var IMAGE_BOX = [0, 0, 1, 1];

  function centre(b) { return [0.5 * (b[0] + b[2]), 0.5 * (b[1] + b[3])]; }
  function extent(b) { return [Math.max(Math.abs(b[2] - b[0]), 1e-6), Math.max(Math.abs(b[3] - b[1]), 1e-6)]; }

  /* Dense prior value for `pred` relative to `anchor`, sampled at (x, y).
     Evaluated analytically at the point -- centroid scoring only ever reads one pixel. */
  function fieldAt(pred, anchor, x, y) {
    var c = centre(anchor), cx = c[0], cy = c[1];

    function cardinal(d) {
      var s;
      if (d === "north") s = cy - y;
      else if (d === "south") s = y - cy;
      else if (d === "west") s = cx - x;
      else s = x - cx;
      var v = Math.min(Math.max(s, 0), 1);          // L = 1 in normalised coords
      return CFG.directionExponent === 1 ? v : Math.pow(v, CFG.directionExponent);
    }

    if (pred === "center") {
      var sigma = Math.max(CFG.centerSigmaFrac, 1e-9);
      var d2 = (x - cx) * (x - cx) + (y - cy) * (y - cy);
      return Math.exp(-d2 / (2 * sigma * sigma));
    }
    if (pred === "near") {
      var e = extent(anchor);
      var L = Math.max(CFG.nearScale * Math.max(0.5 * (e[0] + e[1]), 1e-6), 1e-9);
      var dx = Math.max(anchor[0] - x, 0, x - anchor[2]);
      var dy = Math.max(anchor[1] - y, 0, y - anchor[3]);
      var d = Math.hypot(dx, dy);
      return Math.exp(-(d * d) / (2 * L * L));
    }
    if (DIAGONAL[pred]) {
      var pair = DIAGONAL[pred];
      return Math.min(cardinal(pair[0]), cardinal(pair[1]));   // 'min' t-norm (frozen)
    }
    return cardinal(pred);
  }

  /* score_boxes(method='centroid') + prior_or marginalisation over anchor instances. */
  function scoreCentroid(box, pred, anchors) {
    var c = centre(box), best = 0;
    for (var i = 0; i < anchors.length; i++) {
      var v = fieldAt(pred, anchors[i], c[0], c[1]);
      if (v > best) best = v;
    }
    return best;
  }

  function axisValue(b, axis) {
    var c = centre(b);
    if (axis === "AREA") return Math.max(0, b[2] - b[0]) * Math.max(0, b[3] - b[1]);
    if (axis === "X") return c[0];
    if (axis === "Y") return c[1];
    if (axis === "DIAG_UL_LR") return c[0] + c[1];
    if (axis === "DIAG_UR_LL") return -c[0] + c[1];
    throw new Error("unknown axis " + axis);
  }

  /* Softmax over the candidate set, temperature from candidate spacing (scale-free). */
  function extremalScores(boxes, axis, maximize) {
    var n = boxes.length;
    if (n === 0) return [];
    if (n === 1) return [1];
    var vals = boxes.map(function (b) { return axisValue(b, axis); });
    var mean = vals.reduce(function (a, b) { return a + b; }, 0) / n;
    var varr = vals.reduce(function (a, v) { return a + (v - mean) * (v - mean); }, 0) / n;
    var std = Math.sqrt(varr);
    var scale = std >= 1e-9 ? std : (Math.max.apply(null, vals) - Math.min.apply(null, vals));
    var beta = scale < 1e-9 ? 0 : 1 / scale;
    var sign = maximize ? 1 : -1;
    var logits = vals.map(function (v) { return sign * beta * v; });
    var m = Math.max.apply(null, logits);
    var exp = logits.map(function (l) { return Math.exp(l - m); });
    var tot = exp.reduce(function (a, b) { return a + b; }, 0);
    return exp.map(function (e) { return e / tot; });
  }

  function gap(a, b) {
    var dx = Math.max(a[0] - b[2], b[0] - a[2], 0);
    var dy = Math.max(a[1] - b[3], b[1] - a[3], 0);
    return Math.hypot(dx, dy);
  }
  function charLen(b) { var e = extent(b); return 0.5 * (e[0] + e[1]); }
  function interArea(a, b) {
    return Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0]))
         * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
  }
  function areaOf(b) { return Math.max((b[2] - b[0]) * (b[3] - b[1]), 1e-9); }

  function relationScore(rel, cand, anchorsA) {
    if (!anchorsA || !anchorsA.length) return 0;
    var vals = anchorsA.map(function (a) {
      if (rel === "NEAR") {
        var L = CFG.nearScale * charLen(a), d = gap(cand, a);
        return Math.exp(-(d * d) / (2 * L * L));
      }
      if (rel === "ADJACENT") {
        var L2 = 0.25 * charLen(a), d2 = gap(cand, a);
        return Math.exp(-(d2 * d2) / (2 * L2 * L2));
      }
      if (rel === "CONTAINS") return interArea(cand, a) / areaOf(a);
      if (rel === "INSIDE") return interArea(cand, a) / areaOf(cand);
      throw new Error("unsupported relation " + rel);
    });
    return Math.max.apply(null, vals);
  }

  /* Anchor -> boxes, matching the executor's _resolve_anchor:
     IMAGE              -> the whole frame;
     a bare Select      -> every detected instance (the field is OR-marginalised over them);
     anything constrained (a nested Filter/Argmax/...) -> its top-1 only, because such an anchor
     names ONE object -- resolving it to every instance mis-selects on nested anchors. */
  function resolveAnchor(anchor, dets, trace) {
    if (!anchor || anchor === "image") return [IMAGE_BOX];
    var scored = execute(anchor, dets, trace);
    if (!scored.length) return [];
    if (anchor.op === "select") return scored.map(function (r) { return r.box; });
    var best = scored[0];
    for (var i = 1; i < scored.length; i++) {
      if (scored[i].score > best.score) best = scored[i];
    }
    return [best.box];
  }

  /* ---- execution ------------------------------------------------------------------ */

  /* Evaluate `node` -> [{box, score}]. `trace`, when given, receives one entry per node in
     post-order (leaves first), mirroring the Python executor's trace hook. */
  function execute(node, dets, trace) {
    if (!node) throw new Error("no program");
    var op = node.op, out, note = null;

    if (op === "select") {
      // Select queries the detector for ONE noun phrase, so each phrase has its own candidate
      // pool. An anchor naming a different class therefore resolves against that class's boxes.
      out = ((dets && dets[node.type]) || []).map(function (b) { return { box: b, score: 1 }; });
    } else if (op === "filter") {
      var scored = execute(node.child, dets, trace);
      if (!scored.length) { out = []; }
      else {
        var pred = PRED_VALUE[node.pred];
        var anchors = resolveAnchor(node.anchor, dets, trace);
        if (!anchors.length) {
          // A soft dense field against an absent anchor is not a failure: the executor lets
          // the child scores through untouched rather than zeroing the candidate set.
          anchors = null;
          note = "anchor resolved to nothing — filter passed through";
        }
        out = anchors
          ? scored.map(function (r) { return { box: r.box, score: r.score * scoreCentroid(r.box, pred, anchors) }; })
          : scored;
      }
    } else if (op === "argmax" || op === "argmin") {
      var sc = execute(node.child, dets, trace);
      if (!sc.length) { out = []; }
      else {
        var live = sc.filter(function (r) { return r.score > 0; });
        if (!live.length) live = sc.slice();
        var ex = extremalScores(live.map(function (r) { return r.box; }), node.axis, op === "argmax");
        out = live.map(function (r, i) { return { box: r.box, score: ex[i] }; });
      }
    } else if (op === "nth") {
      var s2 = execute(node.child, dets, trace);
      if (!s2.length) { out = []; }
      else {
        var idx = s2.map(function (_, i) { return i; });
        idx.sort(function (i, j) {
          var d = axisValue(s2[i].box, node.axis) - axisValue(s2[j].box, node.axis);
          return d !== 0 ? d : j - i;
        });
        out = (node.n >= 0 && node.n < idx.length) ? [s2[idx[node.n]]] : [];
      }
    } else if (op === "restrict_count") {
      var s3 = execute(node.child, dets, trace);
      if (node.k >= s3.length) out = s3;
      else {
        var ord = s3.map(function (_, i) { return i; })
          .sort(function (i, j) { return (s3[j].score - s3[i].score) || (i - j); })
          .slice(0, node.k).sort(function (a, b) { return a - b; });
        out = ord.map(function (i) { return s3[i]; });
      }
    } else if (op === "relate") {
      var s4 = execute(node.child, dets, trace);
      if (!s4.length) { out = []; }
      else {
        var anc = resolveAnchor(node.anchor, dets, trace);
        out = s4.map(function (r) {
          return { box: r.box, score: r.score * relationScore(node.rel, r.box, anc) };
        });
      }
    } else {
      throw new Error("unhandled op " + op);
    }

    if (trace) {
      trace.push({
        op: op, node: node, note: note,
        scored: out.map(function (r) { return { box: r.box, score: r.score }; }),
      });
    }
    return out;
  }

  /* Full post-order trace plus the winning box, for the stepper UI. */
  function runTrace(program, dets) {
    var trace = [];
    var out = execute(program, dets, trace);
    var win = null;
    for (var i = 0; i < out.length; i++) if (!win || out[i].score > win.score) win = out[i];
    return { steps: trace, result: out, winner: win };
  }

  /* One-line rendering of a program, matching the paper's notation. */
  function programString(p) {
    if (!p) return "—";
    var anc = function (a) { return (a && typeof a === "object") ? programString(a) : "IMAGE"; };
    if (p.op === "select") return 'Select("' + (p.type || "?") + '")';
    var arg = p.child ? programString(p.child) : "";
    if (p.op === "filter") return "Filter(" + arg + ", " + p.pred + ", " + anc(p.anchor) + ")";
    if (p.op === "argmax" || p.op === "argmin") {
      return (p.op === "argmax" ? "Argmax" : "Argmin") + "(" + arg + ", " + p.axis + ")";
    }
    if (p.op === "nth") return "Nth(" + arg + ", " + p.n + ", " + p.axis + ")";
    if (p.op === "restrict_count") return "RestrictCount(" + arg + ", " + p.k + ")";
    if (p.op === "relate") return "Relate(" + arg + ", " + p.rel + ", " + anc(p.anchor) + ")";
    return p.op + "(" + arg + ")";
  }

  var API = {
    CFG: CFG, PRED_VALUE: PRED_VALUE, IMAGE_BOX: IMAGE_BOX,
    fieldAt: fieldAt, scoreCentroid: scoreCentroid, axisValue: axisValue,
    resolveAnchor: resolveAnchor,
    extremalScores: extremalScores, relationScore: relationScore,
    execute: execute, runTrace: runTrace, programString: programString,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.GeoExec = API;
})(typeof window !== "undefined" ? window : globalThis);
