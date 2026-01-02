---
layout: {{ theme.layout|default('standard') }}
class: {{ theme.base_class|default('p-0 bg-[#0a0a0a] text-gray-100 font-sans overflow-hidden') }}
---

# {{ title }}

<div class="flex items-center gap-3 mb-6">
  <div class="h-1 w-12 bg-gradient-to-r from-blue-500 to-purple-500"></div>
  <span class="text-xs uppercase tracking-widest text-blue-400 font-semibold">{{ category }}</span>
</div>

| {% for h in headers %}{{ h }}{% if not loop.last %} | {% endif %}{% endfor %} |
| {% for h in headers %}:---:{% if not loop.last %} | {% endif %}{% endfor %} |
{% for row in rows %}| {% for cell in row %}{{ cell }}{% if not loop.last %} | {% endif %}{% endfor %} |
{% endfor %}
