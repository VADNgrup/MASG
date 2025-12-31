---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full gap-0">
  <div class="col-span-5 p-16 bg-[#0f0f0f] border-r border-white/5 flex flex-col justify-center">
    <div class="flex items-center gap-2 mb-6">
      <carbon:{{ icon|default('data-blob') }} class="text-blue-400 animate-pulse" />
      <span class="text-xs font-mono text-blue-300 uppercase tracking-widest">{{ badge|default('Code') }}</span>
    </div>
    <h2 class="text-4xl font-black mb-6">{{ title }}</h2>
    <p class="text-gray-400 leading-relaxed mb-8">
      {{ description }}
    </p>
    {% if features %}
    <div class="space-y-4">
      {% for feature in features %}
      <div class="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/10">
        <carbon:checkmark-outline class="text-emerald-400" />
        <span class="text-sm">{{ feature }}</span>
      </div>
      {% endfor %}
    </div>
    {% endif %}
  </div>

  <div class="col-span-7 p-12 bg-black flex items-center justify-center relative">
    <div class="w-full max-w-lg bg-[#1a1a1a] rounded-2xl border border-white/10 shadow-2xl overflow-hidden" v-motion-slide-right>
      <div class="bg-white/5 px-4 py-2 border-b border-white/10 flex gap-2">
        <div class="w-2 h-2 rounded-full bg-red-500/50"></div>
        <div class="w-2 h-2 rounded-full bg-yellow-500/50"></div>
        <div class="w-2 h-2 rounded-full bg-green-500/50"></div>
      </div>
      <div class="p-6 text-[13px] font-mono leading-relaxed">
        {{ code|safe }}
      </div>
    </div>
    <div class="absolute -left-0.1 top-1/2 -translate-y-1/2">
       <carbon:chevron-right class="text-4xl text-blue-500" />
    </div>
  </div>
</div>
