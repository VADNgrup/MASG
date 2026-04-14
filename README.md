# Lecture Generation Pipeline

This repository contains ideas and an experimental pipeline for **automatic lecture generation**, from raw documents to Slidev-based presentation slides.

## Usage
Follow the steps below to generate lectures and slides:

```bash
# Myenv Activate
cd D:\python
.\myenv\Scripts\activate
cd .\LecSlideGen
# Convert all documents in data/raw to slides (speaker information is Optional)
python -m main --speaker_information "Your Information"

# For full pipeline with a single document (document_path is REQUIRED, lecture_title and speaker_information are Optional)
python -m main --document_path data/raw/{file_name}.{file_type} --lecture_title "Your customized Title" --speaker_information "Your Information"

# For debug
#1. Extract from a raw doc file or batch extract
python -m src.extractor.extract_file --input data/raw/{file_name}.{file_type}
#2. Build a lecture from above doc file information
python -m src.preprocessor.preprocessing_context --context data/context/{doc_id}.json
#3. Multimodal Processing
python -m src.multimodal.multimodal_processing --lecture data/lectures/{file_name}.json
#4. Generate a lecture from above lecture information
python -m src.generator.slide_gen --lecture data/lectures/{file_name}.json --title "{Your customized Title}" --speaker "{Your Information}"

# PPT Eval Benchmark
python -m src.evaluation.eval --model Qwen_Qwen3.5-9B
python -m src.evaluation.eval --model gpt-4.1-mini
```

## Pipeline Overview

![Lecture generation pipeline overview](docs/images/images/Lecture-gen-2025-12-31.png)
*Figure 1: End-to-end lecture generation pipeline from raw documents to Slidev slides.*