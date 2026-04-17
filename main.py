import time
import logging
from src.extractor.extract_file import extract_file
from src.preprocessor.preprocessing_context import preprocess_context
from src.multimodal.multimodal_processing import multimodal_processing
from src.generator.slide_gen import run_pipeline as slide_gen
from src.utils.config import Config
import os
import argparse
import asyncio
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')

def gen_slide(document_path, lecture_title, speaker_information):
    print('Start time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    start_time = time.time()
    parsed_context_path = extract_file(document_path)
    t1 = time.time()
    print(f'[timer] extract_file: {t1 - start_time:.2f}s')
    (lecture_path, len_condition) = asyncio.run(preprocess_context(parsed_context_path))
    t2 = time.time()
    print(f'[timer] preprocess_context: {t2 - t1:.2f}s')
    if len_condition == False:
        return
    multimodal_processing(lecture_path)
    t3 = time.time()
    print(f'[timer] multimodal: {t3 - t2:.2f}s')
    slide_gen(lecture_path, lecture_title, speaker_information)
    t4 = time.time()
    print(f'[timer] slidegen: {t4 - t3:.2f}s')
    end_time = t4
    print('End time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    return end_time - start_time

def main():
    parser = argparse.ArgumentParser(description='End-to-End Lecture Slide Generation Slide from a document/old lecture slides')
    parser.add_argument('--document_path', default=None, help='Path to input PDF/Docx file')
    parser.add_argument('--lecture_title', default=None, help='Customized title of the lecture')
    parser.add_argument('--speaker_information', default=None, help='Speaker information')
    parser.add_argument('--limit', help='Limit the number of documents to process')
    args = parser.parse_args()
    default_document_folder = Config.RAW_DIR
    document_path = args.document_path
    lecture_title = args.lecture_title
    speaker_information = args.speaker_information
    limit = int(args.limit) if args.limit is not None else len(os.listdir(default_document_folder))
    if document_path is None and lecture_title is None:
        document_list = os.listdir(default_document_folder)
        count = 1
        for document_name in document_list:
            if document_name.endswith('.pdf') and count <= limit:
                print(f'\nProcessing {count}/{limit}: {document_name} \n')
                a_document_path = os.path.join(default_document_folder, document_name)
                time_taken = gen_slide(a_document_path, lecture_title, speaker_information)
                print(f'[full time taken] {time_taken}s')
                count += 1
                if not time_taken:
                    continue
                if time_taken > 120:
                    print('[main] Waiting 1 minutes before next document...')
                    time.sleep(60)
    elif document_path:
        print(f'\nProcessing {document_path} \n')
        time_taken = gen_slide(document_path, lecture_title, speaker_information)
        print(f'[full time taken] {time_taken}s')
    else:
        print("Your arguments is FAILED, let's read my README.md")
if __name__ == '__main__':
    main()