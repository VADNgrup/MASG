<template>
  <div class="cover-layout" :style="backgroundStyle">
    <div class="cover-content">
      <h1 v-if="title" class="cover-title">{{ title }}</h1>
      <h2 v-if="subtitle" class="cover-subtitle">{{ subtitle }}</h2>
      
      <div v-if="author || date" class="cover-meta">
        <span v-if="author" class="cover-author">{{ author }}</span>
        <span v-if="date" class="cover-date">{{ date }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  title: String,
  subtitle: String,
  author: String,
  date: String,
  background: String
})

const backgroundStyle = computed(() => {
  if (props.background) {
    return {
      background: props.background
    }
  }
  return {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  }
})
</script>

<style scoped>
.cover-layout {
  @apply h-full flex items-center justify-center;
  padding: 4rem 5rem;
}

.cover-content {
  @apply text-center;
  color: white;
}

.cover-title {
  font-size: 4.5rem;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 1.5rem;
  letter-spacing: -0.03em;
}

.cover-subtitle {
  font-size: 2rem;
  font-weight: 400;
  line-height: 1.4;
  opacity: 0.95;
  margin-bottom: 3rem;
}

.cover-meta {
  @apply flex items-center justify-center gap-4;
  font-size: 1.25rem;
  opacity: 0.9;
  margin-top: 4rem;
}

.cover-author,
.cover-date {
  font-weight: 400;
}
</style>

