---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100 font-sans overflow-hidden
---

<div class="grid grid-cols-12 h-full w-full p-12 gap-8">
  <div class="col-span-12 h-1/4">
    <div class="flex items-center gap-3 mb-2" v-motion-slide-left>
      <div class="h-1 w-12 bg-gradient-to-r from-blue-500 to-purple-500"></div>
      <span class="text-xs uppercase tracking-widest text-blue-400 font-semibold">{{ category|default('Content') }}</span>
    </div>
    <h2 class="text-5xl font-black italic">{{ title }}</h2>
  </div>

  {% for card in cards %}
  <div class="col-span-4 p-8 bg-white/5 border border-white/10 rounded-[2rem] backdrop-blur-sm hover:border-{{ card.color|default('blue') }}-500/50 transition-all group">
    <div class="w-12 h-12 rounded-xl bg-{{ card.color|default('blue') }}-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
      <carbon:{{ card.icon|default('cube') }} class="text-2xl text-{{ card.color|default('blue') }}-400" />
    </div>
    <h3 class="text-xl font-bold mb-3">{{ card.heading }}</h3>
    <p class="text-sm text-gray-400 leading-relaxed">{{ card.description }}</p>
  </div>
  {% endfor %}
</div>
