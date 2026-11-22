# Requirements, User Stories & Acceptance Criteria

## Project Overview
The **Personal Expense Tracker** is a console application (CLI) paired with a **FastAPI + SQLite CRUD API** and a **Public API integration** (Frankfurter Exchange Rates API: `https://api.frankfurter.app/latest`).

---

## Functional Requirements
1. **CRUD Expense Management (`expense_api.py` & `database.py`)**:
   - Create an expense (`POST /expenses`) with `name`, `amount` (`> 0`), `category`, and `expense_date` (`YYYY-MM-DD`).
   - Read all expenses (`GET /expenses`), read spending summary (`GET /expenses/summary`), and read a single expense (`GET /expenses/{expense_id}`).
   - Update an existing expense (`PUT /expenses/{expense_id}`) for partial or full fields.
   - Delete an expense (`DELETE /expenses/{expense_id}`).
2. **Public API Integration (`public_api.py`)**:
   - Query live foreign exchange rates from `https://api.frankfurter.app/latest` with timeout and network error handling.
   - Convert expense amounts or total spending from a base currency (e.g., `USD`) into a target currency (e.g., `EUR`, `GBP`, `JPY`, `AZN`).
3. **Console Application (`cli.py`)**:
   - Provide an interactive menu and command-line interface to list, add, update, delete, summarize, and currency-convert expenses.

## Non-Functional Requirements
- **Input Validation**: Pydantic schemas and SQLite `CHECK` constraints reject empty/whitespace strings and non-positive amounts.
- **Testability & Isolation**: Automated `pytest` suite runs with isolated temporary SQLite databases (`tmp_path`) and mocked/controlled public API responses.
- **Maintainability & Clean Code**: Small single-responsibility helpers (`get_expense_or_404`, `compute_category_totals`, `convert_amount`), clear naming, and no duplicated 404 lookup logic.

---

## User Stories & Acceptance Criteria

### US-01: Create Expense
- **User Story**: As a user, I want to add a new expense with a name, positive amount, category, and date so I can track my spending.
- **Acceptance Criteria**:
  - `POST /expenses` with valid payload returns HTTP `201 Created` and persists the record in SQLite.
  - Non-positive amounts (`0`, `-5.0`) or blank/whitespace `name` or `category` return HTTP `422 Unprocessable Entity`.

### US-02: View Expenses & Summary
- **User Story**: As a user, I want to view all expenses, inspect a single expense by ID, and see category/total summaries so I understand where my money goes.
- **Acceptance Criteria**:
  - `GET /expenses` returns HTTP `200 OK` with `total_expenses` and `data` list.
  - `GET /expenses/summary` returns HTTP `200 OK` with `total_amount`, `number_of_expenses`, and `category_totals`.
  - `GET /expenses/{id}` returns HTTP `200 OK` for an existing ID or HTTP `404 Not Found` if missing.

### US-03: Update Expense
- **User Story**: As a user, I want to update fields of an existing expense so I can correct mistakes.
- **Acceptance Criteria**:
  - `PUT /expenses/{id}` with valid updated fields returns HTTP `200 OK` and updates `updated_at`.
  - Sending an empty update body returns HTTP `400 Bad Request`; updating a missing ID returns HTTP `404 Not Found`; invalid values return HTTP `422 Unprocessable Entity`.

### US-04: Delete Expense
- **User Story**: As a user, I want to delete an expense record so I can remove erroneous entries.
- **Acceptance Criteria**:
  - `DELETE /expenses/{id}` for an existing ID removes the record and returns HTTP `204 No Content`.
  - Subsequent `GET /expenses/{id}` or deleting a missing ID returns HTTP `404 Not Found`.

### US-05: Convert Expenses via Public API
- **User Story**: As a user, I want to convert my total expenses into another currency using a public exchange-rate API from the console.
- **Acceptance Criteria**:
  - Converting a positive amount or total with valid currency codes (`from_currency`, `to_currency`) retrieves the exchange rate and calculates the converted amount accurately.
  - Invalid currency codes, non-positive amounts, or network/API failures raise clean, descriptive errors rather than crashing unhandled.
