<template>
  <div class="slidev-layout h-full w-full bg-background text-white flex flex-col justify-center items-center px-16 text-center relative">
    <div class="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-secondary/10 pointer-events-none"></div>
    
    <div class="relative z-10 max-w-5xl">
        <div class="text-6xl md:text-7xl font-serif leading-tight">
            <span class="text-primary opacity-50 absolute -top-12 -left-8 text-9xl">"</span>
            <slot />
            <span class="text-primary opacity-50 absolute -bottom-16 -right-8 text-9xl">"</span>
        </div>
        
        <div v-if="author" class="mt-12 text-2xl text-secondary font-mono tracking-widest uppercase opacity-80">
            {{ author }}
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  author?: string
}>()
</script>
