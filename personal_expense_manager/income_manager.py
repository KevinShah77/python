"""
Income Manager Module for Personal Expenses & Smart Budget Management System
----------------------------------------------------------------------------
Academic Demonstration Concepts:
- Predefined data structures for income sources
- Input validation and exception handling
- Financial balance calculations (Income - Expense)
- Month-over-month income trend tracking
"""

from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from database import (
    add_income,
    get_all_income,
    get_income_by_month,
    get_income_by_id,
    update_income,
    delete_income
)
from expense_manager import get_monthly_expense_total

# Predefined Income Sources as specified in requirements
INCOME_SOURCES: List[str] = [
    "Allowance",
    "Salary",
    "Freelancing",
    "Scholarship",
    "Other Income"
]

INCOME_ICONS: Dict[str, str] = {
    "Allowance": "🪙",
    "Salary": "💼",
    "Freelancing": "💻",
    "Scholarship": "📜",
    "Other Income": "💵"
}

INCOME_COLORS: Dict[str, str] = {
    "Allowance": "#3B82F6",
    "Salary": "#10B981",
    "Freelancing": "#8B5CF6",
    "Scholarship": "#F59E0B",
    "Other Income": "#6B7280"
}


def get_income_icon(source: str) -> str:
    """Return the designated emoji icon for an income source."""
    return INCOME_ICONS.get(source, "💵")


def get_income_color(source: str) -> str:
    """Return the designated color for an income source."""
    return INCOME_COLORS.get(source, "#10B981")


def validate_income(
    income_source: str,
    amount: Any,
    date_val: Any
) -> Tuple[bool, str]:
    """
    Validate input fields for an income entry.
    Ensures positive amount, valid source, and correct date format.
    """
    # 1. Income Source validation
    if not income_source or not str(income_source).strip():
        return False, "Income source is required and cannot be empty."

    # 2. Amount validation (Strict positive number)
    try:
        amt_float = float(amount)
        if amt_float <= 0:
            return False, "Income amount must be strictly greater than ₹0."
        if amt_float > 50_000_000:
            return False, "Income amount cannot exceed ₹5,00,00,000 (5 Crores)."
    except (ValueError, TypeError):
        return False, "Please enter a valid numeric amount."

    # 3. Date validation
    if isinstance(date_val, (date, datetime)):
        pass
    elif isinstance(date_val, str):
        try:
            datetime.strptime(date_val.strip(), "%Y-%m-%d")
        except ValueError:
            return False, "Invalid date format. Expected YYYY-MM-DD."
    else:
        return False, "Invalid date provided."

    return True, ""


def add_new_income(
    income_source: str,
    amount: float,
    date_val: Any,
    description: str = "",
    db_path: Optional[str] = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Validate and store a new income record.
    Returns (success, message, new_id).
    """
    is_valid, err = validate_income(income_source, amount, date_val)
    if not is_valid:
        return False, err, None

    date_str = date_val.strftime("%Y-%m-%d") if isinstance(date_val, (date, datetime)) else str(date_val).strip()

    try:
        new_id = add_income(
            income_source=income_source,
            amount=float(amount),
            date_str=date_str,
            description=description,
            db_path=db_path
        )
        return True, f"Income '{income_source}' of ₹{float(amount):,.2f} recorded successfully!", new_id
    except Exception as e:
        return False, f"Database error adding income: {str(e)}", None


def edit_income(
    income_id: int,
    income_source: str,
    amount: float,
    date_val: Any,
    description: str = "",
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    """Validate and update an existing income record."""
    is_valid, err = validate_income(income_source, amount, date_val)
    if not is_valid:
        return False, err

    date_str = date_val.strftime("%Y-%m-%d") if isinstance(date_val, (date, datetime)) else str(date_val).strip()

    try:
        updated = update_income(
            income_id=income_id,
            income_source=income_source,
            amount=float(amount),
            date_str=date_str,
            description=description,
            db_path=db_path
        )
        if updated:
            return True, f"Income #{income_id} updated successfully!"
        else:
            return False, f"No income record found with ID #{income_id}."
    except Exception as e:
        return False, f"Database error updating income: {str(e)}"


def remove_income(income_id: int, db_path: Optional[str] = None) -> Tuple[bool, str]:
    """Delete an income record with feedback."""
    try:
        deleted = delete_income(income_id, db_path=db_path)
        if deleted:
            return True, f"Income #{income_id} deleted successfully."
        else:
            return False, f"No income record found with ID #{income_id}."
    except Exception as e:
        return False, f"Database error deleting income: {str(e)}"


def get_monthly_income_total(year: int, month: int, db_path: Optional[str] = None) -> float:
    """Calculate the total income for a given year and month."""
    records = get_income_by_month(year, month, db_path=db_path)
    return sum(float(r["amount"]) for r in records)


def get_source_wise_income(year: int, month: int, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Computes source-wise income breakdown for a given month.
    Returns DataFrame: ['source', 'icon', 'color', 'total_amount', 'percentage', 'count'].
    """
    records = get_income_by_month(year, month, db_path=db_path)
    if not records:
        return pd.DataFrame(columns=["source", "icon", "color", "total_amount", "percentage", "count"])

    df = pd.DataFrame(records)
    grouped = df.groupby("income_source").agg(
        total_amount=("amount", "sum"),
        count=("id", "count")
    ).reset_index().rename(columns={"income_source": "source"})

    total_month = grouped["total_amount"].sum()
    grouped["percentage"] = (grouped["total_amount"] / total_month * 100).round(1) if total_month > 0 else 0.0
    grouped["icon"] = grouped["source"].apply(get_income_icon)
    grouped["color"] = grouped["source"].apply(get_income_color)
    grouped = grouped.sort_values(by="total_amount", ascending=False).reset_index(drop=True)
    return grouped


def get_monthly_financial_summary(year: int, month: int, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns full monthly financial breakdown:
    - Total Income
    - Total Expenses
    - Remaining Balance (Savings)
    - Savings Percentage
    """
    income = get_monthly_income_total(year, month, db_path=db_path)
    expenses = get_monthly_expense_total(year, month, db_path=db_path)
    balance = income - expenses
    savings_pct = (balance / income * 100) if income > 0 else 0.0

    return {
        "income": income,
        "expenses": expenses,
        "balance": balance,
        "savings_pct": round(savings_pct, 1),
        "is_deficit": balance < 0
    }
