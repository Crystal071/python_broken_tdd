"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

from shop.money import percent_of

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")


def _is_int(value: str) -> bool:
    """Return True if the string can be parsed as an integer without raising exceptions."""
    stripped = value.strip()
    if not stripped:
        return False
    if stripped[0] in "+-":
        return len(stripped) > 1 and stripped[1:].isdigit()
    return stripped.isdigit()


def _validate_line(idx: int, item: dict[str, str], seen_skus: set[str]) -> str | None:
    """Validate a single order line and record its SKU."""
    for key in REQUIRED_LINE_KEYS:
        if key not in item:
            return f"Missing required key '{key}' in line {idx}"

    sku = item["sku"]
    if not sku:
        return f"Blank SKU in line {idx}"
    if sku in seen_skus:
        return f"Duplicate SKU '{sku}' in line {idx}"
    seen_skus.add(sku)

    qty_str = item["qty"]
    if not _is_int(qty_str):
        return f"Non-numeric quantity '{qty_str}' in line {idx}"
    if int(qty_str) <= 0:
        return f"Quantity must be positive in line {idx}"

    price_str = item["unit_price_kopecks"]
    if not _is_int(price_str):
        return f"Non-numeric price '{price_str}' in line {idx}"
    if int(price_str) < 0:
        return f"Price cannot be negative in line {idx}"

    return None


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    if not lines:
        return "Order has no lines"
    if promo_code and promo_code not in PROMO_CODES:
        return f"Unknown promo code: '{promo_code}'"
    if shipping_city and shipping_city not in SUPPORTED_CITIES:
        return f"Unsupported shipping city: '{shipping_city}'"

    seen_skus: set[str] = set()
    for idx, item in enumerate(lines, start=1):
        error = _validate_line(idx, item, seen_skus)
        if error is not None:
            return error

    return None


def _calculate_tier_discount(total_qty: int) -> int:
    """Return the highest matching volume tier discount percent."""
    best_discount = 0
    for threshold, percent in TIER_DISCOUNTS:
        if total_qty >= threshold and percent > best_discount:
            best_discount = percent
    return best_discount


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    """Return the order total in kopecks, or None if the order is invalid."""
    if validate_order(lines, promo_code, shipping_city) is not None:
        return None

    subtotal = 0
    total_qty = 0
    for item in lines:
        qty = int(item["qty"])
        price = int(item["unit_price_kopecks"])
        subtotal += qty * price
        total_qty += qty

    tier_discount = _calculate_tier_discount(total_qty)
    promo_discount = PROMO_CODES.get(promo_code, 0) if promo_code else 0
    best_percent = max(tier_discount, promo_discount)
    capped_percent = min(best_percent, MAX_DISCOUNT_PERCENT)

    discount = percent_of(subtotal, capped_percent)
    discounted_subtotal = subtotal - discount

    delivery = 0
    if shipping_city and discounted_subtotal < FREE_DELIVERY_FROM_KOPEKS:
        delivery = SHIPPING_KOPEKS

    base = discounted_subtotal + delivery
    vat = percent_of(base, VAT_PERCENT)
    return base + vat
