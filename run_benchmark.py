import os
import time
from src.utils.config import Config

def run_benchmark():
    print('=' * 60)
    print('STARTING BENCHMARK PIPELINE')
    print('=' * 60)
    print("\n[1/2] GENERATING SLIDES FOR ALL DOCUMENTS IN 'data/raw/'...")
    ret_gen = os.system('python -m main')
    if ret_gen != 0:
        print('\nWarning: Some slides failed to generate. Proceeding to evaluation for completed tasks.')
    model_name = (Config.LLM_MODEL_NAME or 'unknown_model').replace('/', '_')
    print('\n[2/2] EVALUATING WITH LLM-AS-A-JUDGE (PPTEVAL)...')
    print(f'Target Directory Model: {model_name}\n')
    ret_eval = os.system(f'python -m src.evaluation.eval --model {model_name}')
    print('\n' + '=' * 60)
    if ret_eval == 0:
        print('BENCHMARK COMPLETED SUCCESSFULLY')
    else:
        print('BENCHMARK FINISHED WITH ERRORS (EVALUATION FAILED)')
    print('=' * 60)
if __name__ == '__main__':
    run_benchmark()