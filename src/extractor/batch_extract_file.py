import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Batch Phase 1: Run extract_file.py on all PDFs in a directory"
    )
    parser.add_argument(
        "--batch_pdf_path",
        required=True,
        help="Path to the directory containing PDF files",
    )
    args = parser.parse_args()

    batch_pdf_path = Path(args.batch_pdf_path)
    if not batch_pdf_path.is_dir():
        print(f"Error: Directory not found: {batch_pdf_path}")
        sys.exit(1)

    pdf_files = sorted(batch_pdf_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in: {batch_pdf_path}")
        sys.exit(0)

    print(f"Found {len(pdf_files)} PDF file(s) in '{batch_pdf_path}'")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for idx, pdf_file in enumerate(pdf_files, start=1):
        print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
        print("-" * 60)

        cmd = [
            sys.executable, "-m", "src.extractor.extract_file",
            "--input", str(pdf_file),
        ]

        result = subprocess.run(cmd, cwd=batch_pdf_path.parent.parent.parent if False else None)

        if result.returncode == 0:
            print(f"✓ Done: {pdf_file.name}")
            success_count += 1
        else:
            print(f"✗ Failed: {pdf_file.name} (exit code {result.returncode})")
            fail_count += 1

    print("\n" + "=" * 60)
    print("BATCH SUMMARY")
    print("=" * 60)
    print(f"Total:   {len(pdf_files)}")
    print(f"Success: {success_count}")
    print(f"Failed:  {fail_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
