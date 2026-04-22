import sys
import os
import json
import argparse
from pathlib import Path

from extractor import extract_text_from_file
from agent import process_claim


def show_result(result, filename):
    print("\n" + "-" * 55)
    print(f"File: {filename}")
    print("-" * 55)
    print(json.dumps(result, indent=2))
    print(f"\nRoute  : {result['recommendedRoute']}")
    print(f"Reason : {result['reasoning']}")
    if result["missingFields"]:
        print(f"Missing: {', '.join(result['missingFields'])}")
    print("-" * 55)


def main():
    parser = argparse.ArgumentParser(description="FNOL Claims Processing Agent")
    parser.add_argument("input", nargs="?", help="Path to a single FNOL file")
    parser.add_argument("--batch", metavar="FOLDER", help="Process all files in a folder")
    parser.add_argument("--demo", action="store_true", help="Run the 5 sample FNOL files")
    parser.add_argument("--output", metavar="FILE", help="Save results to a JSON file")
    args = parser.parse_args()

    results = []

    if args.demo or args.batch:
        folder = Path(".") if args.demo else Path(args.batch)
        files = sorted(folder.glob("*.txt")) + sorted(folder.glob("*.pdf"))
        if not files:
            print(f"No files found in {folder}")
            sys.exit(1)
        for f in files:
            text = extract_text_from_file(str(f))
            result = process_claim(text, f.name)
            show_result(result, f.name)
            results.append(result)

    elif args.input:
        if not os.path.exists(args.input):
            print(f"File not found: {args.input}")
            sys.exit(1)
        text = extract_text_from_file(args.input)
        result = process_claim(text, args.input)
        show_result(result, args.input)
        results.append(result)

    else:
        parser.print_help()

    if args.output and results:
        data = results[0] if len(results) == 1 else results
        with open(args.output, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()