---
layout: standard
class: p-0 bg-[#0a0a0a] flex items-center justify-center
---

<div class="w-[90%] h-[80%] bg-gradient-to-br from-white/10 to-white/5 rounded-[3rem] border border-white/10 backdrop-blur-xl relative overflow-hidden p-16">
  <div class="absolute -top-24 -right-24 w-96 h-96 bg-purple-600/20 blur-[120px] rounded-full"></div>
  <div class="absolute -bottom-24 -left-24 w-96 h-96 bg-blue-600/20 blur-[120px] rounded-full"></div>

  <div class="relative z-10 grid grid-cols-2 h-full items-center">
    <div>
      <h2 class="text-5xl font-black text-white mb-6 leading-tight">{{ title }}</h2>
      <p class="text-gray-400 text-lg mb-8 max-w-md">{{ description }}</p>
      {% if cta_text %}
      <button class="px-8 py-3 bg-white text-black font-bold rounded-full hover:bg-blue-400 hover:text-white transition-all duration-300 transform hover:scale-105 shadow-xl shadow-white/5">
        {{ cta_text }}
      </button>
      {% endif %}
    </div>
    <div class="grid grid-cols-2 gap-4">
      {% for stat in stats %}
      <div class="p-6 h-32 bg-black/40 rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center">
        <span class="text-4xl font-black text-{{ stat.color|default('white') }} mb-1">{{ stat.value }}</span>
        <span class="text-xs uppercase tracking-widest text-gray-500 font-bold">{{ stat.label }}</span>
      </div>
      {% endfor %}
    </div>
  </div>
</div>
