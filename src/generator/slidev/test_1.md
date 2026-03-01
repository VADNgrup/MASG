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

- 1. Introduction and Motivation
- 1.1. The Challenge of Object Recognition in Real-World Settings
- 1.2. The Need for Large-Scale Datasets and Powerful Models
- 1.3. Overview of Convolutional Neural Networks (CNNs) in Vision Tasks
- 2. Dataset and Data Preparation
- 2.1. Overview of ImageNet and ILSVRC
- 2.2. Handling Variable Image Resolutions and Preprocessing
- 2.3. Data Augmentation Techniques
- 2.3.1. Image Translations and Reflections
- 2.3.2. Color and Intensity Variations
- 3. Architecture and Key Innovations
- 3.1. Overall Network Structure and Layer Composition
- 3.2. Use of ReLU Nonlinearities for Faster Training
- 3.3. Multi-GPU Training and Connectivity Patterns
- 3.4. Response Normalization and Overlapping Pooling Layers
- 4. Techniques for Reducing Overfitting
- 4.1. Data Augmentation Strategies
- 4.2. Dropout Regularization in Fully-Connected Layers
- 4.3. Impact of Regularization Methods on Performance
- 5. Results, Analysis, and Qualitative Insights
- 5.1. Performance on ILSVRC-2010 and 2012
- 5.2. Effect of Model Depth and Architectural Choices
- 5.3. Visualization of Learned Kernels and Feature Activations
- 5.4. Qualitative Evaluation of Predictions and Similarity Measures
---
layout: split
---

::title::
# 1. Introduction and Motivation
::left::
- We trained a huge, deep CNN on 1.2 million high-res ImageNet images (1000 classes).
- Achieved top-1 error $37.5\%$, top-5 error $17.0\%$—a massive leap over previous methods.
- Network: 60 million parameters, 650,000 neurons, 5 conv layers + 3 fully-connected layers, 1000-way softmax.
- Used non-saturating neurons and fast GPU convolution for practical training.
- Dropout regularization in fully-connected layers slashed overfitting and boosted performance.
::right::
<img src="/assets/slide_1_slide_1_serper_2.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---

# 1.1. The Challenge of Large-Scale Object Recognition
- Training large CNNs on massive datasets like ImageNet is now feasible thanks to optimized GPU implementations and techniques like dropout.
- Key innovations include ReLU nonlinearities for faster training, overlapping pooling to reduce overfitting, and local response normalization for better generalization.
- Despite the complexity, deeper networks with more convolutional layers significantly improve recognition performance, emphasizing the importance of depth.
- Effective data augmentation—such as translation, reflection, and PCA-based color jittering—helps combat overfitting on massive models.
- Our large-scale CNN achieved record top-1 and top-5 error rates on ImageNet, demonstrating the power of deep learning in large-scale object recognition.
---

# 1.2. Limitations of Small Datasets and the Need for Larger Data
- Small datasets limit model capacity and lead to overfitting, especially for large CNNs.
- Larger datasets like ImageNet enable training deep models without severe overfitting.
- Previously, datasets had only tens of thousands of images; now we have over 15 million labeled images.
- Training on massive datasets requires models with high capacity and strong regularization techniques.
- The move to big data is essential to unlock the full potential of deep convolutional neural networks.
---

# 1.3. The Role of Deep Learning and Convolutional Neural Networks
- Deep CNNs trained on massive datasets like ImageNet achieve record-breaking results.
- Using ReLUs accelerates training times, enabling larger, deeper models to learn faster.
- Multi-GPU training with optimized convolution implementations makes large-scale learning feasible.
- Techniques like local response normalization, overlapping pooling, and dropout help prevent overfitting.
- Depth and capacity of CNNs are crucial; removing layers degrades performance, emphasizing the importance of architecture.
---

# 2. Dataset and Data Handling Techniques
- Our large CNN achieved top-1 error of $37.5\%$ and top-5 of $17.0\%$ on ImageNet-2010.
- Deeper networks are essential; removing any convolutional layer drops performance.
- Key innovations include ReLU nonlinearities, multi-GPU training, local response normalization, and overlapping pooling.
- Dropout and data augmentation techniques significantly reduce overfitting despite 60 million parameters.
- Results demonstrate that massive, deep CNNs trained with these techniques push the boundaries of large-scale visual recognition.
---
layout: split
---

::title::
# 2.1. Overview of ImageNet and Its Subsets
::left::
- ImageNet is a massive dataset with over 15 million labeled high-res images across 22,000 categories.
- The ILSVRC subset contains roughly 1.2 million training images in 1000 classes, used for large-scale recognition.
- Training on such large datasets requires models with high capacity, like deep CNNs, which leverage prior image assumptions.
- Our network architecture includes innovative features like ReLU nonlinearities, multi-GPU training, and overlapping pooling.
- These techniques enable training large, deep models efficiently, achieving record-breaking results on ImageNet challenges.
::right::
<img src="/assets/slide_6_slide_6_serper_3.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split
---

::title::
# 2.2. Image Preprocessing and Data Augmentation
::left::
- Image preprocessing includes resizing images to 256×256 by rescaling and cropping, then subtracting the training set mean.
- Data augmentation boosts training diversity via random translations, horizontal reflections, and PCA-based color jittering, reducing overfitting.
- Using ReLU nonlinearities accelerates training significantly—networks with ReLUs learn several times faster than those with tanh units.
- Overlapping pooling (z=3, s=2) improves accuracy by reducing overfitting and capturing more spatial information than non-overlapping pooling.
- Combining these techniques—resizing, augmentation, ReLUs, and overlapping pooling—enhances model performance and training efficiency.
::right::
<img src="/assets/slide_7_slide_7_serper_1.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---

# 2.2.1. Resizing and Cropping to Fixed Resolution
- Resizing images to fixed resolution is crucial for CNN input consistency.
- We down-sampled images to 256×256: resize shortest side to 256, then center crop.
- Cropping central 256×256 patch ensures uniform input size for training.
- Data augmentation includes random translations, horizontal reflections, and PCA-based color jittering.
- These techniques effectively increase dataset variability, reducing overfitting and improving generalization.
---

# 2.2.2. Horizontal Flips and Translations
- Horizontal and translation invariances are key for CNN robustness.
- Data augmentation with random crops, reflections, and PCA jittering improves generalization.
- Overlapping pooling (s<z) reduces overfitting and enhances model performance.
- Using ReLU nonlinearities accelerates training speed significantly compared to tanh units.
- Multi-GPU training enables larger networks by splitting kernels and managing communication efficiently.
---

# 2.2.3. Intensity and Color Variations
- Intensity and color variations are crucial for robust recognition in large datasets.
- Techniques like PCA-based intensity jittering help the model handle lighting changes.
- Color-specific kernels emerge on different GPUs, showing learned specialization and invariance.
- Overlapping pooling (s=2, z=3) enhances performance by capturing more spatial context.
---

# 2.3. Training Data Organization and Validation
- Training large CNNs on ImageNet requires careful data organization and validation.
- We used extensive data augmentation: translations, flips, and PCA-based color jittering to reduce overfitting.
- Our dataset included 1.2 million images, with fixed 256×256 resolution after rescaling and center cropping.
- Validation involved extracting multiple patches and averaging predictions, enhancing robustness.
- Model performance depends heavily on proper data handling, normalization, and validation strategies.
---
layout: split
---

::title::
# 3. Architecture and Model Design
::left::
- Our architecture features eight learned layers: five convolutional and three fully-connected, with a softmax output for 1000 classes.
- Key innovations include ReLU nonlinearities, multi-GPU training, local response normalization, and overlapping pooling to boost performance.
- ReLUs ($f(x) = \max(0, x)$) accelerate training times, enabling large, deep CNNs to learn efficiently on massive datasets.
- Using two GPUs with a communication scheme reduces overfitting and speeds up training, handling models too big for a single GPU.
::right::
<img src="/assets/slide_12_slide_12_serper_1.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split
---

::title::
# 3.1. Overall Network Structure
::left::
- Overall network structure features five convolutional and three fully-connected layers, ending with a 1000-way softmax.
- The architecture includes innovations like ReLU nonlinearities, overlapping pooling, local response normalization, and multi-GPU training for efficiency.
- The convolutional layers process raw RGB inputs with specific kernel sizes and strides, while the fully-connected layers integrate learned features for classification.
- Design choices like dropout and data augmentation are crucial to combat overfitting in this large, deep model.
::right::
<img src="/assets/slide_13_slide_13_serper_2.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---

# 3.2. Key Architectural Features
- Key architectural features include ReLU nonlinearities for faster training,
- multi-GPU training to handle large models beyond single GPU memory limits,
- local response normalization inspired by biological neurons to improve generalization,
- overlapping pooling with s<z to reduce overfitting and improve performance,
- and a carefully designed overall architecture with convolutional and fully-connected layers.
---

# 3.2.1. Use of ReLU Nonlinearities
- ReLU nonlinearities ($f(x) = \max(0, x)$) enable much faster training than saturating functions like tanh.
- Using ReLUs, deep CNNs train several times faster, crucial for large models on big datasets.
- In our architecture, ReLUs are applied after every convolutional and fully-connected layer to boost learning speed.
- This choice allows training large, deep networks efficiently, making the most of GPU acceleration and large datasets.
- ReLU's non-saturating nature is key to optimizing training time and achieving state-of-the-art results.
---
layout: split
---

::title::
# 3.2.2. Local Response Normalization
::left::
- Local Response Normalization creates competition among neuron outputs, inspired by real neurons.
- It helps improve generalization by normalizing responses across kernel maps at each spatial position.
- The normalized activity $b_{x,y}^i$ is computed as: $$b_{x,y}^i = a_{x,y}^i / \left( k + \alpha \sum_{j=\max(0,i - n/2)}^{\min(N-1,i + n/2)} (a_{x,y}^j)^2 \right)^{\beta}$$
- Constants $k, n, \alpha$, and $\beta$ are hyperparameters tuned via validation, with typical values $k=2$, $n=5$, $\alpha=10^{-4}$, and $\beta=0.75$.
- Response normalization acts like lateral inhibition, encouraging competition among neighboring kernels to boost generalization.
::right::
<img src="/assets/slide_16_slide_16_serper_1.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split
---

::title::
# 3.2.3. Overlapping Pooling
::left::
- Overlapping pooling uses a stride $s=2$ and window size $z=3$, creating overlaps.
- This approach reduces top-1 and top-5 error rates by about 0.4% and 0.3%, respectively.
- Overlapping pooling makes models slightly more resistant to overfitting compared to non-overlapping schemes.
- It enhances the network's ability to summarize features and improves generalization during training.
::right::
<img src="/assets/slide_17_slide_17_serper_2.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---
layout: split
---

::title::
# 3.3. Multi-GPU Training Strategy
::left::
- In multi-GPU training, the network is split across GPUs with selective communication, reducing overhead.
- GPUs communicate only at certain layers, enabling efficient parallelization of large CNNs.
- This approach allows training networks too big for a single GPU, leveraging direct GPU-to-GPU memory access.
- Layer connectivity is carefully tuned to balance computation and communication, boosting performance.
::right::
<img src="/assets/slide_18_slide_18_serper_2.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---

# 3.3.1. Parallelization Scheme
- Parallelization across two GPUs employs a columnar scheme, reducing communication overhead.
- Kernels are distributed so that some layers communicate only within the same GPU, others across GPUs.
- This setup enables training larger networks that don't fit on a single GPU, boosting performance.
- Choosing the connectivity pattern is fine-tuned via cross-validation to balance computation and communication.
- Result: a significant reduction in error rates and faster training times compared to single-GPU setups.
---

# 3.3.2. Connectivity and Communication
- Connectivity across GPUs enables training larger CNNs beyond single GPU memory limits.
- Layer-specific communication patterns balance computation and inter-GPU data transfer.
- Local response normalization introduces competition among kernel responses, aiding generalization.
- Overlapping pooling with stride less than filter size improves accuracy and reduces overfitting.
- These architectural choices build on prior design principles to enhance large-scale CNN performance.
---
layout: split
---

::title::
# 4. Regularization and Overfitting Prevention
::left::
- Effective regularization methods like dropout are crucial for large CNNs to prevent overfitting, especially with millions of parameters.
- Dropout randomly sets neuron outputs to zero during training, forcing the network to learn more robust features and reducing co-adaptation.
- In our approach, dropout is applied to the first two fully-connected layers, roughly doubling training time but significantly improving generalization.
- Combined with data augmentation techniques—such as translation, reflection, and color perturbation—dropout helps achieve state-of-the-art results.
- These regularization strategies are vital for training deep, high-capacity models on massive datasets like ImageNet.
::right::
<img src="/assets/slide_21_slide_21_serper_3.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption
---

# 4.1. Data Augmentation Strategies
- Data augmentation boosts training diversity by label-preserving transformations.
- Methods include random translations, reflections, and PCA-based intensity shifts.
- Augmentation increases effective dataset size, reducing overfitting on large models.
- It enables training on massive datasets like ImageNet without severe overfitting.
- Combining augmentation with dropout and normalization techniques enhances generalization.
---

# 4.2. Dropout Technique and Its Application
- Dropout is a powerful regularization technique that reduces overfitting by randomly dropping neurons during training.
- It forces neurons to learn more robust features, improving generalization on large datasets like ImageNet.
- During training, each hidden neuron is set to zero with probability 0.5, preventing co-adaptation of neurons.
- At test time, all neurons are used with outputs scaled by 0.5 to approximate model averaging, boosting accuracy.
- In our CNN, applying dropout in the first two fully-connected layers significantly lowered overfitting.
---

# 4.3. Impact on Training and Generalization
- Impact on Training & Generalization: Larger CNNs need robust regularization.
- Techniques like data augmentation and dropout significantly improve performance.
- Using ReLUs accelerates training, making large models feasible with GPUs.
- Overlapping pooling and local response normalization further boost accuracy.
- Depth is crucial; removing layers degrades results, highlighting the importance of architecture.
---

# 5. Results, Analysis, and Qualitative Insights
- Our large CNN achieved top-1 error of $37.5\%$ and top-5 of $17.0\%$ on ImageNet-2010.
- Overfitting was tackled with data augmentation and dropout, boosting generalization.
- Data augmentation included random translations, reflections, and PCA-based color jittering.
- Dropout in fully-connected layers prevented co-adaptation, improving robustness during training.
- These regularization techniques are essential for training massive models on large datasets.
---

# 5.1. Performance on ImageNet Challenges
- Deep CNNs trained on ImageNet achieved top-1 error of $37.5\%$ and top-5 error of $17.0\%$, beating previous state-of-the-art.
- Using ReLUs accelerates training times by several times compared to saturating neurons like tanh, enabling larger models.
- Multi-GPU training with communication only at certain layers allows training larger networks beyond single GPU memory limits.
- Overlapping pooling (with stride $s=2$, window $z=3$) reduces overfitting and improves accuracy over non-overlapping pooling.
- Regularization techniques like data augmentation and dropout are crucial to prevent overfitting in models with 60 million parameters.
---

# 5.2. Effect of Model Depth and Architecture
- Deeper CNNs with increased architecture complexity significantly improve ImageNet performance.
- Key architectural choices—like ReLU nonlinearities, overlapping pooling, and local response normalization—accelerate training and boost accuracy.
- Using multiple GPUs with restricted connectivity reduces overfitting and enhances learning capacity.
- Depth is crucial: removing any convolutional layer degrades top-1 performance by about 2%.
- Our large, deep CNN achieved record-breaking results, demonstrating the power of architecture and training innovations.
---
layout: split
---

::title::
# 5.3. Visualization of Learned Features and Predictions
::left::
- Visualization of learned features reveals frequency-, orientation-, and color-selective kernels, showing specialization between GPUs.
- Qualitative analysis includes top-5 predictions on test images, demonstrating the network's recognition capabilities even on off-center objects.
- Feature activation similarity via Euclidean distance in the 4096-dimensional space helps identify semantically related images, aiding interpretability.
- Understanding learned features builds confidence in the model's internal representations, complementing quantitative performance metrics.
::right::
<img src="/assets/slide_28_img_03.png" class="max-h-60 mx-auto"/>
::right-caption::
Image caption

---
 layout: center
class: text-center
---

# Thank You!
----
