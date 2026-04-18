# LecSlideGen: Automated Lecture Generation Pipeline

LecSlideGen is an automated experimental pipeline designed to convert raw academic documents into structured, presentation-ready Slidev decks. The system utilizes a parallel Multi-Agent LLM architecture with built-in reflection and refinement mechanisms to ensure structural integrity and high content faithfulness to the source material.

## Architecture Highlights
- Multi-Agent Workflow: Modular agents handling document planning, slide specification, drafting, peer-reviewing, and active refinement.
- Self-Correction Mechanism: Parallel reviewers and a backtracking system to eliminate content hallucination and formatting failures.
- Pedagogical Layouts: Outputs directly to Slidev, focusing on standard educational presentation rules.

## Setup
Ensure all dependencies are installed, then create your local environment configuration by copying the provided example file:

```bash
cp .env.example .env
```
After copying, update the `.env` file with your specific API keys and model configurations.

## Usage

### 1. Automated Batch Processing
Generate slides for all supported documents placed inside the `data/raw/` directory.
```bash
python -m main --limit 10
```

### 2. Single Document Processing
Convert a specific document into slides, allowing customized overriding of the title and presenter metadata.
```bash
python -m main \
    --document_path "data/raw/document.pdf" \
    --lecture_title "Customized Lecture Title" \
    --speaker_information "John Doe"
```

### 3. Modular Debugging
For analytical purposes or manual intervention, the pipeline can be executed chronologically:
```bash
# Phase 1: Extract textual and tabular context
python -m src.extractor.extract_file --input "data/raw/document.pdf"

# Phase 2: Preprocess context
python -m src.preprocessor.preprocessing_context --context "data/context/doc_id.json"

# Phase 3: Process multimodal assets
python -m src.multimodal.multimodal_processing --lecture "data/lectures/file_name.json"

# Phase 4: Generate slides through the Multi-Agent framework
python -m src.generator.slide_gen --lecture "data/lectures/file_name.json"
```

## Evaluation & Benchmarking
The system supports automated evaluation using the PPTEval framework (LLM-as-a-Judge) to assess ROUGE-L, Content, Design, and Coherence metrics.

```bash
# 1. Run the entire generation and evaluation suite
python run_benchmark.py

# 2. Summarize runtime and quality metrics (automatically filters by model)
python summarize_performance.py --log logs/llm_calls_gpt-4.1-mini.jsonl
```

## System Overview
![Lecture Generation Pipeline](docs/images/Lecture-gen-2025-12-31.png)
*Figure 1: End-to-end framework architecture.*