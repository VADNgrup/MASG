<template>
  <div class="slidev-layout h-full w-full bg-background text-white flex flex-col justify-center items-center relative overflow-hidden">
    <div v-if="image" class="absolute inset-0 z-0 opacity-30">
        <img :src="image" class="w-full h-full object-cover" />
        <div class="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent"></div>
    </div>
    
    <div class="z-10 text-center px-16 max-w-4xl">
      <h1 class="text-6xl font-extrabold mb-6 heading-gradient leading-tight filter drop-shadow-lg">
        <slot name="title">{{ title }}</slot>
      </h1>
      <p class="text-xl text-gray-300 font-light tracking-wide leading-relaxed whitespace-pre-wrap">
        <slot name="default">{{ content }}</slot>
      </p>
    </div>

    <div class="absolute bottom-12 z-10 op-50 text-sm">
        <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  image?: string
  title?: string
  content?: string
}>()
</script>
