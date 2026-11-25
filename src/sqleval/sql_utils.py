"""Pull SQL out of a model's reply and check it is a single read-only query."""
import re

CANNOT_ANSWER = "CANNOT_ANSWER"

FENCE = re.compile(r"```(?:sql|postgresql|postgres)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|vacuum|call|do)\b",
    re.IGNORECASE,
)


def strip_comments(sql):
    """Remove -- line comments and /* block */ comments."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", "", sql)


def extract_sql(reply):
    """Return the SQL from a reply, or None if there is none."""
    if reply is None:
        return None
    match = FENCE.search(reply)
    text = match.group(1) if match else reply
    text = strip_comments(text).strip()
    # Without a code block, start from the first SELECT/WITH (skips "Here is the query:").
    if not match:
        start = re.search(r"\b(select|with)\b", text, re.IGNORECASE)
        if not start:
            return None
        text = text[start.start():]
    return text.strip().rstrip(";").strip() or None


def says_cannot_answer(reply):
    return reply is not None and CANNOT_ANSWER in reply.upper()


def is_read_only(sql):
    """True for a single SELECT/WITH statement with no write or DDL keywords.

    This is a first line of defence; the read-only database user is the real guarantee.
    """
    if ";" in sql.strip().rstrip(";"):
        return False  # more than one statement
    if not re.match(r"^\s*(select|with)\b", sql, re.IGNORECASE):
        return False
    return not FORBIDDEN.search(sql)
