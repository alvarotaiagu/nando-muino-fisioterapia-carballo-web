/* =====================================================================
   Nando Muiño · Fisioterapia y Osteopatía · main.js
   Movimiento pausado y táctil: Lenis (único motor de scroll suave) + GSAP
   ScrollTrigger. Láminas anatómicas SVG que se dibujan (stroke-dashoffset)
   al cargar y al hacer scroll, char-reveal lento en serif, sticky stack de
   tratamientos con lámina que cambia por tarjeta, parallax suave de fotos,
   botones magnéticos, marquee lento, tabla de horario que se "pinta".
   Con prefers-reduced-motion o sin JS todo aparece ya en estado final.
   Sin canvas: aquí no hay nada que se pinte por frame salvo transforms.
   ===================================================================== */
(function () {
  "use strict";
  const root = document.documentElement;
  root.classList.remove("no-js");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const gsapReady = typeof window.gsap !== "undefined" && typeof window.ScrollTrigger !== "undefined";
  const motion = !reduce && gsapReady;
  if (reduce) root.classList.add("is-reduced");
  if (gsapReady) gsap.registerPlugin(ScrollTrigger);

  /* ---------- Lenis ---------- */
  let lenis = null;
  if (motion && typeof window.Lenis !== "undefined") {
    lenis = new Lenis({ lerp: 0.085, wheelMultiplier: 1, smoothWheel: true });
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((t) => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0);
    window.nmLenis = lenis;
  }
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener("click", (e) => {
      const id = a.getAttribute("href");
      if (id.length < 2) return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      closeMenu();
      if (lenis) lenis.scrollTo(target, { offset: -56, duration: 1.4, easing: (t) => 1 - Math.pow(1 - t, 3) });
      else target.scrollIntoView({ behavior: reduce ? "auto" : "smooth" });
      target.setAttribute("tabindex", "-1");
      target.focus({ preventScroll: true });
    });
  });

  /* ---------- Cabecera + FAB ---------- */
  const header = document.querySelector(".site-header");
  const fab = document.querySelector(".call-fab");
  function onScroll() {
    const y = window.scrollY;
    header.classList.toggle("is-scrolled", y > 24);
    if (fab) fab.classList.toggle("is-visible", y > window.innerHeight * 0.7);
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* ---------- Menú móvil ---------- */
  const toggle = document.querySelector(".nav-toggle");
  const menu = document.querySelector(".mobile-menu");
  function closeMenu() {
    if (!menu || !toggle) return;
    menu.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Abrir menú");
    if (lenis) lenis.start();
    document.body.style.overflow = "";
  }
  function openMenu() {
    menu.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", "Cerrar menú");
    if (lenis) lenis.stop();
    document.body.style.overflow = "hidden";
    if (motion) gsap.fromTo(menu.querySelectorAll("nav a"), { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: 0.7, ease: "power2.out", stagger: 0.06 });
  }
  if (toggle && menu) {
    toggle.addEventListener("click", () => (menu.hidden ? openMenu() : closeMenu()));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) closeMenu(); });
  }

  /* ---------- Sección activa en la navegación ---------- */
  const navLinks = [...document.querySelectorAll(".nav-links a")];
  if ("IntersectionObserver" in window && navLinks.length) {
    const map = new Map(navLinks.map((a) => [a.getAttribute("href").slice(1), a]));
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        navLinks.forEach((a) => a.classList.remove("is-active"));
        const a = map.get(en.target.id);
        if (a) a.classList.add("is-active");
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    map.forEach((_, id) => { const s = document.getElementById(id); if (s) io.observe(s); });
  }

  /* ---------- Aviso de cookies ---------- */
  (function cookies() {
    const banner = document.querySelector(".cookie-banner");
    const ack = document.querySelector(".cookie-ack");
    if (!banner || !ack) return;
    const KEY = "nm-cookie-ack";
    let seen = false;
    try { seen = localStorage.getItem(KEY) === "1"; } catch (e) {}
    if (!seen) banner.hidden = false;
    ack.addEventListener("click", () => {
      banner.hidden = true;
      try { localStorage.setItem(KEY, "1"); } catch (e) {}
    });
  })();

  /* ---------- Diálogos legales ---------- */
  document.querySelectorAll("[data-dialog]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dlg = document.getElementById(btn.dataset.dialog);
      if (!dlg) return;
      if (typeof dlg.showModal === "function") dlg.showModal(); else dlg.setAttribute("open", "");
    });
  });
  document.querySelectorAll("dialog .dlg-close").forEach((b) => b.addEventListener("click", () => b.closest("dialog").close()));
  document.querySelectorAll("dialog").forEach((d) => d.addEventListener("click", (e) => { if (e.target === d) d.close(); }));

  /* ---------- Mapa solo con consentimiento (sin API key, sin cookies hasta el clic) ---------- */
  document.querySelectorAll(".map-consent").forEach((btn) => {
    btn.addEventListener("click", () => {
      const box = btn.closest(".map");
      const q = encodeURIComponent(btn.dataset.query || "");
      const iframe = document.createElement("iframe");
      iframe.src = "https://www.google.com/maps?q=" + q + "&output=embed";
      iframe.title = "Mapa de Google con la ubicación de Nando Muiño Fisioterapia y Osteopatía";
      iframe.loading = "lazy";
      iframe.referrerPolicy = "no-referrer-when-downgrade";
      iframe.setAttribute("allowfullscreen", "");
      box.insertBefore(iframe, btn);
      btn.remove();
    });
  });

  /* ---------- Chip "abierto ahora" (hora de Europe/Madrid) ---------- */
  (function openNow() {
    const chip = document.querySelector(".open-chip");
    if (!chip) return;
    const HOURS = { 1: [[8, 22]], 2: [[8, 22]], 3: [[8, 22]], 4: [[8, 22]], 5: [[8, 14]] };
    function update() {
      let day, mins;
      try {
        const parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Madrid", weekday: "short", hour: "numeric", minute: "numeric", hour12: false }).formatToParts(new Date());
        const get = (t) => (parts.find((p) => p.type === t) || {}).value;
        day = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(get("weekday"));
        mins = (parseInt(get("hour"), 10) % 24) * 60 + parseInt(get("minute"), 10);
      } catch (e) { const d = new Date(); day = d.getDay(); mins = d.getHours() * 60 + d.getMinutes(); }
      const ranges = HOURS[day] || [];
      const r = ranges.find(([a, b]) => mins >= a * 60 && mins < b * 60);
      chip.classList.toggle("is-open", !!r);
      chip.classList.toggle("is-closed", !r);
      let txt = "Ahora cerrado · con cita previa";
      if (r) txt = "Abierto ahora · hasta las " + r[1] + ":00";
      else if (ranges.length && mins < ranges[0][0] * 60) txt = "Cerrado · abre hoy a las " + ranges[0][0] + ":00";
      else if (day === 5 || day === 6 || day === 0) txt = "Cerrado · abre el lunes a las 8:00";
      chip.textContent = txt;
    }
    update();
    setInterval(update, 60000);
  })();

  /* ---------- Split de texto en caracteres (texto íntegro para lectores de pantalla) ---------- */
  function splitChars(el) {
    const text = el.textContent;
    el.setAttribute("aria-label", text.replace(/\s+/g, " ").trim());
    const frag = document.createDocumentFragment();
    const walk = (node, parent) => {
      node.childNodes.forEach((n) => {
        if (n.nodeType === 3) {
          n.textContent.split(/(\s+)/).forEach((w) => {
            if (!w) return;
            if (/^\s+$/.test(w)) { parent.appendChild(document.createTextNode(" ")); return; }
            const ws = document.createElement("span");
            ws.className = "w";
            ws.setAttribute("aria-hidden", "true");
            [...w].forEach((ch) => { const c = document.createElement("span"); c.className = "c"; c.textContent = ch; ws.appendChild(c); });
            parent.appendChild(ws);
          });
        } else if (n.nodeType === 1) {
          const clone = n.cloneNode(false);
          walk(n, clone);
          parent.appendChild(clone);
        }
      });
    };
    walk(el, frag);
    el.textContent = "";
    el.appendChild(frag);
    el.classList.add("split");
  }

  const strokes = (svg) => svg.querySelectorAll(".ln, .tape");

  if (!motion) {
    // Estado final: láminas dibujadas y etiquetadas, tarjetas visibles, barras pintadas.
    document.querySelectorAll(".plate").forEach((s) => s.classList.add("is-drawn", "is-labeled"));
    document.querySelectorAll(".timeline").forEach((t) => t.style.setProperty("--line", 1));
    document.querySelectorAll(".h-fill").forEach((b) => { b.style.transform = "none"; });
    document.querySelectorAll(".h-arrow path").forEach((p) => { p.style.strokeDashoffset = 0; });
    return;
  }

  /* ====================================================================
     A partir de aquí: solo con motion (sin reduced-motion y con GSAP)
     ==================================================================== */

  /* Dibuja una lámina: trazos en orden DOM, etiquetas al final */
  function drawPlate(svg, opts) {
    const o = Object.assign({ duration: 1.0, stagger: 0.03, ease: "power2.inOut", delay: 0 }, opts || {});
    const paths = strokes(svg);
    svg.classList.remove("is-drawn", "is-labeled");
    gsap.killTweensOf(paths);
    gsap.set(paths, { strokeDashoffset: 1 });
    return gsap.to(paths, {
      strokeDashoffset: 0, duration: o.duration, ease: o.ease, stagger: o.stagger, delay: o.delay,
      onComplete: () => { svg.classList.add("is-drawn"); svg.classList.add("is-labeled"); },
    });
  }

  /* ---------- Portada: la columna se dibuja, el nombre aparece letra a letra ---------- */
  const hero = document.querySelector(".hero");
  const heroPlate = hero.querySelector(".plate");
  const h1 = hero.querySelector(".hero-title");
  splitChars(h1);
  const heroChars = h1.querySelectorAll(".c");
  gsap.set(heroChars, { yPercent: 108 });
  const heroTl = gsap.timeline({ defaults: { ease: "power2.out" } });
  heroTl
    .add(drawPlate(heroPlate, { duration: 0.9, stagger: 0.032, ease: "power2.inOut" }), 0)
    .to(heroChars, { yPercent: 0, duration: 1.15, stagger: { each: 0.045, from: "start" } }, 0.25)
    .to(hero.querySelectorAll(".hero-anim"), { opacity: 1, y: 0, duration: 1.0, stagger: 0.12 }, 0.9);
  gsap.set(hero.querySelectorAll(".hero-anim"), { y: 18 });
  // Parallax sutil de la lámina al abandonar la portada
  gsap.to(heroPlate.closest(".hero-plate"), { yPercent: -10, ease: "none", scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: true } });
  gsap.to(hero.querySelector(".hero-copy"), { yPercent: 6, opacity: 0.5, ease: "none", scrollTrigger: { trigger: hero, start: "40% top", end: "bottom top", scrub: true } });

  /* ---------- Titulares con char-reveal lento (0.9–1.2 s, power2.out) ---------- */
  document.querySelectorAll("[data-split]").forEach((el) => {
    splitChars(el);
    const chars = el.querySelectorAll(".c");
    gsap.set(chars, { yPercent: 108 });
    ScrollTrigger.create({
      trigger: el, start: "top 85%", once: true,
      onEnter: () => gsap.to(chars, { yPercent: 0, duration: 1.0, ease: "power2.out", stagger: { each: 0.022, from: "start" } }),
    });
  });

  /* ---------- Láminas al margen: se dibujan con el scroll (scrub) ---------- */
  document.querySelectorAll('[data-draw="scroll"] .plate').forEach((svg) => {
    const paths = strokes(svg);
    gsap.set(paths, { strokeDashoffset: 1 });
    gsap.to(paths, {
      strokeDashoffset: 0, ease: "none", stagger: 0.02,
      scrollTrigger: {
        trigger: svg, start: "top 92%", end: "center 45%", scrub: 0.8,
        onLeave: () => svg.classList.add("is-drawn", "is-labeled"),
        onEnterBack: () => svg.classList.remove("is-drawn", "is-labeled"),
      },
    });
    gsap.to(svg, { yPercent: -8, ease: "none", scrollTrigger: { trigger: svg, start: "top bottom", end: "bottom top", scrub: true } });
  });

  /* ---------- Reveals genéricos ---------- */
  document.querySelectorAll(".reveal-up").forEach((el) => {
    gsap.to(el, { opacity: 1, y: 0, duration: 1.0, ease: "power2.out", scrollTrigger: { trigger: el, start: "top 90%", once: true } });
  });

  /* ---------- Parallax suave de fotos ---------- */
  document.querySelectorAll("[data-parallax]").forEach((fig) => {
    const amt = parseFloat(fig.dataset.parallax) || 6;
    const img = fig.querySelector("img");
    gsap.fromTo(img, { yPercent: -Math.abs(amt), scale: 1.08 }, { yPercent: Math.abs(amt), scale: 1.08, ease: "none", scrollTrigger: { trigger: fig, start: "top bottom", end: "bottom top", scrub: true } });
    gsap.fromTo(fig, { y: amt > 0 ? 40 : 80 }, { y: amt > 0 ? -20 : -40, ease: "none", scrollTrigger: { trigger: fig, start: "top bottom", end: "bottom top", scrub: true } });
  });

  /* ---------- Tratamientos: sticky stack con la lámina cambiando por tarjeta ---------- */
  const trat = document.querySelector(".trat");
  if (trat) {
    const plates = [...trat.querySelectorAll(".trat-plate")];
    const cards = [...trat.querySelectorAll(".trat-card")];
    let active = -1;
    function activate(i) {
      if (i === active) return;
      active = i;
      plates.forEach((p, k) => p.classList.toggle("is-active", k === i));
      drawPlate(plates[i].querySelector(".plate"), { duration: 0.9, stagger: 0.02 });
    }
    cards.forEach((card, i) => {
      ScrollTrigger.create({
        trigger: card, start: "top 60%", end: "bottom 60%",
        onEnter: () => activate(i),
        onEnterBack: () => { activate(i); card.classList.remove("is-past"); },
        onLeave: () => card.classList.add("is-past"),
      });
      gsap.from(card, { y: 40, opacity: 0, duration: 0.9, ease: "power2.out", scrollTrigger: { trigger: card, start: "top 92%", once: true } });
    });
    // La primera lámina se dibuja al entrar la sección aunque aún no haya tarjeta "activa"
    ScrollTrigger.create({ trigger: trat.querySelector(".trat-layout"), start: "top 75%", once: true, onEnter: () => { if (active < 0) activate(0); } });
  }

  /* ---------- Sesión: la línea de la timeline se traza con el scroll ---------- */
  const timeline = document.querySelector(".timeline");
  if (timeline) {
    gsap.to(timeline, { "--line": 1, ease: "none", scrollTrigger: { trigger: timeline, start: "top 80%", end: "bottom 60%", scrub: 0.6 } });
  }

  /* ---------- Horario: 8:00 → 22:00 y barras que se pintan ---------- */
  const horario = document.querySelector(".horario");
  if (horario) {
    const big = horario.querySelector(".horario-big");
    const nums = [...big.querySelectorAll("[data-split-chars]")];
    nums.forEach(splitChars);
    const fromChars = nums[0].querySelectorAll(".c");
    const toChars = nums[1].querySelectorAll(".c");
    const arrow = big.querySelectorAll(".h-arrow path");
    gsap.set([fromChars, toChars], { yPercent: 108 });
    gsap.set(arrow, { strokeDashoffset: 1 });
    ScrollTrigger.create({
      trigger: big, start: "top 80%", once: true,
      onEnter: () => {
        const tl = gsap.timeline({ defaults: { ease: "power2.out" } });
        tl.to(fromChars, { yPercent: 0, duration: 1.0, stagger: 0.05 }, 0)
          .to(arrow[0], { strokeDashoffset: 0, duration: 1.1, ease: "power2.inOut" }, 0.5)
          .to(arrow[1], { strokeDashoffset: 0, duration: 0.35, ease: "power2.out" }, 1.4)
          .to(toChars, { yPercent: 0, duration: 1.1, stagger: 0.05 }, 1.2);
      },
    });
    const fills = horario.querySelectorAll(".h-fill");
    gsap.set(fills, { scaleX: 0 });
    ScrollTrigger.create({
      trigger: horario.querySelector(".horario-tabla"), start: "top 80%", once: true,
      onEnter: () => gsap.to(fills, { scaleX: 1, duration: 1.2, ease: "power2.out", stagger: 0.12 }),
    });
  }

  /* ---------- Botones magnéticos (solo puntero fino) ---------- */
  if (finePointer) {
    document.querySelectorAll(".btn").forEach((btn) => {
      const inner = btn.querySelector(".btn-inner") || btn;
      const strength = btn.classList.contains("btn-big") ? 0.4 : 0.28;
      let raf = null;
      btn.addEventListener("mousemove", (e) => {
        const r = btn.getBoundingClientRect();
        const dx = e.clientX - (r.left + r.width / 2);
        const dy = e.clientY - (r.top + r.height / 2);
        if (raf) return;
        raf = requestAnimationFrame(() => {
          gsap.to(btn, { x: dx * strength, y: dy * strength, duration: 0.5, ease: "power3.out" });
          if (inner !== btn) gsap.to(inner, { x: dx * strength * 0.4, y: dy * strength * 0.4, duration: 0.5, ease: "power3.out" });
          raf = null;
        });
      });
      btn.addEventListener("mouseleave", () => {
        gsap.to(btn, { x: 0, y: 0, duration: 0.9, ease: "elastic.out(1, 0.5)" });
        if (inner !== btn) gsap.to(inner, { x: 0, y: 0, duration: 0.9, ease: "elastic.out(1, 0.5)" });
      });
    });
  }

  /* ---------- Marquee lento, siempre hacia la izquierda, con un empuje suave según el scroll ---------- */
  const track = document.querySelector(".marquee-track");
  if (track) {
    const BASE = 26; // px/s: pausado
    let boost = 0, x = 0, half = track.scrollWidth / 2, last = performance.now();
    if (lenis) lenis.on("scroll", ({ velocity }) => { boost = Math.max(boost, Math.min(Math.abs(velocity) * 4, 120)); });
    window.addEventListener("resize", () => { half = track.scrollWidth / 2; }, { passive: true });
    gsap.ticker.add((t) => {
      const now = t * 1000, dt = Math.min((now - last) / 1000, 0.05); last = now;
      x -= (BASE + boost) * dt;
      if (x <= -half) x += half;
      boost *= 0.95;
      track.style.transform = "translate3d(" + x.toFixed(2) + "px,0,0)";
    });
  }

  window.addEventListener("load", () => ScrollTrigger.refresh());
})();
