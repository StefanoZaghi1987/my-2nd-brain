#!/usr/bin/env python3
"""chart.py — Generate a chart PNG for a vault view.

Writes the PNG to wiki/views/assets/ under the vault root so the output
lands alongside other view assets, not next to this template file.

Adapt TITLE, XLABEL, YLABEL, labels, and values for each chart you need.
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def build_chart(vault_root: Path, output_name: str = "chart.png") -> Path:
    """Generate the chart and return the path of the written PNG."""
    output_dir = vault_root / "wiki" / "views" / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Customise below -------------------------------------------------
    TITLE = "Chart title"
    XLABEL = "X"
    YLABEL = "Y"
    labels = ["A", "B", "C"]
    values = [12, 19, 7]
    # --- End customisation -----------------------------------------------

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values)
    ax.set_title(TITLE)
    ax.set_xlabel(XLABEL)
    ax.set_ylabel(YLABEL)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    out = output_dir / output_name
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a chart PNG for a vault view.")
    parser.add_argument(
        "--vault", type=Path, default=Path.cwd(),
        help="Vault root directory (default: current directory)",
    )
    parser.add_argument(
        "--output", default="chart.png",
        help="Output filename (default: chart.png)",
    )
    args = parser.parse_args()
    out = build_chart(args.vault, args.output)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
