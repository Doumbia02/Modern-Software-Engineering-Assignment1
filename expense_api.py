from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

import database


# ==========================================
# 1. DATABASE INITIALIZATION
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize_database()
    yield


app = FastAPI(
    title="Personal Expense Tracker API",
    description="A CRUD API for managing personal expenses.",
    version="1.0.0",
    lifespan=lifespan
)


# ==========================================
# 2. DATA VALIDATION MODELS
# ==========================================

def _validate_non_empty_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("This field cannot be empty.")
    return cleaned


class ExpenseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=50)
    expense_date: date

    @field_validator("name", "category")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = _validate_non_empty_text(value)
        assert cleaned is not None
        return cleaned


class ExpenseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    expense_date: Optional[date] = None

    @field_validator("name", "category")
    @classmethod
    def validate_text(cls, value: Optional[str]) -> Optional[str]:
        return _validate_non_empty_text(value)


# ==========================================
# 3. CLEAN CODE HELPERS
# ==========================================

def get_expense_or_404(expense_id: int) -> dict:
    """Retrieve an expense by ID or raise a 404 Not Found error."""
    expense = database.get_expense_by_id(expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )
    return expense


def compute_expense_summary(expenses: list[dict]) -> dict:
    """Compute total spending, count, and rounded per-category totals."""
    total_amount = sum(item["amount"] for item in expenses)
    category_totals: dict[str, float] = {}

    for item in expenses:
        category = item["category"]
        category_totals[category] = category_totals.get(category, 0.0) + item["amount"]

    return {
        "total_amount": round(total_amount, 2),
        "number_of_expenses": len(expenses),
        "category_totals": {
            category: round(amount, 2)
            for category, amount in category_totals.items()
        }
    }


# ==========================================
# 4. ROOT & HEALTH CHECK
# ==========================================

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Personal Expense Tracker API! of Sait and Youssouf",
        "documentation": "/docs",
        "health_check": "/health"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Personal Expense Tracker API is running."
    }


# ==========================================
# 5. CREATE - ADD A NEW EXPENSE
# ==========================================

@app.post("/expenses", status_code=status.HTTP_201_CREATED)
def create_expense(expense: ExpenseCreate):
    new_expense = database.create_expense(
        name=expense.name,
        amount=expense.amount,
        category=expense.category,
        expense_date=expense.expense_date.isoformat()
    )

    return {
        "message": "Expense created successfully.",
        "data": new_expense
    }


# ==========================================
# 6. READ - GET ALL EXPENSES & SUMMARY
# ==========================================

@app.get("/expenses")
def get_expenses():
    expenses = database.get_all_expenses()
    return {
        "total_expenses": len(expenses),
        "data": expenses
    }


@app.get("/expenses/summary")
def expense_summary():
    expenses = database.get_all_expenses()
    return compute_expense_summary(expenses)


@app.get("/expenses/{expense_id}")
def get_expense(expense_id: int):
    return get_expense_or_404(expense_id)


# ==========================================
# 7. UPDATE - MODIFY AN EXISTING EXPENSE
# ==========================================

@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, expense: ExpenseUpdate):
    updates = expense.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update."
        )

    if "expense_date" in updates and updates["expense_date"] is not None:
        updates["expense_date"] = updates["expense_date"].isoformat()

    updated_expense = database.update_expense(expense_id, updates)
    if updated_expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found."
        )

    return {
        "message": "Expense updated successfully.",
        "data": updated_expense
    }


# ==========================================
# 8. DELETE - REMOVE AN EXPENSE
# ==========================================

@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int):
    get_expense_or_404(expense_id)
    database.delete_expense(expense_id)
    return None
