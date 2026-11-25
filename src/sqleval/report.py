"""Combine all runs into a summary table, a chart and a sheet for manual error review.

    python -m sqleval.report
"""
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")  # draw charts to files, no window needed
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
DIFFICULTY_ORDER = ["easy", "medium", "hard", "unanswerable"]


def load_runs():
    files = sorted((RESULTS / "runs").glob("*.csv"))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df = df[df["model"] != "gold"]  # the self-check is not a real model
    df["run"] = df["model"] + " / " + df["prompt"]
    return df


def pct(series):
    return f"{series.mean():.0%} ({int(series.sum())}/{len(series)})"


def main():
    df = load_runs()

    failures = df[~df["correct"]]

    # Review sheet: every failure, with empty columns for a human to fill in.
    review_file = RESULTS / "error_review.csv"
    review = failures[["run", "id", "difficulty", "question", "error_type", "error_message", "sql"]].copy()
    review["root_cause"] = ""
    review["notes"] = ""
    if review_file.exists():  # keep any review work already done
        done = pd.read_csv(review_file).fillna("")
        review = review.drop(columns=["root_cause", "notes"]).merge(
            done[["run", "id", "root_cause", "notes"]], on=["run", "id"], how="left").fillna("")
    review.to_csv(review_file, index=False)

    # Human-adjusted score: a failure the reviewer marked 'format_only' was a correct answer
    # in a different format (e.g. month as 2026-01-01 instead of 1), so it counts as correct.
    format_only = review.loc[review["root_cause"] == "format_only", ["run", "id"]]
    keys = set(zip(format_only["run"], format_only["id"]))
    reviewed_ok = df.apply(lambda row: (row["run"], row["id"]) in keys, axis=1)
    df["adjusted"] = df["correct"] | reviewed_ok

    overall = df.groupby("run")["correct"].agg(pct).rename("automatic")
    adjusted = df.groupby("run")["adjusted"].agg(pct).rename("after human review")
    by_level = df.pivot_table(index="run", columns="difficulty", values="correct", aggfunc=pct)
    by_level = by_level[[c for c in DIFFICULTY_ORDER if c in by_level.columns]]
    summary = pd.concat([overall, adjusted, by_level], axis=1)

    error_counts = failures.pivot_table(index="error_type", columns="run", values="id",
                                        aggfunc="count", fill_value=0)

    cost = df.groupby("run")[["seconds", "prompt_tokens", "completion_tokens"]].mean().round(1)
    cost.columns = ["avg seconds", "avg prompt tokens", "avg answer tokens"]

    md = ["# Results\n", "## Accuracy\n", "Difficulty columns show the automatic score.\n", summary.to_markdown(), "\n",
          "## Failure types\n", error_counts.to_markdown(), "\n",
          "## Speed and size per question\n", cost.to_markdown(), "\n"]
    (RESULTS / "summary.md").write_text("\n".join(md), encoding="utf-8")

    # Chart: accuracy by difficulty for each run.
    chart = df.pivot_table(index="difficulty", columns="run", values="correct", aggfunc="mean")
    chart = chart.reindex([d for d in DIFFICULTY_ORDER if d in chart.index]) * 100
    # 'Paired' colours: light then dark shade per model, so v1 -> v2 of one model share a colour.
    ax = chart.plot(kind="bar", figsize=(9, 5.5), rot=0, width=0.8,
                    color=plt.cm.Paired.colors[: len(chart.columns)])
    ax.set_ylabel("Accuracy (%)")
    ax.set_xlabel("")
    ax.set_ylim(0, 105)
    ax.set_title("Text-to-SQL accuracy by question difficulty")
    ax.legend(title="", fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.07))
    plt.tight_layout()
    plt.savefig(RESULTS / "accuracy_by_difficulty.png", dpi=150)

    print(summary.to_string())
    print(f"\nWrote summary.md, accuracy_by_difficulty.png and error_review.csv ({len(review)} failures)")


if __name__ == "__main__":
    main()
