from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(step_name: str, cmd: list[str], cwd: Path) -> None:
    print(f"[STEP] {step_name}")
    print("       ", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(cwd))
    if completed.returncode != 0:
        raise RuntimeError(f"Step failed: {step_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full SmartSpend research pipeline.")
    parser.add_argument("--dataset", default="data/transactions.csv")
    parser.add_argument("--seed", default="42")
    parser.add_argument("--notebook", default="notebooks/finset_research_demo_clean.ipynb")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parents[1]

    run(
        "Train models and generate artifacts",
        [
            "python",
            "src/train.py",
            "--dataset",
            args.dataset,
            "--seed",
            args.seed,
            "--run-tag",
            "pipeline-auto",
        ],
        project_dir,
    )

    run(
        "Evaluate latest model",
        [
            "python",
            "src/evaluate.py",
            "--dataset",
            args.dataset,
            "--seed",
            args.seed,
            "--run-tag",
            "pipeline-auto-eval",
        ],
        project_dir,
    )

    run(
        "Export notebook report",
        [
            "python",
            "scripts/export_notebook.py",
            "--notebook",
            args.notebook,
            "--output-dir",
            "reports",
        ],
        project_dir,
    )

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()

