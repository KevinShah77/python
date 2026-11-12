"""
Budget Manager Module for Personal Expenses & Smart Budget Management System
----------------------------------------------------------------------------
Academic Demonstration Concepts:
- Threshold-based state machines and tiered alerts
- Compound conditional branching (if/elif/else)
- Budget vs. Actual financial variance analysis
- Progress bar and utilization metric calculations
"""

from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from database import (
    set_budget,
    get_budgets_by_month,
    get_budget_by_category,
    delete_budget,
    delete_budget_by_category,
    get_expenses_by_month
)
from expense_manager import CATEGORIES, CATEGORY_ICONS, CATEGORY_COLORS, get_monthly_expense_total


def evaluate_budget_status(spent: float, budget_amount: float) -> Dict[str, Any]:
    """
    Evaluate budget utilization and assign status tier, visual color, and message.
    Tiers as specified:
    - Below 75%: Normal spending status (Green)
    - 75% to 89.9%: Budget caution (Yellow/Amber)
    - 90% to 99.9%: High spending warning (Orange)
    - 100% or above: Budget exceeded (Red)
    """
    spent = float(spent)
    budget = float(budget_amount)

    if budget <= 0:
        return {
            "tier": "none",
            "label": "No Budget Set",
            "color": "#94A3B8",
            "message": "No budget defined for this category.",
            "utilization": 0.0,
            "remaining": 0.0,
            "progress_val": 0.0
        }

    utilization = (spent / budget) * 100.0
    remaining = budget - spent
    # Progress value clamped to 1.0 for Streamlit progress bar (or float representation)
    progress_val = min(1.0, max(0.0, spent / budget))

    if utilization < 75.0:
        tier = "normal"
        label = "Normal Status"
        color = "#10B981"  # Emerald Green
        message = f"🟢 Spending is on track ({utilization:.1f}% used). ₹{remaining:,.2f} remaining."
    elif 75.0 <= utilization < 90.0:
        tier = "caution"
        label = "Budget Caution"
        color = "#F59E0B"  # Amber
        message = f"🟡 Caution: {utilization:.1f}% of budget consumed. ₹{remaining:,.2f} remaining."
    elif 90.0 <= utilization < 100.0:
        tier = "warning"
        label = "High Spending Warning"
        color = "#F97316"  # Orange
        message = f"🟠 High spending warning! {utilization:.1f}% used. Only ₹{remaining:,.2f} left."
    else:
        tier = "exceeded"
        label = "Budget Exceeded"
        color = "#EF4444"  # Red
        overspent = spent - budget
        message = f"🔴 Budget exceeded by ₹{overspent:,.2f}! Utilization is at {utilization:.1f}%."

    return {
        "tier": tier,
        "label": label,
        "color": color,
        "message": message,
        "utilization": round(utilization, 1),
        "remaining": round(remaining, 2),
        "progress_val": progress_val
    }


def save_budget(
    category: str,
    budget_amount: float,
    month: int,
    year: int,
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validate and save or update a budget limit.
    Accepts 'Overall' or any predefined expense category.
    """
    valid_categories = ["Overall"] + CATEGORIES
    if category not in valid_categories:
        return False, f"Invalid budget category: '{category}'"

    try:
        amt = float(budget_amount)
        if amt <= 0:
            return False, "Budget amount must be a positive number strictly greater than ₹0."
        if amt > 100_000_000:
            return False, "Budget amount cannot exceed ₹10,00,00,000 (10 Crores)."
    except (ValueError, TypeError):
        return False, "Budget amount must be a valid positive number."

    try:
        set_budget(
            category=category,
            budget_amount=amt,
            month=int(month),
            year=int(year),
            db_path=db_path
        )
        cat_display = "Overall Monthly" if category == "Overall" else f"'{category}'"
        return True, f"Budget of ₹{amt:,.2f} set successfully for {cat_display} ({month:02d}/{year})!"
    except Exception as e:
        return False, f"Database error saving budget: {str(e)}"


def get_overall_budget_summary(year: int, month: int, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns complete status for the overall monthly budget.
    Calculates total actual spending vs allocated overall budget.
    """
    budget_record = get_budget_by_category("Overall", year, month, db_path=db_path)
    budget_amount = float(budget_record["budget_amount"]) if budget_record else 0.0
    total_spent = get_monthly_expense_total(year, month, db_path=db_path)
    status_info = evaluate_budget_status(total_spent, budget_amount)

    return {
        "budget_amount": budget_amount,
        "spent_amount": total_spent,
        "has_budget": budget_amount > 0,
        **status_info
    }


def get_category_budgets_table(year: int, month: int, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Builds a comprehensive comparison DataFrame of all categories:
    Category, Icon, Budget Amount, Spent Amount, Remaining, Utilization %, Status Tier, Status Label, Color.
    Includes categories that have either a budget set or expenses incurred.
    """
    # 1. Fetch all budgets for the month
    budgets_list = get_budgets_by_month(year, month, db_path=db_path)
    budgets_map = {b["category"]: float(b["budget_amount"]) for b in budgets_list if b["category"] != "Overall"}

    # 2. Fetch actual expenses for the month
    expenses = get_expenses_by_month(year, month, db_path=db_path)
    expenses_df = pd.DataFrame(expenses) if expenses else pd.DataFrame(columns=["category", "amount"])
    
    if not expenses_df.empty:
        spent_map = expenses_df.groupby("category")["amount"].sum().to_dict()
    else:
        spent_map = {}

    # Union of categories with budgets or expenses or all predefined categories
    all_cats = list(dict.fromkeys(list(budgets_map.keys()) + list(spent_map.keys()) + CATEGORIES))

    rows = []
    for cat in all_cats:
        budget = budgets_map.get(cat, 0.0)
        spent = spent_map.get(cat, 0.0)

        # Only include if budget is set or expenses exist (or show all with 0 if requested)
        eval_res = evaluate_budget_status(spent, budget)
        rows.append({
            "category": cat,
            "icon": CATEGORY_ICONS.get(cat, "📦"),
            "color": CATEGORY_COLORS.get(cat, "#8D99AE"),
            "budget": budget,
            "spent": spent,
            "remaining": eval_res["remaining"],
            "utilization": eval_res["utilization"],
            "tier": eval_res["tier"],
            "status_label": eval_res["label"],
            "status_color": eval_res["color"],
            "progress_val": eval_res["progress_val"],
            "message": eval_res["message"]
        })

    df = pd.DataFrame(rows)
    # Sort: Categories with budgets first, then highest spent
    df["has_budget"] = df["budget"] > 0
    df = df.sort_values(by=["has_budget", "spent"], ascending=[False, False]).reset_index(drop=True)
    return df


def get_active_budget_alerts(year: int, month: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns a list of alerts for all budgets (overall and categories)
    that are in 'caution', 'warning', or 'exceeded' states.
    Used on Dashboard and Budget Manager for instant notifications.
    """
    alerts: List[Dict[str, Any]] = []

    # 1. Overall budget check
    overall = get_overall_budget_summary(year, month, db_path=db_path)
    if overall["has_budget"] and overall["tier"] in ("caution", "warning", "exceeded"):
        alerts.append({
            "type": "Overall Budget",
            "category": "Overall",
            "icon": "🎯",
            "tier": overall["tier"],
            "label": overall["label"],
            "color": overall["color"],
            "message": overall["message"],
            "utilization": overall["utilization"]
        })

    # 2. Category budgets check
    cat_df = get_category_budgets_table(year, month, db_path=db_path)
    for _, row in cat_df.iterrows():
        if row["budget"] > 0 and row["tier"] in ("caution", "warning", "exceeded"):
            alerts.append({
                "type": "Category Budget",
                "category": row["category"],
                "icon": row["icon"],
                "tier": row["tier"],
                "label": row["status_label"],
                "color": row["status_color"],
                "message": f"{row['icon']} **{row['category']}**: {row['message']}",
                "utilization": row["utilization"]
            })

    return alerts
