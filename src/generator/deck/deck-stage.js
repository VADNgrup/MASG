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
      this.style.cssText = [
        'width:1920px',
        'height:1080px',
        `transform:scale(${scale.toFixed(6)})`,
        'transform-origin:top left',
        'position:fixed',
        `left:${ox.toFixed(2)}px`,
        `top:${oy.toFixed(2)}px`
      ].join(';');
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

  /* =========================================================
     AUTO-FIT TEXT — scales h1/h2/blockquote with data-fit
     Attributes: data-fit, data-fit-lines="N", data-fit-min="px"
     ========================================================= */
  function fitText(el) {
    const lines = parseInt(el.dataset.fitLines || '2', 10);
    const minPx = parseInt(el.dataset.fitMin || '16', 10);
    const parent = el.closest('.slide') || el.parentElement;
    if (!parent) return;

    const availW = parent.offsetWidth - 240;
    const availH = (parent.offsetHeight - 280) / lines;

    let lo = minPx, hi = 400, best = minPx;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      el.style.fontSize = mid + 'px';
      if (el.scrollWidth <= availW && el.scrollHeight <= availH * lines) {
        best = mid;
        lo = mid + 1;
      } else {
        hi = mid - 1;
      }
    }
    el.style.fontSize = best + 'px';
  }

  function runAutoFit() {
    document.querySelectorAll('[data-fit]').forEach(fitText);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runAutoFit);
  } else {
    runAutoFit();
  }
  window.addEventListener('resize', runAutoFit);

})();
