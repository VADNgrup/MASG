<template>
  <div class="card" :class="{ 'card-bordered': bordered, 'card-shadow': shadow }">
    <div v-if="$slots.header" class="card-header">
      <slot name="header" />
    </div>
    <div class="card-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  bordered: {
    type: Boolean,
    default: false
  },
  shadow: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.card {
  padding: 2rem;
  background: white;
  border-radius: 8px;
}

.card-bordered {
  border: 1px solid var(--color-neutral-200);
}

.card-shadow {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-neutral-200);
}

.card-body {
  font-size: var(--font-size-body);
  line-height: var(--line-height-body);
}
</style>

