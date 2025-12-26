# This repository contains ideas for lecture generation

```bash
# 1. Extract document context
python extract_file.py --input data/raw/{name_file}.{type_file}

# 2. Generate lecture with smart metadata
python preprocessing_context.py --context data/context/{doc_id}.json
```