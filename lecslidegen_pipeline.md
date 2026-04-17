
## Phase 1: Trích xuất tài liệu đầu vào (Ingestion & Extraction)
**Module:** `src/ingestion/`
**File chính:** `extract_file.py`

Khi người dùng nhập một tài liệu (PDF, Docx), hệ thống không đưa thẳng cho LLM đọc mà thực hiện "mổ xẻ" tài liệu đó ra:

1. **Text Extraction (Trích xuất văn bản):** 
   - Hàm `DocumentParser` (dùng công cụ Marker) được kích hoạt để đọc toàn bộ chữ, cấu trúc lại thành dạng Markdown, và giữ lại chính xác số trang (pages).
2. **Image Extraction & Filtration (Trích xuất & lọc ảnh):**
   - Hệ thống tự động bắt các mảng bytes của hình ảnh trong tài liệu.
   - Các hình ảnh này được một lớp `ImageFilter` tiền xử lý để loại bỏ những icon, logo hoặc các khối nhiễu nhỏ không mang ý nghĩa học thuật, chỉ giữ lại ảnh chân thực (valid images).
   - VLM (Vision Model) sẽ được gọi để tạo ra các "caption" (phụ đề) thô giải thích cơ bản cho các hình ảnh này. Nội dung ảnh sẽ được lưu trữ bởi `AssetManager`.
3. **Table & Chart Generation (Xử lý Bảng biểu):**
   - Không chỉ trích xuất chữ của bảng (Table), hệ thống tự động chạy kịch bản `generate_charts.py` để tìm các bảng biểu mang tính chất dữ liệu (số liệu tuyến tính, phần trăm...) và tự động convert bảng đó thành Biểu đồ đường/cột (Charts) để hiển thị đẹp hơn trên slide.
4. **Context Building:**
   - Tập hợp tất cả lại thành một cấu trúc chung là `DocumentContext` và lưu cứng vào máy (`data/raw_contexts/{doc_id}.json`).

---

## Phase 2: Lập dàn ý & Viết nội dung (Lecture Generation Workflow)
**Module:** `src/workflow/`
**File chính:** `preprocessing_context.py` & thư mục `agents/`

Hệ thống sử dụng **LangGraph** để tạo ra một Agentic Loop (vòng lặp các tác vụ tư duy) đóng vai trò một giáo sư đại học viết slide. Vòng lặp bao gồm các Agent:

1. **Planner (`planner.py`):** 
   - Đọc Context Markdown ở Phase 1, xác định cấu trúc bài giảng sẽ có bao nhiêu chương, nội dung từng phần là gì.
2. **Plan Specifier (`plan_specer.py`):** 
   - Tạo ra danh sách các Slide Specifications. Với mỗi trang slide, nó định nghĩa một "Goal" (mục tiêu cốt lõi) rõ ràng (Ví dụ: Slide 5 bắt buộc phải định nghĩa được khái niệm X).
3. **Writer (`writer.py`):** 
   - Được giao Spec và bắt đầu viết chữ trực tiếp cho Slide (Drafting).
4. **Reviewer (`writer_reviewer.py` — Đánh giá & Duyệt file):**
   - Đây là lõi đánh giá cực kỳ chi tiết. Reviewer chạy **song song 3 hệ quy chiếu** để bắt lỗi Writer. Cụ thể:
     - **Faithfulness (Độ trung thực):** Nó so sánh Slide với Text gốc ở Phase 1. Nếu tìm thấy lỗi "hallucination" (Tự bịa số liệu, sai lệch thực tế), nó gán mác lỗi là `CRITICAL`.
     - **Coverage & Clarity (Độ phủ & Mạch lạc):** Nó kiểm tra ngược lại với "Goal" ở bước Specifier. Nếu slide đi lạc đề hoặc thiếu sót kiến thức, nó sẽ bắt lỗi.
     - **Presentation Quality (Chất lượng sư phạm):** Có các Rule cứng (Ví dụ: Slide không được vượt quá 5 bullet points, mỗi bullet không quá 15 chữ, tổng slide < 75 chữ). Nếu vượt quá giới hạn trên, nó cảnh báo lỗi format.
5. **Refiner (`writer_refiner.py`):**
   - Nhận lại json các lỗi (Issue list) từ Reviewer. Dựa vào các mức độ lỗi (`critical`, `major`, `minor`), nó sẽ cập nhật lại text cho đúng. Toàn bộ vòng quay này lặp lại liên tục cho đến khi slide "sạch lỗi" hoặc đạt giới hạn số lần lặp.
6. **Output:** Trả về một file JSON gồm các mảng text Slide thuần tuý.

---

## Phase 3: Phân bổ Đa phương tiện (Multimodal Processing)
**Module:** `src/multimodal/`
**File chính:** `agents/image_distribution.py` và `src/utils/semantic_match.py`

Làm thế nào để biết ảnh nào trong PDF gốc nên nhét vào Slide số mấy? Nơi này sử dụng **Embeddings** và Retrieval rất cẩn thận.

1. **Khởi tạo Embedding Model (`semantic_match.py`):**
   - **Mô hình Text**: `Qwen/Qwen3-Embedding-0.6B` (Dùng để tìm kiếm ngữ nghĩa text-to-text).
   - **Mô hình Đa phương thức**: `openai/clip-vit-base-patch32` (Dùng để chéo hóa text và ảnh - Cross-modal).
2. **Cập nhật ý nghĩa cho ảnh ở PDF gốc (Summarising):**
   - VLM gom `Caption` của ảnh và `Context xung quanh ảnh` của file gốc để sinh ra một mô tả bức ảnh hoàn chỉnh. Sau đó, nó tạo 2 embeddings: 1 dãy vector text Qwen, và 1 dãy Vector CLIP.
3. **Mã hóa các trang Text Slide:** 
   - Lấy các Slide mới sinh ở Phase 2, mỗi bullet point đều được mã hoá thành vector Qwen và CLIP.
4. **Thuật toán Matching (Phân bổ):**
   - Tính hệ số khoảng cách cosin (`cosine_similarity`).
   - Tổng điểm trùng khớp = `alpha * Text_sim + (1-alpha) * Image_sim`. (Trong đó text_sim lấy trung bình top 3 bullet có nghĩa tương đồng nhất với ảnh).
   - Nếu điểm vượt Threshold, ảnh sẽ được "gán" vào Slide đó (Tối đa 2 ảnh/slide).
5. **Bù đắp thông tin (Web Search Fallback):**
   - Nếu một slide mang tính khái niệm nhưng **không có ảnh nào** từ PDF phù hợp, Agent sẽ làm 5 thao tác:
     1. Tự động sinh ra 2 từ khoá (Search Queries).
     2. Gửi lệnh lấy ảnh từ Google (qua Serper API).
     3. Lọc bỏ các trang web hàn lâm bị cấm, lọc bỏ ảnh quá dài/quá dẹt (Tỉ lệ W/H bị kiểm soát).
     4. Lấy các ảnh Google trả về, chạy qua mô hình CLIP nhúng lại, so sánh với vector của Slide để tìm bức ảnh thích hợp nhất. Đồng thời so sánh với các ảnh web trước đó để tránh trùng lập (De-duplication).

---

## Phase 4: Biểu diễn & Render bản trình chiếu (Slidev & Layouting)
**Module:** `src/generator/`
**File chính:** `slide_pick_and_merge.py` và `slide_improving.py`

Giai đoạn chắp nối thành phẩm giao diện UI qua nền tảng Slidev, gồm 2 bước độc đáo.

### Bước 4.1. Kiến tạo Layout (Rule-based & LLM Theme)
- LLM sẽ đọc lại dàn ý (Outline) để quyết định **Theme màu sắc** và **Font chữ** (ví dụ bài nói về Computer Science sẽ gợi ý font monospace, bài nói về Lịch sử sẽ là font serif).
- **Rule Layout cứng:** Tuỳ thuộc vào số lượng chữ, việc có một hay hai hình ảnh, và **aspect ratio** (tỉ lệ ngang/dọc) của hình ảnh đó mà nó chọn Layout. (VD: Nếu tỉ lệ > 1.77 (ảnh rất rộng) -> đẩy ảnh lên viền trên cùng hoặc dưới cùng; Nếu ảnh vuông -> thả ảnh sang cột bên trái hoặc cột bên phải).

### Bước 4.2. Tối ưu hoá cỡ ảnh (Fine-tuning không dùng LLM)
File `slide_improving.py` giải quyết bài toán: *Làm sao ảnh to nhất có thể mà chữ vẫn không bị che khuất?*
Nó chạy thuật toán như sau cho mọi file Slidev.
- Dùng `PyMuPDF` để xuất PDF mẫu và soi ảnh nháp.
- Dùng thuật toán học máy **KMeans Clustering** trên toàn pixel của trang PDF để phân tách và xác định đâu là Màu Nền (Background Color) chủ đạo.
- Nó tiến hành một hàm tối ưu hoá (Optimisation Function):
  - Nhích thông số Image Width (Cỡ chiều rộng ảnh) lớn dần.
  - Sau mỗi lần nhích, nó quét lại PDF. Nếu chữ trên slide bị sai lệch so với bản gốc do ảnh đè lên (Thuật toán Levenshtein Fuzzy Score biến động), lập tức nó biết "đã bị đè" và lùi Size lại.
  - Nó liên tục gia tăng cỡ ảnh cho đến khi tiêu diệt được khoảng trống trên slide (pixels trùng màu với Background Color giảm tối thiểu).
- Render thành phẩm cuối cùng: Tập hợp file PDF `*-export.pdf` chuẩn xác và bóc thành các ảnh `.jpg`.
