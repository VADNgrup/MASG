
from src.utils.config import Config
from src.utils.llm import chat, vision_chat, b64_image
from pathlib import Path
from rouge_chinese import Rouge
from jinja2 import Template

import json
import re
import argparse
from tqdm import tqdm
import jieba
import os

rouge = Rouge()


CONTEXT_DIR = Config.CONTEXT_DIR
OUTPUT_DIR = Config.OUTPUT_DIR
EVAL_MODEL = Config.EVAL_LANGUAGE_MODEL
EVAL_BASE_URL = Config.EVAL_BASE_URL
EVAL_API_KEY = Config.EVAL_API_KEY
_PROMPT_DIR = Path(__file__).parent / "prompts"

def parse_full_text(context_path:Path):
    with open(context_path, 'r', encoding='utf-8') as f:
        full_context = f.read()
    context_json = json.loads(full_context)
    full_text = context_json['text_content']['markdown']
    return full_text
def parse_full_slides(output_lecture_path:str) -> str:
    # Lecture_path: output/{lecture_id}/{model_name}.json
    # Image_path: output/{lecture_id}/{model_name}_image_distribution.json
    # Table_distribution_path: output/{lecture_id}/{model_name}_table_distribution.json
    output_lecture_path = Path(output_lecture_path)
    image_path = output_lecture_path.parent / (output_lecture_path.stem + "_image_distribution.json")
    table_distribution_path = output_lecture_path.parent / (output_lecture_path.stem + "_table_distribution.json")

    with open(output_lecture_path, 'r', encoding='utf-8') as f:
        lecture_json = json.load(f)
    with open(image_path, 'r', encoding='utf-8') as f:
        image_distribution_json = json.load(f)
    with open(table_distribution_path, 'r', encoding='utf-8') as f:
        table_distribution_json = json.load(f)

    image_map: dict[int, list[str]] = {}
    for img in image_distribution_json:
        sn = img["slide_number"]
        image_map.setdefault(sn, []).append(img["caption"])

    table_map: dict[int, list[str]] = {}
    for tbl in table_distribution_json:
        sn = tbl["slide_number"]
        table_map.setdefault(sn, []).append(tbl["table_caption"])

    total_slides = lecture_json["metadata"]["total_slides"]
    parts = []

    for slide_entry in lecture_json["slides"]:
        slide_meta = slide_entry["slide"]
        slide_number = slide_meta["slide_number"]
        slide_title = slide_meta["slide_title"]
        content = slide_entry["content"]

        lines = [
            f"Slide {slide_number} of {total_slides}",
            f"Title: {slide_title}",
            json.dumps(content, ensure_ascii=False),
        ]

        for caption in image_map.get(slide_number, []):
            lines.append(f"Image: {caption}")

        for caption in table_map.get(slide_number, []):
            lines.append(f"Table: {caption}")

        parts.append("\n".join(lines))

    return "\n----\n".join(parts)

def rouge_l_score(source_text:str, presentation:str):
    source = " ".join(jieba.cut(str(source_text)))
    presentation = " ".join(jieba.cut(str(presentation)))
    return rouge.get_scores(presentation, source)[0]["rouge-l"]["f"]

def content_score(slide_image_path: str) -> float:
    slide_image_dir = Path(slide_image_path)
    log_path = slide_image_dir / "content_score_log.jsonl"

    slide_images = sorted(
        f for f in slide_image_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )

    describe_prompt = _load_prompt("ppteval_describe_content.txt").render()
    content_prompt_tpl = _load_prompt("ppteval_content.txt")

    content_score_log = []
    scores = []

    for img_path in slide_images:
        image_bytes = img_path.read_bytes()
        mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"

        description = vision_chat(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": describe_prompt},
                    b64_image(image_bytes, mime=mime),
                ],
            }],
            model=EVAL_MODEL,
            base_url=EVAL_BASE_URL,
            api_key=EVAL_API_KEY,
        )

        score_prompt = content_prompt_tpl.render(descr=description)
        score_response = chat(
            model=EVAL_MODEL,
            messages=[{"role": "user", "content": score_prompt}],
            base_url=EVAL_BASE_URL,
            api_key=EVAL_API_KEY,
        )
        result = json.loads(re.search(r"\{.*\}", score_response, re.DOTALL).group())
        result["score"] = int(result["score"])

        log_entry = {
            "slide": img_path.name,
            "description": description,
            "reason": result["reason"],
            "score": result["score"],
        }
        content_score_log.append(log_entry)
        scores.append(result["score"])

    with log_path.open("w", encoding="utf-8") as f:
        for entry in content_score_log:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    avg_content_score = sum(scores) / len(scores) if scores else 0.0
    return avg_content_score

def design_score(slide_image_path: str) -> float:
    slide_image_dir = Path(slide_image_path)
    log_path = slide_image_dir / "style_score_log.jsonl"

    slide_images = sorted(
        f for f in slide_image_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )

    describe_prompt = _load_prompt("ppteval_describe_style.txt").render()
    style_prompt_tpl = _load_prompt("ppteval_style.txt")

    style_score_log = []
    scores = []

    for img_path in slide_images:
        image_bytes = img_path.read_bytes()
        mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"

        description = vision_chat(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": describe_prompt},
                    b64_image(image_bytes, mime=mime),
                ],
            }],
            model=EVAL_MODEL,
            base_url=EVAL_BASE_URL,
            api_key=EVAL_API_KEY,
        )

        score_prompt = style_prompt_tpl.render(descr=description)
        score_response = chat(
            model=EVAL_MODEL,
            messages=[{"role": "user", "content": score_prompt}],
            base_url=EVAL_BASE_URL,
            api_key=EVAL_API_KEY,
        )
        result = json.loads(re.search(r"\{.*\}", score_response, re.DOTALL).group())
        result["score"] = int(result["score"])

        log_entry = {
            "slide": img_path.name,
            "description": description,
            "reason": result["reason"],
            "score": result["score"],
        }
        style_score_log.append(log_entry)
        scores.append(result["score"])

    with log_path.open("w", encoding="utf-8") as f:
        for entry in style_score_log:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    avg_design_score = sum(scores) / len(scores) if scores else 0.0
    return avg_design_score

def coherence_score(presentation: str) -> dict:
    extract_prompt = _load_prompt("ppteval_extract.txt").render(presentation=presentation)
    extract_response = chat(
        model=EVAL_MODEL,
        messages=[{"role": "user", "content": extract_prompt}],
        base_url=EVAL_BASE_URL,
        api_key=EVAL_API_KEY,
    )
    extract_json = json.loads(re.search(r"\{.*\}", extract_response, re.DOTALL).group())

    coherence_prompt = _load_prompt("ppteval_coherence.txt").render(
        presentation=json.dumps(extract_json, ensure_ascii=False, indent=2)
    )
    coherence_response = chat(
        model=EVAL_MODEL,
        messages=[{"role": "user", "content": coherence_prompt}],
        base_url=EVAL_BASE_URL,
        api_key=EVAL_API_KEY,
    )
    result = json.loads(re.search(r"\{.*\}", coherence_response, re.DOTALL).group())
    result["score"] = int(result["score"])
    return result

def _load_prompt(filename: str) -> Template:
    return Template((_PROMPT_DIR / filename).read_text(encoding="utf-8"))

def eval(model):
    lecture_ids = os.listdir(OUTPUT_DIR)
    val_saves = []
    for lecture_id in tqdm(lecture_ids, desc="Evaluating lectures"):
        if not os.path.exists(CONTEXT_DIR / f"{lecture_id}.json"):
            print("Not have information of:", lecture_id)
            continue
        if lecture_id == ".gitkeep":
            print("Skipping .gitkeep")
            continue
        save_path = OUTPUT_DIR / lecture_id / f"{model}" / f"eval_{lecture_id}.json"
        if save_path.exists():
            print("Skipping lecture", lecture_id)
            with save_path.open("r", encoding="utf-8") as f:
                val_save = json.load(f)
            val_saves.append(val_save)
            continue
        else:
            context_path = CONTEXT_DIR / f"{lecture_id}.json"
            output_lecture_path = OUTPUT_DIR / lecture_id / f"{model}" / f"{lecture_id}.json"
            slide_image_path = OUTPUT_DIR / lecture_id / model / "slide_images"
            source_text = parse_full_text(context_path)
            presentation = parse_full_slides(output_lecture_path)
            rouge_score_val = rouge_l_score(source_text, presentation)        
            content_score_val = content_score(slide_image_path)
            design_score_val = design_score(slide_image_path)
            coherence_score_val = coherence_score(presentation)
        
            val_save = {
                "rouge_score": rouge_score_val,
                "content_score": content_score_val,
                "design_score": design_score_val,
                "coherence_score": coherence_score_val,
            }
            val_saves.append(val_save)
            json.dump(val_save, open(save_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("======== ALL EVALUATION=======\n")
    if not val_saves:
        print("No evaluations completed.")
        return
    print("Average Rouge Score:", sum([val["rouge_score"] for val in val_saves]) / len(val_saves))
    print("Average Content Score:", sum([val["content_score"] for val in val_saves]) / len(val_saves))
    print("Average Design Score:", sum([val["design_score"] for val in val_saves]) / len(val_saves))
    print("Average Coherence Score:", sum([val["coherence_score"] if isinstance(val["coherence_score"], int) else val["coherence_score"]["score"] for val in val_saves]) / len(val_saves))

def main():
    parser = argparse.ArgumentParser(description="Evaluation with PPTEval Framework")
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    eval(args.model)

if __name__ == "__main__":
    main()