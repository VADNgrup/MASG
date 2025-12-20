<template>
  <div class="default-layout">
    <div class="default-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.default-layout {
  @apply h-full;
  padding: 4rem 5rem;
  background: white;
}

.default-content {
  max-width: 1200px;
  margin: 0 auto;
}

.default-content h1 {
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 2rem;
  color: var(--color-neutral-900);
  letter-spacing: -0.02em;
}

.default-content h2 {
  font-size: 2.5rem;
  font-weight: 600;
  line-height: 1.2;
  margin-top: 3rem;
  margin-bottom: 1.5rem;
  color: var(--color-neutral-900);
}

.default-content h3 {
  font-size: 2rem;
  font-weight: 600;
  line-height: 1.3;
  margin-top: 2rem;
  margin-bottom: 1rem;
  color: var(--color-neutral-800);
}

.default-content p {
  font-size: 1.5rem;
  line-height: 1.8;
  color: var(--color-neutral-800);
  margin-bottom: 1.5rem;
}

.default-content ul,
.default-content ol {
  font-size: 1.5rem;
  line-height: 1.8;
  color: var(--color-neutral-800);
  margin-bottom: 1.5rem;
  padding-left: 2rem;
}

.default-content li {
  margin-bottom: 0.75rem;
}
</style>

