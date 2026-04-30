import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

log_file = Path("logs/llm_calls_qwen35.jsonl")

# Mốc thời gian từ log của bạn
end_time = datetime.fromisoformat("2026-04-30T15:51:49+00:00")
start_time = end_time - timedelta(seconds=368) # 367s + 1s buffer

stats = []
with open(log_file, "r") as f:
    for line in f:
        try:
            data = json.loads(line)
            log_time = datetime.fromisoformat(data["time"])
            if start_time <= log_time <= end_time:
                stats.append(data)
        except:
            continue

total_prompt = sum(s.get("token_usage", {}).get("prompt_tokens", 0) for s in stats)
total_completion = sum(s.get("token_usage", {}).get("completion_tokens", 0) for s in stats)
total_calls = len(stats)
total_time_llm = sum(s.get("elapsed_s", 0) for s in stats)

print(f"--- FINAL Statistics for Ch03_Keep calm (Full Run) ---")
print(f"Total Time Taken: 367.43s")
print(f"Total LLM Calls: {total_calls}")
print(f"Total Prompt Tokens: {total_prompt:,}")
print(f"Total Completion Tokens: {total_completion:,}")
print(f"Total Tokens: {total_prompt + total_completion:,}")
print(f"LLM Processing Time: {total_time_llm:.2f}s")
print(f"Wait/Other Time (IO/Images/VLM): {367.43 - total_time_llm:.2f}s")
if total_calls > 0:
    print(f"Avg Tokens/Call: {(total_prompt + total_completion)/total_calls:,.2f}")
