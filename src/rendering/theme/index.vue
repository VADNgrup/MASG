<template>
  <div class="slidev-theme-wrapper">
    <slot />
  </div>
</template>

<style>
@import '../styles/design-system.css';

.slidev-theme-wrapper {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
  color: var(--color-neutral-800);
  background: white;
}

.slidev-theme-wrapper h1 {
  font-size: var(--font-size-hero);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
  color: var(--color-neutral-900);
  letter-spacing: -0.02em;
}

.slidev-theme-wrapper h2 {
  font-size: var(--font-size-section);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-normal);
  color: var(--color-neutral-900);
}

.slidev-theme-wrapper h3 {
  font-size: var(--font-size-subsection);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-relaxed);
  color: var(--color-neutral-800);
}

.slidev-theme-wrapper p {
  font-size: var(--font-size-body);
  line-height: var(--line-height-body);
  color: var(--color-neutral-800);
}

.slidev-theme-wrapper strong {
  font-weight: var(--font-weight-semibold);
}
</style>

