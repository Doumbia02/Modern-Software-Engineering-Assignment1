# Personal Expense Tracker (Console CLI + FastAPI CRUD API + Public API)

A Python console application and REST API for tracking personal expenses, backed by SQLite and integrated with the **Frankfurter** public currency exchange API (`https://api.frankfurter.app/latest`).

## Project Structure
- `database.py` — SQLite connection helper, schema initialization, and CRUD functions (`DB_PATH` configurable for testing).
- `expense_api.py` — FastAPI application, Pydantic validation models (`ExpenseCreate`, `ExpenseUpdate`), refactored helpers, and CRUD endpoints.
- `public_api.py` — Public API client for fetching exchange rates and converting amounts with error/timeout handling.
- `cli.py` — Console application (interactive menu + subcommands) interacting with the FastAPI CRUD API and `public_api.py`.
- `test_api.py` — Automated `pytest` suite covering happy paths, boundary conditions, invalid inputs, refactoring logic, public API conversion, and CLI flows.
- `REQUIREMENTS.md` — Functional/non-functional requirements, user stories, and acceptance criteria.
- `DOCS_GIT_AND_REFACTORING.md` — Git/GitHub branch, PR, and code review guide + before/after refactoring walkthrough.

## Setup & Running
```bash
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Start the FastAPI CRUD API
uvicorn expense_api:app --reload

# 2. Run the Console Application (in a second terminal)
python cli.py
```

## Running Unit Tests
```bash
pytest -v
```
