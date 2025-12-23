# This repository contains ideas for lecture generation

```bash
# 1. Extract document context
python main.py --input data/raw/Toan11.pdf

# 2. Generate lecture with smart metadata
python main_phase2.py --context data/context/{doc_id}.json
```