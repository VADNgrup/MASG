---
theme: scholarly
title: Deep Convolutional Networks for ImageNet Classification
author: Slidev with Slide Generation System
katex: true
fonts:
  sans: Roboto
  serif: Roboto
  mono: Roboto
---

# Deep Convolutional Networks for ImageNet Classification
---

<h1 style="color: #e2b96f;">Table Of Content</h1>
<p></p>

<div style="font-size: 1.5rem;">

 1. ImageNet Dataset and Challenge Context \
 1.1. Large-scale ImageNet Collection \
 1.2. ILSVRC Competition Metrics
 2. Deep Convolutional Network Architecture \
 2.1. ReLU Nonlinearity and GPU Parallelization \
 2.2. Local Response Normalization and Pooling

</div>
---

<h1 style="color: #e2b96f;">Table Of Content</h1>
<p></p>

<div style="font-size: 1.5rem;">

 3. Strategies to Prevent Overfitting \
 3.1. Data Augmentation Techniques \
 3.2. Dropout Regularization Method
 4. Experimental Results and Analysis \
 4.1. Performance Comparison with State-of-the-Art \
 4.2. Qualitative Evaluation of Learned Features

</div>
---

<h1 style="color: #e2b96f;">1. ImageNet Dataset and Challenge Context</h1>

<div style="width: 55%; margin: auto; container-type: inline-size;">
  <img src="/assets/slide_1_q1_serper_1.png" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />
  <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0"><b>ImageNet dataset visualization showing diverse object categories and labeled high-resolution image examples</b></p>
</div>

- ImageNet contains over 15 million labeled high-resolution images across 22,000 categories.
- ILSVRC uses a subset of 1.2 million training images across 1000 distinct object classes.
- Images are down-sampled to a fixed 256 × 256 resolution with mean subtraction applied.
- The central 256 × 256 patch is cropped from the rescaled rectangular input images.
- Performance is measured using top-1 and top-5 error rates on the test set.
---

<div style="
    --image-width: 45%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">1.1 Large-scale ImageNet Collection</h1>
  </div>

  <!-- Two columns -->
  <div style="display: grid;
              grid-template-columns: var(--image-width) 1fr;
              align-items: start;
              gap: 2.5rem;
              flex: 1; min-height: 0;">
    <!-- Left: image -->
    <div style="container-type: inline-size;">
      <img src="/assets/slide_2_q1_serper_3.png" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />
      <p style="text-align:center; line-height: 1.2; margin: 0.1rem 0 0 0; font-size: 2.5cqw;"><b>ImageNet dataset visualization showing millions of labeled high-resolution images across diverse object categories</b></p>
    </div>
    <!-- Right: text -->
    <div style="overflow: auto;">
      <ul>
        <li>ImageNet contains over 15 million labeled high-resolution images across roughly 22,000 categories.</li>
        <li>Images were collected from the web and labeled by humans using Amazon's Mechanical Turk.</li>
        <li>The ILSVRC subset used for training includes roughly 1.2 million images in 1,000 categories.</li>
        <li>This massive scale enables learning thousands of objects, overcoming limitations of smaller datasets.</li>
      </ul>
    </div>
  </div>
</div>
---

<h1 style="color: #e2b96f;">1.2 ILSVRC Competition Metrics</h1>

<div style="width: 50%; margin: auto; container-type: inline-size;">
  <img src="/assets/table_001.png" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />
  <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0"><b>Table 1: Comparison of results on ILSVRC-2010 test set. In italics are best results achieved by others.</b></p>
</div>

- Our CNN achieves a top-1 error of 37.5% and top-5 error of 17.0% on the ILSVRC-2010 test set.
- This outperforms the previous best SIFT + FVs approach by 8.7 percentage points in top-5 error.
- We also surpass sparse coding models, which recorded 47.1% top-1 and 28.2% top-5 errors.
- These results represent a significant improvement over all previously reported state-of-the-art methods.
- The deep convolutional architecture effectively handles the 1.2 million high-resolution images in the dataset.
---

<h1 style="color: #e2b96f;">2. Deep Convolutional Network Architecture</h1>

<div style="width: 70%; margin: auto; display: flex; gap: 1rem;">
  <div style="flex: 1; container-type: inline-size;">
    <img src="/assets/img_01.png" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />
    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>Two-GPU CNN architecture with specific layer distribution and neuron counts.</b></p>
  </div>
  <div style="flex: 1; container-type: inline-size;">
    <img src="/assets/img_02.png" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />
    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>96 11×11×3 kernels from the first layer, split across two GPUs.</b></p>
  </div>
</div>

- The network contains eight learned layers: five convolutional and three fully-connected.
- A 1000-way softmax at the output produces a distribution over class labels.
- We spread the network across two GPUs to handle memory constraints of 3GB devices.
- Training on two GPUs reduces top-1 and top-5 error rates compared to single-GPU nets.
- The network size is limited mainly by available GPU memory and training time tolerance.
---

<h1 style="color: #e2b96f;">2.1 ReLU Nonlinearity and GPU Parallelization</h1>

ReLUs ($f(x) = \max(0, x)$) train several times faster than saturating neurons like $\tanh$ or sigmoid.
Figure 1 shows ReLU networks reach 25% training error six times faster than equivalent $\tanh$ networks.
Saturating nonlinearities suffer from slow gradient descent, whereas ReLUs avoid saturation and accelerate learning.
This speedup was essential for experimenting with the large-scale networks required for ImageNet.
---

<div style="
    --image-width: 40%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">2.2 Local Response Normalization and Pooling</h1>
  </div>

  <!-- Two columns -->
  <div style="display: grid;
              grid-template-columns: var(--image-width) 1fr;
              align-items: start;
              gap: 2.5rem;
              flex: 1; min-height: 0;">
    <!-- Left: image -->
    <div style="container-type: inline-size;">
      <img src="/assets/slide_6_q1_serper_1.png" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />
      <p style="text-align:center; line-height: 1.2; margin: 0.1rem 0 0 0; font-size: 2.5cqw;"><b>Diagram illustrating lateral inhibition and competition between neuron outputs in convolutional neural networks</b></p>
    </div>
    <!-- Right: text -->
    <div style="overflow: auto;">
      <ul>
        <li>LRN implements lateral inhibition, creating competition among neuron outputs from different kernels.</li>
        <li>Hyper-parameters k=2, n=5, α=10⁻⁴, and β=0.75 were tuned on a validation set.</li>
        <li>Adding LRN reduced top-1 and top-5 error rates by 1.4% and 1.2% respectively.</li>
        <li>Overlapping pooling (s=2, z=3) reduces error rates by 0.4% and 0.3% compared to non-overlapping schemes.</li>
        <li>Models with overlapping pooling find it slightly more difficult to overfit during training.</li>
      </ul>
    </div>
  </div>
</div>
---

<div style="
    --image-width: 45%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">3. Strategies to Prevent Overfitting</h1>
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
        <li>Overfitting is a significant problem for our 60 million parameter network despite 1.2 million training images.</li>
        <li>We employ data augmentation to artificially enlarge the dataset using label-preserving transformations like translations and reflections.</li>
        <li>We alter RGB channel intensities using PCA to capture invariance to illumination changes in natural images.</li>
        <li>We utilize a regularization method called 'dropout' to reduce complex co-adaptations of neurons in fully-connected layers.</li>
        <li>Dropout forces neurons to learn robust features useful with many different random subsets of other neurons.</li>
        <li>Without these techniques, our network suffers from substantial overfitting that would force us to use smaller networks.</li>
      </ul>
    </div>
    <!-- Right: image -->
    <div style="container-type: inline-size;">
      <img src="/assets/slide_7_q1_serper_3.png" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />
      <p style="text-align:center; line-height: 1.2; margin: 0.1rem 0 0 0; font-size: 2.5cqw;"><b>Data augmentation techniques for image classification including translations reflections and color intensity PCA</b></p>
    </div>

  </div>
</div>
---

<div style="
    --image-width: 35%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">3.1 Data Augmentation Techniques</h1>
  </div>

  <!-- Two columns -->
  <div style="display: grid;
              grid-template-columns: var(--image-width) 1fr;
              align-items: start;
              gap: 2.5rem;
              flex: 1; min-height: 0;">
    <!-- Left: image -->
    <div style="container-type: inline-size;">
      <img src="/assets/slide_8_q1_serper_2.png" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />
      <p style="text-align:center; line-height: 1.2; margin: 0.1rem 0 0 0; font-size: 2.5cqw;"><b>Data augmentation pipeline showing random 224x224 image patches and horizontal reflections from larger source images</b></p>
    </div>
    <!-- Right: text -->
    <div style="overflow: auto;">
      <ul>
        <li>Generate random 224 × 224 patches and their horizontal reflections from 256 × 256 images.</li>
        <li>This translation and reflection scheme increases the training set size by a factor of 2048.</li>
        <li>Perform PCA on RGB pixel values to add multiples of principal components with Gaussian noise.</li>
        <li>This color jittering captures object identity invariance to changes in illumination intensity and color.</li>
        <li>Transformed images are generated on the CPU while the GPU trains, making augmentation computationally free.</li>
        <li>At test time, average predictions from ten patches (five crops and their reflections) for final output.</li>
      </ul>
    </div>
  </div>
</div>
---

<div style="
    --image-width: 40%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">3.2 Dropout Regularization Method</h1>
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
        <li>Dropout sets each hidden neuron's output to zero with probability 0.5 during training.</li>
        <li>Dropped neurons do not contribute to the forward pass or participate in back-propagation.</li>
        <li>Every training iteration samples a different network architecture while sharing weights across all.</li>
        <li>This technique reduces complex co-adaptations, forcing neurons to learn robust features.</li>
        <li>At test time, all neurons are used but their outputs are multiplied by 0.5.</li>
        <li>We apply dropout in the first two fully-connected layers to combat overfitting.</li>
      </ul>
    </div>
    <!-- Right: image -->
    <div style="container-type: inline-size;">
      <img src="/assets/slide_9_q1_serper_3.png" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />
      <p style="text-align:center; line-height: 1.2; margin: 0.1rem 0 0 0; font-size: 2.5cqw;"><b>Neural network diagram showing dropout mechanism with neurons deactivated during training</b></p>
    </div>

  </div>
</div>
---

<div style="
    --image-width: 30%;
    display: flex; flex-direction: column; height: 100%;">

  <!-- Title -->
  <div>
    <h1 style="color: #e2b96f;">4. Experimental Results and Analysis</h1>
  </div>

  <div style="display: grid;
              grid-template-columns: var(--image-width) 1fr;
              align-items: start;
              gap: 1rem;
              flex: 1; min-height: 0;">
    <!-- Left: images -->
    <div style="container-type: inline-size;">
      <div>
        <img src="/assets/img_00.png" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />
        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0; "><b>ReLU networks train six times faster than tanh networks on CIFAR-10 without regularization.</b></p>
      </div>
      <div>
        <img src="/assets/img_03.png" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />
        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0; "><b>Left: Top-5 model predictions with correct label probabilities. Right: Nearest training images for test samples.</b></p>
      </div>
    </div>
    <!-- Right: text -->
    <div style="overflow: auto; font-size: 1rem">
      <ul>
        <li>Achieved top-1 and top-5 error rates of 37.5% and 17.0% on the ILSVRC-2010 test set.</li>
        <li>Outperformed previous state-of-the-art methods by a significant margin on the dataset.</li>
        <li>Won the ILSVRC-2012 competition with a winning top-5 test error rate of 15.3%.</li>
        <li>Qualitative analysis shows the network recognizes off-center objects and plausible label sets.</li>
        <li>Feature similarity at the hidden layer reveals semantic connections despite pixel-level differences.</li>
        <li>Removing any single convolutional layer results in inferior performance, proving depth is critical.</li>
      </ul>
    </div>
  </div>
</div>
---

<h1 style="color: #e2b96f;">4.1 Performance Comparison with State-of-the-Art</h1>

<div style="width: 40%; margin: auto; container-type: inline-size;">
  <img src="/assets/table_002.png" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />
  <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0"><b>Table 1: Comparison of results on ILSVRC-2010 test set. In italics are best results achieved by others.</b></p>
</div>

- Sparse coding models previously achieved 47.1% top-1 and 28.2% top-5 error rates.
- SIFT + FVs approaches reached 45.7% top-1 and 25.7% top-5 error rates.
- Our CNN achieves a new state-of-the-art with 37.5% top-1 and 17.0% top-5 errors.
- This represents a significant improvement over the best previously published results on ILSVRC-2010.
- The results demonstrate the superior performance of deep convolutional networks on large-scale datasets.
---

<h1 style="color: #e2b96f;">4.2 Qualitative Evaluation of Learned Features</h1>

<div style="width: 45%; margin: auto; container-type: inline-size;">
  <img src="/assets/slide_12_q1_serper_3.png" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />
  <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0"><b>Neural network feature visualization showing diverse frequency orientation selective kernels and colored blobs</b></p>
</div>

- Network learned diverse frequency- and orientation-selective kernels plus colored blobs.
- Two GPUs exhibited specialization: GPU 1 kernels are color-agnostic, GPU 2 kernels are color-specific.
- Even off-center objects, like the mite in the top-left, can be successfully recognized.
- Top-5 labels appear reasonable, such as considering only other cat types plausible for a leopard.
- Feature similarity is measured by Euclidean distance in the 4096-dimensional hidden layer.
- Retrieved training images vary in pose and appearance, yet share high-level semantic similarity.
---
layout: cover
---

# Thank you for listening!


