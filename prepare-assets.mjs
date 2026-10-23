// ينسخ الخطوط العربية والمكتبات من node_modules إلى www (يعمل وقت البناء)
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const nm = path.join(root, 'node_modules');
const out = path.join(root, 'www');
fs.mkdirSync(path.join(out, 'fonts'), { recursive: true });
fs.mkdirSync(path.join(out, 'lib'), { recursive: true });

// [اسم الخط في CSS, اسم حزمة fontsource, الأوزان]
const FONTS = [
  ['Amiri', 'amiri', [400, 700]],
  ['Scheherazade New', 'scheherazade-new', [400, 700]],
  ['Noto Naskh Arabic', 'noto-naskh-arabic', [400, 700]],
  ['Lateef', 'lateef', [400, 700]],
  ['Markazi Text', 'markazi-text', [400, 700]],
  ['Aref Ruqaa', 'aref-ruqaa', [400, 700]],
  ['Reem Kufi', 'reem-kufi', [400, 700]],
  ['Noto Kufi Arabic', 'noto-kufi-arabic', [400, 700]],
  ['Cairo', 'cairo', [400, 700]],
  ['El Messiri', 'el-messiri', [400, 700]],
  ['Mirza', 'mirza', [400, 700]],
  ['Harmattan', 'harmattan', [400, 700]],
  ['Katibeh', 'katibeh', [400]],
  ['Rakkas', 'rakkas', [400]],
  ['Lalezar', 'lalezar', [400]],
];

const AR_RANGE = 'U+0600-06FF,U+0750-077F,U+08A0-08FF,U+FB50-FDFF,U+FE70-FEFF,U+200C-200E,U+2010-2011,U+204F,U+25CC';
const LATIN_RANGE = 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215';

let css = '/* مُولَّد تلقائياً بواسطة scripts/prepare-assets.mjs */\n';
let ok = 0, miss = 0;

for (const [family, pkg, weights] of FONTS) {
  const dir = path.join(nm, '@fontsource', pkg, 'files');
  for (const w of weights) {
    for (const [subset, range] of [['arabic', AR_RANGE], ['latin', LATIN_RANGE]]) {
      const name = `${pkg}-${subset}-${w}-normal.woff2`;
      const src = path.join(dir, name);
      if (!fs.existsSync(src)) { if (subset === 'arabic') { miss++; console.warn('مفقود:', name); } continue; }
      fs.copyFileSync(src, path.join(out, 'fonts', name));
      css += `@font-face{font-family:"${family} Local";font-style:normal;font-weight:${w};font-display:swap;` +
             `src:url("${name}") format("woff2");unicode-range:${range}}\n`;
      if (subset === 'arabic') ok++;
    }
  }
}
fs.writeFileSync(path.join(out, 'fonts', 'fonts.css'), css);
console.log(`الخطوط: ${ok} ملف عربي، المفقود: ${miss}`);

const libs = [
  ['html-to-image/dist/html-to-image.js', 'html-to-image.js'],
  ['jspdf/dist/jspdf.umd.min.js', 'jspdf.umd.min.js'],
];
for (const [from, to] of libs) {
  const src = path.join(nm, from);
  if (!fs.existsSync(src)) throw new Error('مكتبة مفقودة: ' + from);
  fs.copyFileSync(src, path.join(out, 'lib', to));
  console.log('مكتبة:', to);
}
