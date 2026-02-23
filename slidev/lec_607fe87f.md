---
theme: seriph
title: Demo Slidev
info: Slide
katex: true
---

# 👋 Presentation about {title}
Speaker: {speaker}

---
layout: split
---

::title::
# ImageNet Classification Overview
::left::
- ImageNet: 15M labeled images, 22,000 categories!
- Deep CNN: 60M parameters, 650,000 neurons, 8 layers
- Achieved top-1 error rate: 37.5%, top-5: 17.0%
- Innovations: ReLU, dropout, GPU optimization
- ILSVRC-2012 top-5 error rate: 15.3%, best result!
::right::
<img src="/assets/img_01.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---

# Introduction to Object Recognition
- Machine learning is key to object recognition.
- Large datasets improve performance; ImageNet is crucial.
- Convolutional Neural Networks (CNNs) excel in image tasks.
- CNNs are efficient with fewer parameters than traditional networks.
- GPU advancements enable large-scale CNN training.
---

# Exploring the ImageNet Dataset
- ImageNet: Over 15 million labeled images in 22,000 categories.
- ILSVRC competitions: Annual challenge using ImageNet subsets.
- Data preprocessing: Down-sampling to 256 × 256 resolution.
- Training: 1.2 million images, 50,000 validation, 150,000 testing.
- Error rates: Top-1 and Top-5 for model evaluation.
---
layout: split
---

::title::
# Deep Dive into CNN Architecture
::left::
- Eight learned layers: five convolutional, three fully-connected
- ReLU nonlinearity accelerates training significantly
- Training on multiple GPUs enhances efficiency
- Dropout technique effectively reduces overfitting
::right::
<img src="/assets/img_00.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split
---

::title::
# ReLU Nonlinearity: Speed and Efficiency
::left::
- ReLUs: $f(x) = \max(0, x)$, faster than $\tanh(x)$
- Deep CNNs with ReLUs train several times faster
- Faster learning boosts large model performance
- ReLUs enable experimentation with large networks
::right::
<img src="/assets/img_02.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---

# Reducing Overfitting in CNNs
- Data augmentation enlarges dataset with label-preserving transformations.
- Dropout: Sets neuron outputs to zero with probability 0.5 during training.
- Dropout prevents complex co-adaptations, forcing robust feature learning.
- Both techniques significantly reduce overfitting in large neural networks.
---
layout: split-2-right-component
---

::title::
# ILSVRC Results and Performance

::left::
- Achieved top-1 error rate of 37.5% and top-5 error rate of 17.0% in ILSVRC-2010.
- CNN model outperformed Sparse coding and SIFT + FVs models significantly.
- In ILSVRC-2012, achieved top-5 error rate of 15.3%, leading the competition.
- Utilized a network with 60 million parameters, five convolutional layers, and three fully-connected layers.
- Implemented dropout and GPU acceleration to enhance model performance and reduce overfitting.

::right-top::
<img src="/assets/table_001_chart.png" class="max-h-60 mx-auto"/>
::right-top-caption::
Top component caption
::right-bottom::
| Model             | Top-1   | Top-5   |
|-------------------|---------|---------|
| Sparse coding [2] | 47.1%   | 28.2%   |
| SIFT + FVs [24]   | 45.7%   | 25.7%   |
| CNN               | 37.5%   | 17.0%   |

::right-bottom-caption::
Bottom component caption
---
layout: split
---

::title::
# Qualitative Evaluations of CNNs
::left::
- Visualize convolutional kernels learned by the network.
- Top-5 predictions on test images reveal model's accuracy.
- Feature activations show image similarity in hidden layers.
- Specialization of kernels across GPUs improves performance.
- Euclidean distance in feature space indicates image similarity.
::right::
<img src="/assets/img_03.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---

# Discussion and Future Directions
- The depth of the network is crucial for performance. Removing any convolutional layer degrades results.
- Unsupervised pre-training holds promise, especially as network sizes increase without more labeled data.
- Future applications could leverage video sequences, utilizing temporal structures for richer information.
---

# CNNs: Key Insights and Future Prospects
- CNNs achieved state-of-the-art results in ImageNet classification with top-5 error rates of 17.0% in 2010 and 15.3% in 2012.
- Techniques like dropout and data augmentation effectively reduce overfitting in large neural networks.
- Future advancements in deep learning for image classification hinge on larger datasets and faster GPUs.
- The architecture's depth is crucial: removing any convolutional layer degrades performance.
- The potential of CNNs extends to video sequences, leveraging temporal information.

---
 layout: center
class: text-center
---

# Thank You!
----
