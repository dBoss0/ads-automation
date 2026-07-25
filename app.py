import argparse
from pathlib import Path

from ads_automation.parser import parse_protocol
from ads_automation.notebook_generator import create_notebook


def process_protocol(protocol_path: Path, output_dir: Path):
    if not protocol_path.exists():
        raise FileNotFoundError(f"Protocol file not found: {protocol_path}")

    result = parse_protocol(protocol_path)
    attrition_steps = result.get("attrition", [])
    if attrition_steps:
        display_steps = [f"({step[1].capitalize()}) {step[2]}" for step in attrition_steps]
    else:
        display_steps = [f"(Inclusion) {step}" for step in result.get("inclusion_steps", [])] + [f"(Exclusion) {step}" for step in result.get("exclusion_steps", [])]

    safe_title = "".join(ch if ch.isalnum() else "_" for ch in result["title"]).strip("_")
    if not safe_title:
        safe_title = "study"
    output_path = output_dir / f"{safe_title[:80]}_attrition.ipynb"
    create_notebook(output_path, result["title"], display_steps)

    print(f"Parsed study title: {result['title']}")
    print(f"Detected data sources: {result['data_sources']}")
    print(f"Notebook created at: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Parse a study protocol and create a notebook")
    parser.add_argument("protocol", type=str, help="Path to the protocol document")
    parser.add_argument("--output-dir", type=str, default="notebooks", help="Directory to store generated notebooks")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    process_protocol(Path(args.protocol), output_dir)


if __name__ == "__main__":
    main()
