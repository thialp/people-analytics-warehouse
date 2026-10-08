const opentype = require('opentype.js'); const fs = require('fs');
const F = w => opentype.loadSync(`node_modules/@fontsource/inter/files/inter-latin-${w}-normal.woff`);
const black = F(800), semi = F(600);
const NAVY = '#13233A', TEAL = '#00938D', WHITE = '#FFFFFF';
// text -> path with manual letter spacing; returns {d, width}
function text(font, str, size, x, y, tracking) {
  let d = '', cx = x;
  for (const ch of str) {
    const g = font.charToGlyph(ch);
    d += g.getPath(cx, y, size).toPathData(2);
    cx += g.advanceWidth / font.unitsPerEm * size + tracking;
  }
  return { d, width: cx - x - tracking };
}
// the mark: a rounded tile, an "A" drawn as a peak, a teal node where the crossbar would be
function mark(x, y, s, onDark = false) {
  const k = s / 120;
  const tile = onDark ? WHITE : NAVY, stroke = onDark ? NAVY : WHITE;
  return `<g transform="translate(${x},${y}) scale(${k})">
    <rect width="120" height="120" rx="28" fill="${tile}"/>
    <path d="M31 93 L60 29 L89 93" fill="none" stroke="${stroke}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="60" cy="75" r="8.5" fill="${onDark ? '#0B7F7A' : '#2EC4B6'}"/>
  </g>`;
}
function horizontal(onDark = false) {
  const ink = onDark ? WHITE : NAVY;
  const word = text(black, 'ARCADIA', 56, 150, 72, 3.5);
  const sub = text(semi, 'SYSTEMS', 18, 152, 104, 9.2);
  const W = Math.ceil(150 + Math.max(word.width, sub.width) + 8);
  return { W, svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} 120" width="${W}" height="120" role="img" aria-label="Arcadia Systems">
  <title>Arcadia Systems</title>${mark(0, 0, 120, onDark)}
  <path d="${word.d}" fill="${ink}"/><path d="${sub.d}" fill="${onDark ? '#5FD3C8' : TEAL}"/></svg>` };
}
const h = horizontal(false), hd = horizontal(true);
fs.writeFileSync('../arcadia_logo_horizontal.svg', h.svg);
fs.writeFileSync('../arcadia_logo_horizontal_reverse.svg', hd.svg);
fs.writeFileSync('../arcadia_logo_mark.svg', `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120" role="img" aria-label="Arcadia Systems"><title>Arcadia Systems</title>${mark(0,0,120)}</svg>`);
console.log('widths', h.W, hd.W);
