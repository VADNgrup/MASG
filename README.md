# This repository contains ideas for lecture generation

```bash
# 1. Extract document context
python -m src.extractor.extract_file --input data/raw/{file_name}.{type_file}

# 2. Generate lecture with smart metadata
python -m src.preprocessor.preprocessing_context --context data/context/{doc_id}.json

# 3. Generate slides
python -m src.generator.slide_generator data/lectures/{file_name}.json slidev/slides.md

# 4. After generating slides, you can run slidev to preview the slides
cd slidev
npm install
npm run dev
```