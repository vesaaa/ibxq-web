// Renders brand/preview.png, an overview of every logo variant. Run by scripts/build-brand.py.
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const DIR = path.resolve(__dirname, '..', 'brand');
const B = '';
const rows = [
  ['原版', 'dark', ['svg/ibxq-mark-original.svg', 'svg/ibxq-logo-zh-original-on-dark.svg', 'svg/ibxq-logo-en-original-on-dark.svg']],
  ['原版（浅色底）', 'light', ['svg/ibxq-mark-original.svg', 'svg/ibxq-logo-zh-original-on-light.svg', 'svg/ibxq-logo-en-original-on-light.svg']],
  ['纯白线条', 'dark', ['svg/ibxq-mark-white.svg', 'svg/ibxq-logo-zh-white.svg', 'svg/ibxq-logo-en-white.svg']],
  ['纯黑线条', 'light', ['svg/ibxq-mark-black.svg', 'svg/ibxq-logo-zh-black.svg', 'svg/ibxq-logo-en-black.svg']],
  ['平面版', 'dark', ['svg/ibxq-mark-flat.svg', 'svg/ibxq-logo-zh-flat-on-dark.svg', 'svg/ibxq-logo-en-flat-on-dark.svg']],
  ['平面版（浅色底）', 'light', ['svg/ibxq-mark-flat.svg', 'svg/ibxq-logo-zh-flat-on-light.svg', 'svg/ibxq-logo-en-flat-on-light.svg']],
];
const small = ['original', 'white', 'flat', 'black'];
const html = `<style>body{margin:0;padding:32px;background:#0B1024;font:13px/1.4 -apple-system,"PingFang SC","Noto Sans SC",sans-serif;color:#98A0B8;width:1136px}
.r{display:grid;grid-template-columns:120px 150px 1fr 1fr;gap:16px;align-items:center;margin-bottom:12px}
.c{border-radius:12px;padding:18px 22px;display:flex;align-items:center;height:108px}.dark{background:#060914}.light{background:#F1F2F6}
.c img{height:72px}.c.m img{height:92px;margin:auto}
.s{display:flex;gap:28px;align-items:center;border-radius:12px;padding:16px 22px}h3{margin:20px 0 10px;color:#ECEEF6;font-size:14px}</style>` +
  rows.map(r => `<div class="r"><div>${r[0]}</div><div class="c m ${r[1]}"><img src="${B + r[2][0]}"></div><div class="c ${r[1]}"><img src="${B + r[2][1]}"></div><div class="c ${r[1]}"><img src="${B + r[2][2]}"></div></div>`).join('') +
  `<h3>小尺寸（32 像素及以下用简化版）与应用图标</h3><div style="display:flex;gap:16px;flex-wrap:wrap">` +
  small.map(s => `<div class="s ${s === 'black' || s === 'flat' ? 'light' : 'dark'}">${[48, 32, 24, 16].map(n => `<img src="${B}png/mark/${s}/ibxq-mark-${s}-${n}.png" width="${n}" height="${n}">`).join('')}</div>`).join('') +
  `<div class="s dark"><img src="${B}app-icon/ibxq-app-icon-rounded-256.png" width="72"><img src="${B}app-icon/ibxq-app-icon-180.png" width="72"></div></div>`;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 800 }, deviceScaleFactor: 2 });
  const tmp = path.join(DIR, '_preview.html');
  fs.writeFileSync(tmp, '<!doctype html><meta charset="utf-8">' + html);
  await p.goto('file://' + tmp); await p.waitForTimeout(600);
  await p.screenshot({ path: path.join(DIR, 'preview.png'), fullPage: true });
  fs.unlinkSync(tmp);
  await b.close();
})();
