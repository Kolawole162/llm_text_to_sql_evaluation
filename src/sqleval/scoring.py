"""Decide whether a model's query result matches the gold result, and label failures.

Execution accuracy: two queries are judged equal when they return the same data,
even if they are written differently. Rules:
  * numbers are compared after rounding to 2 decimal places (Decimal 1 == int 1 == 1.0);
  * text is compared ignoring case and surrounding spaces ('Monday ' == 'monday');
  * column names and column order are ignored;
  * extra columns are allowed, as long as every gold column appears in the model's result;
  * row order is checked only when the question asks for an order (order_matters).
"""
from collections import Counter
from datetime import date, datetime, time
from decimal import Decimal
from itertools import product


def normalise(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return round(float(value), 2)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return str(value).strip().lower()


def _sort_key(value):
    # Sort mixed values (numbers, text, None) without errors.
    return (value is None, str(type(value)), value if value is not None else 0)


def _rows(rows):
    return [tuple(normalise(v) for v in row) for row in rows]


def _column(rows, index):
    return [row[index] for row in rows]


def results_match(gold_rows, pred_rows, order_matters=False):
    """True if the predicted rows contain the gold answer (see module docstring)."""
    gold, pred = _rows(gold_rows), _rows(pred_rows)
    if len(gold) != len(pred):
        return False
    if not gold:
        return True  # both empty
    n_gold, n_pred = len(gold[0]), len(pred[0])
    if n_pred < n_gold:
        return False

    def column_fits(g, p):
        gc, pc = _column(gold, g), _column(pred, p)
        if order_matters:
            return gc == pc
        return sorted(gc, key=_sort_key) == sorted(pc, key=_sort_key)

    # For each gold column, which predicted columns hold the same values?
    candidates = [[p for p in range(n_pred) if column_fits(g, p)] for g in range(n_gold)]
    if any(not c for c in candidates):
        return False

    # Try each way of pairing gold columns with matching predicted columns.
    for mapping in product(*candidates):
        if len(set(mapping)) < n_gold:
            continue  # one predicted column cannot stand in for two gold columns
        projected = [tuple(row[p] for p in mapping) for row in pred]
        if order_matters and projected == gold:
            return True
        if not order_matters and Counter(projected) == Counter(gold):
            return True
    return False


# PostgreSQL error codes -> failure labels.
PG_ERRORS = {
    "42601": "syntax_error",
    "42P01": "unknown_table",
    "42703": "unknown_column",
    "42883": "unknown_function",
    "42803": "grouping_error",
    "42804": "type_error",
    "42725": "ambiguous_function",
    "42702": "ambiguous_column",
    "57014": "timeout",
    "25006": "write_attempt",
}


def classify_db_error(exc):
    """Map a database exception to a failure label using its PostgreSQL error code."""
    code = getattr(getattr(exc, "orig", None), "pgcode", None)
    return PG_ERRORS.get(code, "other_db_error")