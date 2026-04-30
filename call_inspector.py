import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

log_file = Path("logs/llm_calls_qwen35.jsonl")
end_time = datetime.fromisoformat("2026-04-30T15:51:49+00:00")
start_time = end_time - timedelta(seconds=368)

with open(log_file, "r") as f:
    for line in f:
        try:
            data = json.loads(line)
            log_time = datetime.fromisoformat(data["time"])
            if start_time <= log_time <= end_time:
                print(f"Time: {data['time']} | Model: {data['model']} | Duration: {data.get('elapsed_s', 0)}s")
        except:
            continue
