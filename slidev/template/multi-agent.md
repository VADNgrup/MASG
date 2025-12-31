---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100 font-sans overflow-hidden
transition: slide-left
---

<div class="grid grid-cols-12 h-full w-full gap-4 p-4">

  <div class="col-span-5 flex flex-col justify-center pl-8 pr-4 z-10">
    <div class="flex items-center gap-2 mb-6" v-motion-slide-top>
      <span class="h-px w-8 bg-purple-400"></span>
      <span class="text-xs font-mono uppercase tracking-[0.2em] text-purple-300">Future of Tech</span>
    </div>
    <h1 class="text-6xl font-black leading-tight mb-6">
      Hệ Thống <br/>
      <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-pink-400 filter drop-shadow-lg">
        Multi-Agent
      </span>
      <br/> Lecture Generator
    </h1>
    <p class="text-lg text-gray-300/90 leading-relaxed mb-10 pr-10 font-light">
      Khám phá cách các tác nhân AI phối hợp tự động để giải quyết các quy trình phức tạp, tối ưu hóa hiệu suất và giảm thiểu lỗi con người.
    </p>
    <div class="flex items-center gap-4 p-4 bg-white/5 border border-white/10 rounded-2xl w-fit backdrop-blur-md shadow-xl shadow-purple-900/10 hover:bg-white/10 transition-all" v-motion-slide-bottom>
       <div class="bg-gradient-to-br from-blue-500 to-purple-600 p-3 rounded-xl">
         <carbon:chart-line-data class="text-2xl text-white"/>
       </div>
       <div>
         <div class="font-bold text-2xl text-white">95%</div>
         <div class="text-sm text-gray-400">Độ chính xác quy trình</div>
       </div>
    </div>
  </div>
  <div class="col-span-7 relative h-full rounded-[3rem] overflow-hidden group ml-4">
     <img
       src="https://cdn.coin68.com/images/20241126051129-43eb116f-bb75-4a90-8b3b-026af7cdadfb-83.jpg"
       class="absolute inset-0 w-full h-full object-cover transition-transform duration-[1.5s] ease-in-out group-hover:scale-110"
       alt="AI Network"
     />
     <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/40 to-transparent opacity-80"></div>
     <div class="absolute bottom-10 left-10 right-10 p-6 bg-white/10 backdrop-blur-xl border border-white/20 rounded-[2rem] shadow-2xl z-20">
        <div class="flex items-start gap-5">
           <div class="bg-gradient-to-br from-pink-500 to-orange-400 p-4 rounded-2xl shadow-lg shadow-pink-500/20">
              <carbon:idea class="text-3xl text-white" />
           </div>
           <div>
              <h3 class="text-xl font-bold text-white mb-2 flex items-center gap-2">
                Core Insight
                <carbon:arrow-up-right class="text-sm opacity-50"/>
              </h3>
              <p class="text-sm text-gray-200/90 leading-snug font-light italic">
                 "Sự kết hợp giữa AI tạo sinh và kiến trúc tác nhân module là chìa khóa mở ra kỷ nguyên tự động hóa nhận thức."
              </p>
           </div>
        </div>
     </div>
  </div>
  </div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100 font-sans overflow-hidden
---

<div class="grid grid-cols-12 h-full w-full p-12 gap-8">
  <div class="col-span-12 h-1/4">
    <div class="flex items-center gap-3 mb-2" v-motion-slide-left>
      <div class="h-1 w-12 bg-gradient-to-r from-blue-500 to-purple-500"></div>
      <span class="text-xs uppercase tracking-widest text-blue-400 font-semibold">Technical Blueprint</span>
    </div>
    <h2 class="text-5xl font-black italic">Kiến Trúc <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">Pipeline</span></h2>
  </div>

  <div class="col-span-4 p-8 bg-white/5 border border-white/10 rounded-[2rem] backdrop-blur-sm hover:border-blue-500/50 transition-all group">
    <div class="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
      <carbon:data-base class="text-2xl text-blue-400" />
    </div>
    <h3 class="text-xl font-bold mb-3">01. Data Ingestion</h3>
    <p class="text-sm text-gray-400 leading-relaxed">Thu thập và trích xuất dữ liệu đa nguồn, chuyển đổi cấu trúc JSON thô thành ngữ cảnh sẵn sàng cho AI.</p>
  </div>

  <div class="col-span-4 p-8 bg-white/5 border border-white/10 rounded-[2rem] backdrop-blur-sm hover:border-purple-500/50 transition-all group">
    <div class="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
      <carbon:ibm-watson-discovery class="text-2xl text-purple-400" />
    </div>
    <h3 class="text-xl font-bold mb-3">02. RAG Engine</h3>
    <p class="text-sm text-gray-400 leading-relaxed">Truy xuất thông tin thông minh dựa trên vector database, đảm bảo nội dung phản hồi chính xác và có căn cứ.</p>
  </div>

  <div class="col-span-4 p-8 bg-white/5 border border-white/10 rounded-[2rem] backdrop-blur-sm hover:border-pink-500/50 transition-all group">
    <div class="w-12 h-12 rounded-xl bg-pink-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
      <carbon:loop class="text-2xl text-pink-400" />
    </div>
    <h3 class="text-xl font-bold mb-3">03. Agentic Loop</h3>
    <p class="text-sm text-gray-400 leading-relaxed">Hệ thống vòng lặp tự điều chỉnh giữa các tác nhân để tối ưu hóa kết quả đầu ra theo yêu cầu người dùng.</p>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full">
  <div class="col-span-6 relative overflow-hidden p-8">
     <div class="w-full h-full rounded-[2.5rem] overflow-hidden relative border border-white/10">
        <img src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop" class="object-cover w-full h-full scale-105" />
        <div class="absolute inset-0 bg-blue-900/20 mix-blend-overlay"></div>
        <div class="absolute inset-0 bg-gradient-to-tr from-[#0a0a0a] via-transparent to-transparent"></div>
        <div class="absolute top-8 left-8 p-4 bg-black/60 backdrop-blur-md rounded-2xl border border-white/20" v-motion-pop>
            <div class="flex items-center gap-3">
               <div class="h-2 w-2 rounded-full bg-green-400 animate-pulse"></div>
               <span class="text-xs font-mono uppercase tracking-tighter">System Status: Active</span>
            </div>
         </div>
      </div>
   </div>

  <div class="col-span-6 flex flex-col justify-center px-12">
    <h2 class="text-4xl font-bold mb-8 leading-tight">Vòng lặp <br/><span class="text-blue-400 underline decoration-2 underline-offset-8">Tư duy & Hành động</span></h2>
    <div class="space-y-6">
      <div class="flex gap-4 items-start" v-motion-slide-right>
        <div class="text-2xl font-black text-gray-700">01</div>
        <div>
          <h4 class="font-bold text-xl text-white">Planner</h4>
          <p class="text-gray-400 text-sm">Phân rã yêu cầu phức tạp thành các nhiệm vụ nhỏ khả thi.</p>
        </div>
      </div>
      <div class="flex gap-4 items-start" v-motion-slide-right>
        <div class="text-2xl font-black text-gray-700">02</div>
        <div>
          <h4 class="font-bold text-xl text-white">Executor</h4>
          <p class="text-gray-400 text-sm">Thực thi các tác vụ chuyên biệt bằng công cụ (Browsing, Python, SQL).</p>
        </div>
      </div>
      <div class="flex gap-4 items-start" v-motion-slide-right>
        <div class="text-2xl font-black text-gray-700">03</div>
        <div>
          <h4 class="font-bold text-xl text-white">Reviewer</h4>
          <p class="text-gray-400 text-sm">Kiểm định chất lượng và phản hồi lỗi để tối ưu lại quy trình.</p>
        </div>
      </div>
    </div>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] flex items-center justify-center
---

<div class="w-[90%] h-[80%] bg-gradient-to-br from-white/10 to-white/5 rounded-[3rem] border border-white/10 backdrop-blur-xl relative overflow-hidden p-16">
  <div class="absolute -top-24 -right-24 w-96 h-96 bg-purple-600/20 blur-[120px] rounded-full"></div>
  <div class="absolute -bottom-24 -left-24 w-96 h-96 bg-blue-600/20 blur-[120px] rounded-full"></div>

  <div class="relative z-10 grid grid-cols-2 h-full items-center">
    <div>
      <h2 class="text-5xl font-black text-white mb-6 leading-tight">Sức mạnh của <br/>Sự Hiệp Đồng.</h2>
      <p class="text-gray-400 text-lg mb-8 max-w-md">Hệ thống Multi-agent không chỉ làm việc nhanh hơn, mà còn thông minh hơn qua từng iteration.</p>
      <button class="px-8 py-3 bg-white text-black font-bold rounded-full hover:bg-blue-400 hover:text-white transition-all duration-300 transform hover:scale-105 shadow-xl shadow-white/5">
        Xem Case Study
      </button>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div class="p-6 h-32 bg-black/40 rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center">
        <span class="text-4xl font-black text-white mb-1">10x</span>
        <span class="text-xs uppercase tracking-widest text-gray-500 font-bold">Tốc độ xử lý</span>
      </div>
      <div class="p-6 h-32 bg-black/40 rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center">
        <span class="text-4xl font-black text-purple-400 mb-1">-60%</span>
        <span class="text-xs uppercase tracking-widest text-gray-500 font-bold">Chi phí vận hành</span>
      </div>
      <div class="p-6 h-32 bg-black/40 rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center">
        <span class="text-4xl font-black text-blue-400 mb-1">24/7</span>
        <span class="text-xs uppercase tracking-widest text-gray-500 font-bold">Khả năng mở rộng</span>
      </div>
      <div class="p-6 h-32 bg-black/40 rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center">
        <span class="text-4xl font-black text-pink-400 mb-1">Zero</span>
        <span class="text-xs uppercase tracking-widest text-gray-500 font-bold">Thời gian chờ</span>
      </div>
    </div>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="h-full w-full p-16 flex flex-col justify-center">
  <div class="text-center mb-12">
    <h2 class="text-4xl font-black mb-4">Từ Phức Tạp Đến <span class="text-emerald-400">Tối Ưu</span></h2>
    <p class="text-gray-500 uppercase tracking-[0.3em] text-xs">Phá vỡ giới hạn của AI truyền thống</p>
  </div>

  <div class="grid grid-cols-2 gap-12">
    <div class="p-8 rounded-[2rem] bg-white/5 border border-red-500/20 relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <carbon:warning-alt class="text-8xl text-red-500" />
      </div>
      <h3 class="text-xl font-bold text-red-400 mb-6 flex items-center gap-2">
        <carbon:close-filled /> AI Đơn Lẻ (Monolithic)
      </h3>
      <ul class="space-y-4 text-gray-400 text-sm">
        <li class="flex items-center gap-3"> <carbon:dot-mark class="text-red-500"/> Giới hạn trong một ngữ cảnh hẹp </li>
        <li class="flex items-center gap-3"> <carbon:dot-mark class="text-red-500"/> Dễ xảy ra hiện tượng "ảo giác" (Hallucination) </li>
        <li class="flex items-center gap-3"> <carbon:dot-mark class="text-red-500"/> Khó xử lý các quy trình đa bước phức tạp </li>
      </ul>
    </div>
    <div class="p-8 rounded-[2rem] bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-blue-500/30 relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <carbon:checkmark-filled class="text-8xl text-blue-500" />
      </div>
      <h3 class="text-xl font-bold text-blue-400 mb-6 flex items-center gap-2">
        <carbon:checkmark-filled /> Hệ Thống Multi-Agent
      </h3>
      <ul class="space-y-4 text-gray-100 text-sm">
        <li class="flex items-center gap-3 font-medium"> <carbon:flash class="text-yellow-400"/> Phân rã nhiệm vụ (Task Decomposition) </li>
        <li class="flex items-center gap-3 font-medium"> <carbon:flash class="text-yellow-400"/> Tự kiểm chứng chéo giữa các Agent </li>
        <li class="flex items-center gap-3 font-medium"> <carbon:flash class="text-yellow-400"/> Khả năng mở rộng không giới hạn </li>
      </ul>
    </div>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full gap-0">
  <div class="col-span-5 p-16 bg-[#0f0f0f] border-r border-white/5 flex flex-col justify-center">
    <div class="flex items-center gap-2 mb-6">
      <carbon:data-blob class="text-blue-400 animate-pulse" />
      <span class="text-xs font-mono text-blue-300 uppercase tracking-widest">Input Processing</span>
    </div>
    <h2 class="text-4xl font-black mb-6">Xử lý <br/><span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Dữ liệu Cấu trúc</span></h2>
    <p class="text-gray-400 leading-relaxed mb-8">
      Hệ thống tự động phân tích các schema JSON phức tạp, trích xuất thực thể và thiết lập ngữ cảnh (context) cho các Agent tiếp theo.
    </p>
    <div class="space-y-4">
      <div class="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/10">
        <carbon:checkmark-outline class="text-emerald-400" />
        <span class="text-sm">Mapping thuộc tính tự động</span>
      </div>
      <div class="flex items-center gap-3 p-3 bg-white/5 rounded-xl border border-white/10">
        <carbon:checkmark-outline class="text-emerald-400" />
        <span class="text-sm">Khử nhiễu & Chuẩn hóa dữ liệu</span>
      </div>
    </div>
  </div>

  <div class="col-span-7 p-12 bg-black flex items-center justify-center relative">
    <div class="w-full max-w-lg bg-[#1a1a1a] rounded-2xl border border-white/10 shadow-2xl overflow-hidden" v-motion-slide-right>
      <div class="bg-white/5 px-4 py-2 border-b border-white/10 flex gap-2">
        <div class="w-2 h-2 rounded-full bg-red-500/50"></div>
        <div class="w-2 h-2 rounded-full bg-yellow-500/50"></div>
        <div class="w-2 h-2 rounded-full bg-green-500/50"></div>
      </div>
      <div class="p-6 text-[13px] font-mono leading-relaxed">
        <span class="text-purple-400">"input_data"</span>: {<br/>
        &nbsp;&nbsp;<span class="text-blue-400">"topic"</span>: <span class="text-orange-300">"AI Agents"</span>,<br/>
        &nbsp;&nbsp;<span class="text-blue-400">"sections"</span>: [<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;{ <span class="text-blue-400">"id"</span>: <span class="text-orange-300">1</span>, <span class="text-blue-400">"content"</span>: <span class="text-emerald-400">"..."</span> },<br/>
        &nbsp;&nbsp;&nbsp;&nbsp;{ <span class="text-blue-400">"id"</span>: <span class="text-orange-300">2</span>, <span class="text-blue-400">"content"</span>: <span class="text-emerald-400">"..."</span> }<br/>
        &nbsp;&nbsp;],<br/>
        &nbsp;&nbsp;<span class="text-blue-400">"theme_config"</span>: <span class="text-purple-400">"Modern_Dark"</span><br/>
        }
      </div>
    </div>
    <div class="absolute -left-0.1 top-1/2 -translate-y-1/2">
       <carbon:chevron-right class="text-4xl text-blue-500" />
    </div>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="grid grid-cols-12 h-full w-full">
  <div class="col-span-12 p-16 pb-4">
    <h2 class="text-5xl font-black">Linh hoạt <span class="italic text-gray-500">Bố cục.</span></h2>
  </div>
  
  <div class="col-span-12 px-16 grid grid-cols-3 gap-8">
    <div class="group cursor-pointer">
      <div class="aspect-video bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl mb-4 border border-white/10 overflow-hidden relative shadow-lg group-hover:border-blue-500/50 transition-all">
         <div class="absolute inset-0 flex items-center justify-center opacity-20 group-hover:scale-110 transition-transform">
           <carbon:template class="text-6xl" />
         </div>
      </div>
      <h4 class="font-bold text-lg">Minimalist</h4>
      <p class="text-sm text-gray-500 leading-snug">Tối giản, tập trung vào typography và khoảng trắng.</p>
    </div>
    <div class="group cursor-pointer">
      <div class="aspect-video bg-gradient-to-br from-indigo-900 to-purple-900 rounded-2xl mb-4 border border-white/10 overflow-hidden relative shadow-lg group-hover:border-purple-500/50 transition-all">
         <div class="absolute inset-0 flex items-center justify-center opacity-20 group-hover:scale-110 transition-transform">
           <carbon:color-palette class="text-6xl" />
         </div>
      </div>
      <h4 class="font-bold text-lg">High-Tech Neon</h4>
      <p class="text-sm text-gray-500 leading-snug">Mạnh mẽ với dải màu gradient và hiệu ứng phát sáng.</p>
    </div>
    <div class="group cursor-pointer">
      <div class="aspect-video bg-gradient-to-br from-emerald-900 to-teal-900 rounded-2xl mb-4 border border-white/10 overflow-hidden relative shadow-lg group-hover:border-emerald-500/50 transition-all">
         <div class="absolute inset-0 flex items-center justify-center opacity-20 group-hover:scale-110 transition-transform">
           <carbon:presentation-file class="text-6xl" />
         </div>
      </div>
      <h4 class="font-bold text-lg">Corporate Elite</h4>
      <p class="text-sm text-gray-500 leading-snug">Chuyên nghiệp, tin cậy cho các báo cáo doanh nghiệp.</p>
    </div>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100 flex items-center justify-center
---

<div class="grid grid-cols-2 gap-16 max-w-5xl items-center p-12">
  <div class="relative">
    <div class="w-80 h-80 bg-blue-500/10 rounded-full absolute -top-10 -left-10 blur-[80px]"></div>
    <div class="relative bg-white/5 border border-white/10 p-10 rounded-[3rem] backdrop-blur-xl">
       <carbon:security class="text-8xl text-blue-400 mb-6" />
       <h3 class="text-3xl font-black mb-4 leading-tight">An toàn & <br/>Tin cậy Tuyệt đối</h3>
       <p class="text-gray-400 text-sm">Dữ liệu JSON được xử lý trong môi trường sandbox riêng biệt, đảm bảo không rò rỉ thông tin nhạy cảm.</p>
    </div>
  </div>

  <div class="space-y-8">
     <div class="flex gap-6 items-start">
        <div class="p-4 bg-white/5 rounded-2xl"><carbon:flash class="text-2xl text-yellow-400"/></div>
        <div>
           <h5 class="font-bold text-lg">Xử lý Song song</h5>
           <p class="text-sm text-gray-500">Nhiều Agent làm việc cùng lúc, rút ngắn thời gian tạo Slide xuống còn < 10 giây.</p>
        </div>
     </div>
     <div class="flex gap-6 items-start">
        <div class="p-4 bg-white/5 rounded-2xl"><carbon:cloud-service-management class="text-2xl text-purple-400"/></div>
        <div>
           <h5 class="font-bold text-lg">Khả năng Tích hợp</h5>
           <p class="text-sm text-gray-500">API sẵn sàng để kết nối với Slack, Microsoft Teams hoặc Web Dashboard.</p>
        </div>
     </div>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100
---

<div class="h-full w-full flex flex-col justify-center px-12 py-8 relative">
  <div class="absolute top-20 right-20 w-96 h-96 bg-blue-600/10 rounded-full blur-[120px]"></div>
  <div class="absolute bottom-20 left-20 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px]"></div>

  <div class="mb-8 relative z-10" v-motion-slide-top>
    <div class="flex items-center gap-2 mb-2">
      <div class="h-0.5 w-8 bg-gradient-to-r from-blue-500 to-purple-500"></div>
      <span class="text-[10px] uppercase tracking-[0.3em] text-blue-400 font-bold">Product Roadmap</span>
    </div>
    <h2 class="text-4xl font-black">
      Hành Trình <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500">Phát Triển</span>
    </h2>
  </div>

  <div class="relative z-10">
    <div class="absolute top-[48px] left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-emerald-500/20"></div>
    <div class="grid grid-cols-4 gap-4">
      <div class="relative" v-motion-slide-bottom :delay="100">
        <div class="flex flex-col items-center mb-4">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center mb-3 shadow-xl shadow-blue-500/40 relative">
            <carbon:cube class="text-xl text-white" />
            <div class="absolute -inset-0.5 bg-blue-500/20 rounded-xl blur -z-10"></div>
          </div>
          <div class="h-6 w-0.5 bg-gradient-to-b from-blue-500/50 to-transparent"></div>
        </div>
        <div class="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-4 hover:border-blue-500/50 transition-all duration-300 hover:transform hover:scale-105">
          <div class="text-blue-400 font-mono text-[10px] mb-2 uppercase tracking-wider">Q1 2025</div>
          <h3 class="text-base font-black mb-2 text-white">Foundation</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-3">Xây dựng nền tảng RAG engine và Multi-Agent orchestration cơ bản.</p>
          <div class="flex flex-wrap gap-1.5">
            <span class="text-[9px] px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded-full">Core Pipeline</span>
            <span class="text-[9px] px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded-full">RAG v1</span>
          </div>
        </div>
      </div>
      <div class="relative" v-motion-slide-bottom :delay="250">
        <div class="flex flex-col items-center mb-4">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center mb-3 shadow-xl shadow-purple-500/40 relative">
            <carbon:machine-learning-model class="text-xl text-white" />
            <div class="absolute -inset-0.5 bg-purple-500/20 rounded-xl blur -z-10"></div>
          </div>
          <div class="h-6 w-0.5 bg-gradient-to-b from-purple-500/50 to-transparent"></div>
        </div>
        <div class="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-4 hover:border-purple-500/50 transition-all duration-300 hover:transform hover:scale-105">
          <div class="text-purple-400 font-mono text-[10px] mb-2 uppercase tracking-wider">Q3 2025</div>
          <h3 class="text-base font-black mb-2 text-white">Advanced Reasoning</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-3">Tích hợp khả năng suy luận đa bước và tự sửa lỗi thông minh.</p>
          <div class="flex flex-wrap gap-1.5">
            <span class="text-[9px] px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded-full">Self-Correction</span>
            <span class="text-[9px] px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded-full">Chain-of-Thought</span>
          </div>
        </div>
      </div>
      <div class="relative" v-motion-slide-bottom :delay="400">
        <div class="flex flex-col items-center mb-4">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-pink-600 flex items-center justify-center mb-3 shadow-xl shadow-pink-500/40 relative">
            <carbon:network-3 class="text-xl text-white" />
            <div class="absolute -inset-0.5 bg-pink-500/20 rounded-xl blur -z-10"></div>
          </div>
          <div class="h-6 w-0.5 bg-gradient-to-b from-pink-500/50 to-transparent"></div>
        </div>
        <div class="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-4 hover:border-pink-500/50 transition-all duration-300 hover:transform hover:scale-105">
          <div class="text-pink-400 font-mono text-[10px] mb-2 uppercase tracking-wider">Q1 2026</div>
          <h3 class="text-base font-black mb-2 text-white">Ecosystem</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-3">Mở rộng thư viện Agent chuyên biệt cho từng vertical market.</p>
          <div class="flex flex-wrap gap-1.5">
            <span class="text-[9px] px-2 py-0.5 bg-pink-500/20 text-pink-300 rounded-full">Agent Library</span>
            <span class="text-[9px] px-2 py-0.5 bg-pink-500/20 text-pink-300 rounded-full">Marketplace</span>
          </div>
        </div>
      </div>
      <div class="relative" v-motion-slide-bottom :delay="550">
        <div class="flex flex-col items-center mb-4">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center mb-3 shadow-xl shadow-emerald-500/40 relative">
            <carbon:rocket class="text-xl text-white" />
            <div class="absolute -inset-0.5 bg-emerald-500/20 rounded-xl blur -z-10"></div>
          </div>
          <div class="h-6 w-0.5 bg-gradient-to-b from-emerald-500/50 to-transparent"></div>
        </div>
        <div class="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-4 hover:border-emerald-500/50 transition-all duration-300 hover:transform hover:scale-105">
          <div class="text-emerald-400 font-mono text-[10px] mb-2 uppercase tracking-wider">Vision 2027</div>
          <h3 class="text-base font-black mb-2 text-white">Autonomous AGI</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-3">Hệ thống tự học và tiến hóa dựa trên feedback vận hành thực tế.</p>
          <div class="flex flex-wrap gap-1.5">
            <span class="text-[9px] px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-full">Self-Evolution</span>
            <span class="text-[9px] px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-full">AGI Ready</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

---
layout: standard
class: p-0 bg-[#0a0a0a] text-gray-100 flex items-center justify-center overflow-hidden
---

<div class="absolute inset-0 opacity-20">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.3)_0%,transparent_70%)]"></div>
</div>

<div class="relative z-10 text-center px-8">
  <div class="inline-block px-4 py-1 rounded-full border border-white/10 bg-white/5 text-[10px] uppercase tracking-[0.4em] mb-8 animate-pulse text-blue-300">
    Let's Build the Future Together
  </div>
  
  <h1 class="text-8xl font-black mb-12 tracking-tighter">
    Cảm Ơn Các Bạn<br/>
    <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500">
      Đã Lắng Nghe!
    </span>
  </h1>

  <div class="grid grid-cols-3 gap-8 max-w-3xl mx-auto mt-16 p-8 bg-white/5 backdrop-blur-2xl rounded-[2rem] border border-white/10">
    <div class="text-center border-r border-white/10">
      <div class="text-gray-500 text-xs uppercase mb-2">Email Us</div>
      <div class="font-bold text-sm">contact@castudy.vn</div>
    </div>
    <div class="text-center border-r border-white/10">
      <div class="text-gray-500 text-xs uppercase mb-2">Follow Us</div>
      <div class="font-bold text-sm">@castudy</div>
    </div>
    <div class="text-center">
      <div class="text-gray-500 text-xs uppercase mb-2">Website</div>
      <div class="font-bold text-sm">www.castudy.vn</div>
    </div>
  </div>

  <p class="mt-12 text-gray-600 text-[10px] uppercase tracking-widest">
    © 2025 Ca Study. All Rights Reserved.
  </p>
</div>