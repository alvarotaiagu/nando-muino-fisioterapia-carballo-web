// Verificación con Playwright para Nando Muiño · Fisioterapia y Osteopatía:
//  - sin errores JS en carga ni tras scroll
//  - longtasks (PerformanceObserver) durante la intro (columna + nombre) y el scroll completo
//  - la lámina de la portada acaba dibujada (strokeDashoffset 0) y con etiquetas visibles
//  - el aviso de cookies funciona (display:none real) y se recuerda tras recargar
//  - CTAs de portada y cabecera reciben el clic (sin zonas muertas)
//  - el mapa no tiene iframe hasta el clic, y lo tiene después (google.com/maps?q=…&output=embed)
//  - sticky stack de tratamientos: la lámina activa cambia con la tarjeta y se dibuja
//  - horario: barras pintadas (scaleX 1) y flecha dibujada; timeline trazada
//  - reduced-motion: sin Lenis, láminas ya dibujadas y etiquetadas, textos visibles
//  - sin JS: contenido usable, láminas visibles, mapa placeholder visible
//  - sin scroll horizontal a 1440, 400 y 360 px
//  - capturas de cada sección en escritorio (1440) y móvil (400)
// Uso: node scripts/verify.js [baseUrl]   (por defecto http://127.0.0.1:8931/)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const base = process.argv[2] || 'http://127.0.0.1:8931/';
const outDir = path.resolve(__dirname, '..', 'screenshots');
fs.mkdirSync(outDir, { recursive: true });
const report = { ok: true, checks: [], longtasks: {}, screenshots: [] };
const check = (name, pass, detail) => { report.checks.push({ name, pass, detail }); if (!pass) report.ok = false; console.log(`${pass ? 'PASS' : 'FAIL'}  ${name}${detail ? ' — ' + detail : ''}`); };
const SECTIONS = ['#inicio', '#manifiesto', '#osteopatia', '#tratamientos', '#sesion', '#horario', '#resenas', '#contacto', '.site-footer'];
const ownError = (m) => m.type() === 'error' && !/google\.com|googleapis\.com|gstatic\.com/.test((m.location() && m.location().url) || m.text());

async function scrollThrough(page, step = 600, pause = 90) {
  const total = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < total; y += step) { await page.mouse.wheel(0, step); await page.waitForTimeout(pause); }
  await page.waitForTimeout(900);
}
const drawnCount = (page, sel) => page.evaluate((s) => {
  const ps = [...document.querySelectorAll(s + ' .ln, ' + s + ' .tape')];
  return [ps.length, ps.filter((p) => Math.abs(parseFloat(getComputedStyle(p).strokeDashoffset)) < 0.02).length];
}, sel);

(async () => {
  const browser = await chromium.launch();

  /* ---------- Escritorio ---------- */
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.addInitScript(() => {
    window.__lt = [];
    try { new PerformanceObserver((l) => l.getEntries().forEach((e) => window.__lt.push({ d: Math.round(e.duration), t: Math.round(e.startTime) }))).observe({ entryTypes: ['longtask'] }); } catch (e) {}
  });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => { if (ownError(m)) errors.push(m.text()); });
  await page.goto(base, { waitUntil: 'load' });
  const ltLoad = await page.evaluate(() => window.__lt.splice(0));
  report.longtasks.load = ltLoad;
  console.log(`INFO  longtasks hasta load: ${JSON.stringify(ltLoad)}`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3400); // intro: columna (~2.7 s) + nombre
  const ltHero = await page.evaluate(() => window.__lt.splice(0));
  report.longtasks.hero = ltHero;
  check('sin errores JS en carga', errors.length === 0, errors.join(' | '));
  check('sin longtasks (>50ms) durante la intro de la portada', ltHero.filter((e) => e.d > 50).length === 0, JSON.stringify(ltHero));
  const [heroTotal, heroDrawn] = await drawnCount(page, '.hero-plate');
  check('lámina de la portada dibujada por completo', heroTotal > 20 && heroDrawn === heroTotal, `${heroDrawn}/${heroTotal}`);
  const heroLbl = await page.evaluate(() => getComputedStyle(document.querySelector('.hero-plate .lbl')).opacity);
  check('etiquetas de la lámina visibles tras el dibujo', parseFloat(heroLbl) > 0.9, `opacity=${heroLbl}`);
  const titleVisible = await page.evaluate(() => { const c = document.querySelector('.hero-title .c'); const m = new DOMMatrixReadOnly(getComputedStyle(c).transform); return Math.abs(m.f) < 1; });
  check('nombre en portada revelado (char-reveal completado)', titleVisible);

  // --- cookies ---
  const bannerVisible = await page.locator('.cookie-banner').isVisible();
  check('aviso de cookies visible en primera visita', bannerVisible);
  await page.click('.cookie-ack');
  await page.waitForTimeout(150);
  const bannerDisplay = await page.evaluate(() => getComputedStyle(document.querySelector('.cookie-banner')).display);
  check('botón "Entendido" oculta el aviso (display:none real)', bannerDisplay === 'none', `display=${bannerDisplay}`);
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  const bannerAfter = await page.evaluate(() => getComputedStyle(document.querySelector('.cookie-banner')).display);
  check('aviso de cookies recordado tras recargar', bannerAfter === 'none');

  // --- CTAs sin zonas muertas ---
  await page.waitForTimeout(3000);
  const dead = await page.evaluate(() => {
    const out = [];
    for (const sel of ['.hero .btn-big', '.hero .btn-link', '.site-header .nav-cita', '.nav-links a']) {
      const el = document.querySelector(sel); if (!el) { out.push(sel + ' no existe'); continue; }
      const r = el.getBoundingClientRect();
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      if (!hit || !(el === hit || el.contains(hit))) out.push(sel + ' -> ' + (hit ? hit.tagName + '.' + hit.className : 'nada'));
    }
    return out;
  });
  check('CTAs de portada y cabecera reciben el clic', dead.length === 0, dead.join(' | '));

  // --- mapa por consentimiento ---
  const iframesBefore = await page.locator('.map iframe').count();
  check('mapa sin iframe antes del clic', iframesBefore === 0);
  await page.locator('#contacto').scrollIntoViewIfNeeded();
  await page.waitForTimeout(600);
  await page.click('.map-consent');
  await page.waitForTimeout(800);
  const iframesAfter = await page.locator('.map iframe').count();
  const src = iframesAfter ? await page.locator('.map iframe').getAttribute('src') : '';
  check('mapa cargado tras el clic (google.com/maps?q=…&output=embed)', iframesAfter === 1 && /google\.com\/maps\?q=.*output=embed/.test(src), src);

  // --- scroll completo + longtasks ---
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);
  await page.evaluate(() => window.__lt.splice(0));
  await scrollThrough(page);
  const ltScroll = await page.evaluate(() => window.__lt.splice(0));
  report.longtasks.scroll = ltScroll;
  check('sin longtasks (>50ms) durante el scroll completo', ltScroll.filter((e) => e.d > 50).length === 0, JSON.stringify(ltScroll));
  check('sin errores JS tras el scroll', errors.length === 0, errors.join(' | '));
  const sw = await page.evaluate(() => document.documentElement.scrollWidth);
  check('sin scroll horizontal a 1440 px', sw <= 1440, `scrollWidth=${sw}`);

  // --- láminas al margen dibujadas tras el scroll ---
  const [mTot, mDr] = await drawnCount(page, '.inline-plate, .margin-plate');
  check('láminas al margen dibujadas tras pasar por ellas', mTot > 0 && mDr === mTot, `${mDr}/${mTot}`);

  // --- horario y timeline ---
  const fills = await page.evaluate(() => [...document.querySelectorAll('.h-fill')].map((f) => new DOMMatrixReadOnly(getComputedStyle(f).transform).a.toFixed(2)));
  check('horario: las 5 barras pintadas (scaleX 1)', fills.length === 5 && fills.every((v) => v === '1.00'), fills.join('/'));
  const arrow = await page.evaluate(() => [...document.querySelectorAll('.h-arrow path')].map((p) => parseFloat(getComputedStyle(p).strokeDashoffset)));
  check('horario: flecha 8:00 → 22:00 dibujada', arrow.every((v) => Math.abs(v) < 0.02), arrow.join('/'));
  const line = await page.evaluate(() => getComputedStyle(document.querySelector('.timeline')).getPropertyValue('--line').trim());
  check('sesión: línea de la timeline trazada', parseFloat(line) >= 0.99, `--line=${line}`);

  // --- sticky stack tratamientos: lámina activa cambia con la tarjeta ---
  const goCard = async (i) => { await page.evaluate((k) => { const c = document.querySelectorAll('.trat-card')[k]; window.scrollTo(0, c.getBoundingClientRect().top + window.scrollY - window.innerHeight * 0.45); }, i); await page.waitForTimeout(1500); };
  await goCard(0);
  const act0 = await page.evaluate(() => document.querySelector('.trat-plate.is-active').dataset.plate);
  await goCard(3);
  const act3 = await page.evaluate(() => document.querySelector('.trat-plate.is-active').dataset.plate);
  const [tTot, tDr] = await drawnCount(page, '.trat-plate.is-active');
  check('sticky stack: la lámina activa cambia con la tarjeta (0 → 3)', act0 === '0' && act3 === '3', `${act0} -> ${act3}`);
  check('sticky stack: la lámina activa se dibuja por completo', tTot > 0 && tDr === tTot, `${tDr}/${tTot}`);
  const past = await page.evaluate(() => document.querySelectorAll('.trat-card.is-past').length);
  check('sticky stack: tarjetas anteriores marcadas como pasadas', past >= 2, `is-past=${past}`);
  const sticky = await page.evaluate(() => getComputedStyle(document.querySelector('.trat-figure')).position);
  check('sticky stack: la figura es sticky', sticky === 'sticky', sticky);

  // --- capturas de cada sección ---
  for (const sel of SECTIONS) {
    await page.locator(sel).first().scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    const file = path.join(outDir, `desktop-${sel.replace(/[#.]/g, '')}.png`);
    await page.screenshot({ path: file });
    report.screenshots.push(file);
  }
  await ctx.close();

  /* ---------- Reduced motion ---------- */
  const ctxR = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  const pageR = await ctxR.newPage();
  const errR = [];
  pageR.on('pageerror', (e) => errR.push(String(e)));
  await pageR.goto(base, { waitUntil: 'networkidle' });
  await pageR.waitForTimeout(400);
  const rm = await pageR.evaluate(() => ({
    reduced: document.documentElement.classList.contains('is-reduced'),
    lenis: !!window.nmLenis,
    dash: [...document.querySelectorAll('.plate .ln')].every((p) => Math.abs(parseFloat(getComputedStyle(p).strokeDashoffset)) < 0.02),
    lbl: [...document.querySelectorAll('.plate .lbl')].every((l) => parseFloat(getComputedStyle(l).opacity) > 0.9),
    title: getComputedStyle(document.querySelector('.hero-title')).opacity === '1' && !document.querySelector('.hero-title .c'),
    reveals: [...document.querySelectorAll('.reveal-up')].every((el) => getComputedStyle(el).opacity === '1'),
    fills: [...document.querySelectorAll('.h-fill')].every((f) => new DOMMatrixReadOnly(getComputedStyle(f).transform).a > 0.99),
  }));
  check('reduced-motion: clase is-reduced y sin Lenis', rm.reduced && !rm.lenis, JSON.stringify(rm));
  check('reduced-motion: láminas ya dibujadas y etiquetadas', rm.dash && rm.lbl);
  check('reduced-motion: nombre, textos y barras visibles sin animación', rm.title && rm.reveals && rm.fills);
  check('reduced-motion: sin errores JS', errR.length === 0, errR.join(' | '));
  await pageR.screenshot({ path: path.join(outDir, 'reduced-motion.png') });
  await ctxR.close();

  /* ---------- Sin JavaScript ---------- */
  const ctxN = await browser.newContext({ viewport: { width: 1440, height: 900 }, javaScriptEnabled: false });
  const pageN = await ctxN.newPage();
  await pageN.goto(base, { waitUntil: 'load' });
  const noJs = await pageN.evaluate(() => ({
    nojs: document.documentElement.classList.contains('no-js'),
    title: getComputedStyle(document.querySelector('.hero-title')).opacity === '1',
    plate: Math.abs(parseFloat(getComputedStyle(document.querySelector('.hero-plate .ln')).strokeDashoffset)) < 0.02,
    lbl: parseFloat(getComputedStyle(document.querySelector('.hero-plate .lbl')).opacity) > 0.9,
    map: !!document.querySelector('.map-consent') && getComputedStyle(document.querySelector('.map-consent')).display !== 'none',
    fallback: !!document.querySelector('.map-fallback'),
    reveals: [...document.querySelectorAll('.reveal-up')].every((el) => getComputedStyle(el).opacity === '1'),
  }));
  check('sin JS: contenido, láminas y mapa placeholder visibles', noJs.nojs && noJs.title && noJs.plate && noJs.lbl && noJs.map && noJs.fallback && noJs.reveals, JSON.stringify(noJs));
  await pageN.screenshot({ path: path.join(outDir, 'no-js.png') });
  await ctxN.close();

  /* ---------- Móvil 400 y 360 ---------- */
  for (const w of [400, 360]) {
    const ctxM = await browser.newContext({ viewport: { width: w, height: 800 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const pageM = await ctxM.newPage();
    const errM = [];
    pageM.on('pageerror', (e) => errM.push(String(e)));
    await pageM.goto(base, { waitUntil: 'networkidle' });
    await pageM.waitForTimeout(3200);
    await scrollThrough(pageM, 500, 60);
    const swM = await pageM.evaluate(() => document.documentElement.scrollWidth);
    check(`sin scroll horizontal a ${w} px`, swM <= w, `scrollWidth=${swM}`);
    check(`sin errores JS a ${w} px`, errM.length === 0, errM.join(' | '));
    if (w === 400) {
      await pageM.evaluate(() => window.scrollTo(0, 0));
      await pageM.waitForTimeout(600);
      await pageM.click('.nav-toggle');
      await pageM.waitForTimeout(600);
      const menuOpen = await pageM.evaluate(() => !document.querySelector('.mobile-menu').hidden && document.querySelector('.nav-toggle').getAttribute('aria-expanded') === 'true');
      check('móvil: el menú se abre', menuOpen);
      await pageM.screenshot({ path: path.join(outDir, 'mobile-menu.png') });
      await pageM.click('.mobile-menu nav a[href="#horario"]');
      await pageM.waitForTimeout(1800);
      const menuClosed = await pageM.evaluate(() => document.querySelector('.mobile-menu').hidden);
      const nearHorario = await pageM.evaluate(() => Math.abs(document.querySelector('#horario').getBoundingClientRect().top) < 120);
      check('móvil: al elegir una sección el menú se cierra y navega', menuClosed && nearHorario);
      const fab = await pageM.evaluate(() => getComputedStyle(document.querySelector('.call-fab')).display !== 'none');
      check('móvil: botón flotante de llamada presente', fab);
      const stickyM = await pageM.evaluate(() => getComputedStyle(document.querySelector('.trat-figure')).position);
      check('móvil: la figura de tratamientos sigue siendo sticky', stickyM === 'sticky', stickyM);
      for (const sel of SECTIONS) {
        await pageM.locator(sel).first().scrollIntoViewIfNeeded();
        await pageM.waitForTimeout(900);
        const file = path.join(outDir, `mobile-${sel.replace(/[#.]/g, '')}.png`);
        await pageM.screenshot({ path: file });
        report.screenshots.push(file);
      }
    }
    await ctxM.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(__dirname, 'verify-report.json'), JSON.stringify(report, null, 2));
  console.log(report.ok ? '\nTODO OK' : '\nHAY FALLOS');
  process.exit(report.ok ? 0 : 1);
})();
