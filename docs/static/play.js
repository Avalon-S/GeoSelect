/* GeoSelect project page: the opening interaction, "write the rule, then move the board".
   A procedurally drawn aerial scene. The reader picks a referring expression; the program the
   paper's synthesis prompt maps it to (the phrase-to-operator table in the appendix) is executed
   over the drawn boxes by the same browser port of the executor that the Execution Inspector runs
   (inspector/geoexec.js), round by round. Any box of the queried class, and the bridge, can be
   dragged: the program stays fixed and the selection follows the geometry.
   The scene, its boxes and the detector confidences are an illustration. The numbers in the
   side panel are the paper's (selector comparison on RRSIS-D val, operator gain on RISBench test).
   Nothing animates under prefers-reduced-motion. */
(function () {
  "use strict";
  var EX = window.GeoExec;
  var cv = document.getElementById("playCanvas");
  if (!EX || !cv || !cv.getContext) return;

  var $ = function (id) { return document.getElementById(id); };
  var hudEl = $("playHud"), progEl = $("playProg"), roundsEl = $("playRounds"), chipsEl = $("playChips"),
      panelEl = $("playPanel"), judgeBtn = $("playJudge"), replayBtn = $("playReplay"), shuffleBtn = $("playShuffle");
  var reduce = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  var W = 1600, H = 900, TAU = Math.PI * 2;
  var STEP_MS = 760;
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function ease(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }
  function rng(seed) {                       // mulberry32: the same seed draws the same scene
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* data colours: fixed across the two themes, as in the paper's figures and the Inspector */
  var ORD = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"];
  var COL = { cand: "#E8624A", win: "#12B886", mask: "#19C3D6", gold: "#E0AE1F",
              lo: [12, 124, 140], hi: [240, 185, 42] };
  var theme = {};
  function readTheme() {
    var s = getComputedStyle(document.documentElement);
    var v = function (n, d) { return (s.getPropertyValue(n) || "").trim() || d; };
    theme = { ink: v("--indigo", "#16171C"), paper: v("--white", "#FFFFFF"),
              night: document.documentElement.dataset.theme === "night" };
  }

  /* ------------------------------------------------------------------ the scene */
  function riverX(y) { return 330 + 34 * Math.sin(y / 150 + 0.6); }
  var RIVER_W = 118;

  function paintBackground(g) {
    var R = rng(7), i, x, y;
    g.fillStyle = "#A6B383"; g.fillRect(0, 0, W, H);
    // farmland west of the river
    var cols = ["#B9C089", "#A2B276", "#C2C08E", "#9DAE70"];
    for (i = 0; i < 7; i++) {
      var fy = i * 130 - 10, fh = 120;
      g.fillStyle = cols[i % 4]; g.fillRect(14, fy + 8, 232, fh);
      g.strokeStyle = "rgba(255,255,255,.18)"; g.lineWidth = 2;
      for (x = 24; x < 240; x += 12) { g.beginPath(); g.moveTo(x, fy + 12); g.lineTo(x, fy + fh); g.stroke(); }
    }
    // the river and its banks
    g.lineCap = "round"; g.lineJoin = "round";
    var path = function () { g.beginPath(); for (y = -40; y <= H + 40; y += 10) { if (y === -40) g.moveTo(riverX(y), y); else g.lineTo(riverX(y), y); } };
    path(); g.strokeStyle = "#7FA07A"; g.lineWidth = RIVER_W + 34; g.stroke();
    path(); g.strokeStyle = "#4C8A9C"; g.lineWidth = RIVER_W; g.stroke();
    path(); g.strokeStyle = "rgba(255,255,255,.07)"; g.lineWidth = RIVER_W * 0.45; g.stroke();
    // trees on both banks
    for (i = 0; i < 70; i++) {
      y = R() * H; var side = R() < 0.5 ? -1 : 1;
      x = riverX(y) + side * (RIVER_W / 2 + 22 + R() * 26);
      g.fillStyle = "rgba(0,0,0,.16)"; g.beginPath(); g.arc(x + 3, y + 4, 9 + R() * 5, 0, TAU); g.fill();
      g.fillStyle = R() < 0.5 ? "#5E8248" : "#6F9152"; g.beginPath(); g.arc(x, y, 8 + R() * 5, 0, TAU); g.fill();
    }
    // tank-farm pad, courts lawn, apron
    g.fillStyle = "#BDB8A6"; roundRect(g, 452, 30, 590, 438, 10); g.fill();
    g.strokeStyle = "rgba(90,86,74,.35)"; g.lineWidth = 3;
    for (i = 0; i < 4; i++) { g.beginPath(); g.moveTo(470, 120 + i * 100); g.lineTo(1024, 110 + i * 102); g.stroke(); }
    g.fillStyle = "#8DAA74"; roundRect(g, 1086, 40, 500, 300, 10); g.fill();
    g.fillStyle = "#A9AAA5"; g.fillRect(440, 520, W - 440, H - 520);
    g.strokeStyle = "rgba(224,192,74,.75)"; g.lineWidth = 3; g.setLineDash([22, 14]);
    g.beginPath(); g.moveTo(450, 560); g.lineTo(W, 560); g.stroke();
    for (x = 560; x < W; x += 220) { g.beginPath(); g.moveTo(x, 560); g.lineTo(x + 40, H); g.stroke(); }
    g.setLineDash([]);
    // roads: one east-west, one north-south between the pad and the courts
    g.fillStyle = "#86898B"; g.fillRect(440, 478, W - 440, 34); g.fillRect(1050, 0, 30, 478);
    g.strokeStyle = "rgba(242,242,236,.85)"; g.lineWidth = 2; g.setLineDash([18, 16]);
    g.beginPath(); g.moveTo(446, 495); g.lineTo(W, 495); g.stroke();
    g.beginPath(); g.moveTo(1065, 0); g.lineTo(1065, 478); g.stroke(); g.setLineDash([]);
    // buildings south of the courts
    var bx = [1100, 1230, 1388, 1500], bw = [112, 140, 96, 82];
    for (i = 0; i < 4; i++) {
      g.fillStyle = "rgba(0,0,0,.18)"; g.fillRect(bx[i] + 6, 362 + 6, bw[i], 92);
      g.fillStyle = i % 2 ? "#D9D6CD" : "#CBC7BC"; g.fillRect(bx[i], 362, bw[i], 92);
      g.strokeStyle = "rgba(0,0,0,.12)"; g.lineWidth = 2; g.strokeRect(bx[i] + 1, 363, bw[i] - 2, 90);
    }
  }

  function roundRect(g, x, y, w, h, r) {
    g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
    g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
  }

  /* objects of five classes; positions come from a seed, so Shuffle draws a new arrangement */
  var objs = [], seed = 3;
  function makeObjects(sd) {
    var R = rng(sd), out = [], i, guard;
    function far(list, o, d) { return list.every(function (p) { return Math.hypot(p.x - o.x, p.y - o.y) >= d; }); }
    var tanks = [];
    for (guard = 0; tanks.length < 7 && guard < 5000; guard++) {
      var t = { cls: "storage tank", x: 520 + R() * 470, y: 92 + R() * 330, r: 30 + R() * 14 };
      if (far(tanks, t, 112)) tanks.push(t);
    }
    var courts = [];
    for (i = 0; i < 4; i++) courts.push({ cls: "tennis court", x: 1135 + i * 100 + (R() - 0.5) * 24, y: 190 + (R() - 0.5) * 50, w: 62, h: 116, hue: i % 2 });
    var bridge = { cls: "bridge", y: 300 + R() * 300 };
    bridge.x = riverX(bridge.y);
    var ships = [];
    for (guard = 0; ships.length < 5 && guard < 5000; guard++) {
      var sy = 50 + R() * (H - 100);
      var s = { cls: "ship", y: sy, x: riverX(sy) + (R() - 0.5) * 44, len: 78 + R() * 30, rot: Math.PI / 2 + (R() - 0.5) * 0.35, hue: Math.floor(R() * 3) };
      if (Math.abs(sy - bridge.y) > 88 && ships.every(function (p) { return Math.abs(p.y - sy) >= 118; })) ships.push(s);
    }
    var planes = [];
    for (guard = 0; planes.length < 5 && guard < 5000; guard++) {
      var p = { cls: "airplane", x: 520 + R() * 1020, y: 610 + R() * 220, s: 0.9 + R() * 0.25,
                rot: (R() < 0.5 ? -1 : 1) * Math.PI / 2 + (R() - 0.5) * 0.6 };
      if (far(planes, p, 165)) planes.push(p);
    }
    [tanks, courts, ships, planes].forEach(function (list) {
      list.sort(function (a, b) { return list === ships ? a.y - b.y : a.x - b.x; });
      list.forEach(function (o, k) { o.label = k + 1; o.conf = 0.32 + R() * 0.5; out.push(o); });
    });
    bridge.label = 1; bridge.conf = 0.9; out.push(bridge);
    return out;
  }

  function rotPts(o, pts) {
    var c = Math.cos(o.rot), s = Math.sin(o.rot);
    return pts.map(function (p) { return [o.x + p[0] * c - p[1] * s, o.y + p[0] * s + p[1] * c]; });
  }
  function shipPts(o) { var L = o.len / 2; return rotPts(o, [[L, 0], [L - 18, -11], [-L, -11], [-L, 11], [L - 18, 11]]); }
  function planePts(o) {
    var L = 46 * o.s, S = 43 * o.s;
    return rotPts(o, [[L, 0], [L - 10, -5], [6, -5], [-4, -S], [-14, -S], [-10, -5], [-L + 12, -5], [-L + 4, -16],
                      [-L, -16], [-L + 2, 0], [-L, 16], [-L + 4, 16], [-L + 12, 5], [-10, 5], [-14, S], [-4, S], [6, 5], [L - 10, 5]]);
  }
  function bbox(o) {
    var pts;
    if (o.cls === "storage tank") return [o.x - o.r, o.y - o.r, o.x + o.r, o.y + o.r];
    if (o.cls === "tennis court") return [o.x - o.w / 2, o.y - o.h / 2, o.x + o.w / 2, o.y + o.h / 2];
    if (o.cls === "bridge") return [o.x - 90, o.y - 14, o.x + 90, o.y + 14];
    pts = o.cls === "ship" ? shipPts(o) : planePts(o);
    var xs = pts.map(function (p) { return p[0]; }), ys = pts.map(function (p) { return p[1]; });
    return [Math.min.apply(null, xs) - 3, Math.min.apply(null, ys) - 3, Math.max.apply(null, xs) + 3, Math.max.apply(null, ys) + 3];
  }

  function poly(g, pts) { g.beginPath(); pts.forEach(function (p, i) { if (i) g.lineTo(p[0], p[1]); else g.moveTo(p[0], p[1]); }); g.closePath(); }

  /* draw one object; `fill` (optional) paints its silhouette instead, which is how the mask is shown */
  function drawObject(g, o, fill) {
    if (o.cls === "storage tank") {
      if (fill) { g.fillStyle = fill; g.beginPath(); g.arc(o.x, o.y, o.r, 0, TAU); g.fill(); return; }
      g.fillStyle = "rgba(0,0,0,.2)"; g.beginPath(); g.arc(o.x + 5, o.y + 6, o.r, 0, TAU); g.fill();
      g.fillStyle = "#EEEDE6"; g.beginPath(); g.arc(o.x, o.y, o.r, 0, TAU); g.fill();
      g.strokeStyle = "#B4B1A6"; g.lineWidth = 2.5; g.stroke();
      g.strokeStyle = "rgba(120,118,108,.45)"; g.lineWidth = 2; g.beginPath(); g.arc(o.x, o.y, o.r * 0.62, 0, TAU); g.stroke();
      g.fillStyle = "#B4B1A6"; g.beginPath(); g.arc(o.x, o.y, 3.5, 0, TAU); g.fill();
    } else if (o.cls === "tennis court") {
      var x0 = o.x - o.w / 2, y0 = o.y - o.h / 2;
      if (fill) { g.fillStyle = fill; g.fillRect(x0, y0, o.w, o.h); return; }
      g.fillStyle = o.hue ? "#C4683F" : "#4E9466"; g.fillRect(x0, y0, o.w, o.h);
      g.strokeStyle = "rgba(255,255,255,.92)"; g.lineWidth = 2;
      g.strokeRect(x0 + 7, y0 + 9, o.w - 14, o.h - 18);
      g.beginPath(); g.moveTo(x0 + 7, o.y); g.lineTo(x0 + o.w - 7, o.y); g.stroke();
      g.beginPath(); g.moveTo(o.x, y0 + 30); g.lineTo(o.x, y0 + o.h - 30); g.stroke();
    } else if (o.cls === "ship") {
      var sp = shipPts(o);
      if (fill) { g.fillStyle = fill; poly(g, sp); g.fill(); return; }
      g.save(); g.translate(4, 5); g.fillStyle = "rgba(0,0,0,.22)"; poly(g, sp); g.fill(); g.restore();
      g.fillStyle = ["#D9D6CC", "#8B97A6", "#C7553F"][o.hue]; poly(g, sp); g.fill();
      g.strokeStyle = "rgba(0,0,0,.25)"; g.lineWidth = 1.5; g.stroke();
      var deck = rotPts(o, [[-o.len / 2 + 8, -5], [-o.len / 2 + 30, -5], [-o.len / 2 + 30, 5], [-o.len / 2 + 8, 5]]);
      g.fillStyle = "rgba(255,255,255,.75)"; poly(g, deck); g.fill();
    } else if (o.cls === "airplane") {
      var pp = planePts(o);
      if (fill) { g.fillStyle = fill; poly(g, pp); g.fill(); return; }
      g.save(); g.translate(6, 7); g.fillStyle = "rgba(0,0,0,.22)"; poly(g, pp); g.fill(); g.restore();
      g.fillStyle = "#F4F4F0"; poly(g, pp); g.fill();
      g.strokeStyle = "rgba(60,60,60,.35)"; g.lineWidth = 1.5; g.stroke();
    } else if (o.cls === "bridge") {
      var b = bbox(o);
      if (fill) { g.fillStyle = fill; g.fillRect(b[0], b[1], b[2] - b[0], b[3] - b[1]); return; }
      g.fillStyle = "rgba(0,0,0,.25)"; g.fillRect(b[0] + 4, b[1] + 6, b[2] - b[0], b[3] - b[1]);
      g.fillStyle = "#BDB7A9"; g.fillRect(b[0], b[1], b[2] - b[0], b[3] - b[1]);
      g.fillStyle = "#8E8879"; g.fillRect(b[0], b[1], b[2] - b[0], 3); g.fillRect(b[0], b[3] - 3, b[2] - b[0], 3);
      g.strokeStyle = "rgba(0,0,0,.25)"; g.lineWidth = 1.5; g.setLineDash([6, 8]);
      g.beginPath(); g.moveTo(b[0] + 6, o.y); g.lineTo(b[2] - 6, o.y); g.stroke(); g.setLineDash([]);
    }
  }

  /* ------------------------------------------------------------------ the expressions */
  /* Each program follows the paper's phrase-to-operator table. `frame` names the selector-comparison
     column the expression belongs to; `tag` the operator stratum, when the paper reports one. */
  function sel(t) { return { op: "select", type: t }; }
  var EXPRS = [
    { text: "the airplane on the right", cls: "airplane", frame: "IM",
      prog: { op: "filter", pred: "RIGHT", anchor: "image", child: sel("airplane") } },
    { text: "the leftmost storage tank", cls: "storage tank", frame: "IM", tag: "superlative",
      prog: { op: "argmin", axis: "X", child: sel("storage tank") } },
    { text: "the second court from the left", cls: "tennis court", frame: "IM", tag: "ordinal",
      prog: { op: "nth", n: 1, axis: "X", child: sel("tennis court") } },
    { text: "the ship near the bridge", cls: "ship", frame: "OBJ",
      prog: { op: "relate", rel: "NEAR", anchor: sel("bridge"), child: sel("ship") } },
    { text: "the topmost airplane on the left", cls: "airplane", frame: "COMP",
      prog: { op: "argmin", axis: "Y", child: { op: "filter", pred: "LEFT", anchor: "image", child: sel("airplane") } } },
    { text: "the storage tank in the middle", cls: "storage tank", frame: "IM",
      prog: { op: "filter", pred: "CENTER", anchor: "image", child: sel("storage tank") } },
  ];
  EXPRS.forEach(function (e) { if (e.prog.anchor && typeof e.prog.anchor === "object") e.prog.anchor.isAnchor = true; });

  /* the paper's numbers: selector comparison on RRSIS-D val (n = 1,740) and operator gain on RISBench test */
  var SELECTORS = ["Detector confidence", "GeoRSCLIP", "Ours, fields only", "Ours, full program"];
  var BY_FRAME = {
    IM:   { name: "image-relative", v: [44.47, 41.90, 63.34, 63.24], d: "+18.77" },
    OBJ:  { name: "object-anchored", v: [33.80, 35.23, 40.25, 42.70], d: "+7.47" },
    COMP: { name: "compositional", v: [32.75, 34.57, 39.56, 42.98], d: "+8.41" },
  };
  var BY_TAG = {
    superlative: "On RISBench test the superlative stratum (<b>2,424</b> expressions) goes from <b>49.28</b> with fields only to <b>51.50</b> with the full program on the same candidates: <b>+2.22</b> mIoU, 95% CI [+0.52, +3.84].",
    ordinal: "Ordinal phrases are rare in both benchmarks. <b>Nth</b> is in the DSL because no field can say &ldquo;second&rdquo;.",
  };

  /* ------------------------------------------------------------------ state */
  var cur = 0, run = null, playT0 = 0, stage = 0, nSteps = 0, animating = false, user = false, judge = false;
  var idleTimer = 0, nudge = null, drag = null, S = null, bg = null, field = null, fieldKey = "";

  function dets() {
    var d = {};
    objs.forEach(function (o) {
      var b = bbox(o);
      o.box = [b[0] / W, b[1] / H, b[2] / W, b[3] / H];
      (d[o.cls] = d[o.cls] || []).push(o.box);
    });
    return d;
  }
  function objOf(box) { for (var i = 0; i < objs.length; i++) if (objs[i].box === box) return objs[i]; return null; }

  function execute() {
    run = EX.runTrace(EXPRS[cur].prog, dets());
    nSteps = run.steps.length;
    fieldKey = "";
  }

  /* the last step on the head class at or before `st`, and what each candidate looks like there */
  function headStepAt(st) {
    for (var i = Math.min(st, nSteps - 1); i >= 0; i--) if (!run.steps[i].node.isAnchor) return i;
    return -1;
  }
  function lastHeadStep() { return headStepAt(nSteps - 1); }

  /* ------------------------------------------------------------------ layout and drawing */
  function layout() {
    var r = cv.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (!r.width) return;
    cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr);
    S = { w: r.width, h: r.height, dpr: dpr, sc: r.width / W };
    bg = document.createElement("canvas");
    bg.width = Math.round(W * S.sc * dpr); bg.height = Math.round(H * S.sc * dpr);
    var bgc = bg.getContext("2d"); bgc.setTransform(S.sc * dpr, 0, 0, S.sc * dpr, 0, 0); paintBackground(bgc);
    draw();
  }

  function fieldSpec(st) {
    // the field a reader should see at round `st`: the latest Filter or Relate on the head class
    for (var i = Math.min(st, nSteps - 1); i >= 0; i--) {
      var s = run.steps[i];
      if (s.node.isAnchor) continue;
      if (s.op === "filter" || s.op === "relate") return { i: i, node: s.node };
    }
    return null;
  }
  function buildField(spec) {
    var NX = 128, NY = 72, key = spec.i + "|" + (spec.node.anchor && spec.node.anchor !== "image" ? JSON.stringify(anchorBoxes(spec.node)) : "img");
    if (field && fieldKey === key) return field;
    var anchors = spec.node.op === "relate" ? anchorBoxes(spec.node) : null;
    var pred = EX.PRED_VALUE[spec.node.pred], vals = new Float32Array(NX * NY), mx = 0, i, j;
    for (j = 0; j < NY; j++) for (i = 0; i < NX; i++) {
      var x = (i + 0.5) / NX, y = (j + 0.5) / NY, v;
      if (anchors) v = anchors.length ? EX.relationScore(spec.node.rel, [x, y, x, y], anchors) : 0;
      else v = EX.fieldAt(pred, EX.IMAGE_BOX, x, y);
      vals[j * NX + i] = v; if (v > mx) mx = v;
    }
    var c = document.createElement("canvas"); c.width = NX; c.height = NY;
    var g = c.getContext("2d"), im = g.createImageData(NX, NY);
    for (i = 0; i < NX * NY; i++) {
      var t = mx > 0 ? vals[i] / mx : 0;      // each field normalised by its own maximum before colouring
      im.data[i * 4] = Math.round(COL.lo[0] + (COL.hi[0] - COL.lo[0]) * t);
      im.data[i * 4 + 1] = Math.round(COL.lo[1] + (COL.hi[1] - COL.lo[1]) * t);
      im.data[i * 4 + 2] = Math.round(COL.lo[2] + (COL.hi[2] - COL.lo[2]) * t);
      im.data[i * 4 + 3] = Math.round(255 * (0.08 + 0.52 * t));
    }
    g.putImageData(im, 0, 0);
    field = c; fieldKey = key;
    return c;
  }
  /* the anchor boxes the executor actually used: read them off the anchor's own round in the trace
     (re-resolving would rebuild every box array and break the box -> object identity the drawing relies on) */
  function anchorBoxes(node) {
    if (!node.anchor || node.anchor === "image") return [EX.IMAGE_BOX];
    for (var i = 0; i < run.steps.length; i++) {
      if (run.steps[i].node === node.anchor) return run.steps[i].scored.map(function (r) { return r.box; });
    }
    return [];
  }

  function pill(g, x, y, text, bgc, fg, px) {
    var k = 1 / S.sc, fs = (px || 12) * k;
    g.font = "700 " + fs + "px Inter, system-ui, sans-serif";
    var w = g.measureText(text).width + 12 * k, h = fs + 8 * k;
    x = clamp(x, w / 2 + 2 * k, W - w / 2 - 2 * k); y = clamp(y, h / 2 + 2 * k, H - h / 2 - 2 * k);
    g.fillStyle = bgc; roundRect(g, x - w / 2, y - h / 2, w, h, h / 2); g.fill();
    g.fillStyle = fg; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(text, x, y + 0.5 * k);
  }

  function brackets(g, b, color, gap, len) {
    var k = 1 / S.sc, x0 = b[0] - gap * k, y0 = b[1] - gap * k, x1 = b[2] + gap * k, y1 = b[3] + gap * k, L = len * k;
    g.strokeStyle = color; g.lineWidth = 3.2 * k; g.lineCap = "square";
    g.beginPath();
    g.moveTo(x0, y0 + L); g.lineTo(x0, y0); g.lineTo(x0 + L, y0);
    g.moveTo(x1 - L, y0); g.lineTo(x1, y0); g.lineTo(x1, y0 + L);
    g.moveTo(x1, y1 - L); g.lineTo(x1, y1); g.lineTo(x1 - L, y1);
    g.moveTo(x0 + L, y1); g.lineTo(x0, y1); g.lineTo(x0, y1 - L);
    g.stroke(); g.lineCap = "butt";
  }

  function draw() {
    if (!S || !run) return;
    var g = cv.getContext("2d"), k = 1 / S.sc, now = performance.now();
    g.setTransform(S.dpr * S.sc, 0, 0, S.dpr * S.sc, 0, 0);
    g.clearRect(0, 0, W, H);
    g.drawImage(bg, 0, 0, W, H);

    var e = EXPRS[cur], st = stage, prog = animating ? clamp(((now - playT0) % STEP_MS) / STEP_MS, 0, 1) : 1;
    var done = st >= nSteps, headI = headStepAt(st), lastI = lastHeadStep();

    // the field of the latest Filter/Relate, full strength in its own round, fainter after it
    var fs = fieldSpec(st);
    if (fs) {
      var a = fs.i === st && animating ? ease(prog) : (fs.i === st ? 1 : 0.8);
      g.globalAlpha = a; g.imageSmoothingEnabled = true; g.drawImage(buildField(fs), 0, 0, W, H); g.globalAlpha = 1;
    }
    for (var oi = 0; oi < objs.length; oi++) drawObject(g, objs[oi]);
    if (theme.night) { g.fillStyle = "rgba(6,7,14,.22)"; g.fillRect(0, 0, W, H); }

    // the anchor of a relation, once its round has come
    var anchorStep = -1;
    run.steps.forEach(function (s, i) { if (s.node.isAnchor && anchorStep < 0) anchorStep = i; });
    if (anchorStep >= 0 && st >= anchorStep) {
      run.steps[anchorStep].scored.forEach(function (r) {
        var b = r.box.map(function (v, i) { return v * (i % 2 ? H : W); });
        g.strokeStyle = theme.ink; g.lineWidth = 2.4 * k; g.setLineDash([8 * k, 6 * k]);
        g.strokeRect(b[0], b[1], b[2] - b[0], b[3] - b[1]); g.setLineDash([]);
        pill(g, b[2] + 34 * k, (b[1] + b[3]) / 2, "anchor", theme.night ? "#F2EFE6" : "#16171C", theme.night ? "#16171C" : "#FFFFFF", 11);
      });
    }

    // candidates of the head class
    var cands = objs.filter(function (o) { return o.cls === e.cls; });
    var step = headI >= 0 ? run.steps[headI] : null, scoreOf = new Map();
    if (step) step.scored.forEach(function (r) { scoreOf.set(r.box, r.score); });
    var winnerBox = run.winner ? run.winner.box : null;
    var showWin = st >= lastI;
    var axisStep = null;
    for (var si = Math.min(st, nSteps - 1); si >= 0; si--) {
      var sop = run.steps[si].op;
      if (!run.steps[si].node.isAnchor && (sop === "argmin" || sop === "argmax" || sop === "nth")) { axisStep = run.steps[si]; break; }
    }
    if (axisStep) drawAxis(g, axisStep, cands, scoreOf, winnerBox, k);
    var rank = new Map();                                   // order along the axis, for Nth's labels
    if (step && step.op === "nth") cands.slice().sort(function (a, b) { return EX.axisValue(a.box, step.node.axis) - EX.axisValue(b.box, step.node.axis); })
      .forEach(function (o, i) { rank.set(o.box, i); });

    cands.forEach(function (o, idx) {
      var b = [o.box[0] * W, o.box[1] * H, o.box[2] * W, o.box[3] * H];
      if (st === 0 && animating && prog < (idx + 1) / (cands.length + 1)) return;   // entrants walk on one by one
      var has = scoreOf.has(o.box), sc = has ? scoreOf.get(o.box) : 0;
      var out = !has || ((step.op === "filter" || step.op === "relate") && sc < 1e-3);
      var isWin = showWin && o.box === winnerBox;
      if (done && isWin) {                                   // the last round: SAM turns the chosen box into a mask
        g.globalAlpha = 0.55; drawObject(g, o, COL.mask); g.globalAlpha = 1;
      }
      g.lineWidth = (isWin ? 3.2 : 2.2) * k;
      g.strokeStyle = isWin ? COL.win : COL.cand;
      g.globalAlpha = out && !isWin ? 0.35 : 1;
      if (out && !isWin) g.setLineDash([7 * k, 6 * k]);
      g.strokeRect(b[0], b[1], b[2] - b[0], b[3] - b[1]); g.setLineDash([]);
      g.globalAlpha = 1;
      if (isWin) brackets(g, b, COL.win, 7, 14);
      var label;
      if (!step || step.op === "select") label = "#" + o.label;
      else if (step.op === "nth") label = "#" + o.label + " · " + ORD[rank.get(o.box)];
      else label = "#" + o.label + (has ? " · " + sc.toFixed(2) : " · out");
      pill(g, (b[0] + b[2]) / 2, b[1] - 13 * k, label, isWin ? COL.win : (out ? "rgba(90,90,90,.75)" : COL.cand), "#FFFFFF", 11.5);
    });

    // the implicit judge: the detector's most confident box, whatever the words say
    if (judge && st >= 1) {
      var best = null;
      cands.forEach(function (o) { if (!best || o.conf > best.conf) best = o; });
      if (best) {
        var bb = [best.box[0] * W, best.box[1] * H, best.box[2] * W, best.box[3] * H], pad = 11 * k;
        g.strokeStyle = COL.gold; g.lineWidth = 2.6 * k; g.setLineDash([3 * k, 5 * k]);
        g.strokeRect(bb[0] - pad, bb[1] - pad, bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad); g.setLineDash([]);
        pill(g, (bb[0] + bb[2]) / 2, bb[3] + pad + 14 * k, "implicit pick · conf " + best.conf.toFixed(2), COL.gold, "#16171C", 11);
      }
    }
    updateRounds(st);
  }

  /* superlatives and ordinals rank along an axis: draw it, with a tick for every candidate */
  function drawAxis(g, step, cands, scoreOf, winnerBox, k) {
    var ax = step.node.axis, horiz = ax === "X", m = 26 * k;
    var col = theme.night ? "rgba(242,239,230,.92)" : "rgba(22,23,28,.85)";
    g.strokeStyle = col; g.fillStyle = col; g.lineWidth = 2.4 * k;
    g.beginPath();
    if (horiz) { g.moveTo(40 * k, H - m); g.lineTo(W - 40 * k, H - m); } else { g.moveTo(m, 40 * k); g.lineTo(m, H - 40 * k); }
    g.stroke();
    g.beginPath();
    if (horiz) { g.moveTo(W - 40 * k, H - m); g.lineTo(W - 54 * k, H - m - 7 * k); g.lineTo(W - 54 * k, H - m + 7 * k); }
    else { g.moveTo(m, H - 40 * k); g.lineTo(m - 7 * k, H - 54 * k); g.lineTo(m + 7 * k, H - 54 * k); }
    g.fill();
    var name = (step.op === "nth" ? "Nth along " : step.op === "argmin" ? "Argmin " : "Argmax ") + ax;
    if (horiz) pill(g, W - 120 * k, H - m - 18 * k, name + " →", theme.night ? "#F2EFE6" : "#16171C", theme.night ? "#16171C" : "#FFF", 11);
    else pill(g, m + 62 * k, 52 * k, name + " ↓", theme.night ? "#F2EFE6" : "#16171C", theme.night ? "#16171C" : "#FFF", 11);
    cands.forEach(function (o) {
      var live = step.op === "nth" ? true : scoreOf.has(o.box);
      if (!live && step.op !== "nth") return;
      var cx = (o.box[0] + o.box[2]) / 2 * W, cy = (o.box[1] + o.box[3]) / 2 * H, isWin = o.box === winnerBox;
      g.strokeStyle = isWin ? COL.win : "rgba(232,98,74,.75)"; g.lineWidth = 1.6 * k; g.setLineDash([4 * k, 5 * k]);
      g.beginPath(); g.moveTo(cx, cy);
      if (horiz) g.lineTo(cx, H - m); else g.lineTo(m, cy);
      g.stroke(); g.setLineDash([]);
      g.fillStyle = isWin ? COL.win : COL.cand;
      g.beginPath(); if (horiz) g.arc(cx, H - m, 6 * k, 0, TAU); else g.arc(m, cy, 6 * k, 0, TAU); g.fill();
    });
  }

  /* ------------------------------------------------------------------ the text around the board */
  function roundLabel(s) {
    var n = s.node, live = s.scored.filter(function (r) { return r.score > 1e-3; }).length;
    if (n.op === "select") return (n.isAnchor ? "anchor · " : "") + 'Select("' + n.type + '") · ' + s.scored.length;
    if (n.op === "filter") return "Filter(" + n.pred + ") · " + live + " in play";
    if (n.op === "relate") return "Relate(" + n.rel + ")";
    if (n.op === "argmin" || n.op === "argmax") return (n.op === "argmin" ? "Argmin(" : "Argmax(") + n.axis + ")";
    if (n.op === "nth") return "Nth(" + n.n + ", " + n.axis + ") · 1 kept";
    return n.op;
  }
  var roundsKey = "";
  function updateRounds(st) {
    if (!roundsEl) return;
    var labels = run.steps.map(roundLabel).concat(["SAM → mask"]), key = labels.join("|") + "#" + st;
    if (key === roundsKey) return;
    roundsKey = key;
    roundsEl.innerHTML = labels.map(function (l, i) {
      var c = i < st ? "done" : i === st ? "on" : "";
      return '<li class="' + c + '"><span>R' + (i + 1) + "</span>" + l.replace(/</g, "&lt;") + "</li>";
    }).join("");
  }

  function winnerObj() { return run.winner ? objOf(run.winner.box) : null; }
  function scoreTxt(o) {
    var last = run.steps[lastHeadStep()], v = null;
    last.scored.forEach(function (r) { if (r.box === o.box) v = r.score; });
    return v == null ? "" : v.toFixed(2);
  }
  function say() {
    var e = EXPRS[cur], w = winnerObj(), cls = e.cls, n = objs.filter(function (o) { return o.cls === cls; }).length;
    if (!w) return "The program returned nothing here: no candidate survived. On a real image the reliability ladder would fall back to the field-only special case.";
    var W_ = '<span class="win">#' + w.label + "</span>", t;
    switch (cur) {
      case 0:
        t = "<b>Filter(RIGHT)</b> lays a field over the frame that rises from the centre line to the right edge, and reads it at each airplane&rsquo;s centre. " + W_ + " scores highest (" + scoreTxt(w) + "). Drag an airplane across the centre line and its score drops to zero.";
        break;
      case 1:
        t = "<b>Argmin(X)</b> takes the extremum: a softmax over the " + n + " tanks&rsquo; centres puts the most weight on the one furthest left, " + W_ + " (" + scoreTxt(w) + "). Drag another tank past it and the selection moves with it.";
        break;
      case 2:
        t = "<b>Nth(1, X)</b> sorts the courts by the x of their centres and keeps the second, " + W_ + ". A field cannot say &ldquo;second&rdquo;; this is a discrete operator. Drag a court past another and the order, and the winner, change.";
        break;
      case 3:
        t = "<b>Relate(NEAR)</b> scores each ship by its gap to the anchor, the bridge: " + W_ + " is closest (" + scoreTxt(w) + "). Drag the bridge up or down the river and the nearest ship changes.";
        break;
      case 4:
        var left = run.steps[1].scored.filter(function (r) { return r.score > 1e-3; }).length;
        t = "<b>Filter(LEFT)</b> knocks out every airplane right of the centre line (" + left + " of " + n + " stay in play), then <b>Argmin(Y)</b> takes the topmost of the survivors, " + W_ + ". Two rules, one program.";
        break;
      default:
        t = "<b>Filter(CENTER)</b> is a Gaussian around the frame centre (&sigma; = 0.25 of the frame). The tank whose centre sits closest to the middle scores highest: " + W_ + " (" + scoreTxt(w) + ").";
    }
    if (judge) {
      var best = null;
      objs.forEach(function (o) { if (o.cls === cls && (!best || o.conf > best.conf)) best = o; });
      t += best === w
        ? ' <span class="imp">The detector-confidence judge agrees this time</span>, by its own measure: it never reads the words, so moving a box will not move its pick.'
        : ' <span class="imp">The detector-confidence judge picks #' + best.label + "</span> (confidence " + best.conf.toFixed(2) + "): the box the detector is surest about, whatever the words say.";
    }
    return t;
  }
  function narrate(st) {
    if (st >= nSteps) return say();
    var s = run.steps[st], n = s.node;
    if (n.op === "select") return n.isAnchor
      ? "Round " + (st + 1) + ": the anchor is resolved first, <b>Select(&ldquo;" + n.type + "&rdquo;)</b>."
      : "Round " + (st + 1) + ": <b>Select(&ldquo;" + n.type + "&rdquo;)</b> asks the detector for every " + n.type + ". Each one enters with score 1.";
    if (n.op === "filter") return "Round " + (st + 1) + ": <b>Filter(" + n.pred + ")</b> reads a continuous field at every box centre and multiplies it into the score.";
    if (n.op === "relate") return "Round " + (st + 1) + ": <b>Relate(" + n.rel + ")</b> multiplies in a score that falls with the gap to the anchor.";
    if (n.op === "nth") return "Round " + (st + 1) + ": <b>Nth(" + n.n + ", " + n.axis + ")</b> sorts the candidates along " + n.axis + " and keeps one.";
    return "Round " + (st + 1) + ": <b>" + (n.op === "argmin" ? "Argmin" : "Argmax") + "(" + n.axis + ")</b> re-scores the survivors by position along " + n.axis + ".";
  }
  var hudKey = "";
  function setHud(html) { if (hudEl && html !== hudKey) { hudKey = html; hudEl.innerHTML = html; } }

  function renderPanel() {
    if (!panelEl) return;
    var e = EXPRS[cur], f = BY_FRAME[e.frame], mx = 70;
    var rows = SELECTORS.map(function (name, i) {
      var cls = i >= 2 ? "ours" : "imp", top = i === 3 ? " top" : "";
      return '<div class="pp-row ' + cls + top + '"><span class="pp-name">' + name + '</span><span class="pp-bar"><i style="width:' +
        (f.v[i] / mx * 100).toFixed(1) + '%"></i></span><span class="pp-val">' + f.v[i].toFixed(2) + "</span></div>";
    }).join("");
    panelEl.innerHTML =
      '<p class="pp-kicker">The scoreboard &middot; real numbers</p>' +
      '<p class="pp-big"><b>' + f.d + '</b> mIoU</p>' +
      '<p class="pp-lead">over the best implicit selector on <b>' + f.name + '</b> expressions, RRSIS-D val, the stratum this phrase belongs to</p>' +
      '<div class="pp-rows">' + rows + "</div>" +
      '<p class="pp-src">Same detector and same segmenter for every row; only the selector differs.</p>' +
      (e.tag && BY_TAG[e.tag] ? '<p class="pp-tag">' + BY_TAG[e.tag] + "</p>" : "");
  }

  function renderChips() {
    if (!chipsEl) return;
    chipsEl.innerHTML = EXPRS.map(function (e, i) {
      return '<button type="button" class="filter-tab' + (i === cur ? " active" : "") + '" aria-pressed="' + (i === cur) + '" data-i="' + i + '">&ldquo;' + e.text + "&rdquo;</button>";
    }).join("");
  }

  /* ------------------------------------------------------------------ timeline */
  function frame() {
    if (!animating && !nudge) return;
    var now = performance.now();
    if (nudge) {
      var t = clamp((now - nudge.t0) / nudge.dur, 0, 1), q = ease(t);
      nudge.o.x = nudge.x0 + (nudge.x1 - nudge.x0) * q; nudge.o.y = nudge.y0 + (nudge.y1 - nudge.y0) * q;
      if (nudge.o.cls === "bridge") nudge.o.x = riverX(nudge.o.y);
      execute(); setHud(say());
      if (t >= 1) { var nx = nudge.next; nudge = null; if (nx) nx(); }
    }
    if (animating) {
      stage = Math.floor((now - playT0) / STEP_MS);
      if (stage > nSteps) { stage = nSteps; animating = false; setHud(say()); afterPlay(); }
      else setHud(narrate(Math.min(stage, nSteps)));
    }
    draw();
    if (animating || nudge) requestAnimationFrame(frame);
  }
  function play() {
    clearTimeout(idleTimer); nudge = null;
    execute(); renderPanel(); renderChips(); roundsKey = "";
    if (progEl) progEl.textContent = EX.programString(EXPRS[cur].prog);
    if (reduce) { stage = nSteps; animating = false; setHud(say()); draw(); return; }
    stage = 0; playT0 = performance.now(); animating = true;
    requestAnimationFrame(frame);
  }
  function startNudge(o, x1, y1, dur, next) {
    nudge = { o: o, x0: o.x, y0: o.y, x1: x1, y1: y1, t0: performance.now(), dur: dur, next: next };
    requestAnimationFrame(frame);
  }
  /* while nobody is using it, the board demonstrates itself: one box moves, the selection follows */
  function afterPlay() {
    if (user || reduce) return;
    var e = EXPRS[cur], w = winnerObj(), list = objs.filter(function (o) { return o.cls === e.cls; }), mover = null, tx = 0, ty = 0;
    if (w && cur === 1) {                                 // a tank slides past the leftmost one
      var byX = list.slice().sort(function (a, b) { return a.x - b.x; });
      mover = byX[1]; tx = Math.max(470 + mover.r, w.x - w.r - mover.r - 14); ty = clamp(w.y + (mover.y > w.y ? 90 : -90), 70, 430);
    } else if (w && cur === 2) {                          // the leftmost court moves to the far end of the row
      var byX2 = list.slice().sort(function (a, b) { return a.x - b.x; });
      mover = byX2[0]; tx = 1550; ty = mover.y;
    } else if (w && cur === 3) {                          // the bridge moves next to the farthest ship
      var bridge = objs.filter(function (o) { return o.cls === "bridge"; })[0], farS = null;
      list.forEach(function (s) { if (!farS || Math.abs(s.y - bridge.y) > Math.abs(farS.y - bridge.y)) farS = s; });
      mover = bridge; ty = clamp(farS.y + (farS.y > H / 2 ? -78 : 78), 40, H - 40); tx = riverX(ty);
    } else if (w && cur === 0) {                          // the rightmost airplane taxis across the centre line
      mover = w; tx = 0.4 * W; ty = w.y;
    }
    if (!mover) { idleTimer = setTimeout(next, 4600); return; }
    var x0 = mover.x, y0 = mover.y;
    idleTimer = setTimeout(function () {
      if (user) return;
      startNudge(mover, tx, ty, 1500, function () {
        idleTimer = setTimeout(function () {
          if (user) return;
          startNudge(mover, x0, y0, 1100, function () { idleTimer = setTimeout(next, 2200); });
        }, 1700);
      });
    }, 1300);
  }
  function next() { if (user) return; cur = (cur + 1) % EXPRS.length; play(); }

  function takeOver() { user = true; clearTimeout(idleTimer); nudge = null; }

  /* ------------------------------------------------------------------ input */
  function toWorld(ev) {
    var r = cv.getBoundingClientRect();
    return [(ev.clientX - r.left) / S.sc, (ev.clientY - r.top) / S.sc];
  }
  function hit(p) {
    var e = EXPRS[cur], best = null, pad = 10;
    objs.forEach(function (o) {
      var movable = o.cls === e.cls || (o.cls === "bridge" && cur === 3);
      if (!movable) return;
      var b = bbox(o);
      if (p[0] >= b[0] - pad && p[0] <= b[2] + pad && p[1] >= b[1] - pad && p[1] <= b[3] + pad) best = o;
    });
    return best;
  }
  function placeObj(o, x, y) {
    if (o.cls === "bridge") { o.y = clamp(y, 40, H - 40); o.x = riverX(o.y); return; }
    if (o.cls === "ship") { o.y = clamp(y, 40, H - 40); o.x = clamp(x, riverX(o.y) - 34, riverX(o.y) + 34); return; }
    o.x = clamp(x, 40, W - 40); o.y = clamp(y, 40, H - 40);
  }
  cv.addEventListener("pointerdown", function (ev) {
    if (!S) return;
    var p = toWorld(ev), o = hit(p);
    if (!o) return;
    takeOver();
    if (animating) { animating = false; stage = nSteps; }
    drag = { o: o, dx: o.x - p[0], dy: o.y - p[1], id: ev.pointerId };
    try { cv.setPointerCapture(ev.pointerId); } catch (err) {}
    cv.classList.add("grabbing");
    ev.preventDefault();
  });
  cv.addEventListener("pointermove", function (ev) {
    if (!S) return;
    var p = toWorld(ev);
    if (!drag) { cv.classList.toggle("can-grab", !!hit(p)); return; }
    placeObj(drag.o, p[0] + drag.dx, p[1] + drag.dy);
    execute(); setHud(say()); draw();
  });
  function endDrag() { if (drag) { drag = null; cv.classList.remove("grabbing"); } }
  cv.addEventListener("pointerup", endDrag);
  cv.addEventListener("pointercancel", endDrag);

  if (chipsEl) chipsEl.addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-i]");
    if (!b) return;
    takeOver(); cur = +b.getAttribute("data-i"); play();
  });
  if (replayBtn) replayBtn.addEventListener("click", function () { takeOver(); play(); });
  if (shuffleBtn) shuffleBtn.addEventListener("click", function () { takeOver(); seed = (seed * 7 + 11) % 100003; objs = makeObjects(seed); play(); });
  if (judgeBtn) judgeBtn.addEventListener("click", function () {
    takeOver(); judge = !judge; judgeBtn.setAttribute("aria-pressed", String(judge));
    if (!animating) { setHud(say()); draw(); }
  });

  new MutationObserver(function () { readTheme(); draw(); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  var rt = 0;
  window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(layout, 120); });

  /* start when the board is first on screen, so the rounds are seen from the beginning */
  readTheme();
  var qs = /[?&]play=(\d)/.exec(location.search);           // ?play=N opens on expression N, for screenshots
  if (qs && +qs[1] < EXPRS.length) { cur = +qs[1]; user = true; }
  if (/[?&]judge=1/.test(location.search) && judgeBtn) { judge = true; judgeBtn.setAttribute("aria-pressed", "true"); }
  objs = makeObjects(seed);
  execute(); renderChips(); renderPanel();
  if (progEl) progEl.textContent = EX.programString(EXPRS[cur].prog);
  stage = nSteps; setHud(say());
  layout();
  var started = false;
  function begin() { if (started) return; started = true; play(); }
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) begin(); }); }, { threshold: 0.35 }).observe(cv);
  } else begin();
})();
