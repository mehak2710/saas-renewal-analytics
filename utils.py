"""
utils.py
--------
Shared helper functions: number formatting, filtering, and small
reusable pieces used across the app, EDA and visualization modules.
"""

import pandas as pd


def format_currency(value: float, compact: bool = True) -> str:
    """Format a number as USD currency, e.g. $1.2M / $84.5K / $920."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "$0"

    if compact:
        if abs(value) >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        if abs(value) >= 1_000:
            return f"${value / 1_000:.1f}K"
        return f"${value:,.0f}"
    return f"${value:,.2f}"


def format_percent(value: float, decimals: int = 1) -> str:
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return "0.0%"


def format_number(value: float, compact: bool = True) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0"
    if compact:
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        if abs(value) >= 1_000:
            return f"{value / 1_000:.1f}K"
        return f"{value:,.0f}"
    return f"{value:,.0f}"


def health_bucket(score: float) -> str:
    """Bucket a 0-100 health score into a label used for coloring/segmentation."""
    if score >= 75:
        return "Healthy"
    if score >= 50:
        return "Neutral"
    if score >= 30:
        return "At Risk"
    return "Critical"


def risk_bucket(score: float) -> str:
    if score >= 70:
        return "High Risk"
    if score >= 40:
        return "Medium Risk"
    return "Low Risk"


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply a dict of sidebar filters to the dataframe and return a copy.

    filters keys expected (any may be omitted / set to 'All' or empty list):
        date_range: (start_date, end_date) applied to renewal_date
        regions: list[str]
        industries: list[str]
        plans: list[str]
        company_sizes: list[str]
    """
    out = df.copy()

    date_range = filters.get("date_range")
    if date_range and len(date_range) == 2 and date_range[0] and date_range[1]:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        out = out[(out["renewal_date"] >= start) & (out["renewal_date"] <= end)]

    for key, col in [
        ("regions", "region"),
        ("industries", "industry"),
        ("plans", "plan"),
        ("company_sizes", "company_size"),
    ]:
        values = filters.get(key)
        if values:
            out = out[out[col].isin(values)]

    return out


def health_score_color(score: float) -> str:
    """Return a hex color for a health score, for use in charts/badges."""
    if score >= 75:
        return "#10B981"  # emerald
    if score >= 50:
        return "#F5B700"  # gold
    if score >= 30:
        return "#F97316"  # orange
    return "#DC2626"  # red