import argparse
import os
from datetime import date
import requests

from public_api import PublicApiError, convert_currency

DEFAULT_API_BASE_URL = os.getenv("EXPENSE_API_URL", "http://127.0.0.1:8001")


def _api_request(method: str, path: str, base_url: str = DEFAULT_API_BASE_URL, json_data: dict | None = None):
    url = f"{base_url.rstrip('/')}{path}"
    try:
        response = requests.request(method=method, url=url, json=json_data, timeout=5.0)
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not connect to Expense API at {base_url}: {exc}") from exc

    if response.status_code == 204:
        return None

    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}

    if response.status_code >= 400:
        detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
        raise RuntimeError(f"API error ({response.status_code}): {detail}")

    return payload


def cmd_list(base_url: str = DEFAULT_API_BASE_URL) -> dict:
    payload = _api_request("GET", "/expenses", base_url=base_url)
    items = payload.get("data", []) if isinstance(payload, dict) else []
    print(f"Total expenses: {len(items)}")
    for item in items:
        print(f"  [{item['id']}] {item['expense_date']} | {item['name']} ({item['category']}) -> {item['amount']:.2f}")
    return payload


def cmd_add(
    name: str,
    amount: float,
    category: str,
    expense_date: str | None = None,
    base_url: str = DEFAULT_API_BASE_URL
) -> dict:
    payload = {
        "name": name,
        "amount": amount,
        "category": category,
        "expense_date": expense_date or date.today().isoformat(),
    }
    result = _api_request("POST", "/expenses", base_url=base_url, json_data=payload)
    created = result.get("data", result) if isinstance(result, dict) else result
    print(f"Created expense #{created.get('id')}: {created.get('name')} ({created.get('amount')})")
    return result


def cmd_update(
    expense_id: int,
    updates: dict,
    base_url: str = DEFAULT_API_BASE_URL
) -> dict:
    result = _api_request("PUT", f"/expenses/{expense_id}", base_url=base_url, json_data=updates)
    updated = result.get("data", result) if isinstance(result, dict) else result
    print(f"Updated expense #{expense_id}: {updated}")
    return result


def cmd_delete(expense_id: int, base_url: str = DEFAULT_API_BASE_URL) -> None:
    _api_request("DELETE", f"/expenses/{expense_id}", base_url=base_url)
    print(f"Deleted expense #{expense_id}.")


def cmd_summary(base_url: str = DEFAULT_API_BASE_URL) -> dict:
    summary = _api_request("GET", "/expenses/summary", base_url=base_url)
    print(f"Total Amount: {summary['total_amount']:.2f} across {summary['number_of_expenses']} expenses")
    for cat, amt in summary.get("category_totals", {}).items():
        print(f"  - {cat}: {amt:.2f}")
    return summary


def cmd_convert(
    from_currency: str,
    to_currency: str,
    amount: float | None = None,
    base_url: str = DEFAULT_API_BASE_URL
) -> dict:
    if amount is None:
        summary = cmd_summary(base_url=base_url)
        amount = float(summary["total_amount"])
    conversion = convert_currency(amount=amount, from_currency=from_currency, to_currency=to_currency)
    print(
        f"{conversion['original_amount']:.2f} {conversion['base']} = "
        f"{conversion['converted_amount']:.2f} {conversion['target']} (rate: {conversion['rate']})"
    )
    return conversion


def interactive_menu(base_url: str = DEFAULT_API_BASE_URL) -> None:
    while True:
        print("\n=== Personal Expense Tracker CLI ===")
        print("1. List expenses")
        print("2. Add expense")
        print("3. Update expense")
        print("4. Delete expense")
        print("5. View summary")
        print("6. Convert total via public currency API")
        print("0. Exit")
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                cmd_list(base_url)
            elif choice == "2":
                name = input("Name: ").strip()
                amount = float(input("Amount: ").strip())
                category = input("Category: ").strip()
                exp_date = input(f"Date (YYYY-MM-DD) [{date.today().isoformat()}]: ").strip() or None
                cmd_add(name, amount, category, exp_date, base_url)
            elif choice == "3":
                exp_id = int(input("Expense ID to update: ").strip())
                updates = {}
                new_name = input("New name (leave blank to skip): ").strip()
                new_amount = input("New amount (leave blank to skip): ").strip()
                new_cat = input("New category (leave blank to skip): ").strip()
                if new_name:
                    updates["name"] = new_name
                if new_amount:
                    updates["amount"] = float(new_amount)
                if new_cat:
                    updates["category"] = new_cat
                cmd_update(exp_id, updates, base_url)
            elif choice == "4":
                exp_id = int(input("Expense ID to delete: ").strip())
                cmd_delete(exp_id, base_url)
            elif choice == "5":
                cmd_summary(base_url)
            elif choice == "6":
                from_curr = input("Base currency (e.g., USD): ").strip()
                to_curr = input("Target currency (e.g., EUR): ").strip()
                amt_raw = input("Amount to convert (leave blank to use total expenses): ").strip()
                amt = float(amt_raw) if amt_raw else None
                cmd_convert(from_curr, to_curr, amt, base_url)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please choose 0-6.")
        except (ValueError, RuntimeError, PublicApiError) as exc:
            print(f"Error: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal Expense Tracker Console Application")
    parser.add_argument("--api-url", default=DEFAULT_API_BASE_URL, help="Base URL for the CRUD API")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List all expenses")
    subparsers.add_parser("summary", help="Show expense summary")

    p_add = subparsers.add_parser("add", help="Create a new expense")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--amount", type=float, required=True)
    p_add.add_argument("--category", required=True)
    p_add.add_argument("--date", dest="expense_date", default=None)

    p_upd = subparsers.add_parser("update", help="Update an existing expense")
    p_upd.add_argument("--id", type=int, required=True)
    p_upd.add_argument("--name", default=None)
    p_upd.add_argument("--amount", type=float, default=None)
    p_upd.add_argument("--ca tegory", default=None)

    p_del = subparsers.add_parser("delete", help="Delete an expense by ID")
    p_del.add_argument("--id", type=int, required=True)

    p_conv = subparsers.add_parser("convert", help="Convert amount or total expenses via public API")
    p_conv.add_argument("--from", dest="from_currency", required=True)
    p_conv.add_argument("--to", dest="to_currency", required=True)
    p_conv.add_argument("--amount", type=float, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command is None:
            interactive_menu(args.api_url)
        elif args.command == "list":
            cmd_list(args.api_url)
        elif args.command == "summary":
            cmd_summary(args.api_url)
        elif args.command == "add":
            cmd_add(args.name, args.amount, args.category, args.expense_date, args.api_url)
        elif args.command == "update":
            updates = {}
            if args.name is not None:
                updates["name"] = args.name
            if args.amount is not None:
                updates["amount"] = args.amount
            if args.category is not None:
                updates["category"] = args.category
            cmd_update(args.id, updates, args.api_url)
        elif args.command == "delete":
            cmd_delete(args.id, args.api_url)
        elif args.command == "convert":
            cmd_convert(args.from_currency, args.to_currency, args.amount, args.api_url)
        return 0
    except (ValueError, RuntimeError, PublicApiError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
