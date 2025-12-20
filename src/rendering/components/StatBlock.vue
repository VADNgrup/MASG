<template>
  <div class="stat-block">
    <div v-if="icon" class="stat-icon">
      {{ icon }}
    </div>
    <div class="stat-number">{{ number }}</div>
    <div class="stat-label">{{ label }}</div>
    <div v-if="description" class="stat-description">{{ description }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  number: {
    type: String,
    required: true
  },
  label: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.stat-block {
  text-align: center;
  padding: 2rem 1rem;
}

.stat-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  line-height: 1;
}

.stat-number {
  font-size: 4rem;
  font-weight: var(--font-weight-bold);
  line-height: 1;
  color: var(--color-primary);
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: var(--font-size-body-large);
  font-weight: var(--font-weight-medium);
  color: var(--color-neutral-800);
  margin-bottom: 0.5rem;
}

.stat-description {
  font-size: var(--font-size-caption);
  color: var(--color-neutral-700);
  line-height: var(--line-height-body);
}
</style>

