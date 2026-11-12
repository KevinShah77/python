"""
Smart Insights Module for Personal Expenses & Smart Budget Management System
----------------------------------------------------------------------------
Academic Demonstration Concepts:
- Rule-based expert system / heuristic analysis
- Comparative data analysis across temporal windows (Current vs Previous Month)
- Pattern detection (discretionary spending spikes, concentration risk)
- Automated recommendation generation based on financial health rules
"""

import calendar
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd

from database import (
    get_expenses_by_month,
    get_income_by_month
)
from expense_manager import (
    get_category_wise_spending,
    compare_monthly_spending,
    get_category_icon
)
from budget_manager import get_overall_budget_summary, get_category_budgets_table


# Predefined actionable financial tips tailored by category
CATEGORY_RECOMMENDATIONS: Dict[str, str] = {
    "Food & Dining": "Try cooking hostel/home meals or opting for campus dining plans instead of frequent restaurant takeout.",
    "Shopping": "Implement the 48-hour rule for non-essential purchases before placing online orders to avoid impulse buys.",
    "Entertainment": "Review your active streaming/gaming subscriptions and share family plans with friends.",
    "Transportation": "Utilize student transit passes or shared carpools/metro rides for daily college commutes.",
    "Bills & Utilities": "Audit recurring postpaid plans, turn off idle appliances, and check for student discounted mobile/broadband plans.",
    "Travel": "Book weekend travel tickets 3-4 weeks in advance via student discount fares on IRCTC or bus portals.",
    "Education": "Explore open-source textbooks, library lending, and student academic software licenses.",
    "Healthcare": "Check university health center benefits and maintain a basic medicine first-aid kit.",
    "Personal Care": "Purchase grooming essentials in value packs or during seasonal sales.",
    "Others": "Regularly tag uncategorized miscellaneous expenses to keep accurate spending visibility."
}


def generate_smart_insights(year: int, month: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate dynamic, rule-based financial insights and actionable advice
    derived strictly from recorded database transactions.
    """
    insights: List[Dict[str, Any]] = []

    # 1. Fetch current month datasets
    cat_df = get_category_wise_spending(year, month, db_path=db_path)
    mom_comp = compare_monthly_spending(year, month, db_path=db_path)
    budget_sum = get_overall_budget_summary(year, month, db_path=db_path)
    cat_budgets = get_category_budgets_table(year, month, db_path=db_path)
    
    # Financial summary
    cur_income_records = get_income_by_month(year, month, db_path=db_path)
    total_income = sum(float(r["amount"]) for r in cur_income_records)
    total_expense = mom_comp["current_total"]

    # RULE 0: Empty Data Guard
    if cat_df.empty and total_income == 0:
        insights.append({
            "category": "Getting Started",
            "type": "info",
            "icon": "💡",
            "headline": "No Transaction Data for this Month",
            "detail": f"No income or expense records found for {calendar.month_name[month]} {year}.",
            "action_tip": "Click 'Load Demo Sample Data' in the sidebar to populate realistic student records, or add your first transaction via 'Add Expense'."
        })
        return insights

    # RULE 1: Highest Spending Category Identification
    if not cat_df.empty:
        top_row = cat_df.iloc[0]
        top_cat = top_row["category"]
        top_amt = top_row["total_amount"]
        top_pct = top_row["percentage"]
        icon = top_row["icon"]

        insights.append({
            "category": "Peak Expenditure",
            "type": "info" if top_pct < 40 else "warning",
            "icon": icon,
            "headline": f"{top_cat} is your largest expense",
            "detail": f"{top_cat} accounts for {top_pct:.1f}% (₹{top_amt:,.2f}) of your total expenses this month.",
            "action_tip": CATEGORY_RECOMMENDATIONS.get(top_cat, "Review your largest expense to identify cost-saving opportunities.")
        })

    # RULE 2: High Concentration Risk (Categories consuming unusually high portion of total spend)
    if not cat_df.empty:
        # Check if top category or any category consumes >= 40%
        unusual_spending = cat_df[cat_df["percentage"] >= 35.0]
        for _, row in unusual_spending.iterrows():
            insights.append({
                "category": "Concentration Warning",
                "type": "warning",
                "icon": "⚠️",
                "headline": f"Unusually high spending in {row['category']}",
                "detail": f"{row['category']} consumes {row['percentage']:.1f}% of total outflow (₹{row['total_amount']:,.2f}).",
                "action_tip": f"Setting a specific spending limit in Budget Manager can help regulate {row['category']} expenses."
            })

    # RULE 3: Month-over-Month (MoM) Trend Comparison
    prev_month_name = calendar.month_name[mom_comp["prev_month"]]
    if mom_comp["prev_total"] > 0:
        trend = mom_comp["trend"]
        diff = mom_comp["diff"]
        pct = mom_comp["pct_change"]

        if trend == "increased":
            insights.append({
                "category": "MoM Trend",
                "type": "warning" if pct > 15 else "info",
                "icon": "📈",
                "headline": f"Expenses increased by {pct:.1f}% compared to {prev_month_name}",
                "detail": f"You have spent ₹{diff:,.2f} more than last month's total of ₹{mom_comp['prev_total']:,.2f}.",
                "action_tip": "Check which categories escalated and consider cutting discretionary purchases."
            })
        elif trend == "decreased":
            insights.append({
                "category": "MoM Trend",
                "type": "success",
                "icon": "📉",
                "headline": f"Great job! Spending decreased by {abs(pct):.1f}%",
                "detail": f"Your spending is down by ₹{diff:,.2f} compared to {prev_month_name} (₹{mom_comp['prev_total']:,.2f}).",
                "action_tip": "Maintain this disciplined trajectory and allocate the surplus to your savings."
            })
        else:
            insights.append({
                "category": "MoM Trend",
                "type": "info",
                "icon": "➖",
                "headline": f"Spending is unchanged compared to {prev_month_name}",
                "detail": f"Monthly expenses match last month's total of ₹{mom_comp['prev_total']:,.2f}.",
                "action_tip": "Look for discretionary areas where you can trim expenses to increase savings."
            })
    elif total_expense > 0:
        insights.append({
            "category": "MoM Trend",
            "type": "info",
            "icon": "ℹ️",
            "headline": f"Spending tracking active for {calendar.month_name[month]}",
            "detail": f"Total spending is ₹{total_expense:,.2f}. No expenses were recorded in {prev_month_name}.",
            "action_tip": "Continue logging transactions to generate automated month-over-month comparisons."
        })

    # Category-level jump detection across months (supports new category expenses via outer join)
    prev_cat_df = get_category_wise_spending(mom_comp["prev_year"], mom_comp["prev_month"], db_path=db_path)
    if not cat_df.empty:
        if not prev_cat_df.empty:
            merged_cats = pd.merge(
                cat_df[["category", "total_amount"]],
                prev_cat_df[["category", "total_amount"]],
                on="category",
                suffixes=("_cur", "_prev"),
                how="outer"
            ).fillna(0.0)
        else:
            merged_cats = cat_df[["category", "total_amount"]].copy()
            merged_cats.rename(columns={"total_amount": "total_amount_cur"}, inplace=True)
            merged_cats["total_amount_prev"] = 0.0

        merged_cats["increase"] = merged_cats["total_amount_cur"] - merged_cats["total_amount_prev"]
        merged_cats["pct_increase"] = merged_cats.apply(
            lambda r: round((r["increase"] / r["total_amount_prev"] * 100), 1) if r["total_amount_prev"] > 0 else 100.0,
            axis=1
        )

        # Detect categories with significant jump (> ₹500 and > 20% or new category > ₹500)
        jumps = merged_cats[(merged_cats["increase"] > 500) & (merged_cats["pct_increase"] > 20)]
        for _, jrow in jumps.head(2).iterrows():
            jcat = jrow["category"]
            if jrow["total_amount_prev"] > 0:
                detail_text = f"{jcat} spending rose by ₹{jrow['increase']:,.2f} (+{jrow['pct_increase']}%) compared to {prev_month_name}."
            else:
                detail_text = f"You spent ₹{jrow['total_amount_cur']:,.2f} on {jcat} this month (no spending in {prev_month_name})."

            insights.append({
                "category": "Category Escalation",
                "type": "warning",
                "icon": get_category_icon(jcat),
                "headline": f"Your {jcat} expenses are higher than last month",
                "detail": detail_text,
                "action_tip": CATEGORY_RECOMMENDATIONS.get(jcat, "Review specific transactions to identify unexpected charges.")
            })

    # RULE 4: Budget Pacing and Utilization Alerts
    if budget_sum["has_budget"]:
        tier = budget_sum["tier"]
        util = budget_sum["utilization"]
        rem = budget_sum["remaining"]

        if tier == "exceeded":
            insights.append({
                "category": "Budget Alert",
                "type": "warning",
                "icon": "🔴",
                "headline": f"Monthly budget exceeded by ₹{abs(rem):,.2f}",
                "detail": f"You have utilized {util:.1f}% of your allocated ₹{budget_sum['budget_amount']:,.2f} budget.",
                "action_tip": "Pause all discretionary spending (Shopping, Entertainment, Dining out) for the remainder of the month."
            })
        elif tier == "warning":
            insights.append({
                "category": "Budget Alert",
                "type": "warning",
                "icon": "🟠",
                "headline": f"You have already used {util:.1f}% of your monthly budget",
                "detail": f"Only ₹{rem:,.2f} remains in your overall budget limit.",
                "action_tip": "Slow down your spending pace to avoid overshooting your budget before month-end."
            })
        elif tier == "caution":
            insights.append({
                "category": "Budget Alert",
                "type": "info",
                "icon": "🟡",
                "headline": f"Budget Caution: {util:.1f}% utilized",
                "detail": f"You have spent ₹{budget_sum['spent_amount']:,.2f} of your ₹{budget_sum['budget_amount']:,.2f} allowance.",
                "action_tip": "Track daily expenditures closely to stay within the safe 75% threshold."
            })
        elif tier == "normal" and util > 0:
            insights.append({
                "category": "Budget Status",
                "type": "success",
                "icon": "🟢",
                "headline": f"Budget pacing is on track ({util:.1f}% used)",
                "detail": f"₹{rem:,.2f} is safely available for remaining expenses this month.",
                "action_tip": "Keep maintaining your balanced spending habits!"
            })

    # RULE 5: Savings Health & Cashflow Deficit Analysis
    if total_income > 0:
        net_balance = total_income - total_expense
        savings_ratio = (net_balance / total_income) * 100.0

        if net_balance < 0:
            insights.append({
                "category": "Cash Flow Deficit",
                "type": "warning",
                "icon": "🚨",
                "headline": f"Deficit Alert: Expenses exceed income by ₹{abs(net_balance):,.2f}",
                "detail": f"You earned ₹{total_income:,.2f} but spent ₹{total_expense:,.2f}. Cash flow is negative.",
                "action_tip": "Temporarily halt non-essential purchases and review alternative income streams (freelancing, tutoring)."
            })
        elif savings_ratio >= 25.0:
            insights.append({
                "category": "Savings Milestone",
                "type": "success",
                "icon": "🏆",
                "headline": f"Outstanding savings rate of {savings_ratio:.1f}%!",
                "detail": f"You have saved ₹{net_balance:,.2f} from this month's income of ₹{total_income:,.2f}.",
                "action_tip": "Consider allocating a portion of your savings to an emergency fund or a student recurring deposit."
            })
        elif 0 <= savings_ratio < 15.0:
            insights.append({
                "category": "Savings Buffer",
                "type": "info",
                "icon": "🪙",
                "headline": f"Modest savings buffer ({savings_ratio:.1f}%)",
                "detail": f"Net savings are ₹{net_balance:,.2f}. A healthy student target is at least 20%.",
                "action_tip": "Identify one or two small daily expense leaks to boost your monthly savings buffer."
            })

    return insights
