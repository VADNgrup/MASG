---
theme: umn
title: Main Ttile
author: Slidev With Multi-agent System
katex: true
fonts:
  sans: Roboto
  serif: Roboto
  mono: Roboto
---

# Main Title
---

<h1 style="color: #e2b96f;">Table Of Content</h1>

 1. Introduction to Deep Convolutional Neural Networks \
 1.1. Background and Motivation \
 1.2. Key Contributions of the Study \
 1.3. Challenges in Image Recognition 
 2. Architecture of the Deep Convolutional Neural Network \
 2.1. Core Components and Design Choices \
 2.2. Advanced Techniques for Performance Optimization 
 3. Training and Optimization Strategies \
 3.1. Data Augmentation Methods \
 3.2. Regularization Techniques for Overfitting Prevention 
 4. Results and Evaluation \
 4.1. Performance on Benchmark Datasets \
 4.2. Comparative Analysis with Previous Approaches 
---

<div style="
    --image-width: 40%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">Image Right</h1>
  </div>

  <!-- Two columns -->
  <div style="display: grid;
              grid-template-columns: 1fr var(--image-width);
              align-items: start;
              gap: 2.5rem;
              flex: 1; min-height: 0;">
    <!-- Left: text -->
    <div style="overflow: auto;">
      <ul>
        <li>Our network has 60 million parameters and 650,000 neurons...</li>
        <li>We achieved top-1 and top-5 error rates of 37.5% and 17.0%...</li>
        <li>Used ReLU nonlinearity for faster training and dropout regularization...</li>
        <li>Implemented overlapping pooling and local response normalization...</li>
        <li>Trained on two GPUs with efficient convolution implementation...</li>
      </ul>
    </div>
    <!-- Right: image -->
    <div style="container-type: inline-size;">
      <img src="/assets/img_00.png" style="width: 100%; display: block;" />
      <p style="text-align:center; font-size: 2.5cqw;"><b>Figure 1: Figure Caption</b></p>
    </div>

  </div>
</div>
---

<div style="
    --image-width: 20%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">Two Image Right</h1>
  </div>

  <!-- Two columns: chữ và ảnh đều bắt đầu từ mép trên -->
  <div style="display: grid;
              grid-template-columns: 1fr var(--image-width);
              align-items: start;
              gap: 1rem;
              flex: 1; min-height: 0;">
    <!-- Left: text -->
    <div style="overflow: auto;">
      <ul>
        <li>Our network has 60 million parameters and 650,000 neurons... Our network has 60 million parameters and 650,000 neurons... Our network has 60 million parameters and 650,000 neurons... Our network has 60 million parameters and 650,000 neurons... Our network has 60 million parameters and 650,000 neurons... Our network has 60 million parameters and 650,000 neurons... Our network has 60 million parameters and 650,000 neurons...</li>
        <li>We achieved top-1 and top-5 error rates of 37.5% and 17.0%...</li>
        <li>Used ReLU nonlinearity for faster training and dropout regularization...</li>
        <li>Implemented overlapping pooling and local response normalization...</li>
        <li>Trained on two GPUs with efficient convolution implementation...</li>
        <li>Trained on two GPUs with efficient convolution implementation...</li>
        <li>Trained on two GPUs with efficient convolution implementation...</li>
      </ul>
    </div>
    <!-- Right: image -->
    <div style="container-type: inline-size;">
      <div>
        <img src="/assets/img_00.png" style="width: 100%; display: block;" />
        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0;"><b>Figure 1: Figure Caption Figure Caption Figure Caption Figure Caption Figure Caption Figure Caption Figure Caption </b></p>
      </div>
      <div>
        <img src="/assets/img_00.png" style="width: 100%; display: block;" />
        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0;"><b>Figure 2: Figure Caption</b></p>
      </div>
    </div>

  </div>
</div>
---

<h1 style="color: #e2b96f;">Only Content</h1>

- We trained a large, deep CNN to classify 1.2M ImageNet images into 1000 classes with 37.5% top-1 and 17.0% top-5 error rates.
- The network has 60 million parameters and 650,000 neurons with 5 convolutional layers and 3 fully-connected layers.
- Used ReLU nonlinearity for faster training and dropout regularization to reduce overfitting.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.
---

<div style="
    --left-width: 45%;
    --right-width: 45%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">Two cols content</h1>
  </div>

  <!-- Two columns: cả 2 đều bắt đầu từ mép trên -->
  <div style="display: grid;
              grid-template-columns: var(--left-width) var(--right-width);
              align-items: start;
              gap: 2.5rem;
              flex: 1; min-height: 0;">
    <!-- Left -->
    <div style="overflow: auto;">
      <ul>
        <li>Our study trained one of the largest CNNs to date on ImageNet, achieving record-breaking results with 37.5% top-1 and 17.0% top-5 error rates.</li>
        <li>We introduced a highly-optimized GPU implementation of 2D convolution and novel features like ReLU nonlinearity and dropout to improve performance and reduce overfitting.</li>
        <li>The network's depth was crucial - removing any convolutional layer degraded performance by ~2% on top-1 accuracy, highlighting the importance of depth in CNNs.</li>
      </ul>
    </div>
    <!-- Right -->
    <div style="overflow: auto; font-size: 1rem">
      <ul>
        <li>We used data augmentation (image translations, reflections, and PCA-based intensity variations) and dropout to combat overfitting effectively.</li>
        <li>Our architecture featured five convolutional layers and three fully-connected layers with 60 million parameters, trained on 1.2 million images over 5-6 days on two GTX 580 GPUs.</li>
      </ul>
    </div>
  </div>
</div>
---


<h1 style="color: #e2b96f;">Image Above</h1>

<div style="width: 30%; margin: auto; container-type: inline-size;">
  <img src="/assets/img_00.png" style="width: 100%; display: block;" />
  <p style="text-align:center; font-size: 4cqw;"><b>Figure 1: Figure Caption</b></p>
</div>

- We trained a large, deep CNN to classify 1.2M ImageNet images into 1000 classes with 37.5% top-1 and 17.0% top-5 error rates.
- The network has 60 million parameters and 650,000 neurons with 5 convolutional layers and 3 fully-connected layers.
- Used ReLU nonlinearity for faster training and dropout regularization to reduce overfitting.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.

---

<div style="
    --image-width: 45%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">Image Left</h1>
  </div>

  <!-- Two columns: ảnh bên trái, chữ bên phải -->
  <div style="display: grid;
              grid-template-columns: var(--image-width) 1fr;
              align-items: start;
              gap: 2.5rem;
              flex: 1; min-height: 0;">
    <!-- Left: image -->
    <div style="container-type: inline-size;">
      <img src="/assets/img_00.png" style="width: 100%; max-width: 100%; display: block; object-fit: contain;" />
      <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0;"><b>Figure 1: Figure Caption</b></p>
    </div>
    <!-- Right: text -->
    <div style="overflow: auto; font-size: 1rem">
      <ul>
        <li>Our network has 60 million parameters and 650,000 neurons... Our network has 60 million parameters and 650,000 neurons... Our network has 60 million parameters and 650,000 neurons... Our network has 60 million parameters and 650,000 neurons...</li>
        <li>We achieved top-1 and top-5 error rates of 37.5% and 17.0%...</li>
        <li>Used ReLU nonlinearity for faster training and dropout regularization...</li>
        <li>Implemented overlapping pooling and local response normalization...</li>
        <li>Trained on two GPUs with efficient convolution implementation...</li>
      </ul>
    </div>
  </div>
</div>
---

<div style="
    --image-width: 25%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">Two Image Left</h1>
  </div>

  <!-- Two columns: ảnh bên trái, chữ bên phải -->
  <div style="display: grid;
              grid-template-columns: var(--image-width) 1fr;
              align-items: start;
              gap: 1rem;
              flex: 1; min-height: 0;">
    <!-- Left: image -->
    <div style="container-type: inline-size;">
      <div>
        <img src="/assets/img_00.png" style="width: 100%; max-width: 100%; display: block; object-fit: contain;" />
        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0;"><b>Figure Figure Caption Figure Caption Figure Caption Figure Caption Figure Caption Figure Caption Figure</b></p>
      </div>
      <div>
        <img src="/assets/table_002.png" style="width: 100%; max-width: 100%; display: block; object-fit: contain;" />
        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>Figure 2: Figure Caption</b></p>
      </div>
    </div>
    <!-- Right: text -->
    <div style="overflow: auto; font-size: 1rem">
      <ul>
        <li>Our network has 60 million parameters and 650,000 neurons...</li>
        <li>We achieved top-1 and top-5 error rates of 37.5% and 17.0%...</li>
        <li>Used ReLU nonlinearity for faster training and dropout regularization...</li>
        <li>Implemented overlapping pooling and local response normalization...</li>
        <li>Trained on two GPUs with efficient convolution implementation...</li>
      </ul>
    </div>
  </div>
</div>
---

<h1 style="color: #e2b96f;">Image Below</h1>

- We trained a large, deep CNN to classify 1.2M ImageNet images into 1000 classes with 37.5% top-1 and 17.0% top-5 error rates.
- The network has 60 million parameters and 650,000 neurons with 5 convolutional layers and 3 fully-connected layers.
- Used ReLU nonlinearity for faster training and dropout regularization to reduce overfitting.
- The network has 60 million parameters and 650,000 neurons with 5 convolutional layers and 3 fully-connected layers.
- Used ReLU nonlinearity for faster training and dropout regularization 


<div style="width: 30%; margin: auto; container-type: inline-size;">
  <img src="/assets/table_001.png" style="width: 100%; display: block;" />
  <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0;"><b>Figure 1: Figure Caption</b></p>
</div>
---

<h1 style="color: #e2b96f;">Two Image Above</h1>

<div style="width: 50%; margin: auto; display: flex; gap: 1rem;">
  <div style="flex: 1; container-type: inline-size;">
    <img src="/assets/img_00.png" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />
    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0;"><b>Figure 1: Figure Caption</b></p>
  </div>
  <div style="flex: 1; container-type: inline-size;">
    <img src="/assets/img_00.png" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />
    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0;"><b>Figure 2: Figure Caption</b></p>
  </div>
</div>

- We trained a large, deep CNN to classify 1.2M ImageNet images into 1000 classes with 37.5% top-1 and 17.0% top-5 error rates.
- The network has 60 million parameters and 650,000 neurons with 5 convolutional layers and 3 fully-connected layers.
- Used ReLU nonlinearity for faster training and dropout regularization to reduce overfitting.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.
---

<h1 style="color: #e2b96f;">Two Image Below</h1>

- We trained a large, deep CNN to classify 1.2M ImageNet images into 1000 classes with 37.5% top-1 and 17.0% top-5 error rates.
- The network has 60 million parameters and 650,000 neurons with 5 convolutional layers and 3 fully-connected layers.
- Used ReLU nonlinearity for faster training and dropout regularization to reduce overfitting.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.

<div style="width: 70%; margin: auto; display: flex; gap: 1rem;">
  <div style="flex: 1; container-type: inline-size;">
    <img src="/assets/img_00.png" style="width: 100%; display: block;" />
    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0;"><b>Figure 1: Figure Caption</b></p>
  </div>
  <div style="flex: 1; container-type: inline-size;">
    <img src="/assets/img_00.png" style="width: 100%; display: block;" />
    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0;"><b>Figure 2: Figure Caption</b></p>
  </div>
</div>
---

<h1 style="color: #e2b96f;">Formula Below</h1>

- We trained a large, deep CNN to classify 1.2M ImageNet images into 1000 classes with 37.5% top-1 and 17.0% top-5 error rates.
- The network has 60 million parameters and 650,000 neurons with 5 convolutional layers and 3 fully-connected layers.
- Used ReLU nonlinearity for faster training and dropout regularization to reduce overfitting.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.
<!-- Latex Formula Block -->
$$
y = (x+1)^2 \\
  = x^2 + 2x + 1 \\
  = x(x+2) + 1
$$
---

<h1 style="color: #e2b96f;">Formula Top</h1>

<!-- Latex Formula Block -->
$$
y = (x+1)^2 \\
  = x^2 + 2x + 1 \\
  = x(x+2) + 1
$$

- We trained a large, deep CNN to classify 1.2M ImageNet images into 1000 classes with 37.5% top-1 and 17.0% top-5 error rates.
- The network has 60 million parameters and 650,000 neurons with 5 convolutional layers and 3 fully-connected layers.
- Used ReLU nonlinearity for faster training and dropout regularization to reduce overfitting.
- Achieved 15.3% top-5 error rate in ILSVRC-2012 competition, outperforming other entries significantly.
---

<div style="
    --left-width: 45%;
    --right-width: 45%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">Two contents in a slide</h1>
  </div>

  <div style="display: grid;
              grid-template-columns: var(--left-width) var(--right-width);
              align-items: start;
              gap: 2.5rem;
              flex: 1; min-height: 0;">
    <!-- Left -->
    <div style="overflow: auto;">
      <h2>Heading of Content 1</h2>
      <ul>
        <li>Our study trained one of the largest CNNs to date on ImageNet, achieving record-breaking results with 37.5% top-1 and 17.0% top-5 error rates.</li>
        <li>We introduced a highly-optimized GPU implementation of 2D convolution and novel features like ReLU nonlinearity and dropout to improve performance and reduce overfitting.</li>
        <li>The network's depth was crucial - removing any convolutional layer degraded performance by ~2% on top-1 accuracy, highlighting the importance of depth in CNNs.</li>
      </ul>
    </div>
    <!-- Right -->
    <div style="overflow: auto;">
      <h2>Heading of content 2</h2>
      <ul>
        <li>We used data augmentation (image translations, reflections, and PCA-based intensity variations) and dropout to combat overfitting effectively.</li>
        <li>Our architecture featured five convolutional layers and three fully-connected layers with 60 million parameters, trained on 1.2 million images over 5-6 days on two GTX 580 GPUs.</li>
      </ul>
    </div>
  </div>
</div>
---

<h1 style="color: #e2b96f;">Comparison Slide</h1>

| <b>Tiêu chí</b> | <b>Tai nghe</b> | <b>Loa</b> |
|---|---|---|
| <b>Không gian nghe</b> | Cá nhân | Cả phòng |
| <b>Tính di động</b> | Cao | Thấp hơn |
| <b>Riêng tư</b> | Cao | Thấp |
| <b>Trải nghiệm âm thanh</b> | Chi tiết, gần tai | Rộng, lan tỏa |

---

<h1 style="color: #2c3e50;">XIn cahfo</h1>

<div style="width: 90%; margin: auto; display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; container-type: inline-size;">
  <div style="display: flex; flex-direction: column;">
    <img src="/assets/slide_12_q1_serper_3.png" style="width: 100%; max-width: 100%; max-height: 260px; display: block; object-fit: contain;" />
    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>Caption 1</b></p>
  </div>
  <div style="display: flex; flex-direction: column;">
    <img src="/assets/slide_12_q1_serper_3.png" style="width: 100%; max-width: 100%; max-height: 260px; display: block; object-fit: contain;" />
    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>Caption 2</b></p>
  </div>
  <div style="display: flex; flex-direction: column;">
    <img src="/assets/slide_12_q1_serper_3.png" style="width: 100%; max-width: 100%; max-height: 260px; display: block; object-fit: contain;" />
    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>Caption 3</b></p>
  </div>
</div>

- ImageNet contains over 15 million labeled high-resolution images across 22,000 categories.
- ILSVRC uses a subset of 1.2 million training images across 1000 distinct object classes.
- Images are down-sampled to a fixed 256 × 256 resolution with mean subtraction applied.
- The central 256 × 256 patch is cropped from the rescaled rectangular input images.
- Performance is measured using top-1 and top-5 error rates on the test set.
---
layout: cover
---

# Thank you for listening
