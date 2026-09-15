// Genera los iconos PNG (96/180/192/512) a partir de assets/img/logo/icon.svg y la
// imagen Open Graph (1200x630) con el logo rediseñado, usando Chromium (Playwright).
// Uso: node scripts/generate_icons.js
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const root = path.resolve(__dirname, '..');
const logoDir = path.join(root, 'assets', 'img', 'logo');
const webDir = path.join(root, 'assets', 'img', 'web');
fs.mkdirSync(webDir, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const icon = fs.readFileSync(path.join(logoDir, 'icon.svg'), 'utf8');
  for (const size of [96, 180, 192, 512]) {
    const page = await browser.newPage({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
    await page.setContent(`<html><body style="margin:0;background:transparent">${icon.replace('width="120" height="120"', `width="${size}" height="${size}"`)}</body></html>`);
    await page.screenshot({ path: path.join(logoDir, `icon-${size}.png`), omitBackground: true });
    await page.close();
    console.log('icon', size);
  }
  const logo = fs.readFileSync(path.join(logoDir, 'logo.svg'), 'utf8');
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  await page.setContent(`<html><head><style>
    body{margin:0;width:1200px;height:630px;background:#EFE9DF;font-family:Georgia,serif;color:#2B2622;display:flex;flex-direction:column;justify-content:center;padding:0 90px;box-sizing:border-box;position:relative;overflow:hidden}
    svg{width:640px;height:auto}
    p{margin:34px 0 0;font:500 20px/1 Arial,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#59634A}
    .l{position:absolute;left:90px;right:90px;bottom:70px;height:1px;background:rgba(43,38,34,.25)}
    .c{position:absolute;right:90px;bottom:34px;font:500 16px/1 Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#8A8078}
  </style></head><body>${logo}<p>Carballo · Rúa Vila de Ordes, 23 · L–J 8:00–22:00</p><div class="l"></div><div class="c">698 11 16 68</div></body></html>`);
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(webDir, 'og-image.jpg'), type: 'jpeg', quality: 88 });
  console.log('og-image');
  await browser.close();
})();
