<template>
  <div class="h-full w-full flex flex-col justify-center items-center bg-gradient-to-br from-indigo-900 via-blue-800 to-teal-700 text-white p-12 relative overflow-hidden">
    <div class="absolute -top-10 -right-10 w-64 h-64 bg-white opacity-5 rounded-full blur-3xl"></div>
    <div class="absolute -bottom-20 -left-20 w-96 h-96 bg-teal-400 opacity-10 rounded-full blur-3xl"></div>

    <div class="z-10 text-center">
      <div class="mb-4 inline-block px-4 py-1 rounded-full bg-white bg-opacity-20 border border-white border-opacity-30 text-sm uppercase tracking-widest font-medium">
        Lecture Module
      </div>
      <h1 class="text-7xl font-extrabold mb-6 drop-shadow-lg tracking-tight">
        {{ title }}
      </h1>
      <div class="h-1 w-24 bg-teal-400 mx-auto mb-8 rounded-full"></div>
      <p class="text-2xl opacity-90 max-w-3xl mx-auto font-light leading-relaxed">
        {{ shortSummary }}
      </p>
    </div>
  </div>
</template>

<script setup>
defineProps(['title', 'shortSummary'])
</script>