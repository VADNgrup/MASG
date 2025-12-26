<template>
  <div class="slidev-layout h-full w-full bg-background text-white px-12 py-10 flex flex-col">
    <h1 v-if="title" class="text-4xl font-bold mb-8 heading-gradient text-center">
        {{ title }}
    </h1>
    
    <div class="flex-1 overflow-y-auto grid-layout-container">
        <div class="prose prose-invert max-w-none">
            <slot />
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
}>()
</script>

<style>
.grid-layout-container ul {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
    padding: 0;
    list-style: none !important;
}

.grid-layout-container li {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 1.5rem;
    margin: 0 !important;
    display: flex;
    flex-direction: column;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.grid-layout-container li:hover {
    transform: translateY(-2px);
    background: rgba(255, 255, 255, 0.08);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    border-color: rgba(94, 106, 210, 0.5);
}

.grid-layout-container li::before {
    display: none !important;
}
</style>
