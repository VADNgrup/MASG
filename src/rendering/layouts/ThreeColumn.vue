<template>
  <div class="three-column-layout">
    <div class="three-column-container">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.three-column-layout {
  @apply h-full;
  padding: 4rem 5rem;
  background: white;
}

.three-column-container {
  @apply grid grid-cols-3 gap-8;
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  align-items: start;
}

.three-column-container > * {
  min-width: 0;
}

.three-column-container h2 {
  font-size: 2rem;
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 1.5rem;
  color: var(--color-neutral-900);
}

.three-column-container h3 {
  font-size: 1.75rem;
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 1rem;
  color: var(--color-neutral-900);
}

.three-column-container p {
  font-size: 1.25rem;
  line-height: 1.7;
  color: var(--color-neutral-800);
  margin-bottom: 1rem;
}

.three-column-container ul,
.three-column-container ol {
  font-size: 1.25rem;
  line-height: 1.7;
  color: var(--color-neutral-800);
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.three-column-container li {
  margin-bottom: 0.5rem;
}
</style>

