from sqleval.sql_utils import extract_sql, is_read_only, says_cannot_answer


def test_extracts_sql_from_code_block():
    reply = "Here you go:\n```sql\nSELECT COUNT(*) FROM orders;\n```\nThis counts orders."
    assert extract_sql(reply) == "SELECT COUNT(*) FROM orders"


def test_extracts_sql_without_code_block():
    assert extract_sql("The query is: SELECT 1;") == "SELECT 1"


def test_no_sql_returns_none():
    assert extract_sql("I am not sure.") is None


def test_detects_cannot_answer():
    assert says_cannot_answer("CANNOT_ANSWER")
    assert not says_cannot_answer("```sql\nSELECT 1\n```")


def test_read_only_accepts_select_and_with():
    assert is_read_only("SELECT * FROM orders")
    assert is_read_only("WITH t AS (SELECT 1) SELECT * FROM t")
    assert is_read_only("SELECT created_at, updated_at FROM customers")  # 'create' inside a word is fine


def test_read_only_rejects_writes_and_multiple_statements():
    assert not is_read_only("DELETE FROM orders")
    assert not is_read_only("SELECT 1; DROP TABLE orders")
    assert not is_read_only("WITH d AS (DELETE FROM orders RETURNING *) SELECT * FROM d")


def test_comments_are_removed():
    reply = "```sql\n-- Count customers; simple\nSELECT COUNT(*) /* all rows */ FROM customers;\n```"
    sql = extract_sql(reply)
    assert sql == "SELECT COUNT(*)   FROM customers"
    assert is_read_only(sql)
