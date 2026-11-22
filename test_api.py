from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

import database
import expense_api
from expense_api import app
from public_api import PublicApiError, convert_currency
import cli


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_expenses.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    database.initialize_database(test_db)
    return test_db


client = TestClient(app)


def test_crud_lifecycle_create_read_update_delete():
    # Create (201)
    create_res = client.post(
        "/expenses",
        json={
            "name": "Lunch",
            "amount": 12.50,
            "category": "Food",
            "expense_date": "2026-11-22",
        },
    )
    assert create_res.status_code == 201
    created = create_res.json()["data"]
    expense_id = created["id"]
    assert created["name"] == "Lunch"
    assert created["amount"] == 12.50

    # Read list & single (200)
    list_res = client.get("/expenses")
    assert list_res.status_code == 200
    assert list_res.json()["total_expenses"] == 1

    get_res = client.get(f"/expenses/{expense_id}")
    assert get_res.status_code == 200
    assert get_res.json()["category"] == "Food"

    # Update (200)
    update_res = client.put(
        f"/expenses/{expense_id}",
        json={"amount": 18.75},
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["amount"] == 18.75

    # Summary (200)
    summary_res = client.get("/expenses/summary")
    assert summary_res.status_code == 200
    assert summary_res.json()["total_amount"] == 18.75

    # Delete (204) then verify 404
    del_res = client.delete(f"/expenses/{expense_id}")
    assert del_res.status_code == 204
    assert client.get(f"/expenses/{expense_id}").status_code == 404


def test_boundary_minimum_positive_amount():
    res = client.post(
        "/expenses",
        json={
            "name": "Penny candy",
            "amount": 0.01,
            "category": "Snacks",
            "expense_date": "2026-11-22",
        },
    )
    assert res.status_code == 201
    assert res.json()["data"]["amount"] == 0.01


def test_invalid_inputs_negative_zero_and_blank_fields():
    # Zero and negative amounts -> 422
    for bad_amount in [0, 0.0, -5.00]:
        res = client.post(
            "/expenses",
            json={
                "name": "Invalid Amount",
                "amount": bad_amount,
                "category": "Test",
                "expense_date": "2026-11-22",
            },
        )
        assert res.status_code == 422

    # Whitespace-only name -> 422
    res_blank = client.post(
        "/expenses",
        json={
            "name": "   ",
            "amount": 10.0,
            "category": "Test",
            "expense_date": "2026-11-22",
        },
    )
    assert res_blank.status_code == 422

    # Empty update body -> 400
    created_id = client.post(
        "/expenses",
        json={
            "name": "Book",
            "amount": 25.0,
            "category": "Education",
            "expense_date": "2026-11-22",
        },
    ).json()["data"]["id"]
    empty_put = client.put(f"/expenses/{created_id}", json={})
    assert empty_put.status_code == 400


def test_refactored_helper_404_and_summary():
    with pytest.raises(expense_api.HTTPException) as exc_info:
        expense_api.get_expense_or_404(99999)
    assert exc_info.value.status_code == 404

    summary = expense_api.compute_expense_summary([
        {"amount": 10.0, "category": "Food"},
        {"amount": 5.5, "category": "Food"},
        {"amount": 20.0, "category": "Travel"},
    ])
    assert summary["total_amount"] == 35.5
    assert summary["number_of_expenses"] == 3
    assert summary["category_totals"] == {"Food": 15.5, "Travel": 20.0}


def test_public_api_currency_conversion_and_invalid_input():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"rates": {"EUR": 92.0}}

    with patch("public_api.requests.get", return_value=mock_resp):
        converted = convert_currency(100.0, "usd", "eur")
        assert converted["base"] == "USD"
        assert converted["target"] == "EUR"
        assert converted["converted_amount"] == 92.0

    with pytest.raises(PublicApiError):
        convert_currency(10.0, "INVALID", "EUR")

    with pytest.raises(PublicApiError):
        convert_currency(-1.0, "USD", "EUR")


def test_cli_add_and_convert_commands(capsys):
    def fake_request(method, path, base_url="", json_data=None):
        if method == "POST" and path == "/expenses":
            return {
                "data": {
                    "id": 1,
                    "name": json_data["name"],
                    "amount": json_data["amount"],
                    "category": json_data["category"],
                    "expense_date": json_data["expense_date"],
                }
            }
        if method == "GET" and path == "/expenses/summary":
            return {"total_amount": 50.0, "number_of_expenses": 1, "category_totals": {"Food": 50.0}}
        return {}

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"rates": {"EUR": 46.0}}

    with patch("cli._api_request", side_effect=fake_request), patch("public_api.requests.get", return_value=mock_resp):
        exit_add = cli.main(["add", "--name", "Dinner", "--amount", "50.0", "--category", "Food", "--date", "2026-11-22"])
        assert exit_add == 0
        exit_conv = cli.main(["convert", "--from", "USD", "--to", "EUR"])
        assert exit_conv == 0

    out = capsys.readouterr().out
    assert "Created expense #1: Dinner (50.0)" in out
    assert "50.00 USD = 46.00 EUR" in out
