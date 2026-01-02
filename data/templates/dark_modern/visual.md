---
layout: two-cols-header
class: {{ theme.base_class|default('p-0 bg-[#0a0a0a] text-gray-100 font-sans') }}
---

<div class="flex items-center gap-2 mb-4">
  <span class="h-px w-8 bg-purple-400"></span>
  <span class="text-xs font-mono uppercase tracking-[0.2em] text-purple-300">{{ category }}</span>
</div>

# {{ title }}

::left::

{% if key_points %}
{% for point in key_points %}
- {{ point }}
{% endfor %}
{% else %}
{% for sentence in description.split('. ') %}
{% if sentence.strip() %}- {{ sentence.strip().rstrip('.') }}
{% endif %}
{% endfor %}
{% endif %}

::right::

{% if image %}
<img src="{{ image }}" class="rounded-2xl object-cover w-full h-80" />
{% else %}
<div class="h-80 bg-gradient-to-br from-purple-900/30 via-blue-900/30 to-pink-900/30 rounded-2xl flex items-center justify-center">
  <carbon:image class="text-6xl text-white/20" />
</div>
{% endif %}
