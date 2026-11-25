"""Two prompt versions. v1 is a bare baseline; v2 adds the information a careful
human analyst would want. Comparing them measures how much prompt design helps."""
from pathlib import Path

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "db" / "01_schema.sql"


def prompt_v1(question):
    """Baseline: table names only, no rules."""
    return [
        {"role": "user", "content": (
            "A PostgreSQL database has these tables: stores, customers, ingredients, "
            "menu_items, orders, order_items.\n"
            f"Write a SQL query to answer this question: {question}"
        )},
    ]


SYSTEM_V2 = """You write PostgreSQL queries for the RushMore pizzeria database.

Schema:
{schema}

Notes on the data:
- orders.total_amount is the full value of an order. Item-level revenue is order_items.quantity * order_items.unit_price.
- menu_items.category is one of 'Pizza', 'Side', 'Drink', 'Dessert'. Pizza sizes are 'Small', 'Medium', 'Large'.
- stores.city is one of 'Lagos', 'Abuja', 'Port Harcourt', 'Ibadan'. Lagos has two stores.
- The ingredients table is stock only: it is NOT linked to menu items or orders.
- There is no delivery, staff, payment or discount data.

Rules:
1. Reply with exactly one PostgreSQL SELECT query inside a ```sql code block, and nothing else.
2. Use only the tables and columns in the schema above.
3. Return only the columns the question asks for.
4. If the question cannot be answered from this schema, reply with exactly: CANNOT_ANSWER"""

# Worked examples. These are deliberately NOT in the test set, so the test stays fair.
EXAMPLES = [
    ("How many stores are in Lagos?",
     "```sql\nSELECT COUNT(*) FROM stores WHERE city = 'Lagos';\n```"),
    ("What is the total revenue from Side items sold at the Ibadan store?",
     "```sql\nSELECT SUM(oi.quantity * oi.unit_price)\nFROM order_items oi\n"
     "JOIN orders o ON o.order_id = oi.order_id\nJOIN stores s ON s.store_id = o.store_id\n"
     "JOIN menu_items m ON m.item_id = oi.item_id\n"
     "WHERE s.city = 'Ibadan' AND m.category = 'Side';\n```"),
    ("Which staff member took the most orders?", "CANNOT_ANSWER"),
]


def prompt_v2(question):
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    messages = [{"role": "system", "content": SYSTEM_V2.format(schema=schema)}]
    for q, a in EXAMPLES:
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": question})
    return messages


PROMPTS = {"v1": prompt_v1, "v2": prompt_v2}