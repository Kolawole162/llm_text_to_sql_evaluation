"""Run the benchmark for one model and one prompt version, and save every result.

Examples:
    python -m sqleval.run_eval --model openai/gpt-oss-120b --prompt v2
    python -m sqleval.run_eval --model gold        # self-check: gold SQL must score 100%
    python -m sqleval.run_eval --model openai/gpt-oss-120b --prompt v1 --rescore
        # re-mark the saved replies with the current scorer (no API calls)
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import yaml
from sqlalchemy.exc import DBAPIError

from sqleval.db import get_engine, run_sql
from sqleval.prompts import PROMPTS
from sqleval.scoring import classify_db_error, results_match
from sqleval.sql_utils import CANNOT_ANSWER, extract_sql, is_read_only, says_cannot_answer

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "eval" / "questions.yaml"
RUNS_DIR = ROOT / "results" / "runs"


def load_questions():
    return yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))


def score(question, reply, engine):
    """Return (sql, correct, error_type, error_message) for one model reply."""
    answerable = question["gold_sql"] is not None

    if not answerable:
        if says_cannot_answer(reply):
            return None, True, "", ""
        return extract_sql(reply), False, "hallucinated_answer", "answered a question the data cannot support"

    if says_cannot_answer(reply):
        return None, False, "wrongly_refused", ""
    sql = extract_sql(reply)
    if sql is None:
        return None, False, "no_sql", ""
    if not is_read_only(sql):
        return sql, False, "unsafe_sql", "not a single read-only SELECT"

    try:
        _, pred_rows = run_sql(engine, sql)
    except DBAPIError as exc:
        message = str(exc.orig).strip().splitlines()[0] if exc.orig else str(exc)
        return sql, False, classify_db_error(exc), message

    _, gold_rows = run_sql(engine, question["gold_sql"])
    if results_match(gold_rows, pred_rows, question.get("order_matters", False)):
        return sql, True, "", ""
    if len(pred_rows) != len(gold_rows):
        return sql, False, "wrong_row_count", f"{len(pred_rows)} rows, expected {len(gold_rows)}"
    return sql, False, "wrong_values", ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Groq model ID, or 'gold' for the self-check")
    parser.add_argument("--prompt", default="v2", choices=sorted(PROMPTS))
    parser.add_argument("--pause", type=float, default=2.0, help="seconds between API calls")
    parser.add_argument("--limit", type=int, help="only run the first N questions (for testing)")
    parser.add_argument("--rescore", action="store_true",
                        help="re-mark replies already saved for this model and prompt, without new API calls")
    args = parser.parse_args()

    questions = load_questions()[: args.limit]
    engine = get_engine()
    out = RUNS_DIR / f"{args.model.replace('/', '_')}__{args.prompt}.csv"
    saved = pd.read_csv(out).set_index("id") if args.rescore else None
    rows = []

    for q in questions:
        if args.rescore:
            old = saved.loc[q["id"]]
            reply = None if pd.isna(old["reply"]) else old["reply"]
            usage = {"prompt_tokens": old["prompt_tokens"], "completion_tokens": old["completion_tokens"]}
            seconds = old["seconds"]
        elif args.model == "gold":
            reply = CANNOT_ANSWER if q["gold_sql"] is None else f"```sql\n{q['gold_sql']}\n```"
            usage, seconds = {}, 0.0
        else:
            from sqleval.llm import ask
            reply, usage, seconds = ask(args.model, PROMPTS[args.prompt](q["question"]))
            time.sleep(args.pause)

        sql, correct, error_type, error_message = score(q, reply, engine)
        print(f"{q['id']:4} {'PASS' if correct else 'FAIL':4} {error_type}")
        rows.append({
            "id": q["id"], "difficulty": q["difficulty"], "question": q["question"],
            "model": args.model, "prompt": args.prompt,
            "correct": correct, "error_type": error_type, "error_message": error_message,
            "sql": sql, "reply": reply, "seconds": round(seconds, 2),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
        })

    df = pd.DataFrame(rows)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nAccuracy: {df['correct'].mean():.1%} ({df['correct'].sum()}/{len(df)})  ->  {out}")

    # The self-check must be perfect; anything less means a gold query or the scorer is broken.
    if args.model == "gold" and not df["correct"].all():
        sys.exit(1)


if __name__ == "__main__":
    main()
