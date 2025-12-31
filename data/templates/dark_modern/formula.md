---
layout: center
class: text-center
---

# {{ title }}

{% for bullet in bullets -%}
- {{ bullet }}
{% endfor %}

{% for formula in formulas -%}

$$
{{ formula }}
$$
{% endfor %}
