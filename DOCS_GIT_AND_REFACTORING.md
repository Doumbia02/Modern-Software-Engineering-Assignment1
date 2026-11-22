# Git/GitHub Collaboration & Clean Code Refactoring

## 1. Git / GitHub Collaboration Workflow
1. **Branching**: Create and work on a feature branch (`git checkout -b feat/crud-cli-and-tests`) instead of committing unfinished changes directly to `main`.
2. **Atomic Commits**: Commit logical units of work with clear messages:
   - `git commit -m "feat: add public currency API client and console CLI"`
   - `git commit -m "refactor: extract expense lookup and summary helpers"`
   - `git commit -m "test: add boundary, invalid input, API, and CLI tests"`
3. **Pull Request (PR)**: Push the branch (`git push -u origin feat/crud-cli-and-tests`) and open a PR into `main` on GitHub describing the changes and test results.
4. **Code Review**: Perform a structured code review before merging:
   - Verify route ordering (`/expenses/summary` placed before `/expenses/{expense_id}`).
   - Check input validation on both Pydantic models and SQLite `CHECK` constraints.
   - Ensure network calls have timeouts and graceful error messages.
   - Confirm tests use isolated temporary databases (`tmp_path`) rather than mutating production data.

---

## 2. Clean Code & Refactoring (Before vs. After)

### Refactoring Target: Repeated `404 Not Found` Lookup in `expense_api.py`

#### Before Refactoring
```python
@app.get("/expenses/{expense_id}")
def get_expense(expense_id: int):
    expense = database.get_expense_by_id(expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )
    return expense


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int):
    deleted = database.delete_expense(expense_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )
    return None
```

#### After Refactoring
```python
def get_expense_or_404(expense_id: int) -> dict:
    """Fetch an expense by ID or raise a consistent 404 HTTPException."""
    expense = database.get_expense_by_id(expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )
    return expense


@app.get("/expenses/{expense_id}")
def get_expense(expense_id: int):
    return get_expense_or_404(expense_id)


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int):
    get_expense_or_404(expense_id)
    database.delete_expense(expense_id)
    return None
```

### Why This Improves Clean Code
- **Eliminates duplication**: Single source of truth for missing-expense `404` responses.
- **Smaller, clearer functions**: `get_expense_or_404` has one clear responsibility and explicit type annotations.
- **Easier maintenance**: Updating error status or detail messages requires editing only one place.
