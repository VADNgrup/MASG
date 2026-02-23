# Asset Manager - Chart Resolution

## Tổng quan

File `asset_manager.py` hiện đã hỗ trợ **cả images và charts** sử dụng LLM semantic matching.

## Các phương thức chính

### 1. `resolve_image()` - Tìm ảnh phù hợp

```python
async def resolve_image(
    self, 
    query: str, 
    context: DocumentContext,
    slide_title: str = None,
    slide_content: Optional[List[str]] = None
) -> Tuple[ImageReference, Dict[str, Any]]
```

**Luồng xử lý:**
1. Tìm ảnh từ tài liệu gốc (so sánh caption với slide_content)
2. Nếu không tìm thấy → Tìm trên Tavily
3. Nếu Tavily thất bại + concept abstract → Sinh ảnh bằng AI

### 2. `resolve_chart()` - Tìm chart phù hợp

```python
def resolve_chart(
    self,
    slide_title: str,
    slide_content: Optional[List[str]],
    context: DocumentContext,
    used_chart_ids: set = None
) -> Optional[Dict[str, Any]]
```

**Luồng xử lý:**
1. Lấy danh sách charts có `should_visualize == "Yes"` và có `chart_path`
2. Loại bỏ charts đã được sử dụng (dựa vào `used_chart_ids`)
3. So sánh `table_caption` với `slide_content` bằng LLM
4. Trả về chart có điểm relevance cao nhất (≥ 1)

**Kết quả trả về:**
```python
{
    "table_id": "table_001",
    "chart_path": "path/to/chart.png",
    "table_caption": "Sales data by quarter",
    "markdown": "| Q1 | Q2 | Q3 | Q4 |\n|---|---|---|---|\n| 100 | 150 | 200 | 250 |",
    "chart_type": "bar",
    "relevance_score": 2
}
```

## Ví dụ sử dụng

### Trong workflow node

```python
async def asset_manager_node(state: WorkflowState) -> Dict[str, Any]:
    slides = state["slides"]
    image_decisions = state.get("image_decisions", []).copy()
    used_chart_ids = set()
    
    for slide in slides:
        # Resolve image
        if slide.image_query and not slide.image:
            image_ref, decision_log = await asset_manager.resolve_image(
                slide.image_query,
                state["document_context"],
                slide_title=slide.title,
                slide_content=slide.content
            )
            slide.image = image_ref
            image_decisions.append(decision_log)
        
        # Resolve chart
        chart_info = asset_manager.resolve_chart(
            slide_title=slide.title,
            slide_content=slide.content,
            context=state["document_context"],
            used_chart_ids=used_chart_ids
        )
        
        if chart_info:
            # Store chart info in slide metadata
            slide.metadata["chart"] = chart_info
            used_chart_ids.add(chart_info["table_id"])
    
    return {"image_decisions": image_decisions}
```

## So sánh với writer.py

### writer.py - `_get_available_visuals_for_section()`
- Tìm visuals cho **section** (trước khi tạo slide)
- So sánh với `section["title"]` + `section["key_concepts"]`
- Quản lý `used_visuals` set để tránh trùng lặp
- Trả về lists: `relevant_images`, `relevant_charts`

### asset_manager.py - `resolve_image()` + `resolve_chart()`
- Tìm visuals cho **slide** (sau khi slide đã được tạo)
- So sánh với `slide_title` + `slide_content` (chi tiết hơn)
- `resolve_chart()` nhận `used_chart_ids` từ bên ngoài
- Trả về từng item riêng lẻ

## Điểm khác biệt quan trọng

| Khía cạnh | writer.py | asset_manager.py |
|-----------|-----------|------------------|
| **Thời điểm** | Trước khi draft slide | Sau khi draft slide |
| **Input** | Section (title + key_concepts) | Slide (title + content bullets) |
| **Output** | Lists of visuals | Single best match |
| **Quản lý used items** | Internal (used_visuals set) | External (used_chart_ids parameter) |
| **Mục đích** | Planning phase | Execution phase |

## Lưu ý khi sử dụng

1. **Chart path**: Chỉ xét charts đã có `chart_path` (đã được generate)
2. **Caption required**: Cả images và charts đều cần có caption để đánh giá
3. **Threshold**: Chỉ chọn visuals có relevance score ≥ 1
4. **Deduplication**: Cần quản lý `used_chart_ids` ở workflow level
5. **Async vs Sync**: `resolve_image()` là async, `resolve_chart()` là sync

## Cải tiến trong tương lai

- [ ] Thêm caching cho LLM evaluation results
- [ ] Hỗ trợ multiple charts per slide
- [ ] Thêm fallback logic cho charts (tương tự Tavily cho images)
- [ ] Tích hợp chart generation on-demand nếu không tìm thấy chart phù hợp
