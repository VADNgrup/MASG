<template>
  <div class="section-layout">
    <div class="section-content">
      <h1 v-if="title" class="section-title">{{ title }}</h1>
      <p v-if="description" class="section-description">{{ description }}</p>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  title: String,
  description: String
})
</script>

<style scoped>
.section-layout {
  @apply h-full flex items-center justify-center;
  background: var(--color-neutral-50);
  padding: 4rem 5rem;
}

.section-content {
  @apply text-center;
  max-width: 900px;
}

.section-title {
  font-size: 4rem;
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-neutral-900);
  letter-spacing: -0.02em;
  margin-bottom: 1.5rem;
}

.section-description {
  font-size: 1.5rem;
  line-height: 1.6;
  color: var(--color-neutral-700);
  margin-top: 1rem;
}
</style>

