import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Database file location (can be overridden in tests)
DB_PATH = Path(__file__).resolve().parent / "expenses.db"


@contextmanager
def get_connection(db_path: Path | None = None):
    """Establish a SQLite connection with transaction rollback on error."""
    target_path = db_path if db_path is not None else DB_PATH
    connection = sqlite3.connect(target_path)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(db_path: Path | None = None):
    """Create the expenses table if it does not already exist."""
    with get_connection(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL CHECK(length(trim(category)) > 0),
                expense_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def create_expense(name, amount, category, expense_date, db_path: Path | None = None):
    """CREATE: Add a new expense and return the created row as a dict."""
    with get_connection(db_path) as connection:
        cursor = connection.execute("""
            INSERT INTO expenses (name, amount, category, expense_date)
            VALUES (?, ?, ?, ?)
        """, (name, amount, category, expense_date))

        expense_id = cursor.lastrowid
        row = connection.execute(
            "SELECT * FROM expenses WHERE id = ?",
            (expense_id,)
        ).fetchone()

        return dict(row)


def get_all_expenses(db_path: Path | None = None):
    """READ: Retrieve all expenses ordered by date and ID descending."""
    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM expenses ORDER BY expense_date DESC, id DESC"
        ).fetchall()

        return [dict(row) for row in rows]


def get_expense_by_id(expense_id, db_path: Path | None = None):
    """READ: Retrieve a single expense by ID, or None if not found."""
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM expenses WHERE id = ?",
            (expense_id,)
        ).fetchone()

        return dict(row) if row else None


def update_expense(expense_id, updates, db_path: Path | None = None):
    """UPDATE: Modify allowed fields of an existing expense."""
    allowed_fields = {"name", "amount", "category", "expense_date"}

    if not updates or not set(updates).issubset(allowed_fields):
        return None

    fields = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values())
    values.append(expense_id)

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            f"""
            UPDATE expenses
            SET {fields}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            values
        )

        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            "SELECT * FROM expenses WHERE id = ?",
            (expense_id,)
        ).fetchone()

        return dict(row)


def delete_expense(expense_id, db_path: Path | None = None):
    """DELETE: Remove an expense by ID; return True if a row was deleted."""
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )

        return cursor.rowcount > 0
