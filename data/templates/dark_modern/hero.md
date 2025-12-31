---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100 font-sans overflow-hidden
transition: slide-left
---

<div class="grid grid-cols-12 h-full w-full gap-4 p-4">
  <div class="col-span-5 flex flex-col justify-center pl-8 pr-4 z-10">
    <div class="flex items-center gap-2 mb-6" v-motion-slide-top>
      <span class="h-px w-8 bg-purple-400"></span>
      <span class="text-xs font-mono uppercase tracking-[0.2em] text-purple-300">{{ category|default('Presentation') }}</span>
    </div>
    <h1 class="text-6xl font-black leading-tight mb-6">
      {{ title_line1 }}<br/>
      <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-pink-400 filter drop-shadow-lg">
        {{ title_line2 }}
      </span>
      {% if title_line3 %}<br/>{{ title_line3 }}{% endif %}
    </h1>
    <p class="text-lg text-gray-300/90 leading-relaxed mb-10 pr-10 font-light">
      {{ description }}
    </p>
    {% if stat_value %}
    <div class="flex items-center gap-4 p-4 bg-white/5 border border-white/10 rounded-2xl w-fit backdrop-blur-md shadow-xl shadow-purple-900/10 hover:bg-white/10 transition-all" v-motion-slide-bottom>
       <div class="bg-gradient-to-br from-blue-500 to-purple-600 p-3 rounded-xl">
         <carbon:chart-line-data class="text-2xl text-white"/>
       </div>
       <div>
         <div class="font-bold text-2xl text-white">{{ stat_value }}</div>
         <div class="text-sm text-gray-400">{{ stat_label }}</div>
       </div>
    </div>
    {% endif %}
  </div>
  <div class="col-span-7 relative h-full rounded-[3rem] overflow-hidden group ml-4">
     {% if image %}
     <img
       src="{{ image }}"
       class="absolute inset-0 w-full h-full object-cover transition-transform duration-[1.5s] ease-in-out group-hover:scale-110"
       alt="{{ title_line1 }}"
     />
     <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/40 to-transparent opacity-80"></div>
     {% if insight %}
     <div class="absolute bottom-10 left-10 right-10 p-6 bg-white/10 backdrop-blur-xl border border-white/20 rounded-[2rem] shadow-2xl z-20">
        <div class="flex items-start gap-5">
           <div class="bg-gradient-to-br from-pink-500 to-orange-400 p-4 rounded-2xl shadow-lg shadow-pink-500/20">
              <carbon:idea class="text-3xl text-white" />
           </div>
           <div>
              <h3 class="text-xl font-bold text-white mb-2 flex items-center gap-2">
                Core Insight
                <carbon:arrow-up-right class="text-sm opacity-50"/>
              </h3>
              <p class="text-sm text-gray-200/90 leading-snug font-light italic">
                 "{{ insight }}"
              </p>
           </div>
        </div>
     </div>
     {% endif %}
     {% else %}
     <div class="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-blue-900/20 to-pink-900/20"></div>
     {% endif %}
  </div>
</div>
