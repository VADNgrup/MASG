---
layout: Standard
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
      Khái niệm về góc lượng giác và các đơn vị đo như độ và radian.
    </p>
  </div>
  <div class="col-span-7 relative h-full rounded-[3rem] overflow-hidden group ml-4">
     <img
       src="https://via.placeholder.com/800x600"
       class="absolute inset-0 w-full h-full object-cover transition-transform duration-[1.5s] ease-in-out group-hover:scale-110"
       alt="Hình ảnh minh họa góc lượng giác và đơn vị đo"
     />
     <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/40 to-transparent opacity-80"></div>
  </div>
</div>

---
layout: Standard
class: p-0 bg-[#0a0a0a] text-gray-100 font-sans overflow-hidden
---

<div class="grid grid-cols-12 h-full w-full p-12 gap-8">
  <div class="col-span-12 h-1/4">
    <div class="flex items-center gap-3 mb-2" v-motion-slide-left>
      <div class="h-1 w-12 bg-gradient-to-r from-blue-500 to-purple-500"></div>
      <span class="text-xs uppercase tracking-widest text-blue-400 font-semibold">Giá trị lượng giác</span>
    </div>
    <h2 class="text-5xl font-black italic">Giá trị <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">Lượng Giác</span></h2>
  </div>

  <div class="col-span-6 p-8 bg-white/5 border border-white/10 rounded-[2rem] backdrop-blur-sm hover:border-blue-500/50 transition-all group">
    <div class="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
      <carbon:data-base class="text-2xl text-blue-400" />
    </div>
    <h3 class="text-xl font-bold mb-3">Đường tròn lượng giác</h3>
    <p class="text-sm text-gray-400 leading-relaxed">Đường tròn lượng giác có tâm tại gốc tọa độ, bán kính 1. Điểm M(x;y) biểu diễn góc, cosÂ = x, sinÂ = y.</p>
  </div>

  <div class="col-span-6 p-8 bg-white/5 border border-white/10 rounded-[2rem] backdrop-blur-sm hover:border-purple-500/50 transition-all group">
    <div class="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
      <carbon:ibm-watson-discovery class="text-2xl text-purple-400" />
    </div>
    <h3 class="text-xl font-bold mb-3">Giá trị lượng giác</h3>
    <p class="text-sm text-gray-400 leading-relaxed">tanÂ = sinÂ/cosÂ khi cosÂ ≠ 0, cotÂ = cosÂ/sinÂ khi sinÂ ≠ 0. Trục tung là trục sin, trục hoành là trục côsin.</p>
  </div>
</div>

---
layout: Standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full">
  <div class="col-span-6 relative overflow-hidden p-8">
     <div class="w-full h-full rounded-[2.5rem] overflow-hidden relative border border-white/10">
        <img src="https://via.placeholder.com/800x600" class="object-cover w-full h-full scale-105" />
        <div class="absolute inset-0 bg-blue-900/20 mix-blend-overlay"></div>
        <div class="absolute inset-0 bg-gradient-to-tr from-[#0a0a0a] via-transparent to-transparent"></div>
      </div>
   </div>

  <div class="col-span-6 flex flex-col justify-center px-12">
    <h2 class="text-4xl font-bold mb-8 leading-tight">Dấu của <br/><span class="text-blue-400 underline decoration-2 underline-offset-8">Giá Trị Lượng Giác</span></h2>
    <div class="space-y-6">
      <div class="flex gap-4 items-start" v-motion-slide-right>
        <div class="text-2xl font-black text-gray-700">01</div>
        <div>
          <h4 class="font-bold text-xl text-white">Dấu phụ thuộc vào vị trí</h4>
          <p class="text-gray-400 text-sm">Dấu phụ thuộc vào vị trí điểm M trên đường tròn.</p>
        </div>
      </div>
      <div class="flex gap-4 items-start" v-motion-slide-right>
        <div class="text-2xl font-black text-gray-700">02</div>
        <div>
          <h4 class="font-bold text-xl text-white">Trục sin và côsin</h4>
          <p class="text-gray-400 text-sm">Trục tung là trục sin, trục hoành là trục côsin.</p>
        </div>
      </div>
    </div>
  </div>
</div>

---
layout: Standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="h-full w-full p-16 flex flex-col justify-center">
  <div class="text-center mb-12">
    <h2 class="text-4xl font-black mb-4">Giá trị lượng giác của <span class="text-emerald-400">các cung đặc biệt</span></h2>
    <p class="text-gray-500 uppercase tracking-[0.3em] text-xs">Khám phá các giá trị đặc biệt</p>
  </div>

  <div class="grid grid-cols-1 gap-12">
    <div class="p-8 rounded-[2rem] bg-white/5 border border-red-500/20 relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <carbon:warning-alt class="text-8xl text-red-500" />
      </div>
      <h3 class="text-xl font-bold text-red-400 mb-6 flex items-center gap-2">
        <carbon:close-filled /> Giá trị lượng giác
      </h3>
      <table class="w-full text-sm text-left text-gray-400">
        <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
          <tr>
            <th scope="col" class="px-6 py-3">Góc</th>
            <th scope="col" class="px-6 py-3">sin a</th>
            <th scope="col" class="px-6 py-3">tan a</th>
            <th scope="col" class="px-6 py-3">cot a</th>
          </tr>
        </thead>
        <tbody>
          <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
            <td class="px-6 py-4">0</td>
            <td class="px-6 py-4">0</td>
            <td class="px-6 py-4">0</td>
            <td class="px-6 py-4">Không xác định</td>
          </tr>
          <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
            <td class="px-6 py-4">30°</td>
            <td class="px-6 py-4">1/2</td>
            <td class="px-6 py-4">√3/3</td>
            <td class="px-6 py-4">√3</td>
          </tr>
          <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
            <td class="px-6 py-4">45°</td>
            <td class="px-6 py-4">√2/2</td>
            <td class="px-6 py-4">1</td>
            <td class="px-6 py-4">1</td>
          </tr>
          <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
            <td class="px-6 py-4">60°</td>
            <td class="px-6 py-4">√3/2</td>
            <td class="px-6 py-4">√3</td>
            <td class="px-6 py-4">√3/3</td>
          </tr>
          <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
            <td class="px-6 py-4">90°</td>
            <td class="px-6 py-4">1</td>
            <td class="px-6 py-4">Không xác định</td>
            <td class="px-6 py-4">0</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

---
layout: Standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full gap-0">
  <div class="col-span-5 p-16 bg-[#0f0f0f] border-r border-white/5 flex flex-col justify-center">
    <div class="flex items-center gap-2 mb-6">
      <carbon:data-blob class="text-blue-400 animate-pulse" />
      <span class="text-xs font-mono text-blue-300 uppercase tracking-widest">Quan hệ lượng giác</span>
    </div>
    <h2 class="text-4xl font-black mb-6">Quan hệ giữa <br/><span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Giá Trị Lượng Giác</span></h2>
    <p class="text-gray-400 leading-relaxed mb-8">
      Công thức lượng giác cơ bản:
    </p>
    <ul class="list-disc pl-6 text-gray-400">
      <li>sin² x + cos² x = 1</li>
      <li>1/cos² x = 1 + tan² x</li>
      <li>1/sin² x = 1 + cot² x</li>
      <li>tan x.cot x = 1</li>
    </ul>
  </div>

  <div class="col-span-7 p-12 bg-black flex items-center justify-center relative">
    <img src="https://via.placeholder.com/800x600" class="object-cover w-full h-full scale-105" />
  </div>
</div>

---
layout: Standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full">
  <div class="col-span-12 p-16 pb-4">
    <h2 class="text-5xl font-black">Giá trị lượng giác của <span class="italic text-gray-500">góc đặc biệt.</span></h2>
  </div>
  
  <div class="col-span-12 px-16 grid grid-cols-3 gap-8">
    <div class="group cursor-pointer">
      <div class="aspect-video bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl mb-4 border border-white/10 overflow-hidden relative shadow-lg group-hover:border-blue-500/50 transition-all">
         <div class="absolute inset-0 flex items-center justify-center opacity-20 group-hover:scale-110 transition-transform">
           <carbon:template class="text-6xl" />
         </div>
      </div>
      <h4 class="font-bold text-lg">Cung đối nhau</h4>
      <p class="text-sm text-gray-500 leading-snug">Cung đối nhau: $\\alpha$ và $-\\alpha$</p>
      <p class="text-sm text-gray-500 leading-snug">$\\cos(-\\alpha) = \\cos \\alpha$, $\\sin(-\\alpha) = -\\sin \\alpha$</p>
    </div>
    <div class="group cursor-pointer">
      <div class="aspect-video bg-gradient-to-br from-indigo-900 to-purple-900 rounded-2xl mb-4 border border-white/10 overflow-hidden relative shadow-lg group-hover:border-purple-500/50 transition-all">
         <div class="absolute inset-0 flex items-center justify-center opacity-20 group-hover:scale-110 transition-transform">
           <carbon:color-palette class="text-6xl" />
         </div>
      </div>
      <h4 class="font-bold text-lg">Cung bù nhau</h4>
      <p class="text-sm text-gray-500 leading-snug">Cung bù nhau: $\\alpha$ và $\\pi - \\alpha$</p>
      <p class="text-sm text-gray-500 leading-snug">$\\cos(\\pi - \\alpha) = -\\cos \\alpha$, $\\sin(\\pi - \\alpha) = \\sin \\alpha$</p>
    </div>
    <div class="group cursor-pointer">
      <div class="aspect-video bg-gradient-to-br from-emerald-900 to-teal-900 rounded-2xl mb-4 border border-white/10 overflow-hidden relative shadow-lg group-hover:border-emerald-500/50 transition-all">
         <div class="absolute inset-0 flex items-center justify-center opacity-20 group-hover:scale-110 transition-transform">
           <carbon:presentation-file class="text-6xl" />
         </div>
      </div>
      <h4 class="font-bold text-lg">Cung phụ nhau</h4>
      <p class="text-sm text-gray-500 leading-snug">Cung phụ nhau: $\\alpha$ và $\\frac{\\pi}{2} - \\alpha$</p>
    </div>
  </div>
</div>