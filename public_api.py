import re
import requests

FRANKFURTER_LATEST_URL = "https://api.frankfurter.app/latest"
CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


class PublicApiError(Exception):
    """Raised when the public currency API cannot fulfill a conversion request."""


def _normalize_currency_code(code: str) -> str:
    cleaned = code.strip().upper()
    if not CURRENCY_CODE_PATTERN.match(cleaned):
        raise PublicApiError(f"Invalid currency code: '{code}'. Expected a 3-letter ISO code (e.g., USD, EUR).")
    return cleaned


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    timeout: float = 5.0
) -> dict:
    """Convert an amount from one currency to another using the Frankfurter public API."""
    if amount <= 0:
        raise PublicApiError("Amount to convert must be greater than 0.")

    base = _normalize_currency_code(from_currency)
    target = _normalize_currency_code(to_currency)

    if base == target:
        return {
            "base": base,
            "target": target,
            "rate": 1.0,
            "original_amount": round(amount, 2),
            "converted_amount": round(amount, 2),
        }

    try:
        response = requests.get(
            FRANKFURTER_LATEST_URL,
            params={"amount": amount, "from": base, "to": target},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise PublicApiError(f"Failed to reach currency API: {exc}") from exc
    except ValueError as exc:
        raise PublicApiError("Invalid JSON response received from currency API.") from exc

    rates = payload.get("rates", {})
    if target not in rates:
        raise PublicApiError(f"Target currency '{target}' was not returned by the API.")

    converted_value = float(rates[target])
    effective_rate = round(converted_value / amount, 6)

    return {
        "base": base,
        "target": target,
        "rate": effective_rate,
        "original_amount": round(amount, 2),
        "converted_amount": round(converted_value, 2),
    }
