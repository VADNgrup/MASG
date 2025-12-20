<template>
  <div class="icon-text" :class="{ 'icon-text-vertical': vertical }">
    <div v-if="icon" class="icon-text-icon">{{ icon }}</div>
    <div class="icon-text-content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  icon: {
    type: String,
    default: ''
  },
  vertical: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.icon-text {
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
}

.icon-text-vertical {
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.icon-text-icon {
  font-size: 2.5rem;
  line-height: 1;
  flex-shrink: 0;
}

.icon-text-content {
  flex: 1;
  font-size: var(--font-size-body);
  line-height: var(--line-height-body);
}

.icon-text-vertical .icon-text-icon {
  margin-bottom: 0.5rem;
}
</style>

