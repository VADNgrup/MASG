'use strict';
const PptxGenJS = require('pptxgenjs');
const fs   = require('fs');

// cli
const argv = process.argv.slice(2);
const get  = f => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : null; };
const manifestPath = get('--manifest');
const outputPath   = get('--output');
if (!manifestPath || !outputPath) {
  console.error('Usage: node deck_pptx_gen.js --manifest <path> --output <path>');
  process.exit(1);
}
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

// theme
const T      = manifest.theme || {};
const BGDARK = T.bg_dark    || '500014';
const BGLIT  = T.bg_light   || 'F5F3EE';
const ACC    = T.accent     || 'FFCC33';
const FGDRK  = T.text_dark  || 'FFFFFF';
const FGLIT  = T.text_light || '0B0D12';
const DIMDRK = 'AAAAAA';   // muted text on dark slides
const DIMLIT = '888888';   // muted text on light slides

const FDISP = T.font_display || 'Playfair Display';
const FBODY = T.font_body    || 'Source Sans 3';
const FMONO = T.font_mono    || 'IBM Plex Mono';

const C1 = T.c1 || '5b9bd5';
const C2 = T.c2 || 'e07b6a';
const C3 = T.c3 || '7b68c8';
const C4 = T.c4 || 'f0a050';
const CARD_COLORS = [C1, C2, C3, C4];

const DARK_BG = manifest.dark_bg_path || null;

function setBg(slide, isLight) {
  if (isLight) {
    slide.background = { color: BGLIT };
  } else if (DARK_BG && fs.existsSync(DARK_BG)) {
    slide.background = { path: DARK_BG };
  } else {
    slide.background = { color: BGDARK };
  }
}

function fgC(light)  { return light ? FGLIT  : FGDRK;  }
function dimC(light) { return light ? DIMLIT : DIMDRK; }

// geometry
const W  = 13.33;
const H  = 7.50;
const MX = 0.67;              // horizontal margin
const BW = W - MX * 2;       // full body width ≈ 11.99"

const CTOP_Y = 0.35, CTOP_H = 0.28;  // chrome-top band
const CBOT_Y = 6.90, CBOT_H = 0.28;  // chrome-bot band
const TTL_Y  = 1.00, TTL_H  = 1.00;  // title text box
const ULN_Y  = 2.02, ULN_H  = 0.05, ULN_W = 1.4;  // accent underline
const BODY_Y = 2.18;
const BODY_H = CBOT_Y - BODY_Y - 0.10;  // ≈ 4.62"

// Two-column split (55 / 45)
const LHS_W = BW * 0.55;
const RHS_X = MX + LHS_W + 0.20;
const RHS_W = BW - LHS_W - 0.20;

// latex-readable-unicode-text
const LMAP = {
  '\\leq':'≤','\\geq':'≥','\\neq':'≠','\\approx':'≈','\\equiv':'≡',
  '\\times':'×','\\cdot':'·','\\infty':'∞','\\pm':'±','\\mp':'∓',
  '\\alpha':'α','\\beta':'β','\\gamma':'γ','\\delta':'δ',
  '\\epsilon':'ε','\\varepsilon':'ε','\\zeta':'ζ','\\eta':'η','\\theta':'θ',
  '\\iota':'ι','\\kappa':'κ','\\lambda':'λ','\\mu':'μ',
  '\\nu':'ν','\\xi':'ξ','\\pi':'π','\\rho':'ρ',
  '\\sigma':'σ','\\tau':'τ','\\phi':'φ','\\varphi':'φ','\\chi':'χ',
  '\\psi':'ψ','\\omega':'ω',
  '\\Gamma':'Γ','\\Delta':'Δ','\\Theta':'Θ','\\Lambda':'Λ',
  '\\Xi':'Ξ','\\Pi':'Π','\\Sigma':'Σ','\\Phi':'Φ','\\Psi':'Ψ','\\Omega':'Ω',
  '\\rightarrow':'→','\\leftarrow':'←','\\Rightarrow':'⇒','\\Leftarrow':'⇐',
  '\\leftrightarrow':'↔','\\longrightarrow':'⟶','\\longleftarrow':'⟵',
  '\\sum':'∑','\\prod':'∏','\\int':'∫','\\oint':'∮',
  '\\sqrt':'√','\\nabla':'∇','\\partial':'∂',
  '\\forall':'∀','\\exists':'∃','\\in':'∈','\\notin':'∉',
  '\\subset':'⊂','\\supset':'⊃','\\subseteq':'⊆','\\supseteq':'⊇',
  '\\cup':'∪','\\cap':'∩','\\emptyset':'∅',
  '\\not':'¬','\\neg':'¬','\\wedge':'∧','\\vee':'∨',
  '\\langle':'⟨','\\rangle':'⟩','\\|':'‖',
  '\\cdots':'⋯','\\ldots':'…','\\vdots':'⋮','\\ddots':'⋱',
  '\\to':'→','\\gets':'←','\\mapsto':'↦',
  '\\le':'≤','\\ge':'≥','\\ne':'≠','\\ll':'≪','\\gg':'≫',
  '\\propto':'∝','\\sim':'∼','\\simeq':'≃','\\cong':'≅',
  '\\text':'',
};

// Unicode superscript / subscript maps
const SUP_MAP = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵',
                 '6':'⁶','7':'⁷','8':'⁸','9':'⁹',
                 'n':'ⁿ','i':'ⁱ','+':'⁺','-':'⁻','=':'⁼','(':'⁽',')':'⁾'};
const SUB_MAP = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅',
                 '6':'₆','7':'₇','8':'₈','9':'₉',
                 'n':'ₙ','i':'ᵢ','j':'ⱼ','k':'ₖ','m':'ₘ','p':'ₚ',
                 'a':'ₐ','e':'ₑ','o':'ₒ','u':'ᵤ','x':'ₓ'};

function _mapStr(str, map) {
  return str.split('').map(c => map[c] || c).join('');
}

function toMathText(text) {
  // Full conversion of LaTeX to unicode math text (for formula boxes)
  if (!text) return '';
  text = String(text);
  // Strip display delimiters
  text = text.replace(/\$\$(.+?)\$\$/gs, '$1');
  text = text.replace(/\$(.+?)\$/gs,     '$1');
  text = text.replace(/\\\[(.+?)\\\]/gs, '$1');
  text = text.replace(/\\\((.+?)\\\)/gs, '$1');
  // Fractions: \frac{a}{b} → (a)/(b)
  text = text.replace(/\\frac\{([^{}]*)\}\{([^{}]*)\}/g, '($1)/($2)');
  // Superscripts: ^{abc} or ^x
  text = text.replace(/\^\{([^}]+)\}/g, (_, g) => _mapStr(g, SUP_MAP));
  text = text.replace(/\^([a-zA-Z0-9])/g, (_, c) => SUP_MAP[c] || `^${c}`);
  // Subscripts: _{abc} or _x
  text = text.replace(/\_\{([^}]+)\}/g, (_, g) => _mapStr(g, SUB_MAP));
  text = text.replace(/\_([a-zA-Z0-9])/g, (_, c) => SUB_MAP[c] || `_${c}`);
  // sqrt: \sqrt{x} → √x, \sqrt[n]{x} → ⁿ√x
  text = text.replace(/\\sqrt\[([^\]]+)\]\{([^{}]*)\}/g, (_, n, x) => `${_mapStr(n, SUP_MAP)}√(${x})`);
  text = text.replace(/\\sqrt\{([^{}]*)\}/g, (_, x) => `√(${x})`);
  // Apply symbol map
  for (const [k, v] of Object.entries(LMAP)) text = text.split(k).join(v);
  // Remove remaining LaTeX commands with braced args
  text = text.replace(/\\[a-zA-Z]+\{([^}]*)\}/g, '$1');
  text = text.replace(/\\[a-zA-Z]+/g, '');
  text = text.replace(/[{}]/g, '');
  // Alignment markers
  text = text.replace(/&/g, '  ').replace(/\\\\/g, '\n');
  return text.replace(/[ \t]+/g, ' ').trim();
}

function toPlain(text) {
  // Simplified version for bullets/titles (strips math, no unicode conversion)
  if (!text) return '';
  text = String(text);
  text = text.replace(/\$\$(.+?)\$\$/gs, '$1');
  text = text.replace(/\$(.+?)\$/gs,     '$1');
  text = text.replace(/\\\[(.+?)\\\]/gs, '$1');
  text = text.replace(/\\\((.+?)\\\)/gs, '$1');
  for (const [k, v] of Object.entries(LMAP)) text = text.split(k).join(v);
  text = text.replace(/\\frac\{([^{}]*)\}\{([^{}]*)\}/g, '($1)/($2)');
  text = text.replace(/\^\{([^}]+)\}/g, (_, g) => _mapStr(g, SUP_MAP));
  text = text.replace(/\^([a-zA-Z0-9])/g, (_, c) => SUP_MAP[c] || `^${c}`);
  text = text.replace(/\_\{([^}]+)\}/g, (_, g) => _mapStr(g, SUB_MAP));
  text = text.replace(/\_([a-zA-Z0-9])/g, (_, c) => SUB_MAP[c] || `_${c}`);
  text = text.replace(/\\[a-zA-Z]+\{([^}]*)\}/g, '$1');
  text = text.replace(/\\[a-zA-Z]+/g, '');
  text = text.replace(/[{}]/g, '');
  return text.replace(/\s+/g, ' ').trim();
}

// pptxgenjs-instance
const pptx    = new PptxGenJS();
pptx.layout   = 'LAYOUT_WIDE';
pptx.title    = manifest.lecture_title || '';
pptx.author   = manifest.speaker       || '';
pptx.subject  = manifest.lecture_title || '';

// shared-helpers
function addChrome(slide, isLight, pageNum) {
  const dim = dimC(isLight);
  const lt  = (manifest.lecture_title || '');
  const lbl = lt.length > 58 ? lt.slice(0, 58) + '…' : lt;

  // Accent dot
  slide.addShape(pptx.ShapeType.ellipse, {
    x: MX, y: CTOP_Y + 0.09, w: 0.10, h: 0.10,
    fill: { color: ACC }, line: { type: 'none' },
  });
  // Lecture title (truncated)
  if (lbl) {
    slide.addText(lbl, {
      x: MX + 0.18, y: CTOP_Y, w: BW - 0.18 - 1.5, h: CTOP_H,
      fontSize: 11, color: dim, fontFace: FMONO, valign: 'middle', charSpacing: 1.5,
    });
  }
  // Date
  if (manifest.date) {
    slide.addText(manifest.date, {
      x: MX, y: CBOT_Y, w: 3.0, h: CBOT_H,
      fontSize: 9, color: dim, fontFace: FMONO, valign: 'middle',
    });
  }
  // Page number
  if (pageNum) {
    slide.addText(String(pageNum), {
      x: W - MX - 0.9, y: CBOT_Y, w: 0.9, h: CBOT_H,
      fontSize: 9, color: ACC, fontFace: FMONO, valign: 'middle', align: 'right',
    });
  }
}

function titleFontSize(title) {
  // Rough auto-sizing: reduce font as title gets longer
  const len = (title || '').length;
  if (len > 120) return 20;
  if (len > 90)  return 22;
  if (len > 70)  return 26;
  if (len > 50)  return 28;
  return 32;
}

function addTitle(slide, title, isLight, x, y, w, h, fontSize) {
  x  = (x  !== undefined) ? x  : MX;
  y  = (y  !== undefined) ? y  : TTL_Y;
  w  = (w  !== undefined) ? w  : BW;
  h  = (h  !== undefined) ? h  : TTL_H;
  fontSize = fontSize || titleFontSize(title);
  slide.addText(toPlain(title), {
    x, y, w, h, fontSize,
    fontFace: FDISP, color: fgC(isLight),
    valign: 'bottom', wrap: true,
  });
  // Accent underline bar below title
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: ULN_Y, w: ULN_W, h: ULN_H,
    fill: { color: ACC }, line: { type: 'none' },
  });
}

function addBullets(slide, bullets, x, y, w, h, isLight, fontSize) {
  if (!bullets || !bullets.length) return;
  const fs = fontSize || 16;
  const items = bullets.map(b => ({
    text: toPlain(b),
    options: {
      bullet:        { code: '25B8', color: ACC },
      paraSpaceAfter: 5,
      color:         fgC(isLight),
      fontSize:      fs,
      fontFace:      FBODY,
    },
  }));
  slide.addText(items, { x, y, w, h, valign: 'top', margin: [0.05, 0.08, 0.05, 0] });
}

function addImage(slide, imgPath, x, y, w, h) {
  if (!imgPath || !fs.existsSync(imgPath)) return;
  slide.addImage({
    path: imgPath, x, y, w, h,
    sizing: { type: 'contain', w, h },
  });
}

// cover
function buildCover(s) {
  const slide = pptx.addSlide();
  setBg(slide, false);

  const title   = toPlain(s.title || manifest.lecture_title || '');
  const speaker = s.speaker || manifest.speaker || '';
  const date    = manifest.date || '';

  // Left accent bar
  slide.addShape(pptx.ShapeType.rect, {
    x: MX - 0.28, y: 1.2, w: 0.06, h: H - 2.6,
    fill: { color: ACC }, line: { type: 'none' },
  });
  // Accent line above footer
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: H - 1.60, w: BW, h: 0.04,
    fill: { color: ACC }, line: { type: 'none' },
  });
  // Title
  slide.addText(title, {
    x: MX, y: 1.2, w: BW, h: H - 3.2,
    fontSize: 44, fontFace: FDISP,
    color: FGDRK, valign: 'middle', wrap: true,
    shadow: { type: 'outer', color: '000000', blur: 10, offset: 3, angle: 45, opacity: 0.40 },
  });
  // Footer
  const footer = [speaker, date].filter(Boolean).join('   ·   ');
  if (footer) {
    slide.addText(footer, {
      x: MX, y: H - 1.45, w: BW, h: 0.9,
      fontSize: 16, fontFace: FBODY, color: DIMDRK, valign: 'middle',
    });
  }
}

// toc
function buildToc(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);

  // Heading at top — mirrors HTML .toc h2 (full-width, top of body)
  slide.addText('Outline.', {
    x: MX, y: TTL_Y, w: BW, h: TTL_H,
    fontSize: 56, fontFace: FDISP, color: fgC(isLight), valign: 'bottom',
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: ULN_Y, w: ULN_W, h: ULN_H,
    fill: { color: ACC }, line: { type: 'none' },
  });

  const items = s.toc_items || [];
  const n = items.length;
  if (!n) return;

  // 2-column grid — mirrors HTML .toc-grid { grid-template-columns: 1fr 1fr }
  const COLS = 2;
  const colGap = 0.20;
  const colW = (BW - colGap) / COLS;
  const rows = Math.ceil(n / COLS);
  const rowH = Math.min(0.85, BODY_H / rows);

  items.forEach((item, i) => {
    const col = i % COLS;
    const row = Math.floor(i / COLS);
    const x  = MX + col * (colW + colGap);
    const iy = BODY_Y + row * rowH;
    // Top divider line
    slide.addShape(pptx.ShapeType.rect, {
      x, y: iy, w: colW, h: 0.018,
      fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
    });
    // Number
    slide.addText(item.n || String(i + 1).padStart(2, '0'), {
      x: x + 0.04, y: iy + 0.06, w: 0.80, h: rowH - 0.12,
      fontSize: 12, fontFace: FMONO, color: ACC, valign: 'middle',
    });
    // Title
    slide.addText(toPlain(item.t || ''), {
      x: x + 0.90, y: iy + 0.06, w: colW - 0.94, h: rowH - 0.12,
      fontSize: 15, fontFace: FDISP, color: fgC(isLight), valign: 'middle', wrap: true,
    });
  });
  // Bottom border for each column
  for (let col = 0; col < COLS; col++) {
    const colCount = items.filter((_, k) => k % COLS === col).length;
    if (colCount > 0) {
      const x  = MX + col * (colW + colGap);
      const iy = BODY_Y + colCount * rowH;
      slide.addShape(pptx.ShapeType.rect, {
        x, y: iy, w: colW, h: 0.018,
        fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
      });
    }
  }
}

// bullets
function buildBullets(s) {
  const isLight = !!s.is_light;
  const slide   = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const bs = s.bullets || [];
  const fs = bs.length > 7 ? 13 : bs.length > 5 ? 15 : 16;
  addBullets(slide, bs, MX, BODY_Y, BW, BODY_H, isLight, fs);
}

// formula
function _drawFormulaBox(slide, isLight, boxY, boxH) {
  const BAR_W  = 0.06;  // left accent bar width
  const boxBg  = isLight ? 'E8E4DC' : '1A0005';
  // Background panel (slight tint)
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: boxY, w: BW, h: boxH,
    fill: { color: boxBg, transparency: isLight ? 30 : 50 },
    line: { type: 'none' },
  });
  // Accent left bar — mirrors HTML border-left: 4px solid var(--accent)
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: boxY, w: BAR_W, h: boxH,
    fill: { color: ACC }, line: { type: 'none' },
  });
}

function buildFormula(s) {
  const isLight = !!s.is_light;
  const slide   = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);

  const bullets  = s.bullets || [];
  const imgPath     = s.formula_image_path;
  const formulaText = s.formula_text;
  const hasBulls    = bullets.length > 0;

  if (imgPath && fs.existsSync(imgPath)) {
    const boxH = hasBulls ? BODY_H * 0.54 : BODY_H * 0.88;
    const boxY = hasBulls ? BODY_Y : BODY_Y + (BODY_H - boxH) / 2;
    _drawFormulaBox(slide, isLight, boxY, boxH);
    // Formula image (transparent bg) overlaid on top of the box
    addImage(slide, imgPath, MX + 0.10, boxY + 0.10, BW - 0.20, boxH - 0.20);
    if (hasBulls) {
      addBullets(slide, bullets, MX, BODY_Y + boxH + 0.15, BW, BODY_H - boxH - 0.20, isLight, 14);
    }
  } else if (formulaText) {
    const boxH = hasBulls ? BODY_H * 0.50 : BODY_H * 0.80;
    const boxY = hasBulls ? BODY_Y : BODY_Y + (BODY_H - boxH) / 2;
    _drawFormulaBox(slide, isLight, boxY, boxH);
    const eqs = formulaText.split(/\n\s*\n/).map(e => toMathText(e.trim())).filter(Boolean);
    const mathFontSize = eqs.length > 3 ? 14 : eqs.length > 1 ? 16 : 20;
    slide.addText(eqs.join('\n\n'), {
      x: MX + 0.20, y: boxY + 0.15, w: BW - 0.30, h: boxH - 0.30,
      fontSize: mathFontSize, fontFace: 'Cambria Math',
      color: fgC(isLight), valign: 'middle', align: 'center',
    });
    if (hasBulls) {
      addBullets(slide, bullets, MX, boxY + boxH + 0.15, BW, BODY_H - boxH - 0.20, isLight, 14);
    }
  }
}

// two-images-below
function buildTwoImgBelow(s) {
  const isLight = !!s.is_light;
  const slide   = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);

  const bullets = s.bullets || [];
  const images  = s.images  || [];
  const nImgs   = Math.min(images.length, 2);
  const bullH   = nImgs > 0 ? BODY_H * 0.48 : BODY_H;
  const imgY    = BODY_Y + bullH + 0.10;
  const imgH    = BODY_H - bullH - 0.15;

  if (bullets.length) addBullets(slide, bullets, MX, BODY_Y, BW, bullH, isLight, 15);

  if (nImgs === 2) {
    const iW = (BW - 0.20) / 2;
    addImage(slide, images[0], MX,              imgY, iW, imgH);
    addImage(slide, images[1], MX + iW + 0.20,  imgY, iW, imgH);
  } else if (nImgs === 1) {
    addImage(slide, images[0], MX, imgY, BW, imgH);
  }
}

// two-images-right
function buildTwoImgRight(s) {
  const isLight = !!s.is_light;
  const slide   = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);

  const bullets = s.bullets || [];
  const images  = s.images  || [];

  // Title in left column
  slide.addText(toPlain(s.title), {
    x: MX, y: TTL_Y, w: LHS_W, h: TTL_H,
    fontSize: 24, fontFace: FDISP, color: fgC(isLight), valign: 'bottom', wrap: true,
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: ULN_Y, w: ULN_W, h: ULN_H,
    fill: { color: ACC }, line: { type: 'none' },
  });

  const bs = bullets;
  const fs = bs.length > 6 ? 13 : bs.length > 4 ? 14 : 15;
  addBullets(slide, bs, MX, BODY_Y, LHS_W, BODY_H, isLight, fs);

  const nImgs = Math.min(images.length, 2);
  if (nImgs === 2) {
    const iH = (BODY_H - 0.15) / 2;
    addImage(slide, images[0], RHS_X, BODY_Y,            RHS_W, iH - 0.05);
    addImage(slide, images[1], RHS_X, BODY_Y + iH + 0.1, RHS_W, iH - 0.05);
  } else if (nImgs === 1) {
    addImage(slide, images[0], RHS_X, BODY_Y, RHS_W, BODY_H);
  }
}

// two-images-left — 2 stacked images on left, title + bullets on right
function buildTwoImgLeft(s) {
  const isLight = !!s.is_light;
  const slide   = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);

  const bullets = s.bullets || [];
  const images  = s.images  || [];
  const nImgs   = Math.min(images.length, 2);

  if (nImgs === 2) {
    const iH = (BODY_H - 0.15) / 2;
    addImage(slide, images[0], MX, BODY_Y,            RHS_W, iH - 0.05);
    addImage(slide, images[1], MX, BODY_Y + iH + 0.1, RHS_W, iH - 0.05);
  } else if (nImgs === 1) {
    addImage(slide, images[0], MX, BODY_Y, RHS_W, BODY_H);
  }

  const rx = MX + RHS_W + 0.20;
  slide.addText(toPlain(s.title || ''), {
    x: rx, y: TTL_Y, w: LHS_W, h: TTL_H,
    fontSize: 24, fontFace: FDISP, color: fgC(isLight), valign: 'bottom', wrap: true,
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: rx, y: ULN_Y, w: ULN_W, h: ULN_H,
    fill: { color: ACC }, line: { type: 'none' },
  });
  const fs = bullets.length > 6 ? 13 : bullets.length > 4 ? 14 : 15;
  addBullets(slide, bullets, rx, BODY_Y, LHS_W, BODY_H, isLight, fs);
}

// image-right
function buildImgRight(s) {
  const isLight = !!s.is_light;
  const slide   = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight, MX, TTL_Y, LHS_W, TTL_H, 24);

  const bs  = s.bullets || [];
  const img = (s.images || [])[0];
  const fs  = bs.length > 6 ? 13 : bs.length > 4 ? 14 : 15;
  addBullets(slide, bs, MX, BODY_Y, LHS_W, BODY_H, isLight, fs);
  addImage(slide, img, RHS_X, BODY_Y, RHS_W, BODY_H);
}

// image-left
function buildImgLeft(s) {
  const isLight = !!s.is_light;
  const slide   = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);

  const bs  = s.bullets || [];
  const img = (s.images || [])[0];

  // Image on left
  addImage(slide, img, MX, BODY_Y - 0.5, RHS_W, BODY_H + 0.5);

  // Title and bullets on right
  const rx = MX + RHS_W + 0.20;
  slide.addText(toPlain(s.title), {
    x: rx, y: TTL_Y, w: LHS_W, h: TTL_H,
    fontSize: 24, fontFace: FDISP, color: fgC(isLight), valign: 'bottom', wrap: true,
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: rx, y: ULN_Y, w: ULN_W, h: ULN_H,
    fill: { color: ACC }, line: { type: 'none' },
  });
  const fs = bs.length > 6 ? 13 : bs.length > 4 ? 14 : 15;
  addBullets(slide, bs, rx, BODY_Y, LHS_W, BODY_H, isLight, fs);
}

// two-columns — HTML: no vertical divider, just gap between columns
function buildTwoCols(s) {
  const isLight = !!s.is_light;
  const slide   = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);

  const cols = s.cols || [[], []];
  const GAP  = 0.50;
  const colW = (BW - GAP) / 2;

  addBullets(slide, cols[0] || [], MX,            BODY_Y, colW, BODY_H, isLight, 15);
  addBullets(slide, cols[1] || [], MX + colW + GAP, BODY_Y, colW, BODY_H, isLight, 15);
}

// table
function parseMdTable(md) {
  if (!md) return { headers: [], rows: [] };
  const lines  = md.split('\n').map(l => l.trim()).filter(Boolean);
  const data   = lines.filter(l => !/^\|?[-:| ]+\|?$/.test(l));
  const parse  = l => l.split(/(?<!\\)\|/).map(c => c.trim()).filter((_, _i, a) => a.length > 1);
  const rows   = data.map(parse).filter(r => r.length > 0);
  if (!rows.length) return { headers: [], rows: [] };
  const maxC   = Math.max(...rows.map(r => r.length));
  const normed = rows.map(r => [...r, ...Array(maxC - r.length).fill('')]);
  const nonE   = Array.from({length: maxC}, (_, i) => normed.some(r => (r[i] || '').trim()));
  const filt   = normed.map(r => r.filter((_, i) => nonE[i]));
  return { headers: filt[0] || [], rows: filt.slice(1) };
}

function buildTable(s) {
  const isLight = !!s.is_light;
  const slide   = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);

  // Accept either parsed_table (from HTML) or table.table_markdown (JSON fallback)
  let headers = [], rows = [];
  if (s.parsed_table) {
    headers = s.parsed_table.headers || [];
    rows    = s.parsed_table.rows    || [];
  } else if (s.table) {
    const p = parseMdTable(s.table.table_markdown || '');
    headers = p.headers;
    rows    = p.rows;
  }
  if (!headers.length) {
    addBullets(slide, s.bullets || [], MX, BODY_Y, BW, BODY_H, isLight, 15);
    return;
  }

  const nCols  = headers.length;
  const nRows  = rows.length + 1;
  const rowH   = Math.min(0.38, (BODY_H - 0.50) / nRows);
  const tblH   = rowH * nRows;
  const tblTop = BODY_Y + Math.max(0, (BODY_H - tblH) / 2);

  const headBg   = BGDARK;
  const evenBg   = isLight ? 'E8E0D4' : '3D0010';
  const oddBg    = isLight ? BGLIT    : '2A0009';
  const borderC  = isLight ? 'CCBBAA' : '6A2A3A';

  const tblData = [
    headers.map(h => ({
      text: toPlain(h),
      options: {
        bold: true, color: 'FFFFFF',
        fill: { color: headBg },
        align: 'center', valign: 'middle',
        fontFace: FBODY, fontSize: 12,
      },
    })),
    ...rows.map((row, i) =>
      Array.from({length: nCols}, (_, j) => ({
        text: toPlain(row[j] || ''),
        options: {
          fill:  { color: i % 2 === 0 ? evenBg : oddBg },
          color: isLight ? FGLIT : FGDRK,
          align: 'center', valign: 'middle',
          fontFace: FBODY, fontSize: 11,
        },
      }))
    ),
  ];

  slide.addTable(tblData, {
    x: MX, y: tblTop, w: BW, rowH,
    colW: Array(nCols).fill(BW / nCols),
    border: { pt: 0.5, color: borderC },
  });

  const cap = (s.parsed_table && s.parsed_table.caption) || (s.table && s.table.table_caption);
  if (cap) {
    slide.addText(toPlain(cap), {
      x: MX, y: tblTop + tblH + 0.08, w: BW, h: 0.30,
      fontSize: 9, italic: true, color: dimC(isLight),
      fontFace: FBODY, align: 'center',
    });
  }
}

// end
// end — HTML: large display title (320px), 3-col footer with border-top separator
function buildEnd(s) {
  const slide = pptx.addSlide();
  setBg(slide, false);
  addChrome(slide, false, s.page_num);
  // Large title (320px CSS ≈ 80pt practical PPTX)
  slide.addText(toPlain(s.title || 'Thank You'), {
    x: MX, y: 1.00, w: BW, h: H - 3.20,
    fontSize: 80, fontFace: FDISP,
    color: FGDRK, align: 'left', valign: 'top', wrap: true,
  });
  // Footer separator line (border-top: 1px white ~69% opacity)
  const footY = H - 1.62;
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: footY, w: BW, h: 0.018,
    fill: { color: FGDRK, transparency: 32 }, line: { type: 'none' },
  });
  // 3-column footer grid
  const colW = (BW - 0.40) / 3;
  const footItems = [
    { k: 'Presented by', v: manifest.speaker || '' },
    { k: 'Q&A Session', v: 'Open discussion' },
    { k: 'Thank you', v: '' },
  ];
  footItems.forEach((item, i) => {
    const x = MX + i * (colW + 0.20);
    slide.addText(item.k, {
      x, y: footY + 0.10, w: colW, h: 0.28,
      fontSize: 10, fontFace: FMONO, color: DIMDRK, charSpacing: 2,
    });
    if (item.v) {
      slide.addText(item.v, {
        x, y: footY + 0.40, w: colW, h: 0.45,
        fontSize: 16, fontFace: FDISP, color: FGDRK, wrap: true,
      });
    }
  });
}

// image-above
function buildImgAbove(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const img = (s.images || [])[0];
  const bullets = s.bullets || [];
  const hasImg = img && fs.existsSync(img);
  const hasBulls = bullets.length > 0;
  if (hasImg && hasBulls) {
    const imgH = BODY_H * 0.55;
    addImage(slide, img, MX, BODY_Y, BW, imgH);
    addBullets(slide, bullets, MX, BODY_Y + imgH + 0.10, BW, BODY_H - imgH - 0.15, isLight, 14);
  } else if (hasImg) {
    addImage(slide, img, MX, BODY_Y, BW, BODY_H);
  } else if (hasBulls) {
    addBullets(slide, bullets, MX, BODY_Y, BW, BODY_H, isLight, 16);
  }
}

// image-below
function buildImgBelow(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const img = (s.images || [])[0];
  const bullets = s.bullets || [];
  const hasImg = img && fs.existsSync(img);
  const hasBulls = bullets.length > 0;
  if (hasImg && hasBulls) {
    const bullH = BODY_H * 0.42;
    addBullets(slide, bullets, MX, BODY_Y, BW, bullH, isLight, 14);
    addImage(slide, img, MX, BODY_Y + bullH + 0.10, BW, BODY_H - bullH - 0.15);
  } else if (hasImg) {
    addImage(slide, img, MX, BODY_Y, BW, BODY_H);
  } else if (hasBulls) {
    addBullets(slide, bullets, MX, BODY_Y, BW, BODY_H, isLight, 16);
  }
}

// two-images-above
function buildTwoImgAbove(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const images = s.images || [];
  const bullets = s.bullets || [];
  const nImgs = Math.min(images.length, 2);
  const hasBulls = bullets.length > 0;
  const imgH = hasBulls ? BODY_H * 0.52 : BODY_H;
  if (nImgs === 2) {
    const iW = (BW - 0.20) / 2;
    addImage(slide, images[0], MX, BODY_Y, iW, imgH);
    addImage(slide, images[1], MX + iW + 0.20, BODY_Y, iW, imgH);
  } else if (nImgs === 1) {
    addImage(slide, images[0], MX, BODY_Y, BW, imgH);
  }
  if (hasBulls) {
    addBullets(slide, bullets, MX, BODY_Y + imgH + 0.10, BW, BODY_H - imgH - 0.15, isLight, 14);
  }
}

// two-contents — HTML: subtitle has border-bottom:2px accent; no vertical divider
function buildTwoContents(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const blocks = s.blocks || [];
  const GAP  = 0.50;
  const colW = (BW - GAP) / 2;
  blocks.slice(0, 2).forEach((block, i) => {
    const x       = i === 0 ? MX : MX + colW + GAP;
    const subtitle = block.subtitle || '';
    const bullets  = block.bullets || [];
    if (subtitle) {
      slide.addText(toPlain(subtitle), {
        x, y: BODY_Y, w: colW, h: 0.42,
        fontSize: 15, fontFace: FDISP, color: fgC(isLight), bold: false, valign: 'bottom',
      });
      // Accent underline — mirrors border-bottom: 2px solid var(--accent)
      slide.addShape(pptx.ShapeType.rect, {
        x, y: BODY_Y + 0.44, w: colW, h: 0.022,
        fill: { color: ACC }, line: { type: 'none' },
      });
      addBullets(slide, bullets, x, BODY_Y + 0.55, colW, BODY_H - 0.60, isLight, 14);
    } else {
      addBullets(slide, bullets, x, BODY_Y, colW, BODY_H, isLight, 15);
    }
  });
}

// steps — HTML: .track::before = single horizontal line at circle center (y:38px), opacity:0.3
function buildSteps(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const steps = s.steps || [];
  const n = Math.min(steps.length, 5);
  if (!n) return;
  const stepW = BW / n;
  const stepY = BODY_Y + 0.15;
  const stepH = BODY_H - 0.20;
  const CIR_D = 0.53;   // 76px diameter
  // Single horizontal connecting line through circle centers (track::before)
  const lineY = stepY + CIR_D / 2 - 0.011;
  slide.addShape(pptx.ShapeType.rect, {
    x: MX + stepW / 2, y: lineY, w: BW - stepW, h: 0.022,
    fill: { color: ACC, transparency: 70 }, line: { type: 'none' },
  });
  steps.slice(0, n).forEach((step, i) => {
    const x   = MX + i * stepW;
    const cx  = x + stepW / 2 - CIR_D / 2;
    const isCurrent = !!step.current;
    // Circle — filled or outlined for "current" step
    slide.addShape(pptx.ShapeType.ellipse, {
      x: cx, y: stepY, w: CIR_D, h: CIR_D,
      fill: isCurrent ? { type: 'none' } : { color: ACC },
      line: isCurrent ? { color: ACC, pt: 2.5 } : { type: 'none' },
    });
    slide.addText(toPlain(step.num || String(i + 1)), {
      x: cx, y: stepY, w: CIR_D, h: CIR_D,
      fontSize: 18, fontFace: FDISP, color: isCurrent ? ACC : (isLight ? FGLIT : BGDARK),
      bold: true, align: 'center', valign: 'middle',
    });
    if (step.title) {
      slide.addText(toPlain(step.title), {
        x, y: stepY + CIR_D + 0.18, w: stepW - 0.10, h: 0.60,
        fontSize: 13, fontFace: FDISP, color: fgC(isLight),
        bold: false, align: 'left', wrap: true, valign: 'top',
      });
    }
    if (step.body) {
      slide.addText(toPlain(step.body), {
        x, y: stepY + CIR_D + 0.85, w: stepW - 0.10, h: stepH - CIR_D - 0.90,
        fontSize: 11, fontFace: FBODY, color: dimC(isLight),
        align: 'left', wrap: true, valign: 'top',
      });
    }
  });
}

// key-points — HTML: each .pt has border-left:4px accent + rgba bg + border-radius
function buildKeyPoints(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const points = s.points || [];
  const n = points.length;
  if (!n) return;
  const GAP  = 0.08;
  const rowH = Math.min(0.82, (BODY_H - GAP * (n - 1)) / n);
  points.forEach((pt, i) => {
    const y   = BODY_Y + i * (rowH + GAP);
    const boxH = rowH;
    // Semi-transparent background (matches rgba(255,255,255,0.04) / rgba(0,0,0,0.04))
    slide.addShape(pptx.ShapeType.rect, {
      x: MX, y, w: BW, h: boxH,
      fill: { color: isLight ? '000000' : 'FFFFFF', transparency: 96 },
      line: { type: 'none' },
    });
    // Left accent bar — mirrors border-left: 4px solid var(--accent)
    slide.addShape(pptx.ShapeType.rect, {
      x: MX, y, w: 0.055, h: boxH,
      fill: { color: ACC }, line: { type: 'none' },
    });
    // Index
    slide.addText(toPlain(pt.ix || `P·${String(i + 1).padStart(2, '0')}`), {
      x: MX + 0.14, y: y + 0.06, w: 0.72, h: boxH - 0.12,
      fontSize: 10, fontFace: FMONO, color: ACC, valign: 'middle',
    });
    // Title
    slide.addText(toPlain(pt.title || ''), {
      x: MX + 0.90, y: y + 0.07, w: BW - 0.95, h: boxH * 0.50 - 0.07,
      fontSize: 13, fontFace: FBODY, color: fgC(isLight), bold: true, valign: 'bottom',
    });
    // Body
    slide.addText(toPlain(pt.body || ''), {
      x: MX + 0.90, y: y + boxH * 0.50, w: BW - 0.95, h: boxH * 0.44,
      fontSize: 11, fontFace: FBODY, color: dimC(isLight), valign: 'top', wrap: true,
    });
  });
}

// three-columns — HTML: each .col has border-top:4px accent + rgba bg + border-radius
function buildThreeCols(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const cols = s.cols || [];
  const n = Math.min(cols.length, 3);
  if (!n) return;
  const GAP  = 0.20;
  const colW = (BW - GAP * (n - 1)) / n;
  cols.slice(0, n).forEach((col, i) => {
    const x = MX + i * (colW + GAP);
    // Column background (rgba(255,255,255,0.04))
    slide.addShape(pptx.ShapeType.rect, {
      x, y: BODY_Y, w: colW, h: BODY_H,
      fill: { color: isLight ? '000000' : 'FFFFFF', transparency: 96 },
      line: { type: 'none' },
    });
    // Top accent border — mirrors border-top: 4px solid var(--accent)
    slide.addShape(pptx.ShapeType.rect, {
      x, y: BODY_Y, w: colW, h: 0.055,
      fill: { color: ACC }, line: { type: 'none' },
    });
    let y = BODY_Y + 0.22;  // padding-top inside column
    if (col.tag) {
      slide.addText(toPlain(col.tag), {
        x: x + 0.20, y, w: colW - 0.40, h: 0.32,
        fontSize: 11, fontFace: FMONO, color: ACC, valign: 'middle',
      });
      y += 0.37;
    }
    if (col.title) {
      slide.addText(toPlain(col.title), {
        x: x + 0.20, y, w: colW - 0.40, h: 0.55,
        fontSize: 14, fontFace: FBODY, color: fgC(isLight), bold: true, valign: 'top', wrap: true,
      });
      y += 0.60;
    }
    if (col.body) {
      slide.addText(toPlain(col.body), {
        x: x + 0.20, y, w: colW - 0.40, h: 1.00,
        fontSize: 12, fontFace: FBODY, color: dimC(isLight), valign: 'top', wrap: true,
      });
      y += 1.05;
    }
    if (col.bullets && col.bullets.length) {
      addBullets(slide, col.bullets, x + 0.20, y, colW - 0.40, BODY_Y + BODY_H - y - 0.10, isLight, 11);
    }
  });
}

// split-contrast
function buildSplitContrast(s) {
  const slide = pptx.addSlide();
  slide.background = { color: BGDARK };
  const sides = s.sides || [];
  const halfW = W / 2;
  sides.slice(0, 2).forEach((side, i) => {
    const x = i === 0 ? 0 : halfW;
    const isDark = i === 0;
    const bgColor = isDark ? BGDARK : 'F0EDE5';
    const fgColor = isDark ? FGDRK : FGLIT;
    slide.addShape(pptx.ShapeType.rect, {
      x, y: 0, w: halfW, h: H,
      fill: { color: bgColor }, line: { type: 'none' },
    });
    if (side.tag) {
      slide.addText(toPlain(side.tag), {
        x: x + 0.50, y: 1.00, w: halfW - 1.00, h: 0.40,
        fontSize: 11, fontFace: FMONO, color: ACC, valign: 'middle', charSpacing: 2,
      });
    }
    if (side.title) {
      slide.addText(toPlain(side.title), {
        x: x + 0.50, y: 1.55, w: halfW - 1.00, h: 0.80,
        fontSize: 22, fontFace: FDISP, color: fgColor, valign: 'top', wrap: true,
      });
    }
    if (side.bullets && side.bullets.length) {
      addBullets(slide, side.bullets, x + 0.50, 2.50, halfW - 1.00, H - 3.10, !isDark, 13);
    }
    if (isDark) {
      slide.addShape(pptx.ShapeType.rect, {
        x: halfW - 0.04, y: 0.5, w: 0.04, h: H - 1.0,
        fill: { color: ACC }, line: { type: 'none' },
      });
    }
  });
}

// conclusion-cards — HTML: horizontal timeline line + dot circles above 4 color cards
function buildConclCards(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const cards = s.cards || [];
  const n = Math.min(cards.length, 4);
  if (!n) return;
  const GAP    = 0.14;
  const cardW  = (BW - GAP * (n - 1)) / n;
  const DOT_D  = 0.39;   // 56px circle diameter
  const DOT_Y  = BODY_Y + 0.10;
  const CARD_Y = DOT_Y + DOT_D + 0.12;
  const cardH  = CBOT_Y - CARD_Y - 0.15;
  // Horizontal connecting line through dot centers
  const lineY = DOT_Y + DOT_D / 2 - 0.011;
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: lineY, w: BW, h: 0.022,
    fill: { color: isLight ? '000000' : 'FFFFFF', transparency: 80 }, line: { type: 'none' },
  });
  cards.slice(0, n).forEach((card, i) => {
    const x  = MX + i * (cardW + GAP);
    const cc = CARD_COLORS[i % CARD_COLORS.length];
    const cx = x + cardW / 2 - DOT_D / 2;
    // Timeline dot — white circle with card-color border
    slide.addShape(pptx.ShapeType.ellipse, {
      x: cx, y: DOT_Y, w: DOT_D, h: DOT_D,
      fill: { color: 'FFFFFF' }, line: { color: cc, pt: 3 },
    });
    // Card background
    slide.addShape(pptx.ShapeType.rect, {
      x, y: CARD_Y, w: cardW, h: cardH,
      fill: { color: cc }, line: { type: 'none' },
    });
    // Number circle inside card (rgba(255,255,255,0.25) bg)
    const numD = 0.39;
    const numX = x + cardW / 2 - numD / 2;
    slide.addShape(pptx.ShapeType.ellipse, {
      x: numX, y: CARD_Y + 0.18, w: numD, h: numD,
      fill: { color: 'FFFFFF', transparency: 75 }, line: { type: 'none' },
    });
    slide.addText(toPlain(card.num || String(i + 1)), {
      x: numX, y: CARD_Y + 0.18, w: numD, h: numD,
      fontSize: 16, fontFace: FDISP, color: 'FFFFFF', bold: true, align: 'center', valign: 'middle',
    });
    if (card.heading) {
      slide.addText(toPlain(card.heading), {
        x: x + 0.12, y: CARD_Y + 0.64, w: cardW - 0.24, h: 0.75,
        fontSize: 13, fontFace: FBODY, color: 'FFFFFF', bold: true,
        align: 'center', valign: 'top', wrap: true,
      });
    }
    if (card.body) {
      slide.addText(toPlain(card.body), {
        x: x + 0.12, y: CARD_Y + 1.42, w: cardW - 0.24, h: cardH - 1.58,
        fontSize: 11, fontFace: FBODY, color: 'FFFFFF',
        align: 'center', valign: 'top', wrap: true,
      });
    }
  });
}

// numbered-conclusions — HTML: grid 120px|1fr, number 56px display font, heading 40px display
function buildNumConcl(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const rows = s.rows || [];
  const n = rows.length;
  if (!n) return;
  // Scale fonts with row count (mirrors CSS :has() auto-scale)
  let numFs = 28, hdgFs = 20, bFs = 12;
  if (n >= 7) { numFs = 18; hdgFs = 13; bFs = 9; }
  else if (n >= 6) { numFs = 21; hdgFs = 15; bFs = 10; }
  else if (n >= 5) { numFs = 24; hdgFs = 18; bFs = 11; }
  const NUM_W = 0.83;   // 120px ≈ 0.83"
  const GAP   = 0.22;   // 32px gap
  const rowH  = Math.min(0.90, BODY_H / n);
  rows.forEach((row, i) => {
    const y = BODY_Y + i * rowH;
    // Top border
    slide.addShape(pptx.ShapeType.rect, {
      x: MX, y, w: BW, h: 0.018,
      fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
    });
    // Large display number (accent)
    slide.addText(toPlain(row.n || String(i + 1).padStart(2, '0')), {
      x: MX, y: y + 0.05, w: NUM_W, h: rowH - 0.10,
      fontSize: numFs, fontFace: FDISP, color: ACC, valign: 'middle',
    });
    // Heading (display font)
    slide.addText(toPlain(row.heading || ''), {
      x: MX + NUM_W + GAP, y: y + 0.06, w: BW - NUM_W - GAP, h: rowH * 0.50,
      fontSize: hdgFs, fontFace: FDISP, color: fgC(isLight), valign: 'bottom', wrap: true,
    });
    // Body
    slide.addText(toPlain(row.body || ''), {
      x: MX + NUM_W + GAP, y: y + rowH * 0.52, w: BW - NUM_W - GAP, h: rowH * 0.44,
      fontSize: bFs, fontFace: FBODY, color: dimC(isLight), valign: 'top', wrap: true,
    });
  });
  // Bottom border after last row
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: BODY_Y + n * rowH, w: BW, h: 0.018,
    fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
  });
}

// grid-2×2
function buildGrid2x2(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const cells = s.cells || [];
  const n = Math.min(cells.length, 4);
  if (!n) return;
  const cellW = (BW - 0.20) / 2;
  const cellH = (BODY_H - 0.15) / 2;
  const borderColor = isLight ? 'CCBBAA' : '555577';
  cells.slice(0, n).forEach((cell, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = MX + col * (cellW + 0.20);
    const y = BODY_Y + row * (cellH + 0.15);
    slide.addShape(pptx.ShapeType.rect, {
      x, y, w: cellW, h: cellH,
      fill: { color: isLight ? 'E8E4DC' : '1E0008', transparency: isLight ? 20 : 30 },
      line: { color: borderColor, pt: 0.5 },
    });
    slide.addShape(pptx.ShapeType.rect, {
      x: x + 0.15, y: y + 0.15, w: 0.25, h: 0.05,
      fill: { color: ACC }, line: { type: 'none' },
    });
    slide.addText(toPlain(cell.title || ''), {
      x: x + 0.15, y: y + 0.28, w: cellW - 0.30, h: 0.48,
      fontSize: 13, fontFace: FBODY, color: fgC(isLight), bold: true, valign: 'top', wrap: true,
    });
    slide.addText(toPlain(cell.body || ''), {
      x: x + 0.15, y: y + 0.80, w: cellW - 0.30, h: cellH - 0.95,
      fontSize: 11, fontFace: FBODY, color: dimC(isLight), valign: 'top', wrap: true,
    });
  });
}

// research-question — HTML: main-rq box (2px accent border, rgba bg), subs in 3-col grid
function buildResearchQuestion(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const mainQ = s.main_q || '';
  const subQs = s.sub_qs || [];
  const hasSubQs = subQs.length > 0;
  const mainBoxH = hasSubQs ? 1.55 : BODY_H;
  // Main RQ box — border:2px accent + semi-transparent bg
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: BODY_Y, w: BW, h: mainBoxH,
    fill: { color: isLight ? '000000' : 'FFFFFF', transparency: 96 },
    line: { color: ACC, pt: 1.5 },
  });
  slide.addText('Main RQ', {
    x: MX + 0.22, y: BODY_Y + 0.12, w: 1.20, h: 0.28,
    fontSize: 10, fontFace: FMONO, color: ACC, valign: 'middle', charSpacing: 2,
  });
  slide.addText(toPlain(mainQ), {
    x: MX + 0.22, y: BODY_Y + 0.44, w: BW - 0.44, h: mainBoxH - 0.58,
    fontSize: 16, fontFace: FDISP, color: fgC(isLight), valign: 'top', wrap: true, italic: true,
  });
  if (hasSubQs) {
    // Sub-questions in 3-column grid (matches grid-template-columns: repeat(3, 1fr))
    const subStartY = BODY_Y + mainBoxH + 0.18;
    const subH      = CBOT_Y - subStartY - 0.15;
    const subGAP    = 0.19;   // 28px gap
    const subW      = (BW - subGAP * 2) / 3;
    subQs.slice(0, 3).forEach((sub, i) => {
      const x = MX + i * (subW + subGAP);
      slide.addShape(pptx.ShapeType.rect, {
        x, y: subStartY, w: subW, h: subH,
        fill: { color: isLight ? '000000' : 'FFFFFF', transparency: 96 }, line: { type: 'none' },
      });
      slide.addText(toPlain(sub.lbl || `Sub-Q ${String(i + 1).padStart(2, '0')}`), {
        x: x + 0.18, y: subStartY + 0.14, w: subW - 0.36, h: 0.26,
        fontSize: 10, fontFace: FMONO, color: ACC, valign: 'middle', charSpacing: 1.5,
      });
      slide.addText(toPlain(sub.q || ''), {
        x: x + 0.18, y: subStartY + 0.44, w: subW - 0.36, h: subH - 0.56,
        fontSize: 13, fontFace: FBODY, color: fgC(isLight), valign: 'top', wrap: true,
      });
    });
  }
}

// agenda
function buildAgenda(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  slide.addText(toPlain(s.title || ''), {
    x: MX, y: 1.10, w: 3.50, h: H - 2.40,
    fontSize: 36, fontFace: FDISP, color: fgC(isLight), valign: 'middle', italic: true,
  });
  const items = s.items || [];
  const listX = 4.50;
  const listW = W - listX - MX;
  const usable = H - 2.20;
  const rowH = Math.min(0.65, usable / Math.max(items.length, 1));
  const startY = 1.25;
  items.forEach((item, i) => {
    const iy = startY + i * rowH;
    slide.addShape(pptx.ShapeType.rect, {
      x: listX, y: iy, w: listW, h: 0.018,
      fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
    });
    slide.addText(String(i + 1).padStart(2, '0'), {
      x: listX, y: iy + 0.06, w: 0.55, h: rowH - 0.08,
      fontSize: 11, fontFace: FMONO, color: ACC, valign: 'middle',
    });
    slide.addText(toPlain(item.title || ''), {
      x: listX + 0.60, y: iy + 0.06,
      w: item.duration ? listW - 1.40 : listW - 0.65,
      h: rowH - 0.08,
      fontSize: 14, fontFace: FBODY, color: fgC(isLight), valign: 'middle', wrap: true,
    });
    if (item.duration) {
      slide.addText(toPlain(item.duration), {
        x: W - MX - 0.80, y: iy + 0.06, w: 0.80, h: rowH - 0.08,
        fontSize: 11, fontFace: FMONO, color: dimC(isLight), valign: 'middle', align: 'right',
      });
    }
  });
  if (items.length > 0) {
    slide.addShape(pptx.ShapeType.rect, {
      x: listX, y: startY + items.length * rowH, w: listW, h: 0.018,
      fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
    });
  }
}

// quote — HTML: blockquote 96px display font, .who::before = 80px accent line + mono dim text
function buildQuote(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  // Large opening mark
  slide.addText('“', {
    x: MX, y: 0.50, w: 1.20, h: 1.10,
    fontSize: 110, fontFace: FDISP, color: ACC, valign: 'top',
  });
  const quoteEndY = s.attribution ? CBOT_Y - 0.80 : CBOT_Y - 0.20;
  slide.addText(toPlain(s.quote || ''), {
    x: MX + 0.30, y: 1.20, w: BW - 0.30, h: quoteEndY - 1.25,
    fontSize: 36, fontFace: FDISP, color: fgC(isLight),
    valign: 'middle', wrap: true, italic: true,
  });
  if (s.attribution) {
    const attY = CBOT_Y - 0.68;
    // Accent line before attribution (.who::before: 80px wide, 2px high)
    slide.addShape(pptx.ShapeType.rect, {
      x: MX + 0.30, y: attY + 0.14, w: 0.55, h: 0.022,
      fill: { color: ACC }, line: { type: 'none' },
    });
    slide.addText(toPlain(s.attribution), {
      x: MX + 1.00, y: attY, w: BW - 1.05, h: 0.45,
      fontSize: 12, fontFace: FMONO, color: dimC(isLight), valign: 'middle',
      charSpacing: 1.8,
    });
  }
}

// section-divider — HTML always uses accent-color background with dark panel text
function buildSectionDivider(s) {
  const slide = pptx.addSlide();
  slide.background = { color: ACC };
  addChrome(slide, true, s.page_num);  // chrome in "light" style (dark ink on accent bg)
  const fg  = FGLIT;   // panel-text = dark ink
  const dim = '666666';
  if (s.section_num) {
    slide.addText(toPlain(s.section_num), {
      x: MX, y: 1.10, w: BW, h: 0.38,
      fontSize: 14, fontFace: FMONO, color: fg, valign: 'middle', charSpacing: 3,
      transparency: 40,
    });
  }
  const titleLen = (s.title || '').length;
  const titleFs = titleLen > 60 ? 42 : titleLen > 40 ? 54 : titleLen > 25 ? 64 : 80;
  slide.addText(toPlain(s.title || ''), {
    x: MX, y: s.section_num ? 1.60 : 1.10, w: BW, h: H - 3.80,
    fontSize: titleFs, fontFace: FDISP, color: fg, valign: 'middle', wrap: true,
  });
  // Bottom separator line + lead text
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: H - 1.58, w: BW, h: 0.018,
    fill: { color: fg, transparency: 70 }, line: { type: 'none' },
  });
  if (s.lead) {
    slide.addText(toPlain(s.lead), {
      x: MX, y: H - 1.42, w: BW * 0.7, h: 0.50,
      fontSize: 13, fontFace: FBODY, color: dim, valign: 'middle',
    });
  }
}

// image-fullscreen-overlay
function buildImgFull(s) {
  const slide = pptx.addSlide();
  const img = (s.images || [])[0];
  if (img && fs.existsSync(img)) {
    slide.background = { path: img };
    slide.addShape(pptx.ShapeType.rect, {
      x: 0, y: 0, w: W, h: H,
      fill: { color: '000000', transparency: 45 }, line: { type: 'none' },
    });
  } else {
    slide.background = { color: BGDARK };
  }
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: 2.80, w: 0.30, h: 0.05,
    fill: { color: ACC }, line: { type: 'none' },
  });
  if (s.title) {
    slide.addText(toPlain(s.title), {
      x: MX, y: 3.00, w: BW, h: 1.20,
      fontSize: titleFontSize(s.title), fontFace: FDISP, color: FGDRK,
      valign: 'top', wrap: true,
      shadow: { type: 'outer', color: '000000', blur: 10, offset: 3, angle: 45, opacity: 0.60 },
    });
  }
  if (s.body_text) {
    slide.addText(toPlain(s.body_text), {
      x: MX, y: 4.35, w: BW, h: 1.50,
      fontSize: 16, fontFace: FBODY, color: 'DDDDDD', valign: 'top', wrap: true,
    });
  }
}

// stat-cards — HTML: .nums .n has border-top:2px accent, big display number, dim label below
function buildStat(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  if (s.title) {
    slide.addText(toPlain(s.title), {
      x: MX, y: 1.00, w: BW, h: 0.55,
      fontSize: 18, fontFace: FMONO, color: ACC, valign: 'middle', charSpacing: 1.5,
    });
  }
  const stats = s.stats || [];
  const n = Math.min(stats.length, 4);
  if (n) {
    const GAP   = 0.55;   // 80px gap
    const cardW = (BW - GAP * (n - 1)) / n;
    const statY = 1.75;   // area top
    stats.slice(0, n).forEach((stat, i) => {
      const x = MX + i * (cardW + GAP);
      // Accent top border (border-top: 2px solid accent)
      slide.addShape(pptx.ShapeType.rect, {
        x, y: statY, w: cardW, h: 0.022,
        fill: { color: ACC }, line: { type: 'none' },
      });
      // Large value
      slide.addText(toPlain(stat.value || ''), {
        x, y: statY + 0.10, w: cardW, h: 2.10,
        fontSize: 52, fontFace: FDISP, color: ACC, valign: 'top', align: 'left',
      });
      // Label (dim)
      slide.addText(toPlain(stat.label || ''), {
        x, y: statY + 2.25, w: cardW, h: 0.65,
        fontSize: 14, fontFace: FBODY, color: dimC(isLight), align: 'left', wrap: true,
      });
    });
  }
  if (s.note) {
    // Note with top border separator
    slide.addShape(pptx.ShapeType.rect, {
      x: MX, y: CBOT_Y - 0.62, w: BW * 0.55, h: 0.018,
      fill: { color: fgC(isLight), transparency: 85 }, line: { type: 'none' },
    });
    slide.addText(toPlain(s.note), {
      x: MX, y: CBOT_Y - 0.55, w: BW * 0.75, h: 0.42,
      fontSize: 11, fontFace: FMONO, color: dimC(isLight), italic: false,
    });
  }
}

// pricing-cards
function buildPricing(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  addTitle(slide, s.title, isLight);
  const cards = s.cards || [];
  const n = Math.min(cards.length, 4);
  if (!n) return;
  const cardW = (BW - (n - 1) * 0.20) / n;
  cards.slice(0, n).forEach((card, i) => {
    const x = MX + i * (cardW + 0.20);
    const bgColor = isLight ? 'EDEAE2' : '2A0009';
    slide.addShape(pptx.ShapeType.rect, {
      x, y: BODY_Y, w: cardW, h: BODY_H,
      fill: { color: bgColor, transparency: 20 },
      line: { color: isLight ? 'CCBBAA' : ACC, pt: 0.5 },
    });
    slide.addText(toPlain(card.name || ''), {
      x: x + 0.15, y: BODY_Y + 0.20, w: cardW - 0.30, h: 0.40,
      fontSize: 13, fontFace: FBODY, color: fgC(isLight), bold: true, valign: 'middle', align: 'center',
    });
    slide.addText(toPlain(card.price || ''), {
      x: x + 0.15, y: BODY_Y + 0.65, w: cardW - 0.30, h: 0.55,
      fontSize: 20, fontFace: FDISP, color: ACC, valign: 'middle', align: 'center',
    });
    if (card.features && card.features.length) {
      addBullets(slide, card.features, x + 0.10, BODY_Y + 1.25, cardW - 0.20, BODY_H - 1.30, isLight, 11);
    }
  });
}

// toc-vertical — numbered vertical list: accent num | display title | dim page
function buildTocVertical(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  slide.addText(toPlain(s.heading || 'Contents'), {
    x: MX, y: TTL_Y, w: BW, h: TTL_H,
    fontSize: 44, fontFace: FDISP, color: fgC(isLight), valign: 'bottom',
  });
  const items = s.toc_items || [];
  const n = items.length;
  if (!n) return;
  const NUM_W  = 0.55;
  const PAGE_W = 0.60;
  const GAP    = 0.22;
  const rowH   = Math.min(0.75, BODY_H / n);
  items.forEach((item, i) => {
    const y = BODY_Y + i * rowH;
    slide.addShape(pptx.ShapeType.rect, {
      x: MX, y, w: BW, h: 0.018,
      fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
    });
    slide.addText(toPlain(item.n || String(i + 1).padStart(2, '0')), {
      x: MX, y: y + 0.06, w: NUM_W, h: rowH - 0.12,
      fontSize: 11, fontFace: FMONO, color: ACC, valign: 'middle',
    });
    slide.addText(toPlain(item.t || ''), {
      x: MX + NUM_W + GAP, y: y + 0.06, w: BW - NUM_W - GAP - (item.p ? PAGE_W + GAP : 0), h: rowH - 0.12,
      fontSize: 20, fontFace: FDISP, color: fgC(isLight), valign: 'middle', wrap: true,
    });
    if (item.p) {
      slide.addText(toPlain(item.p), {
        x: MX + BW - PAGE_W, y: y + 0.06, w: PAGE_W, h: rowH - 0.12,
        fontSize: 11, fontFace: FMONO, color: dimC(isLight), align: 'right', valign: 'middle',
      });
    }
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: BODY_Y + n * rowH, w: BW, h: 0.018,
    fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
  });
}

// toc_cards – 4-card horizontal layout
function buildTocCards(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);

  // Heading
  slide.addText('Outline', {
    x: MX, y: 1.0, w: BW, h: 0.85,
    fontSize: 56, fontFace: FDISP, color: fgC(isLight), bold: false,
  });

  const cards = s.cards || [];
  const n = Math.min(cards.length, 4);
  if (!n) return;

  // 1×n horizontal layout
  const cardY = 2.1;
  const cardH = H - cardY - 0.85;
  const gap   = 0.18;
  const cardW = (BW - gap * (n - 1)) / n;

  cards.slice(0, n).forEach((card, i) => {
    const x = MX + i * (cardW + gap);
    // Card background
    slide.addShape(pptx.ShapeType.rect, {
      x, y: cardY, w: cardW, h: cardH,
      fill: { color: isLight ? 'E8E4DC' : '1A0005', transparency: isLight ? 20 : 70 },
      line: { color: isLight ? 'CCCCCC' : 'FFFFFF', transparency: 85, pt: 0.5 },
    });
    // Number
    slide.addText(card.n || String(i + 1).padStart(2, '0'), {
      x: x + 0.22, y: cardY + 0.22, w: cardW - 0.44, h: 0.35,
      fontSize: 13, fontFace: FMONO, color: ACC, bold: false,
    });
    // Title (shrinks to fit up to 3 lines)
    const titleH = card.desc ? 1.30 : cardH - 0.75;
    slide.addText(toPlain(card.title || ''), {
      x: x + 0.22, y: cardY + 0.62, w: cardW - 0.44, h: titleH,
      fontSize: 15, fontFace: FDISP, color: fgC(isLight),
      wrap: true, valign: 'top', shrinkText: true,
    });
    // Description — full text, fills rest of card, auto-scales
    if (card.desc) {
      const descY  = cardY + 0.62 + titleH + 0.10;
      const descH  = cardY + cardH - descY - 0.15;
      // Readable color: darker on light slides, 70% white on dark
      const descColor = isLight ? '444444' : 'BBBBBB';
      slide.addText(toPlain(card.desc), {
        x: x + 0.22, y: descY, w: cardW - 0.44, h: descH,
        fontSize: 10, fontFace: FBODY, color: descColor,
        wrap: true, valign: 'top', shrinkText: true,
      });
    }
  });
}

// toc-described — numbered list with title + description + optional duration
function buildTocDescribed(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  slide.addText(toPlain(s.heading || "What we'll cover"), {
    x: MX, y: TTL_Y, w: BW, h: TTL_H,
    fontSize: 44, fontFace: FDISP, color: fgC(isLight), valign: 'bottom',
  });
  const items = s.toc_items || [];
  const n = items.length;
  if (!n) return;
  const NUM_W = 0.55;
  const DUR_W = 0.70;
  const GAP   = 0.28;
  const rowH  = Math.min(0.90, BODY_H / n);
  items.forEach((item, i) => {
    const y = BODY_Y + i * rowH;
    slide.addShape(pptx.ShapeType.rect, {
      x: MX, y, w: BW, h: 0.018,
      fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
    });
    slide.addText(toPlain(item.n || String(i + 1).padStart(2, '0')), {
      x: MX, y: y + 0.05, w: NUM_W, h: rowH - 0.10,
      fontSize: 14, fontFace: FMONO, color: ACC, valign: 'top',
    });
    const bodyW = BW - NUM_W - GAP - (item.dur ? DUR_W + GAP : 0);
    slide.addText(toPlain(item.t || ''), {
      x: MX + NUM_W + GAP, y: y + 0.05, w: bodyW, h: rowH * 0.52,
      fontSize: 20, fontFace: FDISP, color: fgC(isLight), valign: 'bottom', wrap: true,
    });
    if (item.d) {
      slide.addText(toPlain(item.d), {
        x: MX + NUM_W + GAP, y: y + rowH * 0.54, w: bodyW, h: rowH * 0.40,
        fontSize: 12, fontFace: FBODY, color: dimC(isLight), valign: 'top', wrap: true,
      });
    }
    if (item.dur) {
      slide.addText(toPlain(item.dur), {
        x: MX + BW - DUR_W, y: y + 0.05, w: DUR_W, h: 0.38,
        fontSize: 11, fontFace: FMONO, color: dimC(isLight), align: 'right', valign: 'top',
      });
    }
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: BODY_Y + n * rowH, w: BW, h: 0.018,
    fill: { color: fgC(isLight), transparency: 75 }, line: { type: 'none' },
  });
}

// cover-split — large title left, key-value meta rows right, vertical divider
function buildCoverSplit(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  const LHS_W = BW * 0.60;
  const RHS_X = MX + LHS_W + 0.22;
  const RHS_W = W - RHS_X - MX;
  // Vertical divider
  slide.addShape(pptx.ShapeType.rect, {
    x: MX + LHS_W + 0.08, y: 1.00, w: 0.018, h: H - 2.10,
    fill: { color: fgC(isLight), transparency: 85 }, line: { type: 'none' },
  });
  // Eyebrow with accent line
  if (s.eyebrow) {
    slide.addShape(pptx.ShapeType.rect, {
      x: MX, y: 1.12, w: 0.61, h: 0.022,
      fill: { color: ACC }, line: { type: 'none' },
    });
    slide.addText(toPlain(s.eyebrow), {
      x: MX + 0.72, y: 1.00, w: LHS_W - 0.82, h: 0.38,
      fontSize: 13, fontFace: FMONO, color: dimC(isLight), valign: 'middle', charSpacing: 2,
    });
  }
  // Large title
  const titleText = toPlain(manifest.lecture_title || s.title || '');
  const titleFs   = titleText.length > 60 ? 36 : titleText.length > 40 ? 44 : titleText.length > 25 ? 50 : 54;
  slide.addText(titleText, {
    x: MX, y: 1.65, w: LHS_W, h: H - 3.50,
    fontSize: titleFs, fontFace: FDISP, color: fgC(isLight), valign: 'middle', wrap: true,
  });
  // Right side: stacked key-value rows
  const rows  = s.meta_rows || [];
  const rowH  = Math.min(0.88, (H - 2.50) / Math.max(rows.length, 1));
  const rowsStartY = H - rows.length * rowH - 1.20;
  rows.forEach((row, i) => {
    const ry = rowsStartY + i * rowH;
    slide.addShape(pptx.ShapeType.rect, {
      x: RHS_X, y: ry, w: RHS_W, h: 0.018,
      fill: { color: fgC(isLight), transparency: 85 }, line: { type: 'none' },
    });
    slide.addText(toPlain(row.k || ''), {
      x: RHS_X, y: ry + 0.06, w: RHS_W, h: 0.26,
      fontSize: 10, fontFace: FMONO, color: dimC(isLight), valign: 'middle', charSpacing: 2,
    });
    slide.addText(toPlain(row.v || ''), {
      x: RHS_X, y: ry + 0.33, w: RHS_W, h: rowH - 0.38,
      fontSize: 18, fontFace: FDISP, color: fgC(isLight), valign: 'top', wrap: true,
    });
  });
  if (rows.length > 0) {
    slide.addShape(pptx.ShapeType.rect, {
      x: RHS_X, y: rowsStartY + rows.length * rowH, w: RHS_W, h: 0.018,
      fill: { color: fgC(isLight), transparency: 85 }, line: { type: 'none' },
    });
  }
}

// end-with-image — large title + footer on left, image on right
function buildEndWithImage(s) {
  const isLight = !!s.is_light;
  const slide = pptx.addSlide();
  setBg(slide, isLight);
  addChrome(slide, isLight, s.page_num);
  const LHS_W = (BW - 0.20) / 2;
  const RHS_X = MX + LHS_W + 0.20;
  const RHS_W = W - RHS_X - MX;
  // Large end title
  slide.addText(toPlain(s.title || 'Thank You'), {
    x: MX, y: 1.10, w: LHS_W, h: 3.85,
    fontSize: 60, fontFace: FDISP, color: fgC(isLight), valign: 'top', wrap: true,
  });
  // Footer separator
  const footY = CBOT_Y - 0.95;
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: footY, w: LHS_W, h: 0.018,
    fill: { color: fgC(isLight), transparency: 80 }, line: { type: 'none' },
  });
  const items = s.meta_items || [];
  items.slice(0, 3).forEach((item, i) => {
    const iy = footY + 0.10 + i * 0.28;
    slide.addText(toPlain(item.k || ''), {
      x: MX, y: iy, w: LHS_W, h: 0.18,
      fontSize: 9, fontFace: FMONO, color: dimC(isLight), charSpacing: 1.5,
    });
    if (item.v) {
      slide.addText(toPlain(item.v), {
        x: MX, y: iy + 0.19, w: LHS_W, h: 0.22,
        fontSize: 14, fontFace: FDISP, color: fgC(isLight),
      });
    }
  });
  // Image on right (edge to edge vertically)
  const img = (s.images || [])[0];
  if (img && fs.existsSync(img)) {
    addImage(slide, img, RHS_X, 0.35, RHS_W, H - 0.35 - 0.30);
  } else {
    slide.addShape(pptx.ShapeType.rect, {
      x: RHS_X, y: 0.35, w: RHS_W, h: H - 0.65,
      fill: { color: isLight ? '000000' : 'FFFFFF', transparency: 92 }, line: { type: 'none' },
    });
    slide.addText('Image', {
      x: RHS_X, y: H / 2 - 0.20, w: RHS_W, h: 0.40,
      fontSize: 11, fontFace: FMONO, color: dimC(isLight), align: 'center',
    });
  }
}

// end-image-hero — full-bleed image bg + dark gradient overlay + title at bottom
function buildEndImageHero(s) {
  const slide = pptx.addSlide();
  const img = (s.images || [])[0];
  if (img && fs.existsSync(img)) {
    slide.background = { path: img };
  } else {
    slide.background = { color: BGDARK };
  }
  // Bottom-heavy dark overlay
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: H * 0.30, w: W, h: H * 0.70,
    fill: { color: '000000', transparency: 15 }, line: { type: 'none' },
  });
  addChrome(slide, false, s.page_num);
  // Accent bar
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: H - 2.65, w: 0.61, h: 0.022,
    fill: { color: ACC }, line: { type: 'none' },
  });
  // Large title
  const titleText = toPlain(s.title || 'Thank You');
  const titleFs   = titleText.length > 30 ? 60 : titleText.length > 20 ? 72 : 80;
  slide.addText(titleText, {
    x: MX, y: H - 2.50, w: BW, h: 1.60,
    fontSize: titleFs, fontFace: FDISP, color: 'FFFFFF', valign: 'top', wrap: true,
  });
  // Footer separator + items
  const footY = CBOT_Y - 0.10;
  slide.addShape(pptx.ShapeType.rect, {
    x: MX, y: footY, w: BW, h: 0.018,
    fill: { color: 'FFFFFF', transparency: 80 }, line: { type: 'none' },
  });
  const items = s.meta_items || [];
  if (items.length) {
    const colW = (BW - 0.40 * (items.length - 1)) / items.length;
    items.slice(0, 3).forEach((item, i) => {
      const x = MX + i * (colW + 0.40);
      slide.addText(toPlain(item.k || ''), {
        x, y: footY + 0.06, w: colW, h: 0.22,
        fontSize: 9, fontFace: FMONO, color: 'FFFFFF', transparency: 50, charSpacing: 2,
      });
      if (item.v) {
        slide.addText(toPlain(item.v), {
          x, y: footY + 0.28, w: colW, h: 0.24,
          fontSize: 13, fontFace: FDISP, color: 'FFFFFF',
        });
      }
    });
  }
}

// editorial-light — light bg, large display title + lede left, sidebar (pull quote / meta) right
function buildEditorial(s) {
  const slide = pptx.addSlide();
  slide.background = { color: BGLIT };
  addChrome(slide, true, s.page_num);
  // Eyebrow: accent line + mono text
  if (s.eyebrow) {
    slide.addShape(pptx.ShapeType.rect, {
      x: MX, y: 1.12, w: 0.44, h: 0.022,
      fill: { color: ACC }, line: { type: 'none' },
    });
    slide.addText(toPlain(s.eyebrow), {
      x: MX + 0.55, y: 1.00, w: BW - 0.55, h: 0.38,
      fontSize: 13, fontFace: FMONO, color: DIMLIT, valign: 'middle', charSpacing: 2,
    });
  }
  const MAIN_W = BW * 0.56;
  const SIDE_X = MX + MAIN_W + 0.25;
  const SIDE_W = BW - MAIN_W - 0.25;
  // Large title
  const titleLen = (s.title || '').length;
  const titleFs  = titleLen > 60 ? 28 : titleLen > 40 ? 32 : titleLen > 25 ? 36 : 40;
  slide.addText(toPlain(s.title || ''), {
    x: MX, y: 1.55, w: MAIN_W, h: 2.80,
    fontSize: titleFs, fontFace: FDISP, color: FGLIT, valign: 'top', wrap: true,
  });
  // Lede text
  if (s.lede) {
    slide.addText(toPlain(s.lede), {
      x: MX, y: 4.55, w: MAIN_W, h: CBOT_Y - 4.70,
      fontSize: 14, fontFace: FBODY, color: FGLIT, transparency: 22, valign: 'top', wrap: true,
    });
  }
  // Sidebar: pull quote card (accent bg)
  if (s.pull_quote) {
    const pqH = s.pull_attribution ? 2.00 : 1.70;
    slide.addShape(pptx.ShapeType.rect, {
      x: SIDE_X, y: 1.55, w: SIDE_W, h: pqH,
      fill: { color: ACC }, line: { type: 'none' },
    });
    slide.addText('"', {
      x: SIDE_X + 0.18, y: 1.55, w: SIDE_W - 0.18, h: 0.60,
      fontSize: 48, fontFace: FDISP, color: FGLIT, transparency: 40, italic: true, valign: 'top',
    });
    slide.addText(toPlain(s.pull_quote), {
      x: SIDE_X + 0.18, y: 2.15, w: SIDE_W - 0.36, h: pqH - 1.00,
      fontSize: 17, fontFace: FDISP, color: FGLIT, valign: 'top', wrap: true,
    });
    if (s.pull_attribution) {
      slide.addText(toPlain(s.pull_attribution), {
        x: SIDE_X + 0.18, y: 1.55 + pqH - 0.36, w: SIDE_W - 0.36, h: 0.30,
        fontSize: 10, fontFace: FMONO, color: FGLIT, transparency: 30, charSpacing: 1.5,
      });
    }
  }
  // Sidebar: meta items
  if (s.meta && s.meta.length > 0) {
    const metaStartY = s.pull_quote ? 1.55 + (s.pull_attribution ? 2.00 : 1.70) + 0.25 : 1.55;
    s.meta.forEach((m, i) => {
      const my = metaStartY + i * 0.52;
      slide.addText(toPlain((m.key || '') + ' —'), {
        x: SIDE_X, y: my, w: SIDE_W, h: 0.22,
        fontSize: 9, fontFace: FMONO, color: DIMLIT, transparency: 40, charSpacing: 1,
      });
      slide.addText(toPlain(m.value || ''), {
        x: SIDE_X, y: my + 0.22, w: SIDE_W, h: 0.28,
        fontSize: 13, fontFace: FMONO, color: FGLIT,
      });
    });
  }
  // Footline
  if (s.footline_left || s.footline_right) {
    slide.addShape(pptx.ShapeType.rect, {
      x: MX, y: CBOT_Y - 0.60, w: BW, h: 0.018,
      fill: { color: FGLIT, transparency: 85 }, line: { type: 'none' },
    });
    slide.addText(toPlain(s.footline_left || ''), {
      x: MX, y: CBOT_Y - 0.52, w: BW / 2, h: 0.35,
      fontSize: 11, fontFace: FMONO, color: DIMLIT, valign: 'middle', charSpacing: 1,
    });
    if (s.footline_right) {
      slide.addText(toPlain(s.footline_right), {
        x: MX + BW / 2, y: CBOT_Y - 0.52, w: BW / 2, h: 0.35,
        fontSize: 11, fontFace: FMONO, color: DIMLIT, align: 'right', valign: 'middle', charSpacing: 1,
      });
    }
  }
}

// dispatch
for (const s of manifest.slides || []) {
  switch (s.type) {
    case 'cover':            buildCover(s);             break;
    case 'toc':              buildToc(s);               break;
    case 'toc_vertical':     buildTocVertical(s);       break;
    case 'toc_described':    buildTocDescribed(s);      break;
    case 'toc_cards':        buildTocCards(s);          break;
    case 'bullets':          buildBullets(s);           break;
    case 'formula':          buildFormula(s);           break;
    case 'twoimgbelow':      buildTwoImgBelow(s);       break;
    case 'twoimgright':      buildTwoImgRight(s);       break;
    case 'twoimgleft':       buildTwoImgLeft(s);        break;
    case 'imgright':         buildImgRight(s);          break;
    case 'imgleft':          buildImgLeft(s);           break;
    case 'imgabove':         buildImgAbove(s);          break;
    case 'imgbelow':         buildImgBelow(s);          break;
    case 'twoimgabove':      buildTwoImgAbove(s);       break;
    case 'twocols':          buildTwoCols(s);           break;
    case 'twocontents':      buildTwoContents(s);       break;
    case 'cmptable':         buildTable(s);             break;
    case 'stat':             buildStat(s);              break;
    case 'steps':            buildSteps(s);             break;
    case 'keypoints':        buildKeyPoints(s);         break;
    case 'threecol':         buildThreeCols(s);         break;
    case 'splitcontrast':    buildSplitContrast(s);     break;
    case 'conclcards':       buildConclCards(s);        break;
    case 'numconcl':         buildNumConcl(s);          break;
    case 'grid2x2':          buildGrid2x2(s);           break;
    case 'rquestion':        buildResearchQuestion(s);  break;
    case 'agenda':           buildAgenda(s);            break;
    case 'quote':            buildQuote(s);             break;
    case 'section-divider':  buildSectionDivider(s);   break;
    case 'imgfull':          buildImgFull(s);           break;
    case 'pricing':          buildPricing(s);           break;
    case 'cover_split':      buildCoverSplit(s);        break;
    case 'end_with_image':   buildEndWithImage(s);      break;
    case 'end_image_hero':   buildEndImageHero(s);      break;
    case 'editorial':        buildEditorial(s);         break;
    case 'end':              buildEnd(s);               break;
    default:                 buildBullets(s);           break;
  }
}

pptx.writeFile({ fileName: outputPath })
  .then(() => {
    const n = (manifest.slides || []).length;
    console.log(`[pptx] ${n} slides → ${outputPath}`);
    process.exit(0);
  })
  .catch(err => {
    console.error('[pptx] Error: ' + err.message);
    process.exit(1);
  });
