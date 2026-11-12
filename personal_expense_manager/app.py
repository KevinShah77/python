"""
Personal Expenses & Smart Budget Management System
--------------------------------------------------
Main Application Entrypoint (Streamlit)

BTech CSE Python Programming Mini Project
Showcasing:
- Modular Python architecture
- SQLite persistent database operations
- Pandas data aggregation
- Plotly interactive visualizations
- ReportLab PDF export & CSV downloads
- Rule-based smart financial insights
- Responsive SaaS dashboard styling
"""

import os
import sys
import calendar
from datetime import datetime, date
import pandas as pd
import streamlit as st

# Ensure local module directory is in Python path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from database import (
    init_db,
    has_data,
    has_sample_data,
    seed_sample_data,
    clear_sample_data,
    reset_all_data,
    get_available_months_and_years,
    get_all_expenses,
    get_all_income,
    get_unified_transactions,
    delete_expense,
    delete_income,
    delete_budget_by_category
)
from expense_manager import (
    CATEGORIES,
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    PAYMENT_METHODS,
    add_new_expense,
    edit_expense,
    remove_expense,
    get_monthly_expense_total,
    get_category_wise_spending,
    compare_monthly_spending,
    get_category_icon,
    get_category_color
)
from income_manager import (
    INCOME_SOURCES,
    INCOME_ICONS,
    INCOME_COLORS,
    add_new_income,
    edit_income,
    remove_income,
    get_monthly_income_total,
    get_monthly_financial_summary,
    get_source_wise_income,
    get_income_icon
)
from budget_manager import (
    save_budget,
    get_overall_budget_summary,
    get_category_budgets_table,
    get_active_budget_alerts
)
from analytics import (
    calculate_average_metrics,
    plot_category_pie_chart,
    plot_monthly_expense_bar,
    plot_daily_spending_line,
    plot_income_vs_expense_bar,
    plot_category_comparison_bar,
    plot_budget_vs_actual_bar,
    plot_savings_gauge
)
from insights import generate_smart_insights
from reports import generate_csv_report, generate_pdf_report


# ---------------------------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION & STYLING
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Personal Expenses & Smart Budget Management System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema on startup
init_db()

# Custom SaaS styling: dark navy (#1E3A8A), slate, clean cards, subtle shadows
CUSTOM_CSS = """
<style>
    /* Global Font & Header */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Metric Card Styling */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.05);
        margin-bottom: 12px;
        transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(15, 23, 42, 0.08);
    }
    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-sub {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 4px;
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-normal { background-color: #D1FAE5; color: #065F46; }
    .badge-caution { background-color: #FEF3C7; color: #92400E; }
    .badge-warning { background-color: #FFEDD5; color: #9A3412; }
    .badge-exceeded { background-color: #FEE2E2; color: #991B1B; }

    /* Insight Card */
    .insight-box {
        background: #F8FAFC;
        border-left: 4px solid #1E3A8A;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .insight-headline {
        font-weight: 600;
        font-size: 15px;
        color: #0F172A;
    }
    .insight-detail {
        font-size: 13px;
        color: #475569;
        margin-top: 4px;
    }
    .insight-tip {
        font-size: 12px;
        font-style: italic;
        color: #1E3A8A;
        margin-top: 6px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SIDEBAR: LOGO, NAVIGATION & CONTROLS
# ---------------------------------------------------------------------------

with st.sidebar:
    # Logo display
    logo_path = os.path.join(APP_DIR, "assets", "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=240)
    else:
        st.title("💼 SmartBudget")

    st.markdown("<p style='font-size:12px;color:#64748B;margin-top:-10px;'>Personal Expenses & Budget System</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Navigation menu
    PAGES = [
        "📊 Dashboard",
        "💸 Add Expense",
        "💰 Income Management",
        "📜 Transactions",
        "🎯 Budget Manager",
        "📈 Analytics & Reports"
    ]
    selected_page = st.radio("Navigation", PAGES, index=0)

    st.markdown("---")
    st.subheader("🗓️ Active Period")

    # Fetch available periods from DB
    available_periods = get_available_months_and_years()
    today = date.today()
    if (today.year, today.month) not in available_periods:
        available_periods.insert(0, (today.year, today.month))

    period_labels = [f"{calendar.month_name[m]} {y}" for (y, m) in available_periods]
    
    # Safely clamp selected period index to valid bounds
    cur_idx = st.session_state.get("selected_period_idx", 0)
    if cur_idx >= len(period_labels) or cur_idx < 0:
        cur_idx = 0
        st.session_state["selected_period_idx"] = 0

    selected_label = st.selectbox(
        "Select Month & Year",
        period_labels,
        index=cur_idx,
        key="period_selector"
    )
    if selected_label in period_labels:
        st.session_state["selected_period_idx"] = period_labels.index(selected_label)
    else:
        st.session_state["selected_period_idx"] = 0
    sel_year, sel_month = available_periods[st.session_state["selected_period_idx"]]

    st.markdown("---")
    st.subheader("⚙️ Sample Data Controls")

    # Demonstration buttons for evaluator
    if not has_sample_data():
        if st.button("🚀 Load Demo Sample Data", use_container_width=True, type="primary"):
            counts = seed_sample_data(reference_date=today)
            st.success(f"Loaded {counts['expenses']} expenses, {counts['income']} income, {counts['budgets']} budgets!")
            st.rerun()
    else:
        if st.button("🧹 Clear Demo Sample Data", use_container_width=True):
            counts = clear_sample_data()
            st.info(f"Cleared {counts['expenses']} demo expenses, {counts['income']} demo income records.")
            st.rerun()

    with st.expander("⚠️ Database Reset"):
        confirm_reset = st.checkbox("Confirm wipe all data")
        if st.button("Delete Everything", disabled=not confirm_reset, use_container_width=True):
            reset_all_data()
            st.warning("All records deleted from SQLite.")
            st.rerun()

    st.markdown("<div style='font-size:11px;color:#94A3B8;text-align:center;margin-top:20px;'>BTech CSE Mini Project &bull; Python</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PAGE 1: USER DASHBOARD
# ---------------------------------------------------------------------------

if selected_page == "📊 Dashboard":
    month_name = calendar.month_name[sel_month]
    st.title(f"📊 Financial Dashboard &mdash; {month_name} {sel_year}")
    st.markdown(f"Overview of income, expenses, and budget utilization for **{month_name} {sel_year}**.")

    # Calculate financial overview
    fin_summary = get_monthly_financial_summary(sel_year, sel_month)
    overall_budget = get_overall_budget_summary(sel_year, sel_month)
    mom = compare_monthly_spending(sel_year, sel_month)

    # 1. Five Summary Cards
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💵 Total Income</div>
            <div class="metric-value" style="color: #10B981;">₹{fin_summary['income']:,.2f}</div>
            <div class="metric-sub">Recorded inflow</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💸 Total Expenses</div>
            <div class="metric-value" style="color: #EF4444;">₹{fin_summary['expenses']:,.2f}</div>
            <div class="metric-sub">{mom['trend_icon']} {mom['pct_change']}% vs last month</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        bal_color = "#10B981" if fin_summary['balance'] >= 0 else "#EF4444"
        bal_status = f"{fin_summary['savings_pct']}% saved" if fin_summary['balance'] >= 0 else "DEFICIT"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🪙 Remaining Balance</div>
            <div class="metric-value" style="color: {bal_color};">₹{fin_summary['balance']:,.2f}</div>
            <div class="metric-sub">{bal_status}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        bud_text = f"₹{overall_budget['budget_amount']:,.2f}" if overall_budget['has_budget'] else "Not Set"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🎯 Monthly Budget</div>
            <div class="metric-value" style="color: #1E3A8A;">{bud_text}</div>
            <div class="metric-sub">Limit for {month_name}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        util_val = f"{overall_budget['utilization']:.1f}%" if overall_budget['has_budget'] else "0.0%"
        badge_cls = f"badge-{overall_budget['tier']}" if overall_budget['has_budget'] else "badge-normal"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📊 Budget Used</div>
            <div class="metric-value" style="color: {overall_budget['color']};">{util_val}</div>
            <div class="metric-sub"><span class="badge {badge_cls}">{overall_budget['label']}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 2. Budget Alert Notifications Banner
    alerts = get_active_budget_alerts(sel_year, sel_month)
    if alerts:
        for alert in alerts:
            if alert["tier"] == "exceeded":
                st.error(f"🚨 **{alert['label']}**: {alert['message']}")
            elif alert["tier"] == "warning":
                st.warning(f"⚠️ **{alert['label']}**: {alert['message']}")
            elif alert["tier"] == "caution":
                st.info(f"🔔 **{alert['label']}**: {alert['message']}")

    # 3. Overall Budget Progress Bar
    if overall_budget["has_budget"]:
        st.markdown(f"**Monthly Budget Progress ({overall_budget['utilization']:.1f}% utilized)**")
        st.progress(overall_budget["progress_val"])
        st.caption(f"Spent ₹{overall_budget['spent_amount']:,.2f} of ₹{overall_budget['budget_amount']:,.2f} &bull; ₹{overall_budget['remaining']:,.2f} remaining.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Main Two-Column Layout
    left_col, right_col = st.columns([1.1, 0.9])

    with left_col:
        # Category-wise Spending Summary
        st.subheader("📑 Category-wise Spending")
        cat_df = get_category_wise_spending(sel_year, sel_month)
        if not cat_df.empty:
            for _, row in cat_df.iterrows():
                cc1, cc2, cc3 = st.columns([2, 3, 2])
                with cc1:
                    st.write(f"{row['icon']} **{row['category']}**")
                with cc2:
                    st.progress(min(1.0, row['percentage'] / 100.0))
                with cc3:
                    st.write(f"₹{row['total_amount']:,.2f} ({row['percentage']}%)")
        else:
            st.info("No expense transactions recorded for this month.")

        st.markdown("---")
        # Month-over-Month Overview
        st.subheader("🗓️ Month-over-Month Comparison")
        prev_month_name = calendar.month_name[mom['prev_month']]
        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Current Month", f"₹{mom['current_total']:,.2f}")
        mcol2.metric(f"Previous Month ({prev_month_name})", f"₹{mom['prev_total']:,.2f}")
        mcol3.metric("Change", f"{mom['trend_icon']} ₹{mom['diff']:,.2f}", f"{mom['pct_change']}%")

    with right_col:
        # Category Distribution Chart
        st.subheader("🍩 Expense Distribution")
        if not cat_df.empty:
            fig_pie = plot_category_pie_chart(cat_df)
            if fig_pie:
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Visual chart will appear once expenses are added.")

        st.markdown("---")
        # Recent Transactions
        st.subheader("🕒 Recent Transactions")
        start_date = f"{sel_year:04d}-{sel_month:02d}-01"
        end_date = f"{sel_year:04d}-{sel_month:02d}-{calendar.monthrange(sel_year, sel_month)[1]:02d}"
        recents = get_unified_transactions(start_date=start_date, end_date=end_date, sort_by="date", sort_order="DESC")

        if recents:
            for tx in recents[:5]:
                is_inc = tx["type"] == "Income"
                tx_icon = "💰" if is_inc else get_category_icon(tx["category_or_source"])
                tx_color = "#10B981" if is_inc else "#EF4444"
                tx_sign = "+" if is_inc else "-"

                t_c1, t_c2 = st.columns([3, 2])
                with t_c1:
                    st.markdown(f"{tx_icon} **{tx['name']}** <span style='font-size:11px;color:#64748B;'>({tx['date']})</span>", unsafe_allow_html=True)
                with t_c2:
                    st.markdown(f"<div style='text-align:right;font-weight:700;color:{tx_color};'>{tx_sign} ₹{float(tx['amount']):,.2f}</div>", unsafe_allow_html=True)
        else:
            st.info("No recent transactions this month.")


# ---------------------------------------------------------------------------
# PAGE 2: ADD & MANAGE EXPENSES (FEATURE 2 & 3)
# ---------------------------------------------------------------------------

elif selected_page == "💸 Add Expense":
    st.title("💸 Expense Management")
    st.markdown("Record daily expenses, update past entries, or categorize transactions.")

    tab_add, tab_manage = st.tabs(["➕ Add New Expense", "✏️ Edit / Delete Expenses"])

    with tab_add:
        st.subheader("Record a New Expense")
        with st.form("add_expense_form", clear_on_submit=True):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                expense_name = st.text_input("Expense Name *", placeholder="e.g. Canteen Lunch, Metro Pass, Laptop Bag")
                amount = st.number_input("Amount (in INR ₹) *", min_value=0.0, step=50.0, format="%.2f")
                category = st.selectbox("Expense Category *", CATEGORIES, index=0)

            with col_e2:
                expense_date = st.date_input("Transaction Date *", value=date.today())
                payment_method = st.selectbox("Payment Method", PAYMENT_METHODS, index=0)
                description = st.text_area("Description / Notes (Optional)", placeholder="Additional details or reference notes")

            submit_expense = st.form_submit_button("💾 Save Expense", type="primary", use_container_width=True)

            if submit_expense:
                success, msg, new_id = add_new_expense(
                    expense_name=expense_name,
                    amount=amount,
                    category=category,
                    date_val=expense_date,
                    payment_method=payment_method,
                    description=description
                )
                if success:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(f"Validation Error: {msg}")

    with tab_manage:
        st.subheader("Edit or Remove Existing Expenses")
        all_exp = get_all_expenses()
        if not all_exp:
            st.info("No expense records in database to manage.")
        else:
            exp_options = {f"#{e['id']} - {e['expense_name']} (₹{e['amount']:,.2f} on {e['date']})": e['id'] for e in all_exp}
            selected_exp_label = st.selectbox("Select Expense Record to Modify", list(exp_options.keys()))
            selected_exp_id = exp_options[selected_exp_label]
            target_exp = next(e for e in all_exp if e["id"] == selected_exp_id)

            with st.form("edit_expense_form"):
                ee_c1, ee_c2 = st.columns(2)
                with ee_c1:
                    edit_name = st.text_input("Expense Name", value=target_exp["expense_name"])
                    edit_amt = st.number_input("Amount (INR ₹)", value=float(target_exp["amount"]), min_value=0.0, step=50.0)
                    edit_cat = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(target_exp["category"]) if target_exp["category"] in CATEGORIES else 0)

                with ee_c2:
                    current_exp_date = datetime.strptime(target_exp["date"], "%Y-%m-%d").date()
                    edit_date = st.date_input("Date", value=current_exp_date)
                    edit_pm = st.selectbox("Payment Method", PAYMENT_METHODS, index=PAYMENT_METHODS.index(target_exp["payment_method"]) if target_exp["payment_method"] in PAYMENT_METHODS else 0)
                    edit_desc = st.text_area("Description", value=target_exp["description"] or "")

                save_edit = st.form_submit_button("Update Expense Details", type="primary", use_container_width=True)
                if save_edit:
                    ok, res = edit_expense(
                        expense_id=selected_exp_id,
                        expense_name=edit_name,
                        amount=edit_amt,
                        category=edit_cat,
                        date_val=edit_date,
                        payment_method=edit_pm,
                        description=edit_desc
                    )
                    if ok:
                        st.success(res)
                        st.rerun()
                    else:
                        st.error(res)

            st.markdown("---")
            st.markdown("#### 🗑️ Delete Expense")
            del_confirm = st.checkbox(f"Confirm deletion of expense #{selected_exp_id} ({target_exp['expense_name']})")
            if st.button("Delete Expense Record", disabled=not del_confirm, type="secondary"):
                dok, dres = remove_expense(selected_exp_id)
                if dok:
                    st.warning(dres)
                    st.rerun()
                else:
                    st.error(dres)


# ---------------------------------------------------------------------------
# PAGE 3: INCOME MANAGEMENT (FEATURE 4)
# ---------------------------------------------------------------------------

elif selected_page == "💰 Income Management":
    st.title("💰 Income Tracking & Management")
    st.markdown("Record allowances, salaries, freelancing payouts, and other income sources.")

    # Summary metric for the active month
    cur_income_total = get_monthly_income_total(sel_year, sel_month)
    month_name = calendar.month_name[sel_month]
    st.info(f"Total Income Recorded for **{month_name} {sel_year}**: **₹{cur_income_total:,.2f}**")

    tab_inc_add, tab_inc_manage = st.tabs(["➕ Record Income", "✏️ Manage Income Records"])

    with tab_inc_add:
        st.subheader("Add Income Record")
        with st.form("add_income_form", clear_on_submit=True):
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                income_source = st.selectbox("Income Source *", INCOME_SOURCES, index=0)
                income_amount = st.number_input("Amount (in INR ₹) *", min_value=0.0, step=500.0, format="%.2f")

            with col_i2:
                income_date = st.date_input("Date Received *", value=date.today())
                income_desc = st.text_area("Description / Notes", placeholder="e.g. Parental monthly deposit, project client advance")

            submit_income = st.form_submit_button("💾 Save Income", type="primary", use_container_width=True)

            if submit_income:
                ok, msg, new_id = add_new_income(
                    income_source=income_source,
                    amount=income_amount,
                    date_val=income_date,
                    description=income_desc
                )
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(f"Validation Error: {msg}")

    with tab_inc_manage:
        st.subheader("Edit or Remove Income Records")
        all_inc = get_all_income()
        if not all_inc:
            st.info("No income records found in the database.")
        else:
            inc_options = {f"#{i['id']} - {i['income_source']} (₹{i['amount']:,.2f} on {i['date']})": i['id'] for i in all_inc}
            selected_inc_label = st.selectbox("Select Income Record to Modify", list(inc_options.keys()))
            selected_inc_id = inc_options[selected_inc_label]
            target_inc = next(i for i in all_inc if i["id"] == selected_inc_id)

            with st.form("edit_income_form"):
                ie_c1, ie_c2 = st.columns(2)
                with ie_c1:
                    edit_source = st.selectbox("Income Source", INCOME_SOURCES, index=INCOME_SOURCES.index(target_inc["income_source"]) if target_inc["income_source"] in INCOME_SOURCES else 0)
                    edit_amt = st.number_input("Amount (INR ₹)", value=float(target_inc["amount"]), min_value=0.0, step=500.0)

                with ie_c2:
                    current_inc_date = datetime.strptime(target_inc["date"], "%Y-%m-%d").date()
                    edit_date = st.date_input("Date Received", value=current_inc_date)
                    edit_desc = st.text_area("Description", value=target_inc["description"] or "")

                save_inc_edit = st.form_submit_button("Update Income Details", type="primary", use_container_width=True)
                if save_inc_edit:
                    iok, ires = edit_income(
                        income_id=selected_inc_id,
                        income_source=edit_source,
                        amount=edit_amt,
                        date_val=edit_date,
                        description=edit_desc
                    )
                    if iok:
                        st.success(ires)
                        st.rerun()
                    else:
                        st.error(ires)

            st.markdown("---")
            st.markdown("#### 🗑️ Delete Income Record")
            del_inc_confirm = st.checkbox(f"Confirm deletion of income #{selected_inc_id} ({target_inc['income_source']})")
            if st.button("Delete Income Record", disabled=not del_inc_confirm, type="secondary"):
                diok, dires = remove_income(selected_inc_id)
                if diok:
                    st.warning(dires)
                    st.rerun()
                else:
                    st.error(dires)


# ---------------------------------------------------------------------------
# PAGE 4: TRANSACTIONS & REPORT EXPORTS (FEATURE 12)
# ---------------------------------------------------------------------------

elif selected_page == "📜 Transactions":
    st.title("📜 Transaction History & Reports")
    st.markdown("Unified ledger of all recorded expenses and income with search, filter, and export capabilities.")

    # Filter controls
    with st.expander("🔍 Search and Filter Transactions", expanded=True):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            search_query = st.text_input("Search Text", placeholder="Search name, description, method...")
        with fc2:
            tx_type = st.selectbox("Transaction Type", ["All", "Expense", "Income"], index=0)
        with fc3:
            all_cat_options = ["All"] + CATEGORIES + INCOME_SOURCES
            filter_cat = st.selectbox("Category / Source", all_cat_options, index=0)
        with fc4:
            sort_by = st.selectbox("Sort By", ["Date (Newest First)", "Date (Oldest First)", "Amount (High to Low)", "Amount (Low to High)"])

        # Date range filters
        dfc1, dfc2 = st.columns(2)
        with dfc1:
            start_date = st.date_input("From Date", value=date(sel_year, sel_month, 1))
        with dfc2:
            _, max_day = calendar.monthrange(sel_year, sel_month)
            end_date = st.date_input("To Date", value=date(sel_year, sel_month, max_day))

    # Parse sorting parameters
    if "Date (Newest First)" in sort_by:
        s_col, s_ord = "date", "DESC"
    elif "Date (Oldest First)" in sort_by:
        s_col, s_ord = "date", "ASC"
    elif "Amount (High to Low)" in sort_by:
        s_col, s_ord = "amount", "DESC"
    else:
        s_col, s_ord = "amount", "ASC"

    # Fetch filtered transactions
    filtered_tx = get_unified_transactions(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        category=filter_cat,
        tx_type=None if tx_type == "All" else tx_type,
        search_query=search_query,
        sort_by=s_col,
        sort_order=s_ord
    )

    st.markdown(f"**Found {len(filtered_tx)} transactions** matching your filter criteria.")

    # Export Buttons
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        csv_data = generate_csv_report(filtered_tx, year=sel_year, month=sel_month)
        st.download_button(
            label="📥 Download Transactions as CSV",
            data=csv_data,
            file_name=f"transactions_{sel_year}_{sel_month:02d}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with exp_col2:
        try:
            pdf_bytes = generate_pdf_report(sel_year, sel_month)
            st.download_button(
                label="📄 Download Monthly Report as PDF",
                data=pdf_bytes,
                file_name=f"finance_report_{sel_year}_{sel_month:02d}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Render Transaction Table
    if filtered_tx:
        table_rows = []
        for tx in filtered_tx:
            is_inc = tx["type"] == "Income"
            amt_formatted = f"+₹{float(tx['amount']):,.2f}" if is_inc else f"-₹{float(tx['amount']):,.2f}"
            icon = get_income_icon(tx["category_or_source"]) if is_inc else get_category_icon(tx["category_or_source"])
            table_rows.append({
                "ID": tx["id"],
                "Date": tx["date"],
                "Type": f"{'🟢 Income' if is_inc else '🔴 Expense'}",
                "Name": tx["name"],
                "Category / Source": f"{icon} {tx['category_or_source']}",
                "Amount": amt_formatted,
                "Payment Method": tx["payment_method"],
                "Notes": tx["description"] or ""
            })

        tx_df = pd.DataFrame(table_rows)
        st.dataframe(tx_df, use_container_width=True, hide_index=True)

        # Feature 12: Interactive Edit and Delete Transactions on Transaction Ledger
        st.markdown("---")
        with st.expander("✏️ Edit or Delete a Transaction from History", expanded=False):
            st.markdown("##### Modify or remove any recorded transaction from the database")
            tx_label_map = {
                f"[{tx['type']}] #{tx['id']} - {tx['name']} (₹{float(tx['amount']):,.2f} on {tx['date']})": tx
                for tx in filtered_tx
            }
            chosen_label = st.selectbox("Select Transaction to Modify", list(tx_label_map.keys()), key="tx_history_picker")
            target_entry = tx_label_map[chosen_label]

            if target_entry["type"] == "Expense":
                with st.form(f"tx_page_edit_expense_{target_entry['id']}"):
                    t_col1, t_col2 = st.columns(2)
                    with t_col1:
                        mod_name = st.text_input("Expense Name", value=target_entry["name"])
                        mod_amt = st.number_input("Amount (INR ₹)", value=float(target_entry["amount"]), min_value=0.01, step=50.0)
                        cur_cat_idx = CATEGORIES.index(target_entry["category_or_source"]) if target_entry["category_or_source"] in CATEGORIES else 0
                        mod_cat = st.selectbox("Category", CATEGORIES, index=cur_cat_idx)
                    with t_col2:
                        parsed_dt = datetime.strptime(target_entry["date"], "%Y-%m-%d").date()
                        mod_date = st.date_input("Date", value=parsed_dt)
                        cur_pm_idx = PAYMENT_METHODS.index(target_entry["payment_method"]) if target_entry["payment_method"] in PAYMENT_METHODS else 0
                        mod_pm = st.selectbox("Payment Method", PAYMENT_METHODS, index=cur_pm_idx)
                        mod_desc = st.text_area("Description", value=target_entry["description"] or "")

                    if st.form_submit_button("Update Expense", type="primary", use_container_width=True):
                        ok, msg = edit_expense(
                            expense_id=target_entry["id"],
                            expense_name=mod_name,
                            amount=mod_amt,
                            category=mod_cat,
                            date_val=mod_date,
                            payment_method=mod_pm,
                            description=mod_desc
                        )
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                st.markdown("###### 🗑️ Delete Expense Transaction")
                del_exp_confirm = st.checkbox(
                    f"Confirm deletion of Expense #{target_entry['id']} ('{target_entry['name']}')",
                    key=f"del_tx_exp_chk_{target_entry['id']}"
                )
                if st.button("Delete Expense Record", disabled=not del_exp_confirm, type="secondary", key=f"del_tx_exp_btn_{target_entry['id']}"):
                    dok, dmsg = remove_expense(target_entry["id"])
                    if dok:
                        st.warning(dmsg)
                        st.rerun()
                    else:
                        st.error(dmsg)

            else:  # Income
                with st.form(f"tx_page_edit_income_{target_entry['id']}"):
                    ti_col1, ti_col2 = st.columns(2)
                    with ti_col1:
                        cur_src_idx = INCOME_SOURCES.index(target_entry["category_or_source"]) if target_entry["category_or_source"] in INCOME_SOURCES else 0
                        mod_src = st.selectbox("Income Source", INCOME_SOURCES, index=cur_src_idx)
                        mod_amt = st.number_input("Amount (INR ₹)", value=float(target_entry["amount"]), min_value=0.01, step=500.0)
                    with ti_col2:
                        parsed_dt = datetime.strptime(target_entry["date"], "%Y-%m-%d").date()
                        mod_date = st.date_input("Date Received", value=parsed_dt)
                        mod_desc = st.text_area("Description", value=target_entry["description"] or "")

                    if st.form_submit_button("Update Income", type="primary", use_container_width=True):
                        iok, imsg = edit_income(
                            income_id=target_entry["id"],
                            income_source=mod_src,
                            amount=mod_amt,
                            date_val=mod_date,
                            description=mod_desc
                        )
                        if iok:
                            st.success(imsg)
                            st.rerun()
                        else:
                            st.error(imsg)

                st.markdown("###### 🗑️ Delete Income Transaction")
                del_inc_confirm = st.checkbox(
                    f"Confirm deletion of Income #{target_entry['id']} ('{target_entry['name']}')",
                    key=f"del_tx_inc_chk_{target_entry['id']}"
                )
                if st.button("Delete Income Record", disabled=not del_inc_confirm, type="secondary", key=f"del_tx_inc_btn_{target_entry['id']}"):
                    diok, dimsg = remove_income(target_entry["id"])
                    if diok:
                        st.warning(dimsg)
                        st.rerun()
                    else:
                        st.error(dimsg)
    else:
        st.info("No transactions match the selected filters.")


# ---------------------------------------------------------------------------
# PAGE 5: BUDGET MANAGER (FEATURE 6 & 7)
# ---------------------------------------------------------------------------

elif selected_page == "🎯 Budget Manager":
    month_name = calendar.month_name[sel_month]
    st.title(f"🎯 Budget Manager &mdash; {month_name} {sel_year}")
    st.markdown("Set overall monthly spending caps and category limits. Monitor utilization and threshold alerts.")

    tab_b_view, tab_b_set = st.tabs(["📊 Budget Overview & Alerts", "⚙️ Set / Update Limits"])

    with tab_b_view:
        # Overall budget summary
        overall = get_overall_budget_summary(sel_year, sel_month)
        st.subheader("🎯 Overall Monthly Budget")

        if overall["has_budget"]:
            b_c1, b_c2, b_c3 = st.columns([1.5, 1.5, 1])
            with b_c1:
                st.metric("Budget Allocated", f"₹{overall['budget_amount']:,.2f}")
            with b_c2:
                st.metric("Total Spent", f"₹{overall['spent_amount']:,.2f}", f"{overall['utilization']:.1f}% utilized")
            with b_c3:
                rem_color = "normal" if overall["remaining"] >= 0 else "inverse"
                st.metric("Remaining", f"₹{overall['remaining']:,.2f}", delta_color=rem_color)

            st.progress(overall["progress_val"])
            st.markdown(f"**Status:** {overall['message']}")
        else:
            st.warning(f"No overall monthly spending limit set for {month_name} {sel_year}. Set one in the 'Set / Update Limits' tab.")

        st.markdown("---")
        st.subheader("📑 Category-wise Budgets & Utilization")

        cat_budget_df = get_category_budgets_table(sel_year, sel_month)
        active_cat_budgets = cat_budget_df[cat_budget_df["budget"] > 0]

        if not active_cat_budgets.empty:
            for _, row in active_cat_budgets.iterrows():
                with st.container():
                    st.markdown(f"#### {row['icon']} {row['category']}")
                    cb_1, cb_2, cb_3, cb_4 = st.columns(4)
                    cb_1.write(f"**Budget:** ₹{row['budget']:,.2f}")
                    cb_2.write(f"**Spent:** ₹{row['spent']:,.2f}")
                    cb_3.write(f"**Remaining:** ₹{row['remaining']:,.2f}")
                    cb_4.markdown(f"<span class='badge badge-{row['tier']}'>{row['status_label']}</span>", unsafe_allow_html=True)

                    st.progress(row["progress_val"])
                    st.caption(row["message"])
                    st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No individual category budgets established for this month.")

        # Plotly Budget vs Actual comparison chart
        st.markdown("---")
        st.subheader("📊 Budget vs Actual Spent Comparison")
        fig_bva = plot_budget_vs_actual_bar(cat_budget_df)
        if fig_bva:
            st.plotly_chart(fig_bva, use_container_width=True)
        else:
            st.caption("Establish category budgets to view visual comparison.")

    with tab_b_set:
        st.subheader("Establish Budget Caps")
        st.markdown("Configure overall spending limits or category budgets for any chosen month.")

        by_c1, by_c2 = st.columns(2)
        with by_c1:
            b_year = st.selectbox("Target Year", [sel_year - 1, sel_year, sel_year + 1], index=1, key="budget_set_year")
        with by_c2:
            b_month = st.selectbox(
                "Target Month",
                list(range(1, 13)),
                index=sel_month - 1,
                format_func=lambda m: f"{m:02d} - {calendar.month_name[m]}",
                key="budget_set_month"
            )

        b_set_type = st.radio("Budget Scope", ["Overall Monthly Budget", "Individual Category Budget"], horizontal=True)

        if b_set_type == "Overall Monthly Budget":
            current_ob = get_overall_budget_summary(b_year, b_month)
            with st.form("set_overall_budget_form"):
                cur_amt = float(current_ob["budget_amount"]) if current_ob["has_budget"] else 20000.0
                new_budget_amt = st.number_input("Overall Spending Cap (INR ₹) *", min_value=0.0, value=cur_amt, step=1000.0)
                submit_ob = st.form_submit_button("💾 Save Overall Budget", type="primary")

                if submit_ob:
                    ok, msg = save_budget("Overall", new_budget_amt, b_month, b_year)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            with st.form("set_category_budget_form"):
                cat_choice = st.selectbox("Select Category *", CATEGORIES)
                cat_budget_amt = st.number_input("Category Spending Cap (INR ₹) *", min_value=0.0, value=3000.0, step=500.0)
                submit_cb = st.form_submit_button("💾 Save Category Budget", type="primary")

                if submit_cb:
                    ok, msg = save_budget(cat_choice, cat_budget_amt, b_month, b_year)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown("---")
        st.subheader("🗑️ Delete Budget Limits")
        active_budgets = cat_budget_df[cat_budget_df["budget"] > 0]
        if not active_budgets.empty:
            del_cat = st.selectbox("Select Budget to Remove", ["Overall"] + list(active_budgets["category"]), key="budget_del_select")
            del_b_confirm = st.checkbox(f"Confirm deletion of budget limit for '{del_cat}' ({sel_month:02d}/{sel_year})", key="budget_del_chk")
            if st.button("Delete Selected Budget", disabled=not del_b_confirm, type="secondary"):
                deleted = delete_budget_by_category(del_cat, sel_year, sel_month)
                if deleted:
                    st.warning(f"Budget for '{del_cat}' removed.")
                    st.rerun()


# ---------------------------------------------------------------------------
# PAGE 6: ANALYTICS & REPORTS (FEATURE 5, 8, 9, 10, 11)
# ---------------------------------------------------------------------------

elif selected_page == "📈 Analytics & Reports":
    month_name = calendar.month_name[sel_month]
    st.title(f"📈 Financial Analytics & Intelligence &mdash; {month_name} {sel_year}")

    tab_charts, tab_avg, tab_insights, tab_savings = st.tabs([
        "📊 Interactive Charts",
        "📐 Average Spending Metrics",
        "🧠 Smart Spending Insights",
        "💰 Savings Tracker"
    ])

    with tab_charts:
        st.subheader("Interactive Visual Analytics")

        c_col1, c_col2 = st.columns(2)
        with c_col1:
            st.markdown("##### 1. Category Expense Distribution")
            cat_df = get_category_wise_spending(sel_year, sel_month)
            pie_fig = plot_category_pie_chart(cat_df)
            if pie_fig:
                st.plotly_chart(pie_fig, use_container_width=True)
            else:
                st.info("No expense data recorded for pie chart.")

        with c_col2:
            st.markdown("##### 2. Monthly Expense Comparison (Year-to-Date)")
            bar_fig = plot_monthly_expense_bar(sel_year)
            if bar_fig:
                st.plotly_chart(bar_fig, use_container_width=True)
            else:
                st.info("No monthly expense trends available.")

        st.markdown("---")

        c_col3, c_col4 = st.columns(2)
        with c_col3:
            st.markdown(f"##### 3. Daily Spending Trends ({month_name} {sel_year})")
            line_fig = plot_daily_spending_line(sel_year, sel_month)
            if line_fig:
                st.plotly_chart(line_fig, use_container_width=True)
            else:
                st.info("No daily transactions recorded for line chart.")

        with c_col4:
            st.markdown(f"##### 4. Monthly Income vs Expenses Comparison ({sel_year})")
            ive_fig = plot_income_vs_expense_bar(sel_year)
            if ive_fig:
                st.plotly_chart(ive_fig, use_container_width=True)
            else:
                st.info("No income/expense records available for comparison.")

        st.markdown("---")
        st.markdown(f"##### 5. Category Comparison: Spending Across Different Categories ({month_name} {sel_year})")
        cat_comp_fig = plot_category_comparison_bar(cat_df)
        if cat_comp_fig:
            st.plotly_chart(cat_comp_fig, use_container_width=True)
        else:
            st.info("No category expenses available for category comparison.")

    with tab_avg:
        st.subheader("📐 Statistical Spending Averages")
        st.markdown("Automated metrics demonstrating mathematical division, null handling, and aggregation.")

        avg_metrics = calculate_average_metrics(sel_year, sel_month)

        a1, a2, a3 = st.columns(3)
        a1.metric("Avg Daily Spending", f"₹{avg_metrics['avg_daily']:,.2f}", f"Over {avg_metrics['effective_days']} active days")
        a2.metric("Avg Per Transaction", f"₹{avg_metrics['avg_per_transaction']:,.2f}", f"{avg_metrics['tx_count']} transactions")
        a3.metric("Avg Monthly Expense (All-Time)", f"₹{avg_metrics['avg_monthly_all_time']:,.2f}", "Across all history")

        st.markdown("---")
        st.markdown("##### Average Spending Per Category (Current Month)")
        if avg_metrics["avg_by_category"]:
            avg_rows = []
            for cat, val in avg_metrics["avg_by_category"].items():
                avg_rows.append({
                    "Category": f"{get_category_icon(cat)} {cat}",
                    "Average Per Transaction (INR)": f"₹{val:,.2f}"
                })
            st.dataframe(pd.DataFrame(avg_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No category expenditures recorded this month.")

    with tab_insights:
        st.subheader("🧠 Smart Rule-Based Spending Insights")
        st.markdown("Automated heuristics detecting spending spikes, concentration risk, and personalized recommendations.")

        smart_insights = generate_smart_insights(sel_year, sel_month)
        for ins in smart_insights:
            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-headline">{ins['icon']} {ins['headline']}</div>
                <div class="insight-detail">{ins['detail']}</div>
                <div class="insight-tip">💡 <b>Recommendation:</b> {ins['action_tip']}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab_savings:
        st.subheader("💰 Savings Tracker & Net Cash Flow")
        fin = get_monthly_financial_summary(sel_year, sel_month)

        s_col1, s_col2 = st.columns([1.1, 0.9])

        with s_col1:
            sm_c1, sm_c2 = st.columns(2)
            with sm_c1:
                st.metric("Total Income Inflow", f"₹{fin['income']:,.2f}")
                st.metric("Net Savings (Balance)", f"₹{fin['balance']:,.2f}", delta_color="normal" if fin['balance'] >= 0 else "inverse")
            with sm_c2:
                st.metric("Total Expense Outflow", f"₹{fin['expenses']:,.2f}")
                st.metric("Savings Percentage", f"{fin['savings_pct']}%", delta_color="normal" if fin['savings_pct'] >= 20 else ("off" if fin['savings_pct'] >= 0 else "inverse"))

            if fin["is_deficit"]:
                st.error(f"🚨 **Deficit Alert:** Your monthly expenses exceed income by ₹{abs(fin['balance']):,.2f}! Reduce discretionary purchases immediately.")
            else:
                st.success(f"✅ **Positive Cash Flow:** You saved {fin['savings_pct']}% of your income this month!")

        with s_col2:
            st.markdown("##### Savings Rate Gauge")
            gauge_fig = plot_savings_gauge(fin["savings_pct"], fin["balance"])
            st.plotly_chart(gauge_fig, use_container_width=True)
