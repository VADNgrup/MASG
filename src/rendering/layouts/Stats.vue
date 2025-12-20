<template>
  <div class="stats-layout">
    <div class="stats-container">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.stats-layout {
  @apply h-full;
  padding: 4rem 5rem;
  background: white;
}

.stats-container {
  @apply grid grid-cols-2 gap-12;
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  align-items: center;
}

.stats-container.grid-3 {
  @apply grid-cols-3;
}

.stats-container.grid-4 {
  @apply grid-cols-2;
  gap: 8;
}
</style>

