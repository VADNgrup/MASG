---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100 font-sans overflow-hidden
transition: slide-left
---

<div class="grid grid-cols-12 h-full w-full gap-4 p-4">
  <div class="col-span-5 flex flex-col justify-center pl-8 pr-4 z-10">
    <div class="flex items-center gap-2 mb-6" v-motion-slide-top>
      <span class="h-px w-8 bg-purple-400"></span>
      <span class="text-xs font-mono uppercase tracking-[0.2em] text-purple-300">Góc Lượng Giác</span>
    </div>
    <h1 class="text-6xl font-black leading-tight mb-6">
      Góc Lượng Giác <br/>
      <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-pink-400 filter drop-shadow-lg">
        và Đơn Vị Đo
      </span>
    </h1>
    <p class="text-lg text-gray-300/90 leading-relaxed mb-10 pr-10 font-light">
      Khái niệm góc lượng giác: Quay tia Om từ Ou đến Ov. Hệ thức Chasles: sd(Ou, Ov) + sd(Ov, Ow) = sd(Ou, Ow) + k.360. Đơn vị độ: 1° = π/180 rad. Đơn vị radian: Cung tròn dài bằng bán kính R là 1 radian. Quan hệ độ và radian: 1° = π/180 rad, 1 rad = 180/π°.
    </p>
  </div>
  <div class="col-span-7 relative h-full rounded-[3rem] overflow-hidden group ml-4">
     <img
       src="https://cdn.coin68.com/images/20241126051129-43eb116f-bb75-4a90-8b3b-026af7cdadfb-83.jpg"
       class="absolute inset-0 w-full h-full object-cover transition-transform duration-[1.5s] ease-in-out group-hover:scale-110"
       alt="Góc Lượng Giác"
     />
     <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/40 to-transparent opacity-80"></div>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full p-12 gap-8">
  <div class="col-span-6 flex flex-col justify-center">
    <h2 class="text-4xl font-bold mb-8 leading-tight">Giá trị lượng giác của <br/><span class="text-blue-400 underline decoration-2 underline-offset-8">góc lượng giác</span></h2>
    <p class="text-lg text-gray-300/90 leading-relaxed mb-10">
      Đường tròn lượng giác có tâm tại gốc tọa độ, bán kính 1. Điểm M(x;y) biểu diễn góc, cosÂ = x, sinÂ = y. tanÂ = sinÂ/cosÂ khi cosÂ ≠ 0, cotÂ = cosÂ/sinÂ khi sinÂ ≠ 0. Trục tung là trục sin, trục hoành là trục côsin.
    </p>
  </div>
  <div class="col-span-6">
    | Bảng xác định dấu của các giá trị lượng giác | Góc II | Góc III | Góc IV |
    | -------------------------------------------- | ------ | ------- | ------ |
    | sin x                                        |        |         |        |
    | cos x                                        | +      | +       | -      |
    | tan x                                        | +      | -       | -      |
    | cot x                                        | -      | -       | +      |
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full p-12 gap-8">
  <div class="col-span-6 flex flex-col justify-center">
    <h2 class="text-4xl font-bold mb-8 leading-tight">Dấu của <br/><span class="text-blue-400 underline decoration-2 underline-offset-8">Giá Trị Lượng Giác</span></h2>
    <p class="text-lg text-gray-300/90 leading-relaxed mb-10">
      Dấu phụ thuộc vào vị trí điểm M trên đường tròn. Trục tung là trục sin, trục hoành là trục côsin.
    </p>
  </div>
  <div class="col-span-6">
    | Bảng xác định dấu của các giá trị lượng giác | Góc II | Góc III | Góc IV |
    | -------------------------------------------- | ------ | ------- | ------ |
    | sin x                                        |        |         |        |
    | cos x                                        | +      | +       | -      |
    | tan x                                        | +      | -       | -      |
    | cot x                                        | -      | -       | +      |
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full p-12">
  <div class="col-span-12">
    <h2 class="text-4xl font-bold mb-8 leading-tight">Giá trị lượng giác của <br/><span class="text-blue-400 underline decoration-2 underline-offset-8">các cung đặc biệt</span></h2>
    <div class="overflow-x-auto">
      |     | sin a | tan a          | cot a          |
      | --- | ----- | -------------- | -------------- |
      | 0   | 0     | 0              | Không xác định |
      | 30° | 1/2   | √3/3           | √3             |
      | 45° | √2/2  | 1              | 1              |
      | 60° | √3/2  | √3             | √3/3           |
      | 90° | 1     | Không xác định | 0              |
    </div>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full p-12 gap-8">
  <div class="col-span-12">
    <h2 class="text-4xl font-bold mb-8 leading-tight">Quan hệ giữa <br/><span class="text-blue-400 underline decoration-2 underline-offset-8">các giá trị lượng giác</span></h2>
    <p class="text-lg text-gray-300/90 leading-relaxed mb-10">
      Công thức lượng giác cơ bản:
    </p>
    <ul class="list-disc pl-8 text-gray-300/90">
      <li>sin² x + cos² x = 1</li>
      <li>1/cos² x = 1 + tan² x</li>
      <li>1/sin² x = 1 + cot² x</li>
      <li>tan x.cot x = 1</li>
    </ul>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full p-12 gap-8">
  <div class="col-span-12">
    <h2 class="text-4xl font-bold mb-8 leading-tight">Giá trị lượng giác của <br/><span class="text-blue-400 underline decoration-2 underline-offset-8">góc đặc biệt</span></h2>
    <p class="text-lg text-gray-300/90 leading-relaxed mb-10">
      Khám phá giá trị lượng giác của các góc đối, bù, và phụ nhau.
    </p>
    <ul class="list-disc pl-8 text-gray-300/90">
      <li>Cung đối nhau: $\alpha$ và $-\alpha$</li>
      <li>$\cos(-\alpha) = \cos \alpha$, $\sin(-\alpha) = -\sin \alpha$</li>
      <li>Cung bù nhau: $\alpha$ và $\pi - \alpha$</li>
      <li>$\cos(\pi - \alpha) = -\cos \alpha$, $\sin(\pi - \alpha) = \sin \alpha$</li>
      <li>Cung phụ nhau: $\alpha$ và $\frac{\pi}{2} - \alpha$</li>
    </ul>
  </div>
</div>