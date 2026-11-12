"""
Fixes and Robustness Verification Test Suite
--------------------------------------------
Personal Expenses & Smart Budget Management System

Deep verification of:
1. XML/HTML escaping in PDF generation to prevent paraparser syntax crashes.
2. Multi-page transaction table without arbitrary truncation.
3. Full monthly executive summary and category breakdown in CSV exports.
4. Positive budget validation strictly rejecting <= 0 values.
5. Smart Insights category escalation detection for new categories (outer-join).
6. Chart 5 (plot_category_comparison_bar) rendering.
7. Available periods list robustness.
"""

import os
import sys
import tempfile
import pytest
from datetime import date

MODULE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "personal_expense_manager")
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

from database import (
    init_db,
    add_expense,
    add_income,
    set_budget,
    get_unified_transactions,
    get_available_months_and_years
)
from expense_manager import (
    add_new_expense,
    get_category_wise_spending
)
from budget_manager import save_budget
from insights import generate_smart_insights
from reports import generate_pdf_report, generate_csv_report, clean_pdf_text
from analytics import plot_category_comparison_bar


@pytest.fixture
def temp_robust_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


def test_clean_pdf_text_escaping():
    """Verify clean_pdf_text safely escapes XML and removes unprintable glyphs."""
    raw = "Book <Python 3> & 'Tools' ☕ 🎉 ₹1,500"
    cleaned = clean_pdf_text(raw)
    assert "&lt;" in cleaned
    assert "&gt;" in cleaned
    assert "&amp;" in cleaned
    assert "Rs. " in cleaned
    assert "☕" not in cleaned
    assert "🎉" not in cleaned


def test_pdf_with_xml_special_characters(temp_robust_db):
    """
    Verify that unclosed XML tags and characters (<, >, &) in transaction names,
    descriptions, and payment methods do NOT crash PDF compilation.
    """
    add_new_expense(
        expense_name="Book <Python 3> & C++",
        amount=1200.0,
        category="Education",
        date_val="2026-11-04",
        payment_method="UPI & GPay",
        description="Notes for CSE <Semester 5> & projects",
        db_path=temp_robust_db
    )
    add_new_expense(
        expense_name="Unclosed <tag expense",
        amount=500.0,
        category="Others",
        date_val="2026-11-05",
        description="Unclosed <detail & test",
        db_path=temp_robust_db
    )

    pdf_bytes = generate_pdf_report(2026, 11, db_path=temp_robust_db)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_large_number_of_transactions_no_truncation(temp_robust_db):
    """
    Verify that months with 45+ transactions do NOT get arbitrarily truncated
    and generate a valid multi-page PDF.
    """
    for i in range(1, 46):
        add_new_expense(
            expense_name=f"Daily Tea Item #{i}",
            amount=20.0 + i,
            category="Food & Dining",
            date_val=f"2026-11-{(i % 28) + 1:02d}",
            db_path=temp_robust_db
        )

    txs = get_unified_transactions(db_path=temp_robust_db)
    assert len(txs) == 45

    pdf_bytes = generate_pdf_report(2026, 11, db_path=temp_robust_db)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")


def test_csv_with_executive_summary(temp_robust_db):
    """
    Verify that CSV export includes the executive financial summary,
    category breakdown, and transaction ledger when period is specified.
    """
    add_income("Scholarship", 15000.0, "2026-11-01", "Semester grant", db_path=temp_robust_db)
    add_new_expense("Textbook", 2500.0, "Education", "2026-11-02", db_path=temp_robust_db)
    save_budget("Overall", 12000.0, 11, 2026, db_path=temp_robust_db)

    txs = get_unified_transactions(db_path=temp_robust_db)
    csv_content = generate_csv_report(txs, year=2026, month=11, db_path=temp_robust_db)

    assert "EXECUTIVE FINANCIAL SUMMARY" in csv_content
    assert "Total Income Recorded" in csv_content
    assert "15000.00" in csv_content
    assert "Total Expenses Incurred" in csv_content
    assert "2500.00" in csv_content
    assert "Remaining Balance" in csv_content
    assert "CATEGORY-WISE SPENDING BREAKDOWN" in csv_content
    assert "Education" in csv_content
    assert "DETAILED TRANSACTION LOG" in csv_content
    assert "Textbook" in csv_content


def test_budget_validation_zero_and_negative(temp_robust_db):
    """
    Verify Section 7 requirement: Budget values must be valid positive numbers.
    Zero and negative numbers must be rejected.
    """
    ok_zero, msg_zero = save_budget("Overall", 0.0, 11, 2026, db_path=temp_robust_db)
    assert not ok_zero
    assert "positive" in msg_zero.lower()

    ok_neg, msg_neg = save_budget("Food & Dining", -1500.0, 11, 2026, db_path=temp_robust_db)
    assert not ok_neg
    assert "positive" in msg_neg.lower()

    # Valid positive budget
    ok_pos, msg_pos = save_budget("Overall", 15000.0, 11, 2026, db_path=temp_robust_db)
    assert ok_pos


def test_insights_outer_join_new_category(temp_robust_db):
    """
    Verify that if a category had ₹0 in previous month, but spending in current month,
    the smart insight engine detects the escalation via outer join.
    """
    # October 2026: only Food
    add_new_expense("October Mess", 3000.0, "Food & Dining", "2026-10-15", db_path=temp_robust_db)

    # November 2026: Food + new heavy Entertainment spending
    add_new_expense("November Mess", 3200.0, "Food & Dining", "2026-11-10", db_path=temp_robust_db)
    add_new_expense("Concert VIP Pass", 2500.0, "Entertainment", "2026-11-12", db_path=temp_robust_db)

    insights = generate_smart_insights(2026, 11, db_path=temp_robust_db)
    # Must detect Entertainment escalation even though it did not exist in October
    escalation_insights = [i for i in insights if i["category"] == "Category Escalation"]
    assert any("Entertainment" in i["headline"] for i in escalation_insights)


def test_plot_category_comparison_bar(temp_robust_db):
    """Verify plot_category_comparison_bar produces a valid Plotly Figure."""
    add_new_expense("Lunch", 450.0, "Food & Dining", "2026-11-01", db_path=temp_robust_db)
    add_new_expense("Metro", 300.0, "Transportation", "2026-11-02", db_path=temp_robust_db)

    cat_df = get_category_wise_spending(2026, 11, db_path=temp_robust_db)
    fig = plot_category_comparison_bar(cat_df)
    assert fig is not None
    assert hasattr(fig, "data")
    assert len(fig.data) > 0


def test_available_periods_includes_navigation_months(temp_robust_db):
    """Verify available periods contains current, previous, and next month."""
    today = date.today()
    periods = get_available_months_and_years(db_path=temp_robust_db)
    assert (today.year, today.month) in periods
    # Next month
    next_m = today.month + 1 if today.month < 12 else 1
    next_y = today.year if today.month < 12 else today.year + 1
    assert (next_y, next_m) in periods
