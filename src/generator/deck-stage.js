(function () {
  'use strict';

  class DeckStage extends HTMLElement {
    constructor() {
      super();
      this._idx = 0;
      this._slides = [];
      this._total = 0;
      this._onKey = this._onKey.bind(this);
      this._onResize = this._scale.bind(this);
    }

    connectedCallback() {
      this._slides = Array.from(this.querySelectorAll(':scope > section.slide'));
      this._total = this._slides.length;
      if (!this._total) return;

      document.body.style.margin = '0';
      document.body.style.padding = '0';
      document.body.style.overflow = 'hidden';
      document.body.style.background = '#111';

      this._show(0);
      document.addEventListener('keydown', this._onKey);
      window.addEventListener('resize', this._onResize);
      this._scale();
      window.addEventListener('message', this._onMessage.bind(this));
    }

    disconnectedCallback() {
      document.removeEventListener('keydown', this._onKey);
      window.removeEventListener('resize', this._onResize);
    }

    _show(idx) {
      this._idx = Math.max(0, Math.min(idx, this._total - 1));
      this._slides.forEach((s, i) => {
        if (i === this._idx) {
          s.style.display = '';
          s.setAttribute('data-deck-active', '');
        } else {
          s.style.display = 'none';
          s.removeAttribute('data-deck-active');
        }
      });
      this.dispatchEvent(new CustomEvent('slidechange', {
        bubbles: true,
        detail: { index: this._idx, total: this._total }
      }));
    }

    _onKey(e) {
      const fwd = ['ArrowRight', 'ArrowDown', ' ', 'PageDown'];
      const bwd = ['ArrowLeft', 'ArrowUp', 'PageUp'];
      if (fwd.includes(e.key)) {
        e.preventDefault();
        this._show(this._idx + 1);
      } else if (bwd.includes(e.key)) {
        e.preventDefault();
        this._show(this._idx - 1);
      } else if (e.key === 'Home') {
        e.preventDefault();
        this._show(0);
      } else if (e.key === 'End') {
        e.preventDefault();
        this._show(this._total - 1);
      }
    }

    _scale() {
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const scale = Math.min(vw / 1920, vh / 1080);
      const ox = (vw - 1920 * scale) / 2;
      const oy = (vh - 1080 * scale) / 2;
      this.style.width = '1920px';
      this.style.height = '1080px';
      this.style.transform = `scale(${scale.toFixed(6)})`;
      this.style.transformOrigin = 'top left';
      this.style.position = 'fixed';
      this.style.left = `${ox.toFixed(2)}px`;
      this.style.top = `${oy.toFixed(2)}px`;
    }

    _onMessage(e) {
      const d = e.data;
      if (!d || !d.type) return;
      const panel = document.getElementById('twPanel');
      if (d.type === '__activate_edit_mode' && panel) panel.classList.add('show');
      else if (d.type === '__deactivate_edit_mode' && panel) panel.classList.remove('show');
    }
  }

  if (!customElements.get('deck-stage')) {
    customElements.define('deck-stage', DeckStage);
  }


  function fitText(el) {
    const lines = parseInt(el.dataset.fitLines || '2', 10);
    const minPx = parseInt(el.dataset.fitMin || '16', 10);
    const maxPx = parseInt(el.dataset.fitMax || '400', 10);
    const scopeSel = el.dataset.fitScope;
    const parent = scopeSel
      ? (el.closest(scopeSel) || el.parentElement)
      : (el.closest('.slide') || el.parentElement);
    if (!parent) return;

    const cs = getComputedStyle(parent);
    const padH = parseFloat(cs.paddingLeft || '0') + parseFloat(cs.paddingRight || '0');
    const availW = scopeSel ? parent.offsetWidth - padH : parent.offsetWidth - 240;

    let lo = minPx, hi = maxPx, best = minPx;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      el.style.fontSize = mid + 'px';
      const rawLH = getComputedStyle(el).lineHeight;
      const lh = rawLH === 'normal' ? mid * 1.2 : parseFloat(rawLH);
      const actualLines = lh > 0 ? Math.ceil(el.scrollHeight / lh) : Infinity;
      if (el.scrollWidth <= availW && actualLines <= lines) {
        best = mid;
        lo = mid + 1;
      } else {
        hi = mid - 1;
      }
    }
    el.style.fontSize = best + 'px';
  }

  function fitBlock(el) {
    el.style.transform = '';
    el.style.transformOrigin = '';
    el.style.justifyContent = '';
    const availH = el.offsetHeight;
    const contentH = el.scrollHeight;
    if (contentH > availH && availH > 0) {
      el.style.justifyContent = 'flex-start';
      const scale = Math.max(0.65, availH / contentH);
      el.style.transform = `scale(${scale.toFixed(4)})`;
      el.style.transformOrigin = 'top center';
    }
  }

  function runAutoFit() {
    requestAnimationFrame(() => requestAnimationFrame(() => {
      document.querySelectorAll('section.slide').forEach(slide => {
        const hidden = slide.style.display === 'none';
        if (hidden) {
          slide.style.visibility = 'hidden';
          slide.style.display = '';
        }
        slide.querySelectorAll('[data-fit]').forEach(fitText);
        slide.querySelectorAll('[data-fit-block]').forEach(fitBlock);
        if (hidden) {
          slide.style.display = 'none';
          slide.style.visibility = '';
        }
      });
    }));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runAutoFit);
  } else {
    runAutoFit();
  }
  window.addEventListener('resize', runAutoFit);

})();
