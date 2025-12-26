# This repository contains ideas for lecture generation

```bash
# 1. Extract document context
python src/extractor/extract_file.py --input data/raw/{file_name}.{type_file}

# 2. Generate lecture with smart metadata
python src/preprocessor/preprocessing_context.py --context data/context/{doc_id}.json

# 3. Generate slides
python src/generator/slide_generator.py data/lectures/{file_name}.json slidev/slides.md

# 4. After generating slides, you can run slidev to preview the slides
cd slidev
npm install
npm run dev
```