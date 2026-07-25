import json
from pathlib import Path
from typing import List


def create_notebook(output_path: str | Path, title: str, steps: List[str]) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and output_path.is_dir():
        raise IsADirectoryError(f"Output path is a directory: {output_path}")

    cells = []

    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [f"# {title}\n", "\n", "---\n"]
    })

    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["\n", "---\n", "\n"]
    })

    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## ATTRITION STEPS\n", "\n"]
    })

    numbered_steps = []
    for idx, step in enumerate(steps, start=1):
        numbered_steps.append(f"{idx}. {step}\n")

    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": numbered_steps
    })

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.13"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    output_path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
    return output_path
