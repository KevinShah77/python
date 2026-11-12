"""
Comprehensive Unit and Integration Test Suite
---------------------------------------------
Personal Expenses & Smart Budget Management System
Testing:
- Database schema and integrity constraints
- Expense CRUD and validation logic
- Income CRUD and validation logic
- Budget evaluation thresholds and alerts (<75%, 75-89%, 90-99%, >=100%)
- Zero-division safety in statistical averages
- Smart rule-based insights generation
- CSV and PDF report generation
- Sample data seeding and clearing
"""

import os
import sys
import tempfile
import pytest
from datetime import date, datetime

# Add personal_expense_manager to path
MODULE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "personal_expense_manager")
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

from database import (
    init_db,
    add_expense,
    get_all_expenses,
    get_expenses_by_month,
    get_expense_by_id,
    update_expense,
    delete_expense,
    add_income,
    get_all_income,
    get_income_by_month,
    get_income_by_id,
    update_income,
    delete_income,
    set_budget,
    get_budgets_by_month,
    get_budget_by_category,
    delete_budget_by_category,
    get_unified_transactions,
    seed_sample_data,
    clear_sample_data,
    reset_all_data,
    has_sample_data
)
from expense_manager import (
    CATEGORIES,
    validate_expense,
    add_new_expense,
    edit_expense,
    remove_expense,
    get_monthly_expense_total,
    get_category_wise_spending,
    compare_monthly_spending
)
from income_manager import (
    INCOME_SOURCES,
    validate_income,
    add_new_income,
    edit_income,
    remove_income,
    get_monthly_income_total,
    get_monthly_financial_summary
)
from budget_manager import (
    evaluate_budget_status,
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
    plot_budget_vs_actual_bar,
    plot_savings_gauge
)
from insights import generate_smart_insights
from reports import generate_csv_report, generate_pdf_report


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database file for isolated testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


# ---------------------------------------------------------------------------
# 1. EXPENSE VALIDATION & CRUD TESTS
# ---------------------------------------------------------------------------

def test_expense_validation():
    # Empty name
    valid, msg = validate_expense("", 100.0, "Food & Dining", "2026-11-01")
    assert not valid
    assert "name is required" in msg.lower()

    # Negative amount
    valid, msg = validate_expense("Coffee", -50.0, "Food & Dining", "2026-11-01")
    assert not valid
    assert "greater than" in msg.lower()

    # Zero amount
    valid, msg = validate_expense("Coffee", 0.0, "Food & Dining", "2026-11-01")
    assert not valid
    assert "greater than" in msg.lower()

    # Non-numeric amount
    valid, msg = validate_expense("Coffee", "abc", "Food & Dining", "2026-11-01")
    assert not valid
    assert "numeric" in msg.lower()

    # Invalid category
    valid, msg = validate_expense("Coffee", 100.0, "InvalidCategory", "2026-11-01")
    assert not valid
    assert "category" in msg.lower()

    # Invalid date
    valid, msg = validate_expense("Coffee", 100.0, "Food & Dining", "not-a-date")
    assert not valid
    assert "date" in msg.lower()

    # Valid expense
    valid, msg = validate_expense("College Books", 1200.0, "Education", "2026-11-04")
    assert valid
    assert msg == ""


def test_expense_crud(temp_db):
    # Add
    ok, msg, exp_id = add_new_expense("Notebooks", 350.0, "Education", "2026-11-02", "Cash", "Class notes", db_path=temp_db)
    assert ok
    assert exp_id is not None

    # Read
    exp = get_expense_by_id(exp_id, db_path=temp_db)
    assert exp is not None
    assert exp["expense_name"] == "Notebooks"
    assert exp["amount"] == 350.0
    assert exp["category"] == "Education"

    # Monthly total
    total = get_monthly_expense_total(2026, 11, db_path=temp_db)
    assert total == 350.0

    # Edit
    e_ok, e_msg = edit_expense(exp_id, "Spiral Notebooks", 400.0, "Education", "2026-11-02", "UPI / GPay / PhonePe", "Updated notes", db_path=temp_db)
    assert e_ok
    exp_updated = get_expense_by_id(exp_id, db_path=temp_db)
    assert exp_updated["expense_name"] == "Spiral Notebooks"
    assert exp_updated["amount"] == 400.0

    # Delete
    d_ok, d_msg = remove_expense(exp_id, db_path=temp_db)
    assert d_ok
    assert get_expense_by_id(exp_id, db_path=temp_db) is None


# ---------------------------------------------------------------------------
# 2. INCOME VALIDATION & CRUD TESTS
# ---------------------------------------------------------------------------

def test_income_validation():
    # Empty source
    valid, msg = validate_income("", 15000.0, "2026-11-01")
    assert not valid

    # Negative amount
    valid, msg = validate_income("Salary", -100.0, "2026-11-01")
    assert not valid

    # Valid
    valid, msg = validate_income("Allowance", 12000.0, "2026-11-01")
    assert valid


def test_income_crud(temp_db):
    ok, msg, inc_id = add_new_income("Allowance", 20000.0, "2026-11-01", "Monthly college fund", db_path=temp_db)
    assert ok
    assert inc_id is not None

    inc = get_income_by_id(inc_id, db_path=temp_db)
    assert inc["amount"] == 20000.0

    total = get_monthly_income_total(2026, 11, db_path=temp_db)
    assert total == 20000.0

    # Update
    u_ok, u_msg = edit_income(inc_id, "Salary", 25000.0, "2026-11-01", "Internship stipend", db_path=temp_db)
    assert u_ok
    inc_up = get_income_by_id(inc_id, db_path=temp_db)
    assert inc_up["amount"] == 25000.0
    assert inc_up["income_source"] == "Salary"

    # Delete
    del_ok, del_msg = remove_income(inc_id, db_path=temp_db)
    assert del_ok
    assert get_income_by_id(inc_id, db_path=temp_db) is None


# ---------------------------------------------------------------------------
# 3. BUDGET MANAGEMENT & TIERED ALERT TESTS (FEATURE 6 & 7)
# ---------------------------------------------------------------------------

def test_budget_threshold_evaluations():
    # 1. Normal (<75%)
    res_normal = evaluate_budget_status(5000, 10000)
    assert res_normal["tier"] == "normal"
    assert res_normal["utilization"] == 50.0
    assert "🟢" in res_normal["message"]

    # 2. Caution (75% to 89.9%)
    res_caution = evaluate_budget_status(7500, 10000)
    assert res_caution["tier"] == "caution"
    assert res_caution["utilization"] == 75.0
    assert "🟡" in res_caution["message"]

    # 3. Warning (90% to 99.9%)
    res_warning = evaluate_budget_status(9200, 10000)
    assert res_warning["tier"] == "warning"
    assert res_warning["utilization"] == 92.0
    assert "🟠" in res_warning["message"]

    # 4. Exceeded (>=100%)
    res_exceeded = evaluate_budget_status(11500, 10000)
    assert res_exceeded["tier"] == "exceeded"
    assert res_exceeded["utilization"] == 115.0
    assert "🔴" in res_exceeded["message"]

    # 5. Zero / No Budget
    res_zero = evaluate_budget_status(500, 0)
    assert res_zero["tier"] == "none"
    assert res_zero["utilization"] == 0.0


def test_budget_persistence(temp_db):
    # Save overall budget
    ok, msg = save_budget("Overall", 25000.0, 11, 2026, db_path=temp_db)
    assert ok

    # Save category budget
    ok2, msg2 = save_budget("Food & Dining", 6000.0, 11, 2026, db_path=temp_db)
    assert ok2

    summary = get_overall_budget_summary(2026, 11, db_path=temp_db)
    assert summary["has_budget"]
    assert summary["budget_amount"] == 25000.0

    # Add expense exceeding food budget to test alerts
    add_new_expense("Feast", 6200.0, "Food & Dining", "2026-11-05", db_path=temp_db)
    alerts = get_active_budget_alerts(2026, 11, db_path=temp_db)
    assert any(a["category"] == "Food & Dining" and a["tier"] == "exceeded" for a in alerts)


# ---------------------------------------------------------------------------
# 4. STATISTICAL AVERAGES & ZERO-DIVISION SAFEGUARDS (FEATURE 9)
# ---------------------------------------------------------------------------

def test_averages_empty_db(temp_db):
    # Empty DB should not throw ZeroDivisionError
    metrics = calculate_average_metrics(2026, 11, db_path=temp_db)
    assert metrics["avg_daily"] == 0.0
    assert metrics["avg_per_transaction"] == 0.0
    assert metrics["avg_monthly_all_time"] == 0.0
    assert metrics["avg_by_category"] == {}


def test_averages_with_data(temp_db):
    add_new_expense("Exp 1", 1000.0, "Food & Dining", "2026-11-01", db_path=temp_db)
    add_new_expense("Exp 2", 2000.0, "Transportation", "2026-11-02", db_path=temp_db)

    metrics = calculate_average_metrics(2026, 11, db_path=temp_db)
    assert metrics["tx_count"] == 2
    assert metrics["total_monthly_expense"] == 3000.0
    assert metrics["avg_per_transaction"] == 1500.0
    assert metrics["avg_by_category"]["Food & Dining"] == 1000.0
    assert metrics["avg_by_category"]["Transportation"] == 2000.0


# ---------------------------------------------------------------------------
# 5. SMART INSIGHTS HEURISTICS (FEATURE 10)
# ---------------------------------------------------------------------------

def test_smart_insights(temp_db):
    # Empty month insights
    empty_insights = generate_smart_insights(2026, 11, db_path=temp_db)
    assert len(empty_insights) > 0
    assert empty_insights[0]["category"] == "Getting Started"

    # Add income and heavy food spending
    add_new_income("Salary", 30000.0, "2026-11-01", db_path=temp_db)
    add_new_expense("Groceries", 8000.0, "Food & Dining", "2026-11-02", db_path=temp_db)
    add_new_expense("Bus", 500.0, "Transportation", "2026-11-03", db_path=temp_db)

    insights = generate_smart_insights(2026, 11, db_path=temp_db)
    assert any("Food & Dining is your largest expense" in i["headline"] for i in insights)
    assert any("recommendation" in i["action_tip"].lower() or len(i["action_tip"]) > 10 for i in insights)


# ---------------------------------------------------------------------------
# 6. REPORT GENERATION TESTS (FEATURE 12)
# ---------------------------------------------------------------------------

def test_csv_report_generation(temp_db):
    add_new_income("Allowance", 10000.0, "2026-11-01", db_path=temp_db)
    add_new_expense("Books", 1500.0, "Education", "2026-11-02", db_path=temp_db)

    txs = get_unified_transactions(db_path=temp_db)
    csv_str = generate_csv_report(txs)
    assert "Transaction Name" in csv_str
    assert "Allowance" in csv_str
    assert "Books" in csv_str
    assert "1500.00" in csv_str


def test_pdf_report_generation(temp_db):
    add_new_income("Allowance", 15000.0, "2026-11-01", db_path=temp_db)
    add_new_expense("Stationery", 600.0, "Education", "2026-11-02", db_path=temp_db)
    save_budget("Overall", 12000.0, 11, 2026, db_path=temp_db)

    pdf_bytes = generate_pdf_report(2026, 11, db_path=temp_db)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic header
    assert pdf_bytes.startswith(b"%PDF")


# ---------------------------------------------------------------------------
# 7. SAMPLE DATA SEEDING AND CLEANING
# ---------------------------------------------------------------------------

def test_sample_data_lifecycle(temp_db):
    assert not has_sample_data(db_path=temp_db)

    # Add real user record
    add_new_expense("User Personal Laptop", 45000.0, "Shopping", "2026-11-01", db_path=temp_db)

    # Seed demo data
    counts = seed_sample_data(reference_date=date(2026, 11, 4), db_path=temp_db)
    assert counts["expenses"] > 0
    assert counts["income"] > 0
    assert counts["budgets"] > 0
    assert has_sample_data(db_path=temp_db)

    # Clear demo data
    cleared = clear_sample_data(db_path=temp_db)
    assert cleared["expenses"] == counts["expenses"]
    assert not has_sample_data(db_path=temp_db)

    # Check that user data was preserved!
    user_expenses = get_all_expenses(db_path=temp_db)
    assert len(user_expenses) == 1
    assert user_expenses[0]["expense_name"] == "User Personal Laptop"
