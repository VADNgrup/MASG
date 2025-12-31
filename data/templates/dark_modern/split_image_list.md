---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full">
  <div class="col-span-6 relative overflow-hidden p-8">
     <div class="w-full h-full rounded-[2.5rem] overflow-hidden relative border border-white/10">
        {% if image %}
        <img src="{{ image }}" class="object-cover w-full h-full scale-105" />
        <div class="absolute inset-0 bg-blue-900/20 mix-blend-overlay"></div>
        <div class="absolute inset-0 bg-gradient-to-tr from-[#0a0a0a] via-transparent to-transparent"></div>
        {% else %}
        <div class="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-pink-900/20"></div>
        {% endif %}
        {% if badge %}
        <div class="absolute top-8 left-8 p-4 bg-black/60 backdrop-blur-md rounded-2xl border border-white/20" v-motion-pop>
            <div class="flex items-center gap-3">
               <div class="h-2 w-2 rounded-full bg-green-400 animate-pulse"></div>
               <span class="text-xs font-mono uppercase tracking-tighter">{{ badge }}</span>
            </div>
         </div>
        {% endif %}
      </div>
   </div>

  <div class="col-span-6 flex flex-col justify-center px-12">
    <h2 class="text-4xl font-bold mb-8 leading-tight">{{ title }}</h2>
    <div class="space-y-6">
      {% for item in items %}
      <div class="flex gap-4 items-start" v-motion-slide-right>
        <div class="text-2xl font-black text-gray-700">{{ "%02d"|format(loop.index) }}</div>
        <div>
          <h4 class="font-bold text-xl text-white">{{ item.heading }}</h4>
          <p class="text-gray-400 text-sm">{{ item.description }}</p>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</div>
