---
theme: seriph
title: Demo Slidev
info: Slide
katex: true
---

# 👋 Presentation Title Slide
Speaker Information 
---

# 1. Slide with bullet points only
- Bullet Point 1 with equation inline: $sin(x)$
- Bullet Point 2 
- Bullet Point 3
- Bullet Point 4 
---
layout: split
---

::title::
# 2. Slide have two columns layout: bullet points (left) and image (right)
::left::
- Accuracy improves significantly $sin(x)$
- Training time is reduced
- Model is more stable $cos(x)$
::right::
<img src="/assets/table_001_chart.png" class="max-h-60 mx-auto"/>
::right-caption::
This is the caption for the image This is the caption for the image

---
layout: split-2-right-component
---

::title::
# 3. Slide have two columns layout: bullet points (left) and 2 components (right)

::left::
- Bullet Point 1 Bullet Point 3 Bullet Point 3 Bullet Point 3 Bullet Point 3 
- Bullet Point 2
- Bullet Point 3

::right-top::
<img src="/assets/table_001_chart.png" class="max-h-60 mx-auto"/>
::right-top-caption::
This is the caption for the top image 
::right-bottom::
<img src="/assets/table_001_chart.png" class="max-h-80 mx-auto"/>
::right-bottom-caption::
This is the caption for the bottom image

---
layout: only_component
---

::title::
# 4. Slide with component only
::component::
<img src="/assets/table_001_chart.png" class="max-h-60 mx-auto"/>
::caption::
This is the caption for the image This is the caption for the image  


