# Lecture Generation Pipeline

This repository contains ideas and an experimental pipeline for **automatic lecture generation**, from raw documents to Slidev-based presentation slides.

## Usage

Follow the steps below to generate lectures and slides:

```bash
# 1. Extract document context from a raw file
python -m src.extractor.extract_file --input data/raw/{file_name}.{file_type}

# 2. Preprocess context and generate smart metadata
python -m src.preprocessor.preprocessing_context --context data/context/{doc_id}.json

# 3. Generate Slidev-compatible slides
python -m src.generator.slide_generator data/lectures/{file_name}.json slidev/slides.md

# 4. Preview the generated slides using Slidev
cd slidev
npm install
npm run dev
```

## Pipeline Overview

![Lecture generation pipeline overview](images/Lecture-gen-2025-12-31.png)
*Figure 1: End-to-end lecture generation pipeline from raw documents to Slidev slides.*