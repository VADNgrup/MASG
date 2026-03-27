"""
Batch processor for multimodal_processing.
Scans a folder of JSON files and runs:
    python -m src.multimodal.multimodal_processing --lecture data/lectures/<file>
sequentially for each file.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch run multimodal_processing on a folder of JSON files."
    )
    parser.add_argument(
        "--input-dir",
        default="data/lectures",
        help="Folder containing lecture JSON files to process (default: data/lectures)",
    )
    parser.add_argument(
        "--pattern",
        default="*.json",
        help="Glob pattern to match JSON files (default: *.json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N files (default: all)",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Continue processing remaining files even if one fails",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"[ERROR] '{input_dir}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(input_dir.glob(args.pattern))

    if not json_files:
        print(f"[WARN] No files matching '{args.pattern}' found in '{input_dir}'.")
        return

    if args.limit is not None:
        json_files = json_files[: args.limit]

    total = len(json_files)
    print(f"\n{'='*60}")
    print(f"Batch Multimodal Processing")
    print(f"{'='*60}")
    print(f"Directory : {input_dir.resolve()}")
    print(f"Files found: {total}\n")

    failed = []

    for i, json_file in enumerate(json_files, start=1):
        # Build the lecture path relative to project root (e.g. data/lectures/file.json)
        lecture_path = input_dir / json_file.name
        print(f"[{i}/{total}] Processing: {json_file.name}")
        print(f"  Command: python -m src.multimodal.multimodal_processing --lecture {lecture_path}")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.multimodal.multimodal_processing",
                "--lecture",
                str(lecture_path),
            ],
            # Inherit the current working directory so module imports resolve correctly
        )

        if result.returncode != 0:
            print(f"  [FAILED] Exit code {result.returncode}\n")
            failed.append(json_file.name)
            if not args.skip_errors:
                print("[ERROR] Stopping batch due to failure. Use --skip-errors to continue on errors.")
                sys.exit(result.returncode)
        else:
            print(f"  [OK]\n")

    # Summary
    print(f"{'='*60}")
    print(f"Batch Complete: {total - len(failed)}/{total} succeeded")
    if failed:
        print(f"Failed files ({len(failed)}):")
        for name in failed:
            print(f"  - {name}")
    print(f"{'='*60}\n")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
