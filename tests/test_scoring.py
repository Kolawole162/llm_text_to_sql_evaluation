from decimal import Decimal

from sqleval.scoring import results_match


def test_same_numbers_different_types_match():
    assert results_match([(Decimal("34018.47"),)], [(34018.4709,)])


def test_text_ignores_case_and_spaces():
    assert results_match([("Monday",)], [("monday   ",)])


def test_row_order_ignored_unless_required():
    gold = [("Lagos", 2), ("Abuja", 1)]
    pred = [("Abuja", 1), ("Lagos", 2)]
    assert results_match(gold, pred)
    assert not results_match(gold, pred, order_matters=True)


def test_column_order_ignored():
    assert results_match([("Lagos", 2)], [(2, "Lagos")])


def test_extra_columns_allowed():
    gold = [("9 Ring Road",)]
    pred = [(5, "9 Ring Road", Decimal("38471800.00"))]
    assert results_match(gold, pred)


def test_missing_column_fails():
    assert not results_match([("Lagos", 2)], [("Lagos",)])


def test_wrong_row_count_fails():
    assert not results_match([(1,), (2,)], [(1,)])


def test_columns_must_stay_paired_across_rows():
    # Each column alone matches, but the rows are mixed up: must fail.
    gold = [("Lagos", 2), ("Abuja", 1)]
    pred = [("Lagos", 1), ("Abuja", 2)]
    assert not results_match(gold, pred)


def test_null_is_not_zero():
    assert not results_match([(None,)], [(0,)])