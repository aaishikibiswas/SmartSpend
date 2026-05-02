from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path) -> int:
    print("Running:", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(cwd))
    return completed.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Export notebook to HTML and PDF.")
    parser.add_argument("--notebook", default="notebooks/finset_research_demo_clean.ipynb")
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parents[1]
    nb_path = (project_dir / args.notebook).resolve()
    output_dir = (project_dir / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not nb_path.exists():
        raise FileNotFoundError(f"Notebook not found: {nb_path}")

    # HTML export (reliable in most environments)
    html_cmd = [
        sys.executable,
        "-m",
        "nbconvert",
        "--to",
        "html",
        str(nb_path),
        "--output-dir",
        str(output_dir),
    ]
    rc_html = run_cmd(html_cmd, project_dir)
    if rc_html != 0:
        raise RuntimeError("HTML export failed.")

    # PDF export (can fail if LaTeX is unavailable)
    pdf_cmd = [
        sys.executable,
        "-m",
        "nbconvert",
        "--to",
        "pdf",
        str(nb_path),
        "--output-dir",
        str(output_dir),
    ]
    rc_pdf = run_cmd(pdf_cmd, project_dir)
    if rc_pdf != 0:
        print("PDF export skipped/failure detected (likely missing LaTeX). HTML export completed.")
    else:
        print("PDF export completed.")


if __name__ == "__main__":
    main()
