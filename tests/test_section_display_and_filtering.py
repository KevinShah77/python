"""
Test Suite: Distinct Display, Filtering, and Synchronization for Expenses, Income, and Transactions
-----------------------------------------------------------------------------------------------------
Verifies that:
1. REST API returns distinct data arrays for expenses, income, and budgets.
2. The frontend built bundle properly incorporates distinct display logic for Expenses, Income, and Transactions.
3. TransactionTable and RecordsPage render the required column sets, distinct overview strips, and badges.
4. All frontend changes are synchronized with the Downloads folder mirror and zip archive.
"""

import os
import sys
import json
import zipfile
import pytest
from fastapi.testclient import TestClient

MODULE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "personal_expense_manager")
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

from api import app
from database import init_db, add_expense, add_income, seed_sample_data, reset_all_data

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_SRC = os.path.join(ROOT_DIR, "frontend", "src")
FRONTEND_DIST = os.path.join(ROOT_DIR, "frontend", "dist")
DOWNLOADS_DIR = os.path.join(
    os.path.expanduser("~"), "Downloads", "PennyPilot-frontend", "PennyPilot"
)
DOWNLOADS_ZIP = os.path.join(
    os.path.expanduser("~"), "Downloads", "PennyPilot-frontend.zip"
)


@pytest.fixture
def client_with_data(tmp_path):
    db_file = str(tmp_path / "test_distinct.db")
    init_db(db_file)
    app.state.db_path = db_file
    seed_sample_data(db_path=db_file)
    client = TestClient(app)
    yield client
    app.state.db_path = None


def test_api_returns_distinct_expenses_and_income(client_with_data):
    """Ensure /api/data cleanly distinguishes between expense and income records."""
    res = client_with_data.get("/api/data")
    assert res.status_code == 200
    data = res.json()
    assert "expenses" in data and "income" in data and "budgets" in data
    assert len(data["expenses"]) > 0
    assert len(data["income"]) > 0

    # Ensure expense records have expense keys and type='expense'
    for exp in data["expenses"]:
        assert exp["type"] == "expense"
        assert "name" in exp
        assert "category" in exp
        assert "paymentMethod" in exp
        assert "amount" in exp

    # Ensure income records have income keys and type='income'
    for inc in data["income"]:
        assert inc["type"] == "income"
        assert "source" in inc
        assert "amount" in inc
        assert "date" in inc


def test_recordspage_source_code_has_distinct_logic():
    """Verify RecordsPage.tsx implements distinct base data, breakdowns, and strips."""
    records_page_path = os.path.join(FRONTEND_SRC, "pages", "RecordsPage.tsx")
    assert os.path.exists(records_page_path), "RecordsPage.tsx missing in src"

    with open(records_page_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Base derivation must strictly separate expenses vs income
    assert "page === 'Expenses'" in content
    assert "page === 'Income'" in content
    assert "page === 'Transactions'" in content
    assert "Spending by Category" in content
    assert "Income by Source" in content
    assert "Total Outflow" in content
    assert "Total Inflow" in content
    assert "handleExportCsv" in content
    assert "pennypilot-expenses-" in content
    assert "pennypilot-income-" in content
    assert "baseExpenseTotal" in content
    assert "baseIncomeTotal" in content
    assert "getCategoryMeta(item.source)" in content
    assert "setType(event.target.value as 'All' | EntryKind)" in content
    assert "setCategory('All')" in content


def test_transactiontable_source_code_has_mode_support():
    """Verify TransactionTable.tsx supports 'expenses', 'income', and 'all' modes with badges and distinct columns."""
    table_path = os.path.join(FRONTEND_SRC, "components", "TransactionTable.tsx")
    assert os.path.exists(table_path), "TransactionTable.tsx missing in src"

    with open(table_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "mode?: 'expenses' | 'income' | 'all'" in content
    assert "isIncomeMode" in content
    assert "isExpenseMode" in content
    assert "type-badge type-badge-income" in content
    assert "type-badge type-badge-expense" in content
    assert "Income Source" in content
    assert "Description / Notes" in content
    # Category / Source column must NOT be rendered in Income mode to avoid duplicating the source
    assert "{!isIncomeMode && <th>{isExpenseMode ? 'Category' : 'Category / Source'}</th>}" in content


def test_app_tsx_has_key_prop_on_recordspage():
    """Verify App.tsx passes key={page} to RecordsPage to guarantee state re-initialization."""
    app_path = os.path.join(FRONTEND_SRC, "App.tsx")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "<RecordsPage" in content
    assert "key={page}" in content


def test_frontend_dist_built_and_includes_badges():
    """Verify the production dist bundle was built and includes type badges and styles."""
    assert os.path.exists(FRONTEND_DIST), "dist folder does not exist"
    index_html = os.path.join(FRONTEND_DIST, "index.html")
    assert os.path.exists(index_html), "index.html missing in dist"

    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    assert os.path.isdir(assets_dir), "assets dir missing in dist"

    css_files = [f for f in os.listdir(assets_dir) if f.endswith(".css")]
    assert len(css_files) > 0, "No CSS files in dist assets"

    # Read the compiled CSS to ensure badge styles are bundled
    css_content = ""
    for css_file in css_files:
        with open(os.path.join(assets_dir, css_file), "r", encoding="utf-8") as f:
            css_content += f.read()

    assert "type-badge" in css_content
    assert "type-badge-income" in css_content
    assert "type-badge-expense" in css_content


def test_downloads_folder_is_synchronized():
    """Verify the Downloads folder mirror has the exact updated files."""
    assert os.path.isdir(DOWNLOADS_DIR), f"Downloads mirror directory missing: {DOWNLOADS_DIR}"

    downloads_records = os.path.join(DOWNLOADS_DIR, "src", "pages", "RecordsPage.tsx")
    downloads_table = os.path.join(DOWNLOADS_DIR, "src", "components", "TransactionTable.tsx")
    downloads_app = os.path.join(DOWNLOADS_DIR, "src", "App.tsx")

    assert os.path.exists(downloads_records), "RecordsPage.tsx missing in Downloads mirror"
    assert os.path.exists(downloads_table), "TransactionTable.tsx missing in Downloads mirror"
    assert os.path.exists(downloads_app), "App.tsx missing in Downloads mirror"

    with open(downloads_records, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Spending by Category" in content
    assert "Income by Source" in content

    with open(downloads_table, "r", encoding="utf-8") as f:
        content = f.read()
    assert "type-badge-income" in content

    # Check zip archive exists and contains updated records
    assert os.path.exists(DOWNLOADS_ZIP), "PennyPilot-frontend.zip missing in Downloads"
    with zipfile.ZipFile(DOWNLOADS_ZIP, "r") as zf:
        namelist = zf.namelist()
        matched = [n for n in namelist if "RecordsPage.tsx" in n]
        assert len(matched) > 0, "RecordsPage.tsx not found in PennyPilot-frontend.zip"
