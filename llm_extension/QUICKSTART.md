# Pinkyne Extension - Hướng dẫn sử dụng nhanh

## 🎯 Mục đích
Wrapper cho phép sử dụng Pinkyne API (unofficial OpenAI-compatible) mà **KHÔNG cần sửa code gốc** của LecSlideGen.

## 📦 Files đã tạo

Tất cả nằm trong thư mục `pinkyne_extension/`:

1. `__init__.py` - Auto-patching system
2. `pinkyne_config.py` - Configuration
3. `pinkyne_client.py` - OpenAI client wrapper
4. `pinkyne_langchain.py` - LangChain wrapper
5. `test_api.py` - Test suite
6. `setup_pinkyne.py` - Setup script
7. `quick_start.py` - Examples
8. `README.md` - Tài liệu đầy đủ

## ⚡ Sử dụng trong 3 bước

### Bước 1: Cấu hình API Key

Thêm vào file `.env`:
```bash
OPENAI_API_KEY=your_pinkyne_api_key_here
```

### Bước 2: Test API

```bash
cd d:\python\LecSlideGen
python -m pinkyne_extension.test_api
```

Kết quả mong đợi: **5/5 tests passed** ✅

### Bước 3: Sử dụng

**Cách đơn giản nhất:** Thêm `import pinkyne_extension` vào đầu các entry points:

#### Sửa `src/extractor/extract_file.py`:
```python
import pinkyne_extension  # Thêm dòng này ở đầu file
# ... code còn lại giữ nguyên
```

#### Sửa `src/preprocessor/preprocessing_context.py`:
```python
import pinkyne_extension  # Thêm dòng này ở đầu file
# ... code còn lại giữ nguyên
```

#### Sửa `src/generator/slide_generator.py`:
```python
import pinkyne_extension  # Thêm dòng này ở đầu file
# ... code còn lại giữ nguyên
```

**Xong!** Chạy như bình thường:

```bash
# Phase 1: Extract
python -m src.extractor.extract_file --input data/raw/sample.pdf

# Phase 2: Preprocess
python -m src.preprocessor.preprocessing_context --context data/context/xxx.json

# Phase 3: Generate
python -m src.generator.slide_generator data/lectures/lec_xxx.json slidev/slides.md
```

Tất cả API calls sẽ **tự động sử dụng Pinkyne API** thay vì OpenAI! 🎉

## 🔧 Debugging

Nếu cần kiểm tra API đang sử dụng:

```bash
# Bật verbose logging
set PINKYNE_VERBOSE=true  # Windows
export PINKYNE_VERBOSE=true  # Linux/Mac

# Chạy test lại
python -m pinkyne_extension.test_api
```

## 📚 Tài liệu đầy đủ

Xem [README.md](README.md) trong thư mục `pinkyne_extension/` để có:
- Hướng dẫn chi tiết
- Examples đầy đủ
- Troubleshooting guide
- API endpoint mappings

## ⏪ Quay lại OpenAI

Muốn dùng lại OpenAI chính thức? Đơn giản:

```python
# Chỉ cần comment dòng import
# import pinkyne_extension

# Code còn lại giữ nguyên
```

**That's it!** Không cần thay đổi gì khác.

## ✅ Checklist

- [ ] Đã thêm API key vào `.env`
- [ ] Đã chạy test: `python -m pinkyne_extension.test_api`
- [ ] Test passed (5/5)
- [ ] Đã thêm `import pinkyne_extension` vào entry points
- [ ] Đã test Phase 1 với file mẫu
- [ ] Mọi thứ hoạt động tốt!

---

**Good luck! Giờ bạn có thể tiết kiệm chi phí bằng Pinkyne API! 🚀💰**
