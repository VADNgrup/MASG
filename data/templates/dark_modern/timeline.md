---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="h-full w-full flex flex-col justify-center px-12 py-8 relative">
  <div class="absolute top-20 right-20 w-96 h-96 bg-blue-600/10 rounded-full blur-[120px]"></div>
  <div class="absolute bottom-20 left-20 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px]"></div>

  <div class="mb-8 relative z-10" v-motion-slide-top>
    <div class="flex items-center gap-2 mb-2">
      <div class="h-0.5 w-8 bg-gradient-to-r from-blue-500 to-purple-500"></div>
      <span class="text-[10px] uppercase tracking-[0.3em] text-blue-400 font-bold">{{ category|default('Timeline') }}</span>
    </div>
    <h2 class="text-4xl font-black">{{ title }}</h2>
  </div>

  <div class="relative z-10">
    <div class="absolute top-[48px] left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-emerald-500/20"></div>
    <div class="grid grid-cols-{{ milestones|length }} gap-4">
      {% for milestone in milestones %}
      <div class="relative" v-motion-slide-bottom :delay="{{ loop.index * 150 }}">
        <div class="flex flex-col items-center mb-4">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-{{ milestone.color|default('blue') }}-500 to-{{ milestone.color|default('blue') }}-600 flex items-center justify-center mb-3 shadow-xl shadow-{{ milestone.color|default('blue') }}-500/40 relative">
            <carbon:{{ milestone.icon|default('cube') }} class="text-xl text-white" />
            <div class="absolute -inset-0.5 bg-{{ milestone.color|default('blue') }}-500/20 rounded-xl blur -z-10"></div>
          </div>
          <div class="h-6 w-0.5 bg-gradient-to-b from-{{ milestone.color|default('blue') }}-500/50 to-transparent"></div>
        </div>
        <div class="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-4 hover:border-{{ milestone.color|default('blue') }}-500/50 transition-all duration-300 hover:transform hover:scale-105">
          <div class="text-{{ milestone.color|default('blue') }}-400 font-mono text-[10px] mb-2 uppercase tracking-wider">{{ milestone.period }}</div>
          <h3 class="text-base font-black mb-2 text-white">{{ milestone.title }}</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-3">{{ milestone.description }}</p>
          {% if milestone.tags %}
          <div class="flex flex-wrap gap-1.5">
            {% for tag in milestone.tags %}
            <span class="text-[9px] px-2 py-0.5 bg-{{ milestone.color|default('blue') }}-500/20 text-{{ milestone.color|default('blue') }}-300 rounded-full">{{ tag }}</span>
            {% endfor %}
          </div>
          {% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</div>
