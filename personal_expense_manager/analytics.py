"""
Analytics Module for Personal Expenses & Smart Budget Management System
----------------------------------------------------------------------
Academic Demonstration Concepts:
- Zero-division defensive calculations
- Pandas groupby, aggregate, and time-series resampling
- Plotly Express and Graph Objects for interactive data visualization
- SaaS navy/slate visual styling and color harmonies
- Statistical indicators (averages, ratios, percentages)
"""

import calendar
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database import (
    get_all_expenses,
    get_expenses_by_month,
    get_all_income,
    get_income_by_month
)
from expense_manager import (
    CATEGORIES,
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    get_category_wise_spending,
    get_monthly_expense_total
)
from income_manager import get_monthly_income_total


# ---------------------------------------------------------------------------
# FEATURE 9: AVERAGE EXPENSE CALCULATIONS
# ---------------------------------------------------------------------------

def calculate_average_metrics(year: int, month: int, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate average daily, monthly, per-transaction, and category-wise spending.
    Strictly safeguards against ZeroDivisionError and empty databases.
    """
    expenses = get_expenses_by_month(year, month, db_path=db_path)
    all_expenses = get_all_expenses(db_path=db_path)

    total_monthly_expense = sum(float(r["amount"]) for r in expenses)
    tx_count_monthly = len(expenses)

    # 1. Average Daily Expenditure in the selected month
    # Number of days in the specific month (handles leap years via calendar.monthrange)
    _, days_in_month = calendar.monthrange(year, month)
    
    # If viewing current month, optionally use elapsed days so daily avg isn't artificially deflated
    today = date.today()
    if year == today.year and month == today.month:
        effective_days = max(1, today.day)
    else:
        effective_days = max(1, days_in_month)

    avg_daily = total_monthly_expense / effective_days if effective_days > 0 else 0.0

    # 2. Average Expenditure per Transaction
    avg_per_tx = total_monthly_expense / tx_count_monthly if tx_count_monthly > 0 else 0.0

    # 3. Average Monthly Expenditure across all recorded history
    if all_expenses:
        df_all = pd.DataFrame(all_expenses)
        df_all["year_month"] = df_all["date"].str.slice(0, 7)
        monthly_totals = df_all.groupby("year_month")["amount"].sum()
        total_unique_months = max(1, len(monthly_totals))
        avg_monthly_all_time = df_all["amount"].sum() / total_unique_months
    else:
        avg_monthly_all_time = 0.0

    # 4. Average Spending by Category in current month
    avg_by_cat: Dict[str, float] = {}
    if expenses:
        df_cur = pd.DataFrame(expenses)
        cat_grouped = df_cur.groupby("category")["amount"].agg(["sum", "count"]).reset_index()
        for _, row in cat_grouped.iterrows():
            avg_by_cat[row["category"]] = round(row["sum"] / row["count"], 2)

    return {
        "avg_daily": round(avg_daily, 2),
        "avg_per_transaction": round(avg_per_tx, 2),
        "avg_monthly_all_time": round(avg_monthly_all_time, 2),
        "avg_by_category": avg_by_cat,
        "total_monthly_expense": total_monthly_expense,
        "tx_count": tx_count_monthly,
        "effective_days": effective_days,
        "days_in_month": days_in_month
    }


# ---------------------------------------------------------------------------
# FEATURE 8: PLOTLY CHARTS & VISUALIZATIONS
# ---------------------------------------------------------------------------

# Common layout template for SaaS aesthetic
PLOT_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#1E293B"),
    margin=dict(l=20, r=20, t=40, b=20),
    hoverlabel=dict(bgcolor="#0F172A", font_size=12, font_color="#FFFFFF")
)


def plot_category_pie_chart(cat_df: pd.DataFrame) -> Optional[go.Figure]:
    """
    1. Pie/Donut Chart: Category-wise expense distribution for selected month.
    Uses designated category colors and clean percentage callouts.
    """
    if cat_df.empty or cat_df["total_amount"].sum() <= 0:
        return None

    # Map colors according to the category names
    color_map = {cat: CATEGORY_COLORS.get(cat, "#8D99AE") for cat in cat_df["category"]}

    fig = px.pie(
        cat_df,
        names="category",
        values="total_amount",
        hole=0.45,
        color="category",
        color_discrete_map=color_map
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>",
        marker=dict(line=dict(color="#FFFFFF", width=2))
    )

    fig.update_layout(
        **PLOT_LAYOUT_DEFAULTS,
        title=dict(text="<b>Expense Distribution by Category</b>", font=dict(size=16, color="#0F172A")),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )

    return fig


def plot_monthly_expense_bar(year: int, db_path: Optional[str] = None) -> Optional[go.Figure]:
    """
    2. Bar Chart: Monthly expense comparison across the selected calendar year.
    Displays trend bars for months Jan through Dec.
    """
    all_expenses = get_all_expenses(db_path=db_path)
    if not all_expenses:
        return None

    df = pd.DataFrame(all_expenses)
    df["year"] = pd.to_datetime(df["date"]).dt.year
    df["month"] = pd.to_datetime(df["date"]).dt.month
    df_year = df[df["year"] == year]

    # Pre-populate all 12 months with 0.0
    month_names = [calendar.month_abbr[m] for m in range(1, 13)]
    monthly_data = {m: 0.0 for m in range(1, 13)}

    if not df_year.empty:
        grouped = df_year.groupby("month")["amount"].sum().to_dict()
        for m, amt in grouped.items():
            monthly_data[m] = float(amt)

    summary_df = pd.DataFrame({
        "Month": month_names,
        "Month_Num": list(range(1, 13)),
        "Total_Expenses": [monthly_data[m] for m in range(1, 13)]
    })

    if summary_df["Total_Expenses"].sum() == 0:
        return None

    fig = px.bar(
        summary_df,
        x="Month",
        y="Total_Expenses",
        text="Total_Expenses",
        color="Total_Expenses",
        color_continuous_scale=[[0, "#93C5FD"], [1, "#1E3A8A"]]
    )

    fig.update_traces(
        texttemplate="₹%{y:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Total Expenses: ₹%{y:,.2f}<extra></extra>",
        marker_line_color="#1E3A8A",
        marker_line_width=1.5
    )

    fig.update_layout(
        **PLOT_LAYOUT_DEFAULTS,
        title=dict(text=f"<b>Monthly Expenses Trend ({year})</b>", font=dict(size=16, color="#0F172A")),
        xaxis=dict(title="Month", showgrid=False),
        yaxis=dict(title="Expenses (₹)", showgrid=True, gridcolor="#E2E8F0"),
        coloraxis_showscale=False
    )

    return fig


def plot_daily_spending_line(year: int, month: int, db_path: Optional[str] = None) -> Optional[go.Figure]:
    """
    3. Line Chart: Daily spending trends for the selected month.
    Shows day-by-day expenditure with markers and cumulative trend.
    """
    expenses = get_expenses_by_month(year, month, db_path=db_path)
    if not expenses:
        return None

    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.day

    # Daily aggregation
    daily_grouped = df.groupby("day")["amount"].sum().reset_index()

    # Create full month timeline
    _, days_in_month = calendar.monthrange(year, month)
    full_month = pd.DataFrame({"day": list(range(1, days_in_month + 1))})
    merged = pd.merge(full_month, daily_grouped, on="day", how="left").fillna(0.0)
    merged["cumulative"] = merged["amount"].cumsum()

    fig = go.Figure()

    # Daily expense bar / markers
    fig.add_trace(go.Bar(
        x=merged["day"],
        y=merged["amount"],
        name="Daily Spending",
        marker_color="#3B82F6",
        hovertemplate="Day %{x}: ₹%{y:,.2f}<extra></extra>",
        opacity=0.75
    ))

    # Cumulative trend line
    fig.add_trace(go.Scatter(
        x=merged["day"],
        y=merged["cumulative"],
        mode="lines+markers",
        name="Cumulative Spending",
        line=dict(color="#1E3A8A", width=3, dash="solid"),
        marker=dict(size=5, color="#1E3A8A"),
        yaxis="y2",
        hovertemplate="Cumulative (Day %{x}): ₹%{y:,.2f}<extra></extra>"
    ))

    month_name = calendar.month_name[month]
    fig.update_layout(
        **PLOT_LAYOUT_DEFAULTS,
        title=dict(text=f"<b>Daily Spending Timeline ({month_name} {year})</b>", font=dict(size=16, color="#0F172A")),
        xaxis=dict(title="Day of Month", tickmode="linear", dtick=2, showgrid=False),
        yaxis=dict(title="Daily Amount (₹)", showgrid=True, gridcolor="#E2E8F0"),
        yaxis2=dict(title="Cumulative (₹)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )

    return fig


def plot_income_vs_expense_bar(year: int, db_path: Optional[str] = None) -> Optional[go.Figure]:
    """
    4. Bar Chart: Income versus Expenses across all months of the year.
    Side-by-side grouped bars for direct visual cash flow comparison.
    """
    all_expenses = get_all_expenses(db_path=db_path)
    all_income = get_all_income(db_path=db_path)

    if not all_expenses and not all_income:
        return None

    month_names = [calendar.month_abbr[m] for m in range(1, 13)]
    expense_data = {m: 0.0 for m in range(1, 13)}
    income_data = {m: 0.0 for m in range(1, 13)}

    if all_expenses:
        df_exp = pd.DataFrame(all_expenses)
        df_exp["year"] = pd.to_datetime(df_exp["date"]).dt.year
        df_exp["month"] = pd.to_datetime(df_exp["date"]).dt.month
        df_exp_yr = df_exp[df_exp["year"] == year]
        for m, val in df_exp_yr.groupby("month")["amount"].sum().to_dict().items():
            expense_data[m] = float(val)

    if all_income:
        df_inc = pd.DataFrame(all_income)
        df_inc["year"] = pd.to_datetime(df_inc["date"]).dt.year
        df_inc["month"] = pd.to_datetime(df_inc["date"]).dt.month
        df_inc_yr = df_inc[df_inc["year"] == year]
        for m, val in df_inc_yr.groupby("month")["amount"].sum().to_dict().items():
            income_data[m] = float(val)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=month_names,
        y=[income_data[m] for m in range(1, 13)],
        name="Income",
        marker_color="#10B981",
        hovertemplate="<b>%{x} Income:</b> ₹%{y:,.2f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=month_names,
        y=[expense_data[m] for m in range(1, 13)],
        name="Expenses",
        marker_color="#EF4444",
        hovertemplate="<b>%{x} Expenses:</b> ₹%{y:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        **PLOT_LAYOUT_DEFAULTS,
        title=dict(text=f"<b>Income vs Expenses Comparison ({year})</b>", font=dict(size=16, color="#0F172A")),
        barmode="group",
        xaxis=dict(title="Month", showgrid=False),
        yaxis=dict(title="Amount (₹)", showgrid=True, gridcolor="#E2E8F0"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )

    return fig
def plot_category_comparison_bar(cat_df: pd.DataFrame) -> Optional[go.Figure]:
    """
    5. Category Comparison: Spending across different categories.
    Ranked horizontal bar chart showing expenditure comparisons with category colors and percentage badges.
    """
    if cat_df.empty or cat_df["total_amount"].sum() <= 0:
        return None

    df_sorted = cat_df.sort_values(by="total_amount", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[f"{row['icon']} {row['category']}" for _, row in df_sorted.iterrows()],
        x=df_sorted["total_amount"],
        orientation="h",
        marker=dict(
            color=[row["color"] for _, row in df_sorted.iterrows()],
            line=dict(color="#1E3A8A", width=1)
        ),
        text=[f"₹{amt:,.2f} ({pct}%)" for amt, pct in zip(df_sorted["total_amount"], df_sorted["percentage"])],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Total Spent: ₹%{x:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        **PLOT_LAYOUT_DEFAULTS,
        title=dict(text="<b>Category Comparison: Spending Across Categories</b>", font=dict(size=16, color="#0F172A")),
        xaxis=dict(title="Amount (₹)", showgrid=True, gridcolor="#E2E8F0"),
        yaxis=dict(title="", showgrid=False),
        height=max(360, len(df_sorted) * 42),
        showlegend=False
    )

    return fig



def plot_budget_vs_actual_bar(budget_df: pd.DataFrame) -> Optional[go.Figure]:
    """
    5. Category Comparison: Spending across different categories vs allocated budget.
    Horizontal grouped bar chart showing Budget vs Actual Spent.
    """
    if budget_df.empty:
        return None

    # Filter categories that have either spending > 0 or budget > 0
    filtered = budget_df[(budget_df["budget"] > 0) | (budget_df["spent"] > 0)].copy()
    if filtered.empty:
        return None

    # Sort by spent descending
    filtered = filtered.sort_values(by="spent", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=filtered["category"],
        x=filtered["budget"],
        name="Allocated Budget",
        orientation="h",
        marker_color="#94A3B8",
        hovertemplate="<b>%{y} Budget:</b> ₹%{x:,.2f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        y=filtered["category"],
        x=filtered["spent"],
        name="Actual Spent",
        orientation="h",
        marker_color="#3B82F6",
        hovertemplate="<b>%{y} Spent:</b> ₹%{x:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        **PLOT_LAYOUT_DEFAULTS,
        title=dict(text="<b>Category Comparison: Budget vs Actual Spent</b>", font=dict(size=16, color="#0F172A")),
        barmode="group",
        xaxis=dict(title="Amount (₹)", showgrid=True, gridcolor="#E2E8F0"),
        yaxis=dict(title="Category", showgrid=False),
        height=max(360, len(filtered) * 45),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )

    return fig


def plot_savings_gauge(savings_pct: float, balance: float) -> go.Figure:
    """
    Visual gauge chart displaying user's savings rate percentage.
    Ranges from 0% to 100% (or negative deficit).
    """
    # Clamp display for needle while showing actual in text
    display_val = max(0.0, min(100.0, savings_pct))
    bar_color = "#10B981" if savings_pct >= 20.0 else ("#F59E0B" if savings_pct >= 0 else "#EF4444")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=display_val,
        number=dict(suffix="%", font=dict(size=28, color=bar_color)),
        title=dict(text=f"<b>Savings Rate</b><br><span style='font-size:12px;color:#64748B'>Net: ₹{balance:,.2f}</span>", font=dict(size=14)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#94A3B8"),
            bar=dict(color=bar_color, thickness=0.3),
            bgcolor="#F1F5F9",
            borderwidth=1,
            bordercolor="#E2E8F0",
            steps=[
                dict(range=[0, 20], color="#FEE2E2"),
                dict(range=[20, 50], color="#FEF3C7"),
                dict(range=[50, 100], color="#D1FAE5")
            ],
            threshold=dict(
                line=dict(color="#1E3A8A", width=3),
                thickness=0.75,
                value=20.0  # 20% healthy savings benchmark
            )
        )
    ))

    fig.update_layout(
        **PLOT_LAYOUT_DEFAULTS,
        height=220,
        margin=dict(l=20, r=20, t=30, b=10)
    )

    return fig
