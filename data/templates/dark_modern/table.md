---
layout: center
class: text-center
---

# {{ title }}

| {{ headers|join(' | ') }} |
| {% for h in headers %}---{% if not loop.last %} | {% endif %}{% endfor %} |
{% for row in rows -%}
| {{ row|join(' | ') }} |
{% endfor %}
