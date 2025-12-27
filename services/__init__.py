from dateutil import parser as dateparser


def parse_amount(raw: str) -> str:
    """Normalize amount string to positive decimal string (Firefly expects positive amount and type reflects direction)."""
    s = raw.strip().replace(",", "")  # remove thousands separators
    # If CSV has debit as negative, make positive; keep sign to decide type later if you want.
    # Here we'll treat all card lines as withdrawals.
    if s == "":
        return "0.00"
    # Remove currency symbols if present
    s = s.lstrip("₹$€")
    # Ensure two decimals
    try:
        val = float(s)
    except Exception:
        # fallback: strip non-numeric
        filtered = ''.join(ch for ch in s if (ch.isdigit() or ch in ".-"))
        val = float(filtered) if filtered else 0.0
    return f"{val:.2f}"


def normalize_date(raw: str) -> str:
    """Return date in YYYY-MM-DD format (or ISO if needed)."""
    dt = dateparser.parse(raw)
    return dt.date().isoformat()
