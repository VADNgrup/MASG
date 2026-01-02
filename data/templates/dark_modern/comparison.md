---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="h-full w-full p-16 flex flex-col justify-center">
  <div class="text-center mb-12">
    <h2 class="text-4xl font-black mb-4">{{ title }}</h2>
    {% if subtitle %}
    <p class="text-gray-500 uppercase tracking-[0.3em] text-xs">{{ subtitle }}</p>
    {% endif %}
  </div>

  <div class="grid grid-cols-2 gap-12">
    <div class="p-8 rounded-[2rem] bg-white/5 border border-red-500/20 relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <carbon:warning-alt class="text-8xl text-red-500" />
      </div>
      <h3 class="text-xl font-bold text-red-400 mb-6 flex items-center gap-2">
        <carbon:close-filled /> {{ left_title }}
      </h3>
      <ul class="space-y-4 text-gray-400 text-sm">
        {% for item in left_items %}
        <li class="flex items-center gap-3"> <carbon:dot-mark class="text-red-500"/> {{ item|latex }} </li>
        {% endfor %}
      </ul>
    </div>
    <div class="p-8 rounded-[2rem] bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-blue-500/30 relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <carbon:checkmark-filled class="text-8xl text-blue-500" />
      </div>
      <h3 class="text-xl font-bold text-blue-400 mb-6 flex items-center gap-2">
        <carbon:checkmark-filled /> {{ right_title }}
      </h3>
      <ul class="space-y-4 text-gray-100 text-sm">
        {% for item in right_items %}
        <li class="flex items-center gap-3 font-medium"> <carbon:flash class="text-yellow-400"/> {{ item|latex }} </li>
        {% endfor %}
      </ul>
    </div>
  </div>
</div>
