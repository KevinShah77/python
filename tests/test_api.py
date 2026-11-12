"""
Unit and Integration Tests for PennyPilot FastAPI Backend API
--------------------------------------------------------------
Tests:
- API status endpoint (/api/status)
- Full data retrieval (/api/data)
- Expense CRUD and validation errors
- Income CRUD and validation errors
- Budget upsert and delete operations
- Sample data seeding and clearing
- Complete database reset
- CSV report generation
- PDF report generation
- Static frontend index serving
"""

import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

# Ensure personal_expense_manager is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_DIR = os.path.join(ROOT_DIR, "personal_expense_manager")
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

from api import app
from database import init_db


@pytest.fixture
def client():
    """Create a test client connected to an isolated temporary SQLite database."""
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db_path = temp_db.name
    temp_db.close()

    init_db(temp_db_path)
    app.state.db_path = temp_db_path

    with TestClient(app) as test_client:
        yield test_client

    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
    app.state.db_path = None


def test_api_status(client):
    """Test health check and status reporting."""
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["app"] == "PennyPilot"
    assert data["db_connected"] is True
    assert "counts" in data
    assert data["counts"]["expenses"] == 0
    assert data["counts"]["income"] == 0


def test_empty_app_data(client):
    """Test retrieving initial empty data."""
    res = client.get("/api/data")
    assert res.status_code == 200
    data = res.json()
    assert data["expenses"] == []
    assert data["income"] == []
    assert data["budgets"] == []


def test_expense_crud_and_validation(client):
    """Test adding, reading, updating, and deleting an expense."""
    # 1. Invalid payload (empty name)
    bad_res = client.post("/api/expenses", json={
        "name": "",
        "amount": 150.0,
        "category": "Food & Dining",
        "date": "2026-11-04"
    })
    assert bad_res.status_code in (400, 422)

    # 2. Invalid amount (negative)
    bad_res2 = client.post("/api/expenses", json={
        "name": "Lunch",
        "amount": -50.0,
        "category": "Food & Dining",
        "date": "2026-11-04"
    })
    assert bad_res2.status_code == 422 or bad_res2.status_code == 400

    # 3. Invalid category
    bad_res3 = client.post("/api/expenses", json={
        "name": "Lunch",
        "amount": 150.0,
        "category": "NonExistentCategory",
        "date": "2026-11-04"
    })
    assert bad_res3.status_code == 400

    # 4. Valid expense creation
    create_res = client.post("/api/expenses", json={
        "name": "Campus Canteen Lunch",
        "amount": 180.0,
        "category": "Food & Dining",
        "date": "2026-11-04",
        "paymentMethod": "UPI / GPay / PhonePe",
        "description": "Lunch with friends"
    })
    assert create_res.status_code == 201
    created = create_res.json()
    expense_id = created["id"]
    assert created["name"] == "Campus Canteen Lunch"
    assert created["amount"] == 180.0
    assert created["category"] == "Food & Dining"
    assert created["paymentMethod"] == "UPI / GPay / PhonePe"

    # 5. Verify it appears in /api/data
    data_res = client.get("/api/data")
    assert data_res.status_code == 200
    assert len(data_res.json()["expenses"]) == 1

    # 6. Update expense
    update_res = client.put(f"/api/expenses/{expense_id}", json={
        "name": "Updated Lunch",
        "amount": 220.0,
        "category": "Food & Dining",
        "date": "2026-11-04",
        "paymentMethod": "Cash",
        "description": "Updated note"
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Lunch"
    assert update_res.json()["amount"] == 220.0

    # 7. Update non-existent expense
    not_found_res = client.put("/api/expenses/9999", json={
        "name": "Ghost",
        "amount": 100.0,
        "category": "Food & Dining",
        "date": "2026-11-04"
    })
    assert not_found_res.status_code == 404

    # 8. Delete expense
    del_res = client.delete(f"/api/expenses/{expense_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 9. Verify deletion
    data_res2 = client.get("/api/data")
    assert len(data_res2.json()["expenses"]) == 0

    # 10. Delete non-existent expense
    del_ghost = client.delete("/api/expenses/9999")
    assert del_ghost.status_code == 404


def test_income_crud_and_validation(client):
    """Test adding, reading, updating, and deleting an income entry."""
    # 1. Invalid income source
    bad_res = client.post("/api/income", json={
        "source": "LotteryWin",
        "amount": 5000.0,
        "date": "2026-11-01"
    })
    assert bad_res.status_code == 400

    # 2. Invalid amount (zero)
    bad_res2 = client.post("/api/income", json={
        "source": "Allowance",
        "amount": 0.0,
        "date": "2026-11-01"
    })
    assert bad_res2.status_code == 422 or bad_res2.status_code == 400

    # 3. Valid creation
    create_res = client.post("/api/income", json={
        "source": "Allowance",
        "amount": 18000.0,
        "date": "2026-11-01",
        "description": "Monthly parental allowance"
    })
    assert create_res.status_code == 201
    income_id = create_res.json()["id"]
    assert create_res.json()["source"] == "Allowance"
    assert create_res.json()["amount"] == 18000.0

    # 4. Update income
    update_res = client.put(f"/api/income/{income_id}", json={
        "source": "Scholarship",
        "amount": 20000.0,
        "date": "2026-11-01",
        "description": "Updated merit grant"
    })
    assert update_res.status_code == 200
    assert update_res.json()["source"] == "Scholarship"
    assert update_res.json()["amount"] == 20000.0

    # 5. Delete income
    del_res = client.delete(f"/api/income/{income_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 6. Delete non-existent income
    del_ghost = client.delete("/api/income/9999")
    assert del_ghost.status_code == 404


def test_budget_operations(client):
    """Test setting, upserting, and deleting budgets."""
    # 1. Invalid category
    bad_res = client.post("/api/budgets", json={
        "category": "InvalidCat",
        "amount": 5000.0,
        "period": "2026-11"
    })
    assert bad_res.status_code == 400

    # 2. Invalid period format
    bad_res2 = client.post("/api/budgets", json={
        "category": "Food & Dining",
        "amount": 5000.0,
        "period": "not-a-period"
    })
    assert bad_res2.status_code == 400

    # 3. Valid budget creation (Overall)
    b_res = client.post("/api/budgets", json={
        "category": "Overall",
        "amount": 25000.0,
        "period": "2026-11"
    })
    assert b_res.status_code == 200
    b_data = b_res.json()
    assert b_data["category"] == "Overall"
    assert b_data["amount"] == 25000.0
    assert b_data["period"] == "2026-11"
    budget_id = b_data["id"]

    # 4. Valid budget creation (Category)
    b_cat_res = client.post("/api/budgets", json={
        "category": "Food & Dining",
        "amount": 6000.0,
        "period": "2026-11"
    })
    assert b_cat_res.status_code == 200
    assert b_cat_res.json()["category"] == "Food & Dining"

    # 5. Upsert budget
    upsert_res = client.post("/api/budgets", json={
        "category": "Food & Dining",
        "amount": 7500.0,
        "period": "2026-11"
    })
    assert upsert_res.status_code == 200
    assert upsert_res.json()["amount"] == 7500.0

    # 6. Delete budget
    del_res = client.delete(f"/api/budgets/{budget_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_sample_data_and_reset(client):
    """Test seeding demo data, checking data, and clearing demo data."""
    # Seed
    seed_res = client.post("/api/sample-data/seed")
    assert seed_res.status_code == 200
    counts = seed_res.json()["counts"]
    assert counts["expenses"] > 0
    assert counts["income"] > 0
    assert counts["budgets"] > 0

    # Verify counts in /api/data
    data_res = client.get("/api/data")
    assert data_res.status_code == 200
    body = data_res.json()
    assert len(body["expenses"]) == counts["expenses"]
    assert len(body["income"]) == counts["income"]

    # Clear sample data
    clear_res = client.post("/api/sample-data/clear")
    assert clear_res.status_code == 200
    data_after_clear = client.get("/api/data").json()
    assert len(data_after_clear["expenses"]) == 0
    assert len(data_after_clear["income"]) == 0

    # Reset
    reset_res = client.post("/api/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["success"] is True


def test_report_downloads(client):
    """Test generating CSV and PDF reports via API."""
    # Seed sample data first
    client.post("/api/sample-data/seed")

    # CSV report
    csv_res = client.get("/api/reports/csv?period=2026-11")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert len(csv_res.text) > 50

    # PDF report
    pdf_res = client.get("/api/reports/pdf?period=2026-11")
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers.get("content-type", "")
    assert pdf_res.content.startswith(b"%PDF")


def test_frontend_serving(client):
    """Test serving the production React single page application."""
    res = client.get("/")
    assert res.status_code == 200
    assert "<!doctype html>" in res.text.lower() or "<div id=\"root\">" in res.text


def test_expense_invalid_payment_method(client):
    """Test that invalid payment methods are rejected."""
    bad_res = client.post("/api/expenses", json={
        "name": "Dinner",
        "amount": 250.0,
        "category": "Food & Dining",
        "date": "2026-11-04",
        "paymentMethod": "Cryptocurrency"
    })
    assert bad_res.status_code == 400
    assert "Invalid payment method" in bad_res.json()["detail"]


def test_budget_strict_validation(client):
    """Test that zero, negative, and excessive budgets are rejected."""
    # Zero amount rejected
    res_zero = client.post("/api/budgets", json={
        "category": "Food & Dining",
        "amount": 0.0,
        "period": "2026-11"
    })
    assert res_zero.status_code in (400, 422)

    # Negative amount rejected
    res_neg = client.post("/api/budgets", json={
        "category": "Food & Dining",
        "amount": -500.0,
        "period": "2026-11"
    })
    assert res_neg.status_code in (400, 422)

    # Excessive amount rejected (> 10 Crores)
    res_huge = client.post("/api/budgets", json={
        "category": "Food & Dining",
        "amount": 200_000_000.0,
        "period": "2026-11"
    })
    assert res_huge.status_code in (400, 422)


def test_budget_delete_not_found(client):
    """Test that deleting a non-existent budget returns 404."""
    res = client.delete("/api/budgets/999999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_report_invalid_period_rejected(client):
    """Test that malformed or out-of-range period parameters return 400."""
    # Month > 12
    res_m15 = client.get("/api/reports/pdf?period=2026-15")
    assert res_m15.status_code == 400
    assert "Invalid period" in res_m15.json()["detail"]

    # Month 0
    res_m0 = client.get("/api/reports/csv?period=2026-00")
    assert res_m0.status_code == 400

    # Malformed string
    res_bad = client.get("/api/reports/csv?period=invalid-string")
    assert res_bad.status_code == 400


def test_sqlite_wal_mode_enabled(client):
    """Test that SQLite database connection uses WAL journal mode and busy timeout."""
    from database import get_connection
    db_path = client.app.state.db_path
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        # In memory or file, WAL or memory is valid
        assert mode.lower() in ("wal", "memory")
        cursor.execute("PRAGMA busy_timeout;")
        timeout = cursor.fetchone()[0]
        assert timeout >= 5000
    finally:
        conn.close()

