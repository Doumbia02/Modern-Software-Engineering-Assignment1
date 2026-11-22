import re
import requests

OPEN_ER_API_URL = "https://open.er-api.com/v6/latest/{base}"
CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


class PublicApiError(Exception):
    """Raised when the public currency API cannot fulfill a conversion request."""


def _normalize_currency_code(code: str) -> str:
    cleaned = code.strip().upper()
    if not CURRENCY_CODE_PATTERN.match(cleaned):
        raise PublicApiError(
            f"Invalid currency code: '{code}'. Expected a 3-letter ISO code (e.g., USD, EUR, XOF, AZN)."
        )
    return cleaned


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    timeout: float = 5.0
) -> dict:
    """Convert an amount across currencies using ExchangeRate-API's open endpoint."""
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
            OPEN_ER_API_URL.format(base=base),
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise PublicApiError(f"Failed to reach currency API: {exc}") from exc
    except ValueError as exc:
        raise PublicApiError("Invalid JSON response received from currency API.") from exc

    if payload.get("result") != "success":
        error_type = payload.get("error-type", "unknown error")
        raise PublicApiError(f"Currency API error for '{base}': {error_type}.")

    rates = payload.get("rates", {})
    if target not in rates:
        raise PublicApiError(f"Target currency '{target}' was not found in API rates.")

    rate = float(rates[target])
    converted_value = amount * rate

    return {
        "base": base,
        "target": target,
        "rate": round(rate, 6),
        "original_amount": round(amount, 2),
        "converted_amount": round(converted_value, 2),
    }