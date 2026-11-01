/* GeoSelect project page, theme layer: the selection show.
   - the lighting switch (day stage / night broadcast), remembered in localStorage;
   - section reveal (the round caption slams in);
   - the arena behind the hero: entrants appear, rounds knock them out, one is crowned, again;
   - the opening: a desire card, ENTRY, SET, three rounds, WINNER, the shutter opens.
     Any click, tap, key, wheel or touch ends it at once. ?still skips it; ?fx=0.6 draws it frozen at 60%.
     Clicking the mark or the title plays it again.
   The entrants and rounds here are an illustration of how a program narrows a candidate set; the real
   cases are in the Execution Inspector. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const root = document.documentElement;
  const css = (k) => getComputedStyle(root).getPropertyValue(k).trim();
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const ease = (t) => 1 - Math.pow(1 - t, 3);
  const back = (t) => { const c = 1.7; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
  const DISPLAY = "'Bebas Neue', Impact, sans-serif";

  /* ---- lighting ---- */
  const btn = $("showBtn");
  if (btn) btn.addEventListener("click", () => {
    const next = root.dataset.theme === "night" ? "day" : "night";
    root.dataset.theme = next;
    try { localStorage.setItem("geoselect-show", next); } catch (e) { /* private mode */ }
  });

  /* ---- reading progress: the tri-colour rule under the nav fills as the page scrolls ---- */
  function progress() {
    const H = document.documentElement.scrollHeight - innerHeight;
    root.style.setProperty("--read", (H > 0 ? clamp(scrollY / H, 0, 1) : 0).toFixed(4));
  }
  window.addEventListener("scroll", progress, { passive: true });
  window.addEventListener("resize", progress);
  progress();

  /* ---- section reveal ---- */
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }), { threshold: 0.12 });
  document.querySelectorAll("section").forEach((s) => io.observe(s));

  /* a deterministic set of entrants: boxes spread over a field, the rightmost is the one the card asks for */
  function entrants(w, h, n, seed, top, bottom, sides) {
    let x = seed;
    const rnd = () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; };
    const out = [];
    for (let i = 0; i < n; i++) {
      const bw = 46 + rnd() * 50, bh = 30 + rnd() * 34;
      const cx = sides
        ? (i % 2 ? 0.80 + 0.15 * rnd() : 0.04 + 0.15 * rnd()) * w
        : (0.08 + 0.84 * ((i + rnd() * 0.7) / n)) * w;
      const cy = top + rnd() * (bottom - top - bh);
      out.push({ x: cx - bw / 2, y: cy, w: bw, h: bh, id: i + 1, ang: (rnd() - .5) * .5 });
    }
    // knock-out order: the rightmost box wins; the others leave over three rounds
    const order = out.map((b, i) => i).sort((a, b) => out[a].x - out[b].x);
    const win = order[order.length - 1];
    const rest = order.slice(0, -1).sort(() => rnd() - .5);
    const r1 = Math.ceil(rest.length * .5), r2 = Math.ceil(rest.length * .85);
    out.forEach((b, i) => { b.round = i === win ? 9 : (rest.indexOf(i) < r1 ? 1 : rest.indexOf(i) < r2 ? 2 : 3); });
    return { boxes: out, win };
  }
  function drawBox(g, b, col, a, lw, label, tagCol) {
    g.save(); g.globalAlpha = a;
    g.strokeStyle = col; g.lineWidth = lw; g.strokeRect(b.x, b.y, b.w, b.h);
    if (label) {
      g.font = "15px " + DISPLAY; const tw = g.measureText(label).width + 10;
      g.fillStyle = tagCol || col; g.fillRect(b.x - lw / 2, b.y - 18, tw, 18);
      g.fillStyle = "#0B0B10"; g.fillText(label, b.x + 5 - lw / 2, b.y - 4);
    }
    g.restore();
  }
  function cross(g, b, col, a) {
    g.save(); g.globalAlpha = a; g.strokeStyle = col; g.lineWidth = 3; g.lineCap = "round";
    g.beginPath(); g.moveTo(b.x + 6, b.y + 6); g.lineTo(b.x + b.w - 6, b.y + b.h - 6);
    g.moveTo(b.x + b.w - 6, b.y + 6); g.lineTo(b.x + 6, b.y + b.h - 6); g.stroke(); g.restore();
  }
  function crown(g, cx, cy, s, fill, edge, a) {
    g.save(); g.globalAlpha = a; g.translate(cx, cy); g.scale(s, s);
    g.beginPath(); g.moveTo(-20, 0); g.lineTo(-14, -16); g.lineTo(-6, -6); g.lineTo(0, -20); g.lineTo(6, -6); g.lineTo(14, -16); g.lineTo(20, 0); g.closePath();
    g.fillStyle = fill; g.fill(); g.lineWidth = 2.4 / s; g.strokeStyle = edge; g.stroke(); g.restore();
  }
  function fit(cv) {
    const dpr = Math.min(2, window.devicePixelRatio || 1), r = cv.getBoundingClientRect();
    cv.width = Math.max(1, r.width * dpr); cv.height = Math.max(1, r.height * dpr);
    const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { g, w: r.width, h: r.height };
  }

  /* ---- the arena behind the hero (faint, slow, loops) ---- */
  (function () {
    const cv = $("arena"); if (!cv) return;
    const make = () => entrants(F.w, F.h, 10, 7, F.h * .1, F.h * .9, F.w > 900);
    let F = fit(cv), E = make(), visible = true;
    window.addEventListener("resize", () => { F = fit(cv); E = make(); });
    new IntersectionObserver((es) => { visible = es[0].isIntersecting; }).observe(cv);
    const LOOP = 14000;
    function draw(now) {
      const { g, w, h } = F, t = (now % LOOP) / LOOP;
      g.clearRect(0, 0, w, h);
      const ink = css("--indigo"), gold = css("--gold"), red = css("--red");
      const fade = t > .92 ? 1 - (t - .92) / .08 : 1;
      E.boxes.forEach((b, i) => {
        const appear = clamp((t - i * .012) / .06, 0, 1);
        const out = b.round === 1 ? t > .35 : b.round === 2 ? t > .52 : b.round === 3 ? t > .68 : false;
        const winNow = b.round === 9 && t > .74;
        const a = appear * fade * (out ? .1 : winNow ? .55 : .2);
        drawBox(g, b, winNow ? gold : ink, a, winNow ? 3 : 1.5, (winNow ? "WINNER  " : "No.") + String(b.id).padStart(2, "0"), winNow ? gold : ink);
        if (out) cross(g, b, red, .25 * fade);
        if (winNow) crown(g, b.x + b.w / 2, b.y - 26, .7, gold, ink, .6 * fade * ease(clamp((t - .74) / .05, 0, 1)));
      });
    }
    function loop(now) { if (visible) draw(now); requestAnimationFrame(loop); }
    if (reduce) draw(LOOP * .8); else requestAnimationFrame(loop);
  })();

  /* ---- the opening ---- */
  (function () {
    const cv = $("fxShow"), hint = $("fxHint"), emblem = $("emblem"), title = $("heroTitle");
    if (!cv) return;
    function arm() {
      [emblem, title].forEach((n) => { if (!n) return; n.classList.remove("lock", "lit", "pre"); void n.getBoundingClientRect(); });
      if (emblem) emblem.classList.add("lock");
      if (title) title.classList.add("lit");
    }
    const freeze = parseFloat((location.search.match(/fx=([\d.]+)/) || [])[1]);
    const still = /[?&]still/.test(location.search);
    const EV = ["pointerdown", "keydown", "wheel", "touchstart"];
    let end = () => {};

    function play() {
      end();
      const night = "#0B0B10", gold = "#FFC83D", red = "#FF3B57", ink = "#F2EFE6";
      cv.style.display = "block"; cv.classList.remove("cover"); hint.classList.remove("gone");
      const { g, w, h } = fit(cv);
      const card = { w: Math.min(520, w * .86), h: 92 };
      const E = entrants(w, h, 9, 11, h * .42, h * .76, false);
      const ops = ["SELECT  airplane", "FILTER  right", "ARGMAX  x"];
      const big = Math.round(clamp(w * .085, 46, 112));
      const t0 = performance.now(), dur = 3600;
      let raf = 0, done = false, armed = false;
      if (emblem) { emblem.classList.remove("lock"); emblem.classList.add("pre"); }

      function caption(text, t, a, b, col) {   // a big word that slams in between a and b
        if (t < a || t > b) return;
        const k = (t - a) / (b - a), s = k < .25 ? 1.6 - .6 * back(k / .25) : 1;
        const al = k < .1 ? k / .1 : k > .8 ? (1 - k) / .2 : 1;
        g.save(); g.globalAlpha = al; g.translate(w / 2, h * .3); g.scale(s, s); g.transform(1, 0, -.2, 1, 0, 0);
        g.font = big + "px " + DISPLAY; g.textAlign = "center"; g.textBaseline = "middle";
        g.fillStyle = red; g.fillText(text, 6, 6); g.fillStyle = col; g.fillText(text, 0, 0); g.restore();
      }
      function frame(now) {
        const t = clamp((now - t0) / dur, 0, 1);
        g.clearRect(0, 0, w, h);
        // the shutter: slats lift one after another at the end
        const slats = 8, sw = w / slats;
        for (let i = 0; i < slats; i++) {
          const k = ease(clamp((t - .86 - i * .012) / .1, 0, 1));
          g.fillStyle = night; g.fillRect(i * sw - .5, -k * h, sw + 1, h);
          g.fillStyle = i % 2 ? "rgba(255,200,61,.06)" : "rgba(255,255,255,.02)"; g.fillRect(i * sw - .5, -k * h, sw + 1, h);
        }
        g.save(); g.beginPath(); g.rect(0, 0, w, h * (1 - ease(clamp((t - .86) / .14, 0, 1)))); g.clip();
        // stage lights
        [-1, 1].forEach((sd) => {
          const gr = g.createRadialGradient(w / 2 + sd * w * .32, -40, 10, w / 2 + sd * w * .32, -40, h * 1.1);
          gr.addColorStop(0, "rgba(255,200,61,.18)"); gr.addColorStop(1, "rgba(255,200,61,0)");
          g.fillStyle = gr; g.fillRect(0, 0, w, h);
        });
        // the desire card: the referring expression, the thing to be granted
        const ka = back(clamp(t / .1, 0, 1)), up = ease(clamp((t - .12) / .08, 0, 1));
        const cx = w / 2, cy = h * (.5 - .38 * up) + 4 * up;
        if (t < .86) {
          g.save(); g.translate(cx, cy); g.scale(ka, ka);
          g.fillStyle = "#F2EFE6"; g.fillRect(-card.w / 2, -card.h / 2, card.w, card.h);
          g.fillStyle = gold; g.fillRect(-card.w / 2, -card.h / 2, card.w, 22);
          g.fillStyle = "#16171C"; g.font = "18px " + DISPLAY; g.textAlign = "left"; g.textBaseline = "middle";
          g.fillText("DESIRE CARD", -card.w / 2 + 12, -card.h / 2 + 12);
          g.font = "600 " + Math.round(clamp(card.w * .052, 15, 24)) + "px Inter, sans-serif"; g.textAlign = "center";
          g.fillText("“the airplane on the right”", 0, 14);
          g.restore();
        }
        caption("ENTRY", t, .16, .32, ink);
        caption("SET", t, .32, .44, ink);
        caption("READY", t, .44, .5, ink);
        caption("FIGHT!", t, .5, .57, gold);
        // the entrants
        if (t > .18 && t < .86) {
          E.boxes.forEach((b, i) => {
            const ap = back(clamp((t - .18 - i * .012) / .05, 0, 1));
            if (ap <= 0) return;
            const outAt = b.round === 1 ? .6 : b.round === 2 ? .67 : b.round === 3 ? .74 : 9;
            const out = t > outAt, win = b.round === 9 && t > .76;
            const bb = { x: b.x + b.w / 2 * (1 - ap), y: b.y + b.h / 2 * (1 - ap), w: b.w * ap, h: b.h * ap };
            drawBox(g, bb, win ? gold : out ? "#55535E" : ink, out ? .45 : 1, win ? 4 : 2,
              (win ? "WINNER " : "No.") + String(b.id).padStart(2, "0"), win ? gold : out ? "#55535E" : ink);
            if (out) cross(g, bb, red, clamp((t - outAt) / .02, 0, 1));
            if (win) {
              const k = back(clamp((t - .76) / .05, 0, 1));
              crown(g, bb.x + bb.w / 2, bb.y - 30 - (1 - k) * 40, 1.1, gold, "#16171C", clamp((t - .76) / .03, 0, 1));
              if (t < .8) { g.globalAlpha = .45 * (1 - (t - .76) / .04); g.fillStyle = gold; g.fillRect(0, 0, w, h); g.globalAlpha = 1; }
            }
          });
        }
        // the program cards, then the round counter
        if (t > .32 && t < .86) {
          ops.forEach((op, i) => {
            const k = back(clamp((t - .33 - i * .03) / .06, 0, 1));
            const cw = Math.min(220, w * .28), x = w / 2 + (i - 1) * (cw + 12) - cw / 2, y = h - 110 + (1 - k) * 130;
            const lit = (i === 0 && t > .6) || (i === 1 && t > .67) || (i === 2 && t > .74);
            g.fillStyle = lit ? gold : "#1C1C24"; g.fillRect(x, y, cw, 40);
            g.strokeStyle = gold; g.lineWidth = 2; g.strokeRect(x, y, cw, 40);
            g.fillStyle = lit ? "#16171C" : ink; g.font = "13px Fira Code, monospace"; g.textAlign = "center"; g.textBaseline = "middle";
            g.fillText(op, x + cw / 2, y + 21);
          });
          const left = E.boxes.filter((b) => b.round === 9 || t <= (b.round === 1 ? .6 : b.round === 2 ? .67 : .74)).length;
          g.font = "26px " + DISPLAY; g.textAlign = "right"; g.textBaseline = "top"; g.fillStyle = gold;
          g.fillText("ENTRANTS " + String(left).padStart(2, "0"), w - 24, 20);
        }
        if (t > .8 && t < .9) {   // the winner's caption
          const k = back(clamp((t - .8) / .04, 0, 1));
          g.save(); g.translate(w / 2, h * .3); g.scale(k, k); g.transform(1, 0, -.2, 1, 0, 0);
          g.font = big + "px " + DISPLAY; g.textAlign = "center"; g.textBaseline = "middle";
          g.fillStyle = red; g.fillText("WINNER!", 6, 6); g.fillStyle = gold; g.fillText("WINNER!", 0, 0); g.restore();
        }
        g.restore();
        if (t >= .86) hint.classList.add("gone");
        if (t >= .9 && !armed) { armed = true; arm(); }
        if (!isNaN(freeze)) return;
        if (t < 1) raf = requestAnimationFrame(frame); else end();
      }
      end = () => {
        if (done) return; done = true;
        cancelAnimationFrame(raf); g.clearRect(0, 0, w, h); cv.style.display = "none"; hint.classList.add("gone");
        EV.forEach((e) => window.removeEventListener(e, end, true));
        if (!armed) { armed = true; arm(); }
      };
      if (!isNaN(freeze)) { for (let k = 0; k <= freeze + 1e-9; k += .01) frame(t0 + k * dur); return; }
      EV.forEach((e) => window.addEventListener(e, end, { capture: true, passive: true }));
      raf = requestAnimationFrame(frame);
    }

    [emblem, title].forEach((n) => n && n.addEventListener("click", () => { if (!reduce) setTimeout(play, 0); }));
    if (still || reduce) { cv.style.display = "none"; hint.classList.add("gone"); arm(); }
    else {
      if (emblem) emblem.classList.add("pre");
      // start once the display face is in (or after 1.2 s); the canvas covers the page until then
      const ready = document.fonts ? document.fonts.ready : Promise.resolve();
      Promise.race([ready, new Promise((r) => setTimeout(r, 1200))]).then(() => setTimeout(play, 40));
    }
  })();
})();
