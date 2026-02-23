<template>
  <div class="slidev-layout h-full flex flex-col">
    <!-- Title (full width) -->
    <div class="mb-6">
      <slot name="title" />
    </div>

    <!-- Content (split into 2 columns) -->
    <div class="flex-1 grid grid-cols-2 gap-10">
      <div class="left">
        <slot name="left" />
      </div>

      <div class="right flex flex-col items-center justify-center">
        <div class="flex items-center justify-center flex-1">
          <slot name="right" />
        </div>
        <div class="text-gray-500 italic text-center" :style="`font-size: 0.9rem; margin-top: 0.01rem;`">
          <slot name="right-caption" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  captionGap: {
    type: String,
    default: '0.1rem'
  }
})
</script>


