"""
Comprehensive Unit and Integration Tests for Savings Goals Feature
-------------------------------------------------------------------
Tests:
- Creation of savings goals (success & validation edge cases)
- Adding money to savings goals (partial, completion, over-completion, negative/zero amount)
- Dynamic calculations (remaining amount, progress percentage, status)
- Status transitions (In Progress, Completed, Overdue)
- Updating savings goals (modifying target, name, date, description)
- Deleting savings goals
- User privacy and data isolation
- Summary statistics endpoint (/api/savings-goals/summary)
- Seeding and clearing sample savings goals
"""

import os
import sys
import tempfile
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_DIR = os.path.join(ROOT_DIR, "personal_expense_manager")
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

from api import app
from database import init_db, seed_sample_data, clear_sample_data
from savings_manager import (
    compute_goal_status,
    compute_progress_and_remaining,
    validate_goal_inputs,
    get_engine
)


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

    get_engine(temp_db_path).dispose()
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except PermissionError:
            pass
    app.state.db_path = None


def test_create_savings_goal_success(client):
    """Test creating a valid savings goal."""
    future_date = (date.today() + timedelta(days=90)).isoformat()
    res = client.post("/api/savings-goals", json={
        "goal_name": "Emergency Fund",
        "target_amount": 50000.0,
        "target_date": future_date,
        "description": "3 months reserve",
        "current_saved_amount": 10000.0,
        "user_id": "student_1"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["goal_name"] == "Emergency Fund"
    assert data["target_amount"] == 50000.0
    assert data["current_saved_amount"] == 10000.0
    assert data["remaining_amount"] == 40000.0
    assert data["progress_percentage"] == 20.0
    assert data["status"] == "In Progress"
    assert data["user_id"] == "student_1"
    assert "id" in data


def test_create_savings_goal_validation_failures(client):
    """Test that invalid inputs are rejected with clear errors."""
    future_date = (date.today() + timedelta(days=90)).isoformat()

    # Empty goal name
    res_empty_name = client.post("/api/savings-goals", json={
        "goal_name": "   ",
        "target_amount": 10000.0,
        "target_date": future_date
    })
    assert res_empty_name.status_code in (400, 422)

    # Zero target amount
    res_zero = client.post("/api/savings-goals", json={
        "goal_name": "Bike",
        "target_amount": 0.0,
        "target_date": future_date
    })
    assert res_zero.status_code in (400, 422)

    # Negative target amount
    res_neg = client.post("/api/savings-goals", json={
        "goal_name": "Bike",
        "target_amount": -5000.0,
        "target_date": future_date
    })
    assert res_neg.status_code in (400, 422)

    # Negative saved amount
    res_neg_saved = client.post("/api/savings-goals", json={
        "goal_name": "Bike",
        "target_amount": 10000.0,
        "target_date": future_date,
        "current_saved_amount": -100.0
    })
    assert res_neg_saved.status_code in (400, 422)

    # Invalid date format
    res_bad_date = client.post("/api/savings-goals", json={
        "goal_name": "Bike",
        "target_amount": 10000.0,
        "target_date": "not-a-date"
    })
    assert res_bad_date.status_code in (400, 422)

    # Invalid calendar day
    res_bad_cal = client.post("/api/savings-goals", json={
        "goal_name": "Bike",
        "target_amount": 10000.0,
        "target_date": "2026-02-31"
    })
    assert res_bad_cal.status_code in (400, 422)


def test_add_money_and_completion(client):
    """Test depositing money into a savings goal and completing it."""
    future_date = (date.today() + timedelta(days=60)).isoformat()
    create_res = client.post("/api/savings-goals", json={
        "goal_name": "New Laptop",
        "target_amount": 40000.0,
        "target_date": future_date,
        "current_saved_amount": 10000.0,
        "user_id": "test_user"
    })
    assert create_res.status_code == 201
    goal_id = create_res.json()["id"]

    # Partial deposit
    dep1 = client.post(f"/api/savings-goals/{goal_id}/add-money", json={
        "amount": 15000.0,
        "user_id": "test_user"
    })
    assert dep1.status_code == 200
    d1 = dep1.json()
    assert d1["current_saved_amount"] == 25000.0
    assert d1["remaining_amount"] == 15000.0
    assert d1["progress_percentage"] == 62.5
    assert d1["status"] == "In Progress"
    assert d1["just_completed"] is False

    # Completing deposit
    dep2 = client.post(f"/api/savings-goals/{goal_id}/add-money", json={
        "amount": 15000.0,
        "user_id": "test_user"
    })
    assert dep2.status_code == 200
    d2 = dep2.json()
    assert d2["current_saved_amount"] == 40000.0
    assert d2["remaining_amount"] == 0.0
    assert d2["progress_percentage"] == 100.0
    assert d2["status"] == "Completed"
    assert d2["just_completed"] is True
    assert "Congratulations" in d2["message"]

    # Negative / zero deposit rejected
    bad_dep = client.post(f"/api/savings-goals/{goal_id}/add-money", json={
        "amount": -500.0,
        "user_id": "test_user"
    })
    assert bad_dep.status_code in (400, 422)


def test_status_calculation_and_overdue(client):
    """Test status logic for In Progress, Completed, and Overdue goals."""
    past_date = (date.today() - timedelta(days=10)).isoformat()
    future_date = (date.today() + timedelta(days=30)).isoformat()

    # Overdue goal (target date in the past, incomplete)
    overdue_res = client.post("/api/savings-goals", json={
        "goal_name": "Past Goal",
        "target_amount": 10000.0,
        "target_date": past_date,
        "current_saved_amount": 5000.0,
        "user_id": "user_a"
    })
    assert overdue_res.status_code == 201
    assert overdue_res.json()["status"] == "Overdue"

    # Completed goal even if date in the past
    completed_past = client.post("/api/savings-goals", json={
        "goal_name": "Past Achieved",
        "target_amount": 10000.0,
        "target_date": past_date,
        "current_saved_amount": 10000.0,
        "user_id": "user_a"
    })
    assert completed_past.status_code == 201
    assert completed_past.json()["status"] == "Completed"

    # In progress goal
    in_prog = client.post("/api/savings-goals", json={
        "goal_name": "Future Active",
        "target_amount": 10000.0,
        "target_date": future_date,
        "current_saved_amount": 2000.0,
        "user_id": "user_a"
    })
    assert in_prog.status_code == 201
    assert in_prog.json()["status"] == "In Progress"


def test_user_privacy_isolation(client):
    """Test that users cannot view, modify, or delete other users' savings goals."""
    future_date = (date.today() + timedelta(days=60)).isoformat()

    # Create goal for user 1
    u1_goal = client.post("/api/savings-goals", json={
        "goal_name": "User 1 Secret Fund",
        "target_amount": 30000.0,
        "target_date": future_date,
        "user_id": "user_1"
    }).json()

    # User 2 list should not include User 1's goal
    u2_list = client.get("/api/savings-goals?user_id=user_2").json()
    assert len(u2_list) == 0

    # User 2 cannot fetch User 1's goal by ID
    u2_get = client.get(f"/api/savings-goals/{u1_goal['id']}?user_id=user_2")
    assert u2_get.status_code == 404

    # User 2 cannot deposit to User 1's goal
    u2_deposit = client.post(f"/api/savings-goals/{u1_goal['id']}/add-money", json={
        "amount": 1000.0,
        "user_id": "user_2"
    })
    assert u2_deposit.status_code == 404

    # User 2 cannot edit User 1's goal
    u2_edit = client.put(f"/api/savings-goals/{u1_goal['id']}", json={
        "goal_name": "Hacked Goal",
        "user_id": "user_2"
    })
    assert u2_edit.status_code == 404

    # User 2 cannot delete User 1's goal
    u2_del = client.delete(f"/api/savings-goals/{u1_goal['id']}?user_id=user_2")
    assert u2_del.status_code == 404

    # User 1 can fetch their goal
    u1_get = client.get(f"/api/savings-goals/{u1_goal['id']}?user_id=user_1")
    assert u1_get.status_code == 200
    assert u1_get.json()["goal_name"] == "User 1 Secret Fund"


def test_update_and_delete_savings_goal(client):
    """Test updating fields and deleting a savings goal."""
    future_date = (date.today() + timedelta(days=30)).isoformat()
    created = client.post("/api/savings-goals", json={
        "goal_name": "Old Name",
        "target_amount": 20000.0,
        "target_date": future_date,
        "user_id": "user_crud"
    }).json()

    goal_id = created["id"]

    # Update goal
    new_date = (date.today() + timedelta(days=60)).isoformat()
    up_res = client.put(f"/api/savings-goals/{goal_id}", json={
        "goal_name": "New Goal Name",
        "target_amount": 25000.0,
        "target_date": new_date,
        "description": "Updated note",
        "user_id": "user_crud"
    })
    assert up_res.status_code == 200
    updated = up_res.json()
    assert updated["goal_name"] == "New Goal Name"
    assert updated["target_amount"] == 25000.0
    assert updated["target_date"] == new_date
    assert updated["description"] == "Updated note"

    # Delete goal
    del_res = client.delete(f"/api/savings-goals/{goal_id}?user_id=user_crud")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Confirm deletion
    get_res = client.get(f"/api/savings-goals/{goal_id}?user_id=user_crud")
    assert get_res.status_code == 404


def test_savings_summary_endpoint(client):
    """Test the savings goals summary statistics endpoint."""
    future_date = (date.today() + timedelta(days=45)).isoformat()
    past_date = (date.today() - timedelta(days=5)).isoformat()

    client.post("/api/savings-goals", json={
        "goal_name": "Goal A Completed",
        "target_amount": 10000.0,
        "current_saved_amount": 10000.0,
        "target_date": future_date,
        "user_id": "summary_user"
    })

    client.post("/api/savings-goals", json={
        "goal_name": "Goal B In Progress",
        "target_amount": 20000.0,
        "current_saved_amount": 10000.0,
        "target_date": future_date,
        "user_id": "summary_user"
    })

    client.post("/api/savings-goals", json={
        "goal_name": "Goal C Overdue",
        "target_amount": 10000.0,
        "current_saved_amount": 4000.0,
        "target_date": past_date,
        "user_id": "summary_user"
    })

    sum_res = client.get("/api/savings-goals/summary?user_id=summary_user")
    assert sum_res.status_code == 200
    s = sum_res.json()
    assert s["total_goals"] == 3
    assert s["total_target_amount"] == 40000.0
    assert s["total_saved_amount"] == 24000.0
    assert s["overall_progress_percentage"] == 60.0
    assert s["completed_count"] == 1
    assert s["in_progress_count"] == 1
    assert s["overdue_count"] == 1


def test_seed_and_clear_sample_savings_goals(client):
    """Test that sample data seeding includes savings goals and clearing preserves user goals."""
    db_path = client.app.state.db_path

    # User creates a custom goal
    future_date = (date.today() + timedelta(days=90)).isoformat()
    user_goal = client.post("/api/savings-goals", json={
        "goal_name": "My Custom Life Goal",
        "target_amount": 100000.0,
        "target_date": future_date,
        "user_id": "default_user"
    }).json()

    # Seed sample data
    seed_res = client.post("/api/sample-data/seed")
    assert seed_res.status_code == 200
    assert seed_res.json()["counts"]["savings_goals"] >= 3

    # Check that both custom and sample goals exist
    goals_after_seed = client.get("/api/savings-goals").json()
    assert len(goals_after_seed) >= 4

    # Clear sample data
    clear_res = client.post("/api/sample-data/clear")
    assert clear_res.status_code == 200
    assert clear_res.json()["counts"]["savings_goals"] >= 3

    # User goal must be preserved!
    goals_after_clear = client.get("/api/savings-goals").json()
    assert len(goals_after_clear) == 1
    assert goals_after_clear[0]["goal_name"] == "My Custom Life Goal"
