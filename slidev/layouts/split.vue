<template>
  <div class="slidev-layout h-full w-full bg-background text-white flex items-center gap-12 px-12 py-8">
    <div class="flex-1 flex flex-col justify-center h-full">
        <h1 v-if="title" class="text-4xl font-bold mb-6 heading-gradient">
            {{ title }}
        </h1>
        <div class="prose prose-invert prose-lg leading-relaxed text-gray-200">
            <slot />
        </div>
    </div>
    
    <div class="flex-1 h-full flex items-center justify-center relative">
        <div class="relative w-full h-[80%] rounded-2xl overflow-hidden shadow-2xl border border-white/10 group">
            <img 
                v-if="image" 
                :src="image" 
                class="w-full h-full object-cover transition duration-500 transform group-hover:scale-105" 
            />
            <div v-else class="w-full h-full bg-white/5 flex items-center justify-center text-gray-500">
                No Image
            </div>
            <div class="absolute inset-0 ring-1 ring-inset ring-white/10 rounded-2xl"></div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  image?: string
  title?: string
}>()
</script>
