"""
Expense Manager Module for Personal Expenses & Smart Budget Management System
-----------------------------------------------------------------------------
Academic Demonstration Concepts:
- Dictionary mapping for categories, colors, and unicode icons
- Form validation algorithms (boundary checks, type enforcement)
- Date parsing and calendar arithmetic with datetime
- Data aggregation and category-wise grouping
- MoM (Month-over-Month) percentage change calculation
"""

from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from database import (
    add_expense,
    get_all_expenses,
    get_expenses_by_month,
    get_expense_by_id,
    update_expense,
    delete_expense
)

# 10 Predefined Expense Categories with standard names
CATEGORIES: List[str] = [
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Education",
    "Healthcare",
    "Entertainment",
    "Bills & Utilities",
    "Travel",
    "Personal Care",
    "Others"
]

# Distinct, professional hex colors matching each category for charts & badges
CATEGORY_COLORS: Dict[str, str] = {
    "Food & Dining": "#FF6B6B",      # Coral Red
    "Transportation": "#4D96FF",     # Azure Blue
    "Shopping": "#FFD93D",           # Sunny Gold
    "Education": "#6BCB77",          # Emerald Green
    "Healthcare": "#FF6584",         # Rose Pink
    "Entertainment": "#9B51E0",      # Deep Purple
    "Bills & Utilities": "#FB8500",  # Amber Orange
    "Travel": "#00B4D8",             # Teal Cyan
    "Personal Care": "#E056FD",      # Neon Orchid
    "Others": "#8D99AE"              # Slate Grey
}

# Unicode emoji icons for category badges and lists
CATEGORY_ICONS: Dict[str, str] = {
    "Food & Dining": "🍔",
    "Transportation": "🚗",
    "Shopping": "🛍️",
    "Education": "🎓",
    "Healthcare": "🏥",
    "Entertainment": "🎬",
    "Bills & Utilities": "💡",
    "Travel": "✈️",
    "Personal Care": "💅",
    "Others": "📦"
}

PAYMENT_METHODS: List[str] = [
    "UPI / GPay / PhonePe",
    "Cash",
    "Debit Card",
    "Credit Card",
    "Net Banking",
    "Other"
]


def get_category_color(category: str) -> str:
    """Return the designated hex color for a category."""
    return CATEGORY_COLORS.get(category, "#8D99AE")


def get_category_icon(category: str) -> str:
    """Return the designated emoji icon for a category."""
    return CATEGORY_ICONS.get(category, "🏷️")


def validate_expense(
    expense_name: str,
    amount: Any,
    category: str,
    date_val: Any
) -> Tuple[bool, str]:
    """
    Validate all input fields for an expense entry.
    Demonstrates defensive programming and type validation.
    Returns (True, '') if valid, or (False, error_message) if invalid.
    """
    # 1. Expense Name validation
    if not expense_name or not str(expense_name).strip():
        return False, "Expense name is required and cannot be empty."

    if len(str(expense_name).strip()) > 100:
        return False, "Expense name cannot exceed 100 characters."

    # 2. Amount validation (Strict positive number)
    try:
        amt_float = float(amount)
        if amt_float <= 0:
            return False, "Expense amount must be strictly greater than ₹0."
        if amt_float > 10_000_000:
            return False, "Expense amount cannot exceed ₹1,00,00,000 (1 Crore)."
    except (ValueError, TypeError):
        return False, "Please enter a valid numeric amount."

    # 3. Category validation
    if not category or str(category).strip() not in CATEGORIES:
        return False, f"Please select a valid expense category from the predefined list."

    # 4. Date validation
    if isinstance(date_val, (date, datetime)):
        date_str = date_val.strftime("%Y-%m-%d")
    elif isinstance(date_val, str):
        try:
            datetime.strptime(date_val.strip(), "%Y-%m-%d")
            date_str = date_val.strip()
        except ValueError:
            return False, "Invalid date format. Expected YYYY-MM-DD."
    else:
        return False, "Invalid date provided."

    return True, ""


def add_new_expense(
    expense_name: str,
    amount: float,
    category: str,
    date_val: Any,
    payment_method: str = "Cash",
    description: str = "",
    db_path: Optional[str] = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Validates and stores a new expense.
    Returns (success, message, new_id).
    """
    is_valid, err = validate_expense(expense_name, amount, category, date_val)
    if not is_valid:
        return False, err, None

    date_str = date_val.strftime("%Y-%m-%d") if isinstance(date_val, (date, datetime)) else str(date_val).strip()

    try:
        new_id = add_expense(
            expense_name=expense_name,
            amount=float(amount),
            category=category,
            date_str=date_str,
            payment_method=payment_method,
            description=description,
            db_path=db_path
        )
        return True, f"Expense '{expense_name}' of ₹{float(amount):,.2f} added successfully!", new_id
    except Exception as e:
        return False, f"Database error adding expense: {str(e)}", None


def edit_expense(
    expense_id: int,
    expense_name: str,
    amount: float,
    category: str,
    date_val: Any,
    payment_method: str = "Cash",
    description: str = "",
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validates and updates an existing expense record.
    Returns (success, message).
    """
    is_valid, err = validate_expense(expense_name, amount, category, date_val)
    if not is_valid:
        return False, err

    date_str = date_val.strftime("%Y-%m-%d") if isinstance(date_val, (date, datetime)) else str(date_val).strip()

    try:
        updated = update_expense(
            expense_id=expense_id,
            expense_name=expense_name,
            amount=float(amount),
            category=category,
            date_str=date_str,
            payment_method=payment_method,
            description=description,
            db_path=db_path
        )
        if updated:
            return True, f"Expense #{expense_id} updated successfully!"
        else:
            return False, f"No expense found with ID #{expense_id}."
    except Exception as e:
        return False, f"Database error updating expense: {str(e)}"


def remove_expense(expense_id: int, db_path: Optional[str] = None) -> Tuple[bool, str]:
    """Delete an expense record with feedback."""
    try:
        deleted = delete_expense(expense_id, db_path=db_path)
        if deleted:
            return True, f"Expense #{expense_id} deleted successfully."
        else:
            return False, f"No expense found with ID #{expense_id}."
    except Exception as e:
        return False, f"Database error deleting expense: {str(e)}"


def get_monthly_expense_total(year: int, month: int, db_path: Optional[str] = None) -> float:
    """Calculate the total expense amount for a given year and month."""
    records = get_expenses_by_month(year, month, db_path=db_path)
    return sum(float(r["amount"]) for r in records)


def get_category_wise_spending(year: int, month: int, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Computes category-wise expense breakdown for a given month.
    Returns a DataFrame with columns: ['category', 'icon', 'color', 'total_amount', 'percentage', 'count'].
    """
    records = get_expenses_by_month(year, month, db_path=db_path)
    if not records:
        return pd.DataFrame(columns=["category", "icon", "color", "total_amount", "percentage", "count"])

    df = pd.DataFrame(records)
    grouped = df.groupby("category").agg(
        total_amount=("amount", "sum"),
        count=("id", "count")
    ).reset_index()

    total_month = grouped["total_amount"].sum()
    grouped["percentage"] = (grouped["total_amount"] / total_month * 100).round(1) if total_month > 0 else 0.0
    grouped["icon"] = grouped["category"].apply(get_category_icon)
    grouped["color"] = grouped["category"].apply(get_category_color)
    grouped = grouped.sort_values(by="total_amount", ascending=False).reset_index(drop=True)
    return grouped


def compare_monthly_spending(year: int, month: int, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compares the current month's expenses with the previous month.
    Demonstrates conditional logic, arithmetic diffs, and trend analysis.
    """
    cur_total = get_monthly_expense_total(year, month, db_path=db_path)

    # Calculate previous month calendar values
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    prev_total = get_monthly_expense_total(prev_year, prev_month, db_path=db_path)
    diff = cur_total - prev_total

    if prev_total > 0:
        pct_change = round((diff / prev_total) * 100, 1)
    else:
        pct_change = 100.0 if cur_total > 0 else 0.0

    if diff > 0:
        trend = "increased"
        trend_icon = "🔺"
    elif diff < 0:
        trend = "decreased"
        trend_icon = "🔻"
    else:
        trend = "unchanged"
        trend_icon = "➖"

    return {
        "current_total": cur_total,
        "prev_total": prev_total,
        "diff": abs(diff),
        "signed_diff": diff,
        "pct_change": pct_change,
        "trend": trend,
        "trend_icon": trend_icon,
        "prev_year": prev_year,
        "prev_month": prev_month
    }
