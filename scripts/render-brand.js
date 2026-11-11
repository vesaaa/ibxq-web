// Renders the PNG exports listed by scripts/build-brand.py. Not meant to be run on its own.
const fs = require('fs');
const { chromium } = require('playwright');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const [src, out, w, h] of jobs) {
    const svg = fs.readFileSync(src, 'utf8');
    const vb = svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
    const height = h || Math.round(w * vb[3] / vb[2]), width = w || Math.round(h * vb[2] / vb[3]);
    await page.setViewportSize({ width, height });
    await page.setContent('<style>html,body{margin:0;background:transparent}svg{display:block;width:' + width + 'px;height:' + height + 'px}</style>' + svg);
    await page.screenshot({ path: out, omitBackground: true, clip: { x: 0, y: 0, width, height } });
  }
  await browser.close();
})();
