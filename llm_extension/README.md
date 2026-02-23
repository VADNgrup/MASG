# Pinkyne Extension - OpenAI Unofficial API Wrapper

🎯 **Mục đích**: Wrapper cho phép sử dụng Pinkyne API (unofficial OpenAI-compatible) thay vì OpenAI chính thức, **không cần sửa code gốc**.

## 📋 Tổng quan

Pinkyne extension là một layer wrapper trong suốt (transparent) cho OpenAI API. Khi bạn import module này, tất cả các API calls sẽ tự động được chuyển hướng đến Pinkyne API mà không cần thay đổi bất kỳ code nào trong dự án.

### Tính năng

✅ **Không sửa code gốc**: Tất cả code trong `src/` giữ nguyên  
✅ **Tự động patch imports**: Chỉ cần import 1 dòng  
✅ **Tương thích 100%**: Giữ nguyên interface OpenAI  
✅ **Hỗ trợ đầy đủ**: Chat, Vision, Image Generation  
✅ **Dễ dàng bật/tắt**: Comment/uncomment để switch

## 🚀 Cài đặt nhanh

### Bước 1: Cấu hình API Key

Thêm API key vào file `.env`:

```bash
# Option 1: Dùng biến riêng cho Pinkyne
PINKYNE_API_KEY=your_pinkyne_api_key_here

# Option 2: Hoặc dùng chung biến OPENAI_API_KEY
OPENAI_API_KEY=your_pinkyne_api_key_here
```

### Bước 2: Chạy setup script

```bash
python pinkyne_extension/setup_pinkyne.py
```

Script này sẽ:
- ✅ Kiểm tra environment
- ✅ Verify dependencies
- ✅ Tạo example script
- ✅ Hướng dẫn cách sử dụng

### Bước 3: Test API

```bash
python -m pinkyne_extension.test_api
```

Script test sẽ kiểm tra:
- ✅ Chat completions
- ✅ LangChain integration
- ✅ Vision API
- ✅ Image generation
- ✅ Structured output

## 💻 Cách sử dụng

### Cách 1: Import trong mỗi script

Thêm import này **ở đầu file** (trước các import OpenAI):

```python
import pinkyne_extension  # Tự động patch tất cả OpenAI APIs

# Bây giờ dùng như bình thường
from openai import OpenAI
from langchain_openai import ChatOpenAI

client = OpenAI()  # Thực ra là PinkyneClient
llm = ChatOpenAI()  # Thực ra là ChatPinkyne
```

### Cách 2: Sửa entry points

Thêm vào `main.py` hoặc các entry point scripts:

```python
# main.py
import pinkyne_extension  # Thêm dòng này

# ... rest of your code
```

Sau đó chạy như bình thường:

```bash
python main.py
```

### Cách 3: Sử dụng trong pipeline hiện tại

**Phase 1: Extract**
```bash
python -m src.extractor.extract_file --input data/raw/sample.pdf
```

**Phase 2: Preprocessing**
```bash  
python -m src.preprocessor.preprocessing_context --context data/context/xxx.json
```

**Phase 3: Generate**
```bash
python -m src.generator.slide_generator data/lectures/lec_xxx.json slidev/slides.md
```

Chỉ cần thêm import `pinkyne_extension` vào đầu các file:
- `src/extractor/extract_file.py`
- `src/preprocessor/preprocessing_context.py`
- `src/generator/slide_generator.py`

## 🔧 Cấu trúc thư mục

```
pinkyne_extension/
├── __init__.py              # Auto-patching logic
├── pinkyne_config.py        # Configuration (base URLs, API key)
├── pinkyne_client.py        # Wrapper cho openai.OpenAI
├── pinkyne_langchain.py     # Wrapper cho ChatOpenAI
├── setup_pinkyne.py         # Setup script
├── test_api.py             # Test suite
└── README.md               # Tài liệu này
```

## 📡 API Endpoints

Pinkyne sử dụng các endpoints tương thích OpenAI:

| OpenAI Endpoint | Pinkyne Endpoint |
|----------------|------------------|
| `https://api.openai.com/v1/chat/completions` | `https://api.pinkyne.com/v1/chat/completions` |
| `https://api.openai.com/v1/images/generations` | `https://api.pinkyne.com/v1/images/generations` |

## 🎯 Ví dụ sử dụng

### Example 1: Chat Completion

```python
import pinkyne_extension
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
print(response.choices[0].message.content)
```

### Example 2: LangChain

```python
import pinkyne_extension
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
response = llm.invoke("What is AI?")
print(response.content)
```

### Example 3: Vision API

```python
import pinkyne_extension
from openai import OpenAI
import base64

client = OpenAI()

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
    }]
)
print(response.choices[0].message.content)
```

### Example 4: Image Generation

```python
import pinkyne_extension
from openai import OpenAI

client = OpenAI()
response = client.images.generate(
    model="dall-e-3",
    prompt="A futuristic city at sunset",
    size="1024x1024"
)
print(response.data[0].url)
```

## 🐛 Debugging

### Bật verbose logging

```bash
export PINKYNE_VERBOSE=true  # Linux/Mac
set PINKYNE_VERBOSE=true     # Windows

python -m pinkyne_extension.test_api
```

### Kiểm tra API đang được sử dụng

```python
import pinkyne_extension
from openai import OpenAI

client = OpenAI()
print(client)  # Should show: PinkyneClient(base_url='https://api.pinkyne.com/v1')
```

### Unpatch để sử dụng OpenAI gốc

```python
import pinkyne_extension

# ... làm việc với Pinkyne ...

# Restore về OpenAI gốc
pinkyne_extension.unpatch_all()
```

## ⚠️ Lưu ý quan trọng

### 1. Import order quan trọng

**❌ SAI:**
```python
from openai import OpenAI  # Import trước
import pinkyne_extension   # Quá muộn!
```

**✅ ĐÚNG:**
```python
import pinkyne_extension   # Import TRƯỚC
from openai import OpenAI  # Bây giờ mới import
```

### 2. API compatibility

Pinkyne API phải tương thích 100% với OpenAI API format. Nếu có sự khác biệt, bạn có thể cần điều chỉnh trong `pinkyne_config.py`.

### 3. Rate limits

Pinkyne có thể có rate limits khác với OpenAI. Monitor logs để detect issues.

### 4. Error handling  

Một số error codes có thể khác. Test kỹ và thêm error handling nếu cần.

## 🔄 Chuyển đổi giữa OpenAI và Pinkyne

### Sử dụng Pinkyne

```python
import pinkyne_extension
# ... code của bạn ...
```

### Sử dụng OpenAI gốc

```python
# Chỉ cần comment dòng import
# import pinkyne_extension
# ... code của bạn ...
```

Đơn giản như vậy! Không cần sửa gì khác.

## 📊 Testing

Chạy test suite để verify setup:

```bash
python -m pinkyne_extension.test_api
```

Kết quả mong đợi:
```
🧪 Pinkyne API Test Suite
======================================================================
✅ Configuration valid
✅ Clients initialized

Test 1: Simple Chat Completion
----------------------------------------------------------------------
✅ Chat completion successful

Test 2: LangChain ChatPinkyne  
----------------------------------------------------------------------
✅ LangChain chat successful

Test 3: Vision API (Image Analysis)
----------------------------------------------------------------------
✅ Vision API successful

Test 4: Image Generation (DALL-E)
----------------------------------------------------------------------
✅ Image generation successful

Test 5: Structured JSON Output
----------------------------------------------------------------------
✅ Structured output successful

📊 Test Summary
======================================================================
Total tests: 5
✅ Passed: 5
❌ Failed: 0

🎉 All tests passed! Your Pinkyne API key is working correctly.
```

## 🆘 Troubleshooting

### Lỗi: "API key not found"

```bash
# Kiểm tra .env file
cat .env | grep API_KEY

# Hoặc set trực tiếp
export PINKYNE_API_KEY=your_key
```

### Lỗi: "Module not found"

```bash
# Install dependencies
pip install -r requirements.txt
```

### Lỗi: "Connection refused"

- Kiểm tra Pinkyne API có hoạt động không
- Verify base URL trong `pinkyne_config.py`
- Check network/firewall settings

### API calls vẫn đi OpenAI

- Đảm bảo import `pinkyne_extension` **TRƯỚC** import OpenAI
- Clear Python cache: `rm -rf __pycache__`
- Restart Python interpreter

## 📞 Hỗ trợ

Nếu gặp vấn đề:

1. Chạy test script: `python -m pinkyne_extension.test_api`
2. Bật verbose logging: `PINKYNE_VERBOSE=true`
3. Kiểm tra logs trong console
4. Verify API key còn hoạt động

## 📝 License

Phần mở rộng này tương thích với license của dự án LecSlideGen.

---

**Good luck! 🚀**
