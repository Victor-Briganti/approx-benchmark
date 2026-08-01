"""Speedup comparison visualization script for benchmark applications.

This module reads benchmark performance data from a DuckDB database and generates
a publication-ready grouped bar chart comparing the average speedup achieved by each
technique (including non-approximated execution labeled 'no-approx') across different thread counts,
aggregated over all applications.
"""

import argparse
from pathlib import Path
import sys
from typing import Sequence

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def get_database_path(args: Sequence[str] | None = None) -> Path:
    """Parse command line arguments to retrieve the database file path.

    Args:
        args: Optional sequence of argument strings. Defaults to sys.argv[1:].

    Returns:
        Path object pointing to the database file.
    """
    parser = argparse.ArgumentParser(
        description="Plot average speedup per technique across thread counts."
    )
    parser.add_argument(
        "db_path",
        nargs="?",
        type=Path,
        default=Path("database_v1.db"),
        help="Path to the DuckDB database file (default: database_v1.db)",
    )
    parsed_args = parser.parse_args(args)
    return parsed_args.db_path


def fetch_speedup_data(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Query benchmark results and compute average speedup per thread count and technique.

    Includes both approximation variants and non-approximated executions (labeled 'no-approx').
    Averages speedups across all benchmark applications.

    Args:
        conn: Active DuckDB connection.

    Returns:
        DataFrame containing number of threads, technique (approx_type), and mean speedup.
    """
    query = """
        WITH baselines AS (
            SELECT 
                eg.bench_name, 
                AVG(p.value) AS base_elapsed
            FROM ExecutionGroup eg
            JOIN Performance p ON eg.id = p.group_id
            WHERE eg.type = 'omp' 
              AND eg.num_threads = 1 
              AND p.name = 'elapsed'
            GROUP BY eg.bench_name
        ),
        all_app_speedups AS (
            SELECT 
                eg.bench_name,
                eg.approx_type AS technique,
                eg.num_threads,
                (b.base_elapsed / AVG(p.value)) AS speedup
            FROM ExecutionGroup eg
            JOIN Performance p ON eg.id = p.group_id
            JOIN baselines b ON eg.bench_name = b.bench_name
            WHERE eg.approx_type IS NOT NULL
              AND p.name = 'elapsed'
            GROUP BY eg.bench_name, eg.approx_type, eg.num_threads, b.base_elapsed

            UNION ALL

            SELECT 
                eg.bench_name,
                'no-approx' AS technique,
                eg.num_threads,
                (b.base_elapsed / AVG(p.value)) AS speedup
            FROM ExecutionGroup eg
            JOIN Performance p ON eg.id = p.group_id
            JOIN baselines b ON eg.bench_name = b.bench_name
            WHERE eg.type = 'omp'
              AND p.name = 'elapsed'
            GROUP BY eg.bench_name, eg.num_threads, b.base_elapsed
        )
        SELECT 
            num_threads,
            technique AS approx_type,
            AVG(speedup) AS speedup
        FROM all_app_speedups
        GROUP BY num_threads, technique
        ORDER BY num_threads, approx_type;
    """
    return conn.execute(query).df()


def plot_speedup_comparison(df: pd.DataFrame, output_path: Path) -> None:
    """Generate and save the figure formatted for document insertion.

    Args:
        df: DataFrame containing the aggregated speedup data.
        output_path: Path where the resulting PDF figure will be saved.
    """
    if df.empty:
        raise ValueError("The provided DataFrame is empty. Cannot generate plot.")

    threads = sorted(df["num_threads"].unique())
    # Order techniques putting 'no-approx' first as baseline reference if present
    raw_techniques = df["approx_type"].unique()
    techniques = sorted([t for t in raw_techniques if t != "no-approx"])
    if "no-approx" in raw_techniques:
        techniques = ["no-approx"] + techniques

    # Curated vivid color palette for techniques
    vivid_colors = [
        "#7f7f7f",  # Neutral Gray for no-approx baseline
        "#1f77b4",  # Vivid Blue
        "#ff7f0e",  # Vivid Orange
        "#2ca02c",  # Vivid Green
        "#d62728",  # Vivid Red
        "#9467bd",  # Vivid Purple
        "#17becf",  # Vivid Cyan
    ]

    technique_color_map = {
        tech: vivid_colors[i % len(vivid_colors)] for i, tech in enumerate(techniques)
    }

    # Document-tailored figure dimensions (8.2 x 4.8 inches)
    fig_width = 8.2
    fig_height = 4.8
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    group_width = 0.84
    bar_width = group_width / len(techniques)
    x_indices = np.arange(len(threads))

    # Plot bars for each technique
    for t_idx, tech in enumerate(techniques):
        tech_df = df[df["approx_type"] == tech]
        speedup_map = dict(zip(tech_df["num_threads"], tech_df["speedup"]))
        y_values = [speedup_map.get(th, 0.0) for th in threads]

        offset = (t_idx - (len(techniques) - 1) / 2) * bar_width
        bars = ax.bar(
            x_indices + offset,
            y_values,
            width=bar_width,
            color=technique_color_map[tech],
            edgecolor="black",
            linewidth=0.7,
            label=tech,
        )

        # Rotated data value labels on top of bars
        ax.bar_label(
            bars,
            fmt="%.2f",
            padding=3,
            fontsize=10.0,
            fontweight="bold",
            rotation=90,
        )

    # Document-proportional titles and labels
    ax.set_title(
        "Speedup por Técnica de Aproximação e Número de Threads",
        fontsize=13.5,
        fontweight="bold",
        pad=14,
    )
    ax.set_xlabel("Número de Threads", fontsize=12.5, fontweight="bold", labelpad=6)
    ax.set_ylabel("Speedup", fontsize=12.5, fontweight="bold", labelpad=6)

    # Tick labels
    thread_labels = [f"{th} Thread{'s' if th > 1 else ''}" for th in threads]
    ax.set_xticks(x_indices)
    ax.set_xticklabels(thread_labels, fontsize=11.5, fontweight="bold")
    ax.tick_params(axis="y", labelsize=11)

    # Grid styling
    ax.grid(axis="y", linestyle="--", alpha=0.6, linewidth=0.7)
    ax.set_axisbelow(True)

    # Legend placement
    ax.legend(
        title="Técnica de Aproximação",
        title_fontsize=10.5,
        fontsize=9.5,
        loc="upper left",
        frameon=True,
        edgecolor="gray",
    )

    # Y-axis headroom for bar value labels
    y_max = df["speedup"].max()
    ax.set_ylim(0, y_max * 1.25)

    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    """Main entry point for database querying and plot generation."""
    db_path = get_database_path()
    if not db_path.exists():
        print(f"Error: Database file '{db_path}' not found.", file=sys.stderr)
        sys.exit(1)

    output_file = Path("speedup_comparison.pdf")

    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            df = fetch_speedup_data(conn)
    except Exception as exc:
        print(f"Error connecting to database or querying data: {exc}", file=sys.stderr)
        sys.exit(1)

    plot_speedup_comparison(df, output_file)
    print(f"Successfully saved figure to '{output_file}'")


if __name__ == "__main__":
    main()
