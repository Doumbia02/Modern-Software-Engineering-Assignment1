from database import (
    initialize_database,
    create_expense,
    get_all_expenses,
    get_expense_by_id,
    update_expense,
    delete_expense
)

initialize_database()
print("Database initialized successfully!")

expense = create_expense(
    name="Lunch",
    amount=15.00,
    category="Food",
    expense_date="2026-11-14"
)

print("\nCreated expense:")
print(expense)

print("\nAll expenses:")
print(get_all_expenses())

print("\nSearch result:")
print(get_expense_by_id(expense["id"]))

updated = update_expense(expense["id"], {"amount": 20.00})
print("\nUpdated expense:")
print(updated)

deleted = delete_expense(expense["id"])
print("\nDeleted successfully:", deleted)
