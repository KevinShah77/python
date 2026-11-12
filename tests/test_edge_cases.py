"""
Edge Cases and Boundary Condition Tests
---------------------------------------
Testing:
- SQL injection resistance (parameterized queries)
- January month wrap-around to December of previous year
- Leap year calendar handling in daily averages
- Extremes and boundary values (e.g. ₹0.01, large amounts)
- Special characters, unicode, and emojis in text fields
- Unified transactions multi-filter combinations
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
    get_unified_transactions,
    get_all_expenses,
    get_all_income,
    set_budget,
    get_budget_by_category
)
from expense_manager import (
    add_new_expense,
    compare_monthly_spending,
    get_category_wise_spending,
    validate_expense
)
from income_manager import add_new_income, validate_income
from analytics import calculate_average_metrics
from budget_manager import evaluate_budget_status


@pytest.fixture
def temp_edge_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


def test_sql_injection_defense(temp_edge_db):
    """Verify that malicious SQL payloads in inputs do not execute or corrupt the DB."""
    malicious_name = "Lunch'; DROP TABLE expenses; --"
    malicious_desc = "' OR '1'='1"

    ok, msg, exp_id = add_new_expense(
        expense_name=malicious_name,
        amount=250.0,
        category="Food & Dining",
        date_val="2026-11-04",
        description=malicious_desc,
        db_path=temp_edge_db
    )
    assert ok
    # Expenses table must still exist and contain the literal string
    all_exp = get_all_expenses(db_path=temp_edge_db)
    assert len(all_exp) == 1
    assert all_exp[0]["expense_name"] == malicious_name
    assert all_exp[0]["description"] == malicious_desc


def test_january_month_transition(temp_edge_db):
    """Verify comparing January (Month 1) correctly references December (Month 12) of previous year."""
    # Add expense in December 2025
    add_new_expense("Year-End Party", 5000.0, "Entertainment", "2025-12-31", db_path=temp_edge_db)
    # Add expense in January 2026
    add_new_expense("New Year Books", 2000.0, "Education", "2026-01-05", db_path=temp_edge_db)

    comp = compare_monthly_spending(2026, 1, db_path=temp_edge_db)
    assert comp["prev_month"] == 12
    assert comp["prev_year"] == 2025
    assert comp["current_total"] == 2000.0
    assert comp["prev_total"] == 5000.0
    assert comp["diff"] == 3000.0
    assert comp["trend"] == "decreased"
    assert comp["pct_change"] == -60.0


def test_leap_year_handling(temp_edge_db):
    """2024 is a leap year (February has 29 days). Verify effective days & averages."""
    add_new_expense("Feb Expense", 2900.0, "Shopping", "2024-02-15", db_path=temp_edge_db)
    metrics = calculate_average_metrics(2024, 2, db_path=temp_edge_db)
    assert metrics["days_in_month"] == 29
    assert metrics["effective_days"] == 29
    assert metrics["avg_daily"] == 100.0  # 2900 / 29


def test_boundary_amounts(temp_edge_db):
    """Test boundary amounts (smallest penny ₹0.01 and large figures)."""
    # 1 Paisa
    ok, _, _ = add_new_expense("Test Micro", 0.01, "Others", "2026-11-01", db_path=temp_edge_db)
    assert ok

    # Zero amount must fail
    v_ok, _ = validate_expense("Free Item", 0.0, "Others", "2026-11-01")
    assert not v_ok

    # Exorbitant amount > 1 Crore should be caught by validation
    v_huge, msg = validate_expense("Island", 100_000_001.0, "Others", "2026-11-01")
    assert not v_huge
    assert "cannot exceed" in msg


def test_special_characters_and_emojis(temp_edge_db):
    """Test utf-8 emojis and symbols in transaction records."""
    name = "Café & Crêpes ☕🥐"
    desc = "Celebration with friends 🎉 #project #college"
    ok, _, exp_id = add_new_expense(name, 450.0, "Food & Dining", "2026-11-03", description=desc, db_path=temp_edge_db)
    assert ok

    txs = get_unified_transactions(search_query="☕", db_path=temp_edge_db)
    assert len(txs) == 1
    assert txs[0]["name"] == name


def test_budget_upsert_overwrite(temp_edge_db):
    """Verify that setting a budget multiple times for the same month/year updates rather than duplicates."""
    set_budget("Overall", 20000.0, 11, 2026, db_path=temp_edge_db)
    b1 = get_budget_by_category("Overall", 2026, 11, db_path=temp_edge_db)
    assert b1["budget_amount"] == 20000.0

    # Overwrite
    set_budget("Overall", 28000.0, 11, 2026, db_path=temp_edge_db)
    b2 = get_budget_by_category("Overall", 2026, 11, db_path=temp_edge_db)
    assert b2["budget_amount"] == 28000.0
    assert b2["id"] == b1["id"]  # Row updated in place
