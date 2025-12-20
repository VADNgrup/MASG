<template>
  <div class="text-image-layout">
    <div class="text-image-container" :class="{ 'image-right': imagePosition === 'right', 'image-left': imagePosition === 'left' }">
      <div class="text-image-text">
        <slot />
      </div>
      <div v-if="image" class="text-image-image">
        <img :src="image" :alt="imageAlt || 'Image'" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  image: String,
  imagePosition: {
    type: String,
    default: 'right'
  },
  imageAlt: String
})
</script>

<style scoped>
.text-image-layout {
  @apply h-full;
  padding: 4rem 5rem;
  background: white;
}

.text-image-container {
  @apply h-full flex items-center gap-12;
  max-width: 1400px;
  margin: 0 auto;
}

.text-image-container.image-left {
  flex-direction: row-reverse;
}

.text-image-text {
  flex: 1;
  min-width: 0;
}

.text-image-text h1 {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 2rem;
  color: var(--color-neutral-900);
  letter-spacing: -0.02em;
}

.text-image-text h2 {
  font-size: 2.25rem;
  font-weight: 600;
  line-height: 1.2;
  margin-top: 2rem;
  margin-bottom: 1.5rem;
  color: var(--color-neutral-900);
}

.text-image-text p {
  font-size: 1.5rem;
  line-height: 1.8;
  color: var(--color-neutral-800);
  margin-bottom: 1.5rem;
}

.text-image-text ul,
.text-image-text ol {
  font-size: 1.5rem;
  line-height: 1.8;
  color: var(--color-neutral-800);
  margin-bottom: 1.5rem;
}

.text-image-image {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.text-image-image img {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 8px;
}
</style>

