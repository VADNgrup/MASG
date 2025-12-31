---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100 font-sans overflow-hidden
---

<div class="grid grid-cols-12 h-full w-full gap-4 p-4">
  <div class="col-span-5 flex flex-col justify-center pl-8 pr-4 z-10">
    <div class="flex items-center gap-2 mb-6" v-motion-slide-top>
      <span class="h-px w-8 bg-purple-400"></span>
      <span class="text-xs font-mono uppercase tracking-[0.2em] text-purple-300">{{ category|default('Presentation') }}</span>
    </div>
    <h1 class="text-6xl font-black leading-tight mb-6">
      {{ title }}
    </h1>
    <p class="text-lg text-gray-300/90 leading-relaxed mb-10 pr-10 font-light">
      {{ description }}
    </p>
  </div>
  <div class="col-span-7 relative h-full rounded-[3rem] overflow-hidden group ml-4">
     {% if image %}
     <img
       src="{{ image }}"
       class="absolute inset-0 w-full h-full object-cover transition-transform duration-[1.5s] ease-in-out group-hover:scale-110"
       alt="{{ title }}"
     />
     <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/40 to-transparent opacity-80"></div>
     {% else %}
     <div class="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-blue-900/20 to-pink-900/20"></div>
     {% endif %}
  </div>
</div>
