---
layout: {{ theme.layout|default('standard') }}
class: {{ theme.base_class|default('p-0 bg-[#0a0a0a] text-gray-100 font-sans overflow-hidden') }}
---

# {{ title }}

<div class="flex items-center gap-3 mb-6">
  <div class="h-1 w-12 bg-gradient-to-r from-blue-500 to-purple-500"></div>
  <span class="text-xs uppercase tracking-widest text-blue-400 font-semibold">{{ category }}</span>
</div>

{% if bullets %}
{% for bullet in bullets %}
- {{ bullet }}
{% endfor %}
{% endif %}

<div class="grid grid-cols-2 gap-6 mt-8">
{% for formula in formulas %}
<div class="formula-card">

${{ formula }}$

</div>
{% endfor %}
</div>

<style>
.formula-card {
  @apply bg-white/5 border border-white/10 rounded-2xl p-6 text-center;
}
</style>
