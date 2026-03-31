from src.extractor.extract_file import extract_file
from src.preprocessor.preprocessing_context import preprocess_context
from src.multimodal.multimodal_processing import multimodal_processing
from src.generator.slide_gen import run_pipeline as slide_gen
from src.utils.config import Config

import os
import argparse
import asyncio

def gen_slide(document_path, lecture_title, speaker_information):
    parsed_context_path = extract_file(document_path)
    lecture_path = asyncio.run(preprocess_context(parsed_context_path))
    multimodal_processing(lecture_path)
    slide_gen(lecture_path, lecture_title, speaker_information)

def main():
    parser = argparse.ArgumentParser(
        description="End-to-End Lecture Slide Generation Slide from a document/old lecture slides"
    )
    parser.add_argument("--document_path", required=True, help="Path to input PDF/Docx file")
    parser.add_argument("--lecture_title", default=None, help="Customized title of the lecture")
    parser.add_argument("--speaker_information", default=None, help="Speaker information")

    args = parser.parse_args()
    default_document_folder = Config.RAW_DIR
    document_path = args.document_path
    lecture_title = args.lecture_title
    speaker_information = args.speaker_information

    if document_path is None and lecture_title is None:
        document_list = os.listdir(default_document_folder)
        for document_name in document_list:
            if document_name.endswith(".pdf"):
                a_document_path = os.path.join(default_document_folder, document_name)
                gen_slide(a_document_path, lecture_title, speaker_information)
    elif document_path:
        gen_slide(document_path, lecture_title, speaker_information)
    else:
        print("Your arguments is FAILED, let's read my README.md")

if __name__ == "__main__":
    main()
    