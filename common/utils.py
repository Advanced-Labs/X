"""Shared utility functions used by api and ui build tools."""

import re


def format_currency(amount, symbol="$"):
    """Format a number as currency string."""
    return f"{symbol}{amount:,.2f}"


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def truncate(text, max_length=100, suffix="..."):
    """Truncate text to max_length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def validate_email(email):
    """Basic email validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def get_category_name(category_id):
    """Look up a category name by its ID. Returns 'Unknown' if not found."""
    from .constants import CATEGORIES
    return CATEGORIES.get(category_id, "Unknown")


def parse_id(value):
    """Parse a string value to integer ID, return None if invalid."""
    try:
        result = int(value)
        return result if result > 0 else None
    except (ValueError, TypeError):
        return None
