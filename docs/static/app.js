/* GeoSelect project page — interactions.
   Data: window.CASES (static/cases-data.js). Works under file:// (no fetch). */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  /* ---- render a synthesised program (AST) as a one-line expression ---- */
  function progStr(p) {
    if (!p) return "—";
    const op = p.op;
    const anc = (a) => (a && typeof a === "object" ? progStr(a) : a || "image");
    if (op === "select") return 'select("' + (p.type || "?") + '")';
    const arg = p.child != null ? progStr(p.child) : "";
    if (op === "filter") return "filter(" + arg + ", " + (p.pred || "?") + " vs " + anc(p.anchor) + ")";
    if (op === "argmax" || op === "argmin") return op + "(" + arg + ", " + (p.axis || "?") + ")";
    if (op === "nth") return "nth(" + arg + ", n=" + p.n + ", " + (p.axis || "?") + ")";
    if (op === "restrict_count") return "restrict_count(" + arg + ", k=" + p.k + ")";
    if (op === "relate") return "relate(" + arg + ", " + (p.rel || "?") + ", " + anc(p.anchor) + (p.anchor2 ? ", " + anc(p.anchor2) : "") + ")";
    if (op === "and" || op === "or" || op === "not") {
      const kids = (p.children || [p.child]).filter(Boolean).map(progStr).join(", ");
      return op + "(" + kids + ")";
    }
    return op + "(" + arg + ")";
  }
  function renderProgram(p) {
    if (!p) return '<div class="r-card"><div class="r-empty">no legal program: field-only fallback</div></div>';
    return '<div class="r-card"><div class="r-title">// synthesised program π</div>' +
      '<code class="prog">' + esc(progStr(p)) + "</code></div>";
  }

  /* ---- Pipeline stepper (real trace; RISBench "the westernmost storage tank in the line of tanks") ---- */
  const STEP_PROG = { op: "argmin", axis: "X", child: { op: "filter", pred: "LEFT", anchor: "image", child: { op: "select", type: "storage tank" } } };
  const STEPS = [
    { n: "1", tag: "INPUT", title: "Aerial image + expression", img: "static/images/method_input.png",
      desc: "The frozen pipeline takes an aerial image and a referring expression; here, “the westernmost storage tank in the line of tanks.” No component is trained or fine-tuned.",
      flow: "input &rarr; <code>synthesise</code>" },
    { n: "2", tag: "SYNTHESISE", title: "Synthesise a typed program π", prog: STEP_PROG,
      desc: "A text-only LLM (Qwen3-4B) compiles the expression, without ever seeing the image, into a typed program in a small DSL. A well-formedness checker accepts it before execution.",
      flow: "<code>π</code> = synthesise(expression)" },
    { n: "3", tag: "SELECT", title: "Detector candidate set", img: "static/images/method_select.png",
      desc: "The select leaf queries open-vocabulary detection (LAE-DINO + SAHI) for the target phrase, returning the initial scored candidate set C.",
      flow: "<code>select</code> &rarr; candidate set C" },
    { n: "4", tag: "FILTER", title: "Continuous geometric field", img: "static/images/method_field.png",
      desc: "The continuous filter re-weights every candidate by a dense geometric field for the predicate (here LEFT), shown as a heat map; warmer where the phrase points.",
      flow: "<code>filter</code>: s[b] *= field(b)" },
    { n: "5", tag: "ARGMIN", title: "Discrete extremum", img: "static/images/method_argmin.png",
      desc: "The discrete argmin re-scores the live set to its extremum along the axis (green = winner). Continuous fields and discrete operators share one type, so they compose and nest freely.",
      flow: "<code>argmin</code>(C, axis X)" },
    { n: "6", tag: "SEGMENT", title: "SAM ViT-L referent mask", img: "static/images/method_mask.png",
      desc: "SAM ViT-L turns the top-scoring box into the final mask. Every intermediate (program, field, ranking) is exposed, so the whole trace is open to inspection rather than a black box.",
      flow: "<code>mask</code> = SAM(image, box)" },
  ];
  function renderStep(i) {
    const s = STEPS[i];
    document.querySelectorAll(".step-tab").forEach((t, j) => t.classList.toggle("active", j === i));
    $("stepperViz").innerHTML = s.prog ? renderProgram(s.prog) : '<img src="' + s.img + '" alt="' + esc(s.title) + '">';
    $("stepTag").textContent = s.n + " · " + s.tag;
    $("stepTitle").textContent = s.title;
    $("stepDesc").textContent = s.desc;
    $("stepFlow").innerHTML = s.flow;
  }
  (function initStepper() {
    const tabs = $("stepperTabs");
    STEPS.forEach((s, i) => {
      const b = document.createElement("button");
      b.className = "step-tab";
      b.innerHTML = '<span class="st-n">' + s.n + "</span>" + s.tag.charAt(0) + s.tag.slice(1).toLowerCase();
      b.onclick = () => renderStep(i);
      tabs.appendChild(b);
    });
    renderStep(0);
  })();

  /* ---- Teaser: implicit vs explicit toggle ---- */
  const CMP = {
    ours: { img: "static/images/teaser_ours.png", verdict: "GeoSelect executes the program and picks the airplane matching the ground truth ✓", cls: "ok" },
    clip: { img: "static/images/teaser_clip.png", verdict: "Implicit region–text matching (GeoRSCLIP) selects the wrong instance ✗", cls: "bad" },
  };
  document.querySelectorAll(".cmp-btn").forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll(".cmp-btn").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      const m = CMP[b.dataset.mode];
      $("cmpMain").src = m.img;
      const v = $("cmpVerdict");
      v.textContent = m.verdict;
      v.className = "compare-verdict " + m.cls;
    };
  });

  /* ---- Case gallery + modal ---- */
  const CASES = window.CASES || [];
  const gallery = $("caseGallery");
  const thumbFor = (c) => c.stages.thumb || c.stages.mask || c.stages.input;
  function renderGallery(filter) {
    gallery.innerHTML = "";
    CASES.filter((c) => filter === "all" || c.dataset === filter || c.type === filter).forEach((c) => {
      const d = document.createElement("div");
      d.className = "gallery-item";
      d.onclick = () => openCaseModal(c.id);
      d.innerHTML =
        '<span class="gi-type ' + c.type + '">' + c.type + "</span>" +
        '<img src="' + thumbFor(c) + '" alt="' + esc(c.type) + '" loading="lazy">' +
        '<div class="gi-label">' + esc(c.dataset) + " · #" + c.idx + "</div>";
      gallery.appendChild(d);
    });
    if (!gallery.children.length) gallery.innerHTML = '<p class="gallery-hint">No cases for this filter.</p>';
  }
  document.querySelectorAll(".filter-tab").forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll(".filter-tab").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      renderGallery(b.dataset.filter);
    };
  });

  const STAGE_VIEW = [
    ["input", "input", ""],
    ["candidates", "candidates", ""],
    ["scored", "scored candidate set", ""],
    ["mask", "GeoSelect mask", "ours"],
    ["gt", "ground truth", "gt"],
  ];

  window.openCaseModal = function (id) {
    const c = CASES.find((x) => x.id === id);
    if (!c) return;
    $("cmDs").textContent = c.dataset;
    const t = $("cmType"); t.textContent = c.type; t.className = "badge-type " + c.type;
    $("cmIdx").textContent = "#" + c.idx + (c.iou != null ? "  ·  IoU " + c.iou : "");
    $("cmSentence").textContent = "“" + c.sentence + "”";
    $("cmRcard").innerHTML = renderProgram(c.program);
    const st = $("cmStages"); st.innerHTML = "";
    STAGE_VIEW.forEach(([key, label, cls]) => {
      const src = c.stages[key];
      if (!src) return;
      const f = document.createElement("figure");
      f.className = "cm-stage " + cls;
      f.innerHTML = '<img src="' + src + '" alt="' + esc(label) + '"><figcaption>' + label + "</figcaption>";
      st.appendChild(f);
    });
    const cc = $("cmCompare");
    cc.style.display = "none";
    cc.innerHTML = "";
    $("caseModal").classList.add("active");
  };
  window.closeCaseModal = function () { $("caseModal").classList.remove("active"); };
  $("caseModal").addEventListener("click", function (e) { if (e.target === this) closeCaseModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeCaseModal(); });
  renderGallery("all");

  /* ---- Copy BibTeX ---- */
  window.copyBib = function () {
    const text = $("bibtex").textContent;
    navigator.clipboard.writeText(text).then(() => {
      const b = document.querySelector(".copy-btn");
      b.textContent = "Copied!";
      setTimeout(() => (b.textContent = "Copy"), 2000);
    });
  };

  /* ---- Sticky nav active highlight ---- */
  const siteNav = $("siteNav");
  const links = siteNav.querySelectorAll("a");
  const ids = ["abstract", "motivation", "method", "pipeline", "results", "findings", "cases", "citation"];
  const secs = ids.map((i) => $(i)).filter(Boolean);
  function updateNav() {
    let cur = "";
    for (const s of secs) if (s.getBoundingClientRect().top <= 120) cur = s.id;
    links.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === "#" + cur));
  }
  window.addEventListener("scroll", updateNav, { passive: true });
  updateNav();
})();
