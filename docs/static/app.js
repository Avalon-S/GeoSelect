/* GeoSelect project page — interactions.
   Data: window.TRACES (inspector/traces.js), loaded before this file. Works under file://
   (no fetch). The old window.CASES / static/cases-data.js pair is gone: the inspector's data
   covers more cases and comes from the pipeline's own caches. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  /* The fixed six-step stepper and the 112-case gallery that used to live here are both gone:
     the Execution Inspector runs the real programs over the real candidate sets, and the Program
     Library below indexes into it. Neither needs static/cases-data.js any more. */

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

  /* ---- Program Library: one worked example per operator, indexing into the inspector ----
     Built from the inspector's own data (window.TRACES), so the two can never disagree about
     what a case contains. */
  const TRACES = window.TRACES || [];
  const BASE = window.INSPECTOR_BASE || "";
  const has = (c, op) => (c.ops || []).indexOf(op) >= 0;
  const PER_FAMILY = 6;

  const FAMILIES = [
    { key: "filter", label: "Filter",
      desc: "a dense geometric field re-weights every candidate",
      test: (c) => c.mode !== "fallback" && has(c, "filter") &&
        !["argmax", "argmin", "nth", "relate"].some((o) => has(c, o)) },
    { key: "extremum", label: "Argmax / Argmin",
      desc: "a superlative — a softmax over the candidate set, not a field",
      test: (c) => c.mode !== "fallback" && (has(c, "argmax") || has(c, "argmin")) },
    { key: "nth", label: "Nth",
      desc: "an ordinal takes the n-th candidate in reading order",
      test: (c) => c.mode !== "fallback" && has(c, "nth") },
    { key: "relate", label: "Relate",
      desc: "a relation against an anchor the detector had to find separately",
      test: (c) => c.mode !== "fallback" && has(c, "relate") },
    { key: "select", label: "Select only",
      desc: "no spatial operator: the noun phrase alone resolves the referent",
      test: (c) => c.mode !== "fallback" && (c.ops || []).length === 1 },
    { key: "fallback", label: "Fallback",
      desc: "the program never ran; the field-only selector still answered",
      test: (c) => c.mode === "fallback" },
  ];

  /* take the clearest few, split across the two benchmarks so neither dominates */
  function pick(list) {
    const byIoU = (a, b) => (b.iou || 0) - (a.iou || 0);
    const half = Math.ceil(PER_FAMILY / 2);
    const rr = list.filter((c) => c.dataset === "RRSIS-D").sort(byIoU).slice(0, half);
    const ris = list.filter((c) => c.dataset === "RISBench").sort(byIoU).slice(0, half);
    return rr.concat(ris).slice(0, PER_FAMILY);
  }

  function progLine(c) {
    if (!c.program) return "no legal program";
    return window.GeoExec ? window.GeoExec.programString(c.program) : c.ops.join(" → ");
  }

  function renderLibrary() {
    const host = $("libGroups");
    if (!host) return;
    host.innerHTML = FAMILIES.map((f) => {
      const chosen = pick(TRACES.filter(f.test));
      if (!chosen.length) return "";
      return '<div class="lib-group">' +
        '<div class="lib-head"><h3>' + f.label + "</h3>" +
        '<span class="lib-desc">' + f.desc + "</span></div>" +
        '<div class="lib-grid">' + chosen.map((c) =>
          '<button class="lib-card" data-id="' + c.id + '">' +
          '<img src="' + BASE + (c.img.mask || c.img.input) + '" alt="" loading="lazy">' +
          '<span class="lib-expr">&ldquo;' + esc(c.sentence) + "&rdquo;</span>" +
          '<code class="lib-prog">' + esc(progLine(c)) + "</code>" +
          '<span class="lib-meta">' + esc(c.dataset) +
          (c.iou != null ? ' &middot; IoU <b>' + c.iou + "</b>" : "") + "</span>" +
          "</button>").join("") +
        "</div></div>";
    }).join("");

    host.querySelectorAll(".lib-card").forEach((b) => {
      b.onclick = () => {
        if (window.GeoInspector && window.GeoInspector.open(b.dataset.id)) {
          const sec = $("inspector");
          if (sec && sec.scrollIntoView) sec.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      };
    });
  }
  renderLibrary();

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
  const ids = ["abstract", "motivation", "method", "inspector", "results", "findings", "programs", "citation"];
  const secs = ids.map((i) => $(i)).filter(Boolean);
  function updateNav() {
    let cur = "";
    for (const s of secs) if (s.getBoundingClientRect().top <= 120) cur = s.id;
    links.forEach((a) => a.classList.toggle("active", a.getAttribute("href") === "#" + cur));
  }
  window.addEventListener("scroll", updateNav, { passive: true });
  updateNav();
})();
