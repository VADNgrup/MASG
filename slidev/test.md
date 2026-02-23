---
theme: seriph
title: Demo Slidev
info: Slide
katex: true
---

# 👋 Presentation about {title}
Speaker: {speaker}

---

# 📋 Table of Contents

- 1. Dataset and Evaluation Protocol
- 1.1. Preprocessing and Metrics
- 2. Network Architecture
- 2.1. Nonlinearity and Normalization
- 2.2. Connectivity and Layer Design
- 3. Reducing Overfitting
- 3.1. Data Augmentation
- 3.2. Dropout
- 4. Results and Analysis
- 4.1. Performance and Visualizations
---
layout: split
---

::title::
# 1. Dataset and Evaluation Protocol
::left::
- The dataset used is ImageNet, with over 15 million labeled high-res images across 22,000 categories.
- Training on large datasets like ImageNet requires models with high capacity, such as deep CNNs, to handle variability.
- Image resolution is standardized to 256×256 by rescaling and center cropping, with mean subtraction for preprocessing.
- Evaluation reports top-1 and top-5 error rates; for example, our model achieved 37.5% and 17.0% on ILSVRC-2010.
- The dataset's size and complexity demand efficient training protocols, including multi-GPU setups and data augmentation.
::right::
<img src="/assets/slide_1_slide_1_serper_1.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split
---

::title::
# 1.1. Preprocessing and Metrics
::left::
- Preprocessing and metrics are crucial for evaluating CNN performance.
- Image normalization involved subtracting the training set mean activity from each pixel.
- Error rates are reported as top-1 and top-5, indicating the fraction of incorrect predictions.
- Data augmentation, like translations, reflections, and color jittering, helps reduce overfitting.
- Dropout randomly zeroes neuron outputs during training, boosting model robustness.
::right::
<img src="/assets/slide_2_img_01.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split-2-right-component
---

::title::
# 2. Network Architecture

::left::
- Deep CNNs trained on large datasets like ImageNet achieve record-breaking accuracy.
- Key innovations include ReLU nonlinearities, multi-GPU training, local response normalization, and overlapping pooling.
- ReLUs (\$f(x) = \max(0, x)\$) enable faster training compared to saturating functions like tanh.
- Using multiple GPUs with strategic connectivity reduces training time and improves performance.
- Overlapping pooling (s < z) helps reduce overfitting and enhances model generalization.

::right-top::
<img src="/assets/slide_3_slide_3_serper_3.png" class="max-h-60 mx-auto"/>
::right-top-caption::
Top component caption
::right-bottom::
| Model          | Top-1 (val)   | Top-5 (val)   | Top-5 (test)   |
|----------------|---------------|---------------|----------------|
| SIFT + FVs [7] | -             | -             | 26.2%          |
| 1 CNN          | 40.7%         | 18.2%         | -              |
| 5 CNNs         | 38.1%         | 16.4%         | 16.4%          |
| 1 CNN*         | 39.0%         | 16.6%         | -              |
| 7 CNNs*        | 36.7%         | 15.4%         | 15.3%          |

::right-bottom-caption::
Bottom component caption
---
layout: split
---

::title::
# 2.1. Nonlinearity and Normalization
::left::
- Nonlinearity and normalization are key for deep CNNs' success.
- ReLU nonlinearity ($f(x) = \max(0, x)$) speeds up training dramatically.
- Local response normalization creates competition among neurons, aiding generalization.
- Overlapping pooling ($s < z$) slightly improves accuracy and reduces overfitting.
- Proper normalization and nonlinearity choices are crucial for training large, deep models.
::right::
<img src="/assets/slide_4_slide_4_serper_2.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split
---

::title::
# 2.2. Connectivity and Layer Design
::left::
- Connectivity and layer design are crucial for CNN performance, enabling deep architectures.
- Using multiple GPUs with restricted inter-layer communication reduces error rates and training time.
- Overlapping pooling (s < z) improves accuracy by providing more robust feature summaries.
- Local response normalization creates competition among neurons, aiding generalization.
::right::
<img src="/assets/slide_5_slide_5_serper_2.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---

# 3. Reducing Overfitting
- Deep CNNs trained on large datasets like ImageNet require effective overfitting reduction techniques.
- Dropout, data augmentation, and architectural choices like overlapping pooling help combat overfitting.
- Dropout randomly zeroes neuron outputs during training, promoting robust feature learning.
- Data augmentation via image translation, reflection, and PCA-based color jittering artificially enlarges the dataset.
- Overlapping pooling (s < z) reduces overfitting and improves model generalization during training.
---
layout: split
---

::title::
# 3.1. Data Augmentation
::left::
- 3.1 Data Augmentation boosts training data with label-preserving transformations.
- It includes image translations, reflections, and RGB intensity alterations, reducing overfitting.
- Transformations generate many effective training examples without extra storage or significant cost.
- Adding PCA-based RGB variations helps the model learn invariance to illumination changes.
- These techniques significantly improve the model's generalization on large datasets like ImageNet.
::right::
<img src="/assets/slide_7_img_03.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split
---

::title::
# 3.2. Dropout
::left::
- Dropout is a powerful regularization technique that reduces overfitting by randomly zeroing neuron outputs during training.
- It forces neurons to learn more robust features, avoiding co-adaptations, and is applied in the first two fully-connected layers.
- During training, each hidden neuron is dropped with probability 0.5; at test time, outputs are scaled by 0.5 to approximate model averaging.
- Dropout roughly doubles training iterations but significantly improves generalization, especially in large, deep CNNs.
::right::
<img src="/assets/slide_8_slide_8_serper_3.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split-2-right-component
---

::title::
# 4. Results and Analysis

::left::
- Our large CNN achieved state-of-the-art results on ImageNet with 37.5% top-1 and 17.0% top-5 error rates.
- Techniques like data augmentation and dropout were key to reducing overfitting and boosting performance.
- Using ReLU nonlinearities sped up training times significantly compared to traditional tanh units.
- Training across multiple GPUs with restricted connectivity improved accuracy and efficiency.
- Overall, depth and regularization strategies proved crucial for handling massive models on large datasets.

::right-top::
<img src="/assets/slide_9_slide_9_serper_3.png" class="max-h-60 mx-auto"/>
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

# 4.1. Performance and Visualizations
- Deep CNNs trained on large datasets like ImageNet achieve record-breaking results, with top-1 error of $$37.5\%$$ and top-5 error of $$17.0\%$$ on ILSVRC-2010.
- Key innovations include ReLU nonlinearities, multi-GPU training, local response normalization, and overlapping pooling, boosting learning speed and accuracy.
- Regularization techniques such as data augmentation and dropout are crucial to combat overfitting in models with 60 million parameters.
- The architecture's depth—five convolutional and three fully-connected layers—proves essential; removing any convolutional layer degrades performance.
- Results demonstrate the power of large, deep CNNs for visual recognition, with the potential for further improvements as hardware and datasets grow.

---
 layout: center
class: text-center
---

# Thank You!
----
