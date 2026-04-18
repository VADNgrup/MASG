import json
import os
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from src.utils.config import Config

def summarize():
    parser = argparse.ArgumentParser(description='Summarize performance from LLM call logs and evaluation results.')
    parser.add_argument('--log', type=str, default=None, help='Path to the llm_calls.jsonl file. If not provided, uses current model log.')
    args = parser.parse_args()

    if args.log:
        log_path = Path(args.log)
    else:
        log_path = Config.get_log_path()
        
    output_dir = Config.OUTPUT_DIR

    if not log_path.exists():
        print(f'Không tìm thấy file log: {log_path}')
        return

    model_filter = "*"
    if args.log:
        log_name = Path(args.log).stem
        if "llm_calls_" in log_name:
            model_filter = log_name.replace("llm_calls_", "")
    
    eval_files_list = list(output_dir.glob(f"{model_filter}/**/eval_*.json"))
    if not eval_files_list:
        eval_files_list = list(output_dir.glob("**/eval_*.json"))

    eval_start_ts = 0
    if eval_files_list:
        eval_start_ts = min((os.path.getmtime(f) for f in eval_files_list))

    total_calls_gen = 0
    total_tokens_gen = 0
    total_time_gen = 0
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                total_calls_gen += 1
                usage = data.get('token_usage', {})
                total_tokens_gen += usage.get('total_tokens', 0)
                total_time_gen += data.get('elapsed_s', 0)
            except:
                continue

    all_lectures = [d for d in output_dir.glob(f"{model_filter}/*") if d.is_dir()]
    if not all_lectures:
        all_lectures = [d for d in output_dir.iterdir() if d.is_dir()]

    success_count = 0
    for lec_dir in all_lectures:
        pdf_files = list(lec_dir.glob('**/*-export.pdf'))
        if pdf_files:
            success_count += 1

    total_attempted = len(all_lectures)
    failed_count = total_attempted - success_count

    eval_files = list(output_dir.glob(f"{model_filter}/**/eval_*.json"))
    if not eval_files:
        eval_files = list(output_dir.glob("**/eval_*.json"))
    avg_metrics = defaultdict(float)
    count_metrics = 0
    for ef in eval_files:
        try:
            with open(ef, 'r', encoding='utf-8') as f:
                e_data = json.load(f)
                avg_metrics['rouge'] += e_data.get('rouge_score', 0)
                avg_metrics['content'] += e_data.get('content_score', 0)
                avg_metrics['design'] += e_data.get('design_score', 0)
                c_score = e_data.get('coherence_score', {})
                avg_metrics['coherence'] += c_score if isinstance(c_score, (int, float)) else c_score.get('score', 0)
                count_metrics += 1
        except:
            continue

    if count_metrics > 0:
        for k in avg_metrics:
            avg_metrics[k] /= count_metrics

    avg_call = total_calls_gen / success_count if success_count > 0 else 0
    avg_token_k = total_tokens_gen / success_count / 1000 if success_count > 0 else 0
    avg_done_time_m = total_time_gen / success_count / 60 if success_count > 0 else 0

    print('\n' + '=' * 40)
    print('   GENERATION PERFORMANCE')
    print('=' * 40)
    print(f"Log source: {log_path.name}")
    print(f"{'Metric':<25} | {'Value':<10}")
    print('-' * 40)
    print(f"{'Call (Avg)':<25} | {avg_call:.1f}")
    print(f"{'Total Token per output':<25} | {avg_token_k:.1f}")
    print(f"{'Failed':<25} | {failed_count}")
    print(f"{'Done time (m)':<25} | {avg_done_time_m:.2f}")
    print(f"{'Success Rate':<25} | {(success_count / total_attempted * 100 if total_attempted > 0 else 0):.2f}%")
    print('-' * 40)
    print(f"{'ROUGE-L':<25} | {avg_metrics['rouge'] * 100:.2f}")
    print(f"{'Content':<25} | {avg_metrics['content']:.2f}")
    print(f"{'Design':<25} | {avg_metrics['design']:.2f}")
    print(f"{'Coherence':<25} | {avg_metrics['coherence']:.2f}")
    print('=' * 40)

if __name__ == '__main__':
    summarize()