---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100 flex items-center justify-center overflow-hidden
---

<div class="absolute inset-0 opacity-20">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.3)_0%,transparent_70%)]"></div>
</div>

<div class="relative z-10 text-center px-8">
  {% if badge %}
  <div class="inline-block px-4 py-1 rounded-full border border-white/10 bg-white/5 text-[10px] uppercase tracking-[0.4em] mb-8 animate-pulse text-blue-300">
    {{ badge }}
  </div>
  {% endif %}
  
  <h1 class="text-8xl font-black mb-12 tracking-tighter">
    {{ title_line1 }}<br/>
    <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500">
      {{ title_line2 }}
    </span>
  </h1>

  {% if contacts %}
  <div class="grid grid-cols-{{ contacts|length }} gap-8 max-w-3xl mx-auto mt-16 p-8 bg-white/5 backdrop-blur-2xl rounded-[2rem] border border-white/10">
    {% for contact in contacts %}
    <div class="text-center {% if not loop.last %}border-r border-white/10{% endif %}">
      <div class="text-gray-500 text-xs uppercase mb-2">{{ contact.label }}</div>
      <div class="font-bold text-sm">{{ contact.value }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if footer_text %}
  <p class="mt-12 text-gray-600 text-[10px] uppercase tracking-widest">
    {{ footer_text }}
  </p>
  {% endif %}
</div>
