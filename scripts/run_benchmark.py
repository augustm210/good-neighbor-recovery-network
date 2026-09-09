from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from good_neighbor.evaluation import run_benchmark  # noqa: E402
from good_neighbor.scenario import load_demo_scenario  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic 60-case benchmark")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    report = run_benchmark(scenario)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
