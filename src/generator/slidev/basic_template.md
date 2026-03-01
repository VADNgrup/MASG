---
theme: seriph
title: Demo Slidev
info: Slide
katex: true
fonts:
  sans: Times New Roman
  serif: Times New Roman
  mono: Times New Roman
background: /assets/slide_7_img_00.png
---

<h1 style="color: #e2b96f;">Greeting and Goodbye Slide</h1>
<h2 style="color: #e2b96f;">Speaker Information </h2>
---

<h1 style="color: #e2b96f;">Table of Contents: less than 10 sections (major sections + sub-sections)</h1>
<p></p>

 1. Introduction and Motivation \
 1.1. The Challenge of Object Recognition in RealWorld Settings \
 1.2. The Need for LargeScale Datasets and Powerful Models \
 1.3. Overview of Convolutional Neural Networks (CNNs) in Vision Tasks 
 2. Dataset and Data Preparation \
 2.1. Overview of ImageNet and ILSVRC \
 2.2. Handling Variable Image Resolutions and Preprocessing \
 2.3. Data Augmentation Techniques \
 2.3.1. Image Translations and Reflections \
 2.3.2. Color and Intensity Variations 

---
layout: two-cols-content
---

::title::
<h1 style="color: #e2b96f;">Table of Contents: more than 10 sections</h1>

::left::

 1. Introduction and Motivation \
 1.1. The Challenge of Object Recognition in RealWorld Settings \
 1.2. The Need for LargeScale Datasets and Powerful Models \
 1.3. Overview of Convolutional Neural Networks (CNNs) in Vision Tasks 
 2. Dataset and Data Preparation \
 2.1. Overview of ImageNet and ILSVRC \
 2.2. Handling Variable Image Resolutions and Preprocessing \
 2.3. Data Augmentation Techniques \
 2.3.1. Image Translations and Reflections \
 2.3.2. Color and Intensity Variations 

::right::

 3. Introduction and Motivation \
 3.1. The Challenge of Object Recognition in RealWorld Settings \
 3.2. The Need for LargeScale Datasets and Powerful Models \
 3.3. Overview of Convolutional Neural Networks (CNNs) in Vision Tasks 
---

<h1 style="color: #e2b96f;">Slide only contents</h1>
- Bullet Point 1 Bullet Point 3 Bullet Point 3 Bullet Point 3 Bullet Point 3 
- Bullet Point 2
- Bullet Point 3
---
layout: split
imageWidth: 40%
---

::title::
<h1 style="color: #e2b96f;">2. Slide have two columns layout: bullet points (left) and image (right) with imageWidth can modify </h1>
::left::
- Accuracy improves significantly $sin(x)$ - Accuracy improves significantly $sin(x)$ - Accuracy improves significantly $sin(x)$ - Accuracy improves significantly $sin(x)$
- Training time is reduced
- Model is more stable $cos(x)$
::right::
<img src="/assets/slide_7_img_00.png" class="max-h-60 mx-auto"/>

---
layout: split-2-right-component
imageWidth: 30%
---

::title::
<h1 style="color: #e2b96f;">3. Slide have two columns layout: bullet points (left) and 2 images (right) with imageWidth can modify </h1>

::left::
- Bullet Point 1 Bullet Point 3 Bullet Point 3 Bullet Point 3 Bullet Point 3 
- Bullet Point 2
- Bullet Point 3

::right-top::
<img src="/assets/slide_7_img_00.png" class="max-h-60 mx-auto"/>
::right-bottom::
<img src="/assets/slide_7_img_00.png" class="max-h-80 mx-auto"/>

---
layout: comparison
---

::title::
<h1 style="color: #e2b96f;">4. Slide Comparison: Two Approaches</h1>

::left-title::
## Approach A title

::left::
- Fast training time
- Lower memory usage
- Easier to implement

::right-title::
## Approach B title

::right::
- Higher accuracy
- Better generalization
- More robust to noise

---
layout: two-cols-content
---

::title::
<h1 style="color: #e2b96f;">5. Slide Two Columns Content</h1>

::left::
- Left Bullet Point 1 content
- Left Bullet Point 2 content
- Left Bullet Point 3 content

::right::
- Right Bullet Point 1 content
- Right Bullet Point 2 content
- Right Bullet Point 3 content

---
layout: image_above
imageHeight: 50%
---

::title::
<h1 style="color: #e2b96f;">6. Slide Image Above (imageHeight can modify)</h1>

::image::
<img src="/assets/slide_7_img_00.png" class="max-w-full max-h-full mx-auto"/>

::content::
- Bullet Point 1 content
- Bullet Point 2 content
- Bullet Point 3 content
