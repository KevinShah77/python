"""
FastAPI Backend REST API for PennyPilot Personal Finance Management System
--------------------------------------------------------------------------
Connects the PennyPilot modern web frontend with the SQLite database.
Provides RESTful CRUD operations for Expenses, Income, and Budgets,
plus CSV and PDF report streaming, and serves the production frontend.
"""

import os
import sys
import calendar
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Ensure personal_expense_manager is in path
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

from database import (
    init_db,
    add_expense,
    get_all_expenses,
    get_expense_by_id,
    update_expense,
    delete_expense,
    add_income,
    get_all_income,
    get_income_by_id,
    update_income,
    delete_income,
    set_budget,
    get_all_budgets,
    get_budget_by_id,
    get_budget_by_category,
    delete_budget,
    get_unified_transactions,
    seed_sample_data,
    clear_sample_data,
    reset_all_data,
    has_data,
    has_sample_data,
    DEFAULT_DB_PATH
)
from expense_manager import CATEGORIES, PAYMENT_METHODS, validate_expense
from income_manager import INCOME_SOURCES, validate_income
from budget_manager import save_budget
from reports import generate_csv_report, generate_pdf_report
from savings_manager import (
    create_savings_goal,
    get_all_savings_goals,
    get_savings_goal_by_id,
    update_savings_goal,
    delete_savings_goal,
    add_money_to_savings_goal,
    get_savings_summary,
    validate_goal_inputs,
    compute_goal_status,
    compute_progress_and_remaining
)


app = FastAPI(
    title="PennyPilot API",
    description="RESTful API for PennyPilot Personal Finance & Budget Management System",
    version="1.0.0"
)

# Enable CORS for local dev servers (Vite defaults to 3000, 5173, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_active_db() -> Optional[str]:
    """Return database path configured on app.state or fallback to default."""
    return getattr(app.state, "db_path", None)


def parse_period(period_str: Optional[str]) -> Tuple[int, int]:
    """Parse and validate a YYYY-MM period string. Raises HTTP 400 if invalid."""
    if not period_str or not isinstance(period_str, str):
        raise HTTPException(
            status_code=400,
            detail="Period parameter is required in format YYYY-MM (e.g. 2026-11)"
        )
    try:
        parts = period_str.strip().split("-")
        if len(parts) != 2:
            raise ValueError
        year, month = int(parts[0]), int(parts[1])
        if not (1 <= month <= 12 and 2000 <= year <= 2100):
            raise ValueError
        return year, month
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period format: '{period_str}'. Expected YYYY-MM (e.g. 2026-11) with month between 01 and 12."
        )


# ---------------------------------------------------------------------------
# PYDANTIC DATA MODELS
# ---------------------------------------------------------------------------

class ExpensePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0, le=10_000_000)
    category: str
    date: str
    paymentMethod: Optional[str] = "Cash"
    description: Optional[str] = ""


class IncomePayload(BaseModel):
    source: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0, le=50_000_000)
    date: str
    description: Optional[str] = ""


class BudgetPayload(BaseModel):
    category: str
    amount: float = Field(..., gt=0, le=100_000_000)
    period: str  # Format: "YYYY-MM"


class SavingsGoalCreatePayload(BaseModel):
    goal_name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0, le=100_000_000)
    target_date: str
    description: Optional[str] = Field(default="", max_length=300)
    current_saved_amount: Optional[float] = Field(default=0.0, ge=0, le=100_000_000)
    user_id: Optional[str] = Field(default="default_user", max_length=100)


class SavingsGoalUpdatePayload(BaseModel):
    goal_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    target_amount: Optional[float] = Field(default=None, gt=0, le=100_000_000)
    target_date: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=300)
    current_saved_amount: Optional[float] = Field(default=None, ge=0, le=100_000_000)
    user_id: Optional[str] = Field(default="default_user", max_length=100)


class AddMoneyPayload(BaseModel):
    amount: float = Field(..., gt=0, le=50_000_000)
    user_id: Optional[str] = Field(default="default_user", max_length=100)



# ---------------------------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------------------------

@app.get("/api/status")
def api_status():
    """System health and SQLite connection status."""
    db_path = get_active_db()
    init_db(db_path)
    expenses = get_all_expenses(db_path)
    income = get_all_income(db_path)
    budgets = get_all_budgets(db_path)
    savings_goals = get_all_savings_goals(user_id=None, db_path=db_path)
    return {
        "status": "online",
        "app": "PennyPilot",
        "version": "1.0.0",
        "db_connected": True,
        "db_path": db_path or DEFAULT_DB_PATH,
        "has_data": len(expenses) > 0 or len(income) > 0 or len(savings_goals) > 0,
        "has_sample_data": has_sample_data(db_path),
        "counts": {
            "expenses": len(expenses),
            "income": len(income),
            "budgets": len(budgets),
            "savings_goals": len(savings_goals),
        }
    }


@app.get("/api/data")
def get_full_app_data(auto_seed: bool = False, user_id: str = "default_user"):
    """
    Retrieve all expenses, income, budgets, and savings goals formatted for the PennyPilot frontend.
    Optionally seeds realistic sample data if the database is currently empty.
    """
    db_path = get_active_db()
    init_db(db_path)

    if auto_seed and not has_data(db_path):
        seed_sample_data(db_path=db_path)

    raw_expenses = get_all_expenses(db_path)
    raw_income = get_all_income(db_path)
    raw_budgets = get_all_budgets(db_path)
    savings_goals = get_all_savings_goals(user_id=user_id, db_path=db_path)

    expenses = [
        {
            "id": r["id"],
            "type": "expense",
            "name": r["expense_name"],
            "amount": float(r["amount"]),
            "category": r["category"],
            "date": r["date"],
            "paymentMethod": r["payment_method"] or "Cash",
            "description": r["description"] or "",
        }
        for r in raw_expenses
    ]

    income = [
        {
            "id": r["id"],
            "type": "income",
            "source": r["income_source"],
            "amount": float(r["amount"]),
            "date": r["date"],
            "description": r["description"] or "",
        }
        for r in raw_income
    ]

    budgets = [
        {
            "id": r["id"],
            "category": r["category"],
            "amount": float(r["budget_amount"]),
            "period": f"{int(r['year']):04d}-{int(r['month']):02d}",
        }
        for r in raw_budgets
    ]

    return {"expenses": expenses, "income": income, "budgets": budgets, "savings_goals": savings_goals}


# ---------------------------------------------------------------------------
# EXPENSES CRUD
# ---------------------------------------------------------------------------

@app.post("/api/expenses", status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpensePayload):
    """Add a new expense to SQLite after strict validation."""
    db_path = get_active_db()
    init_db(db_path)

    if payload.paymentMethod and payload.paymentMethod not in PAYMENT_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment method: '{payload.paymentMethod}'. Allowed: {', '.join(PAYMENT_METHODS)}"
        )

    is_valid, err = validate_expense(
        expense_name=payload.name,
        amount=payload.amount,
        category=payload.category,
        date_val=payload.date
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=err)

    new_id = add_expense(
        expense_name=payload.name,
        amount=payload.amount,
        category=payload.category,
        date_str=payload.date,
        payment_method=payload.paymentMethod or "Cash",
        description=payload.description or "",
        db_path=db_path
    )

    row = get_expense_by_id(new_id, db_path=db_path)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created expense")

    return {
        "id": row["id"],
        "type": "expense",
        "name": row["expense_name"],
        "amount": float(row["amount"]),
        "category": row["category"],
        "date": row["date"],
        "paymentMethod": row["payment_method"] or "Cash",
        "description": row["description"] or "",
    }


@app.put("/api/expenses/{expense_id}")
def update_expense_by_id(expense_id: int, payload: ExpensePayload):
    """Update an existing expense in SQLite."""
    db_path = get_active_db()
    init_db(db_path)

    existing = get_expense_by_id(expense_id, db_path=db_path)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Expense with ID {expense_id} not found")

    if payload.paymentMethod and payload.paymentMethod not in PAYMENT_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment method: '{payload.paymentMethod}'. Allowed: {', '.join(PAYMENT_METHODS)}"
        )

    is_valid, err = validate_expense(
        expense_name=payload.name,
        amount=payload.amount,
        category=payload.category,
        date_val=payload.date
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=err)

    success = update_expense(
        expense_id=expense_id,
        expense_name=payload.name,
        amount=payload.amount,
        category=payload.category,
        date_str=payload.date,
        payment_method=payload.paymentMethod or "Cash",
        description=payload.description or "",
        db_path=db_path
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update expense")

    row = get_expense_by_id(expense_id, db_path=db_path)
    return {
        "id": row["id"],
        "type": "expense",
        "name": row["expense_name"],
        "amount": float(row["amount"]),
        "category": row["category"],
        "date": row["date"],
        "paymentMethod": row["payment_method"] or "Cash",
        "description": row["description"] or "",
    }


@app.delete("/api/expenses/{expense_id}")
def delete_expense_by_id(expense_id: int):
    """Delete an expense record from SQLite."""
    db_path = get_active_db()
    init_db(db_path)

    existing = get_expense_by_id(expense_id, db_path=db_path)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Expense with ID {expense_id} not found")

    delete_expense(expense_id, db_path=db_path)
    return {"success": True, "deleted_id": expense_id}


# ---------------------------------------------------------------------------
# INCOME CRUD
# ---------------------------------------------------------------------------

@app.post("/api/income", status_code=status.HTTP_201_CREATED)
def create_income(payload: IncomePayload):
    """Add a new income entry to SQLite after strict validation."""
    db_path = get_active_db()
    init_db(db_path)

    if payload.source not in INCOME_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid income source: '{payload.source}'. Allowed: {', '.join(INCOME_SOURCES)}"
        )

    is_valid, err = validate_income(
        income_source=payload.source,
        amount=payload.amount,
        date_val=payload.date
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=err)

    new_id = add_income(
        income_source=payload.source,
        amount=payload.amount,
        date_str=payload.date,
        description=payload.description or "",
        db_path=db_path
    )

    row = get_income_by_id(new_id, db_path=db_path)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created income")

    return {
        "id": row["id"],
        "type": "income",
        "source": row["income_source"],
        "amount": float(row["amount"]),
        "date": row["date"],
        "description": row["description"] or "",
    }


@app.put("/api/income/{income_id}")
def update_income_by_id(income_id: int, payload: IncomePayload):
    """Update an existing income entry in SQLite."""
    db_path = get_active_db()
    init_db(db_path)

    existing = get_income_by_id(income_id, db_path=db_path)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Income with ID {income_id} not found")

    if payload.source not in INCOME_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid income source: '{payload.source}'. Allowed: {', '.join(INCOME_SOURCES)}"
        )

    is_valid, err = validate_income(
        income_source=payload.source,
        amount=payload.amount,
        date_val=payload.date
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=err)

    success = update_income(
        income_id=income_id,
        income_source=payload.source,
        amount=payload.amount,
        date_str=payload.date,
        description=payload.description or "",
        db_path=db_path
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update income")

    row = get_income_by_id(income_id, db_path=db_path)
    return {
        "id": row["id"],
        "type": "income",
        "source": row["income_source"],
        "amount": float(row["amount"]),
        "date": row["date"],
        "description": row["description"] or "",
    }


@app.delete("/api/income/{income_id}")
def delete_income_by_id(income_id: int):
    """Delete an income record from SQLite."""
    db_path = get_active_db()
    init_db(db_path)

    existing = get_income_by_id(income_id, db_path=db_path)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Income with ID {income_id} not found")

    delete_income(income_id, db_path=db_path)
    return {"success": True, "deleted_id": income_id}


# ---------------------------------------------------------------------------
# BUDGETS CRUD
# ---------------------------------------------------------------------------

@app.post("/api/budgets")
def save_budget_endpoint(payload: BudgetPayload):
    """Create or update a budget limit in SQLite."""
    db_path = get_active_db()
    init_db(db_path)

    valid_categories = ["Overall"] + CATEGORIES
    if payload.category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: '{payload.category}'. Allowed: {', '.join(valid_categories)}"
        )

    if payload.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Budget amount must be a positive number strictly greater than ₹0."
        )

    if payload.amount > 100_000_000:
        raise HTTPException(
            status_code=400,
            detail="Budget amount cannot exceed ₹10,00,00,000 (10 Crores)."
        )

    year, month = parse_period(payload.period)

    ok, msg = save_budget(
        category=payload.category,
        budget_amount=payload.amount,
        month=month,
        year=year,
        db_path=db_path
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    row = get_budget_by_category(payload.category, year=year, month=month, db_path=db_path)
    return {
        "id": row["id"] if row else 1,
        "category": row["category"] if row else payload.category,
        "amount": float(row["budget_amount"]) if row else payload.amount,
        "period": f"{year:04d}-{month:02d}",
    }


@app.delete("/api/budgets/{budget_id}")
def delete_budget_endpoint(budget_id: int):
    """Delete a budget limit by ID from SQLite."""
    db_path = get_active_db()
    init_db(db_path)

    existing = get_budget_by_id(budget_id, db_path=db_path)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Budget with ID {budget_id} not found")

    deleted = delete_budget(budget_id, db_path=db_path)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Budget with ID {budget_id} not found")
    return {"success": True, "deleted_id": budget_id}


# ---------------------------------------------------------------------------
# SAVINGS GOALS CRUD & ADD-MONEY
# ---------------------------------------------------------------------------

@app.get("/api/savings-goals")
def list_savings_goals(
    status: Optional[str] = None,
    user_id: str = Query("default_user")
):
    """Retrieve all savings goals for the specified user."""
    db_path = get_active_db()
    init_db(db_path)
    return get_all_savings_goals(user_id=user_id, status_filter=status, db_path=db_path)


@app.get("/api/savings-goals/summary")
def get_savings_summary_endpoint(user_id: str = Query("default_user")):
    """Get high-level summary metrics across user's savings goals."""
    db_path = get_active_db()
    init_db(db_path)
    return get_savings_summary(user_id=user_id, db_path=db_path)


@app.get("/api/savings-goals/{goal_id}")
def get_savings_goal_endpoint(goal_id: int, user_id: str = Query("default_user")):
    """Retrieve a single savings goal by ID, enforcing user privacy."""
    db_path = get_active_db()
    init_db(db_path)
    goal = get_savings_goal_by_id(goal_id=goal_id, user_id=user_id, db_path=db_path)
    if not goal:
        raise HTTPException(status_code=404, detail=f"Savings goal with ID {goal_id} not found")
    return goal


@app.post("/api/savings-goals", status_code=status.HTTP_201_CREATED)
def create_savings_goal_endpoint(payload: SavingsGoalCreatePayload):
    """Create a new savings goal with strict Pydantic validation."""
    db_path = get_active_db()
    init_db(db_path)

    is_valid, err = validate_goal_inputs(
        goal_name=payload.goal_name,
        target_amount=payload.target_amount,
        target_date=payload.target_date,
        current_saved_amount=payload.current_saved_amount or 0.0
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=err)

    created = create_savings_goal(
        goal_name=payload.goal_name,
        target_amount=payload.target_amount,
        target_date=payload.target_date,
        description=payload.description or "",
        current_saved_amount=payload.current_saved_amount or 0.0,
        user_id=payload.user_id or "default_user",
        db_path=db_path
    )
    return created


@app.put("/api/savings-goals/{goal_id}")
def update_savings_goal_endpoint(goal_id: int, payload: SavingsGoalUpdatePayload):
    """Update an existing savings goal with validation and privacy enforcement."""
    db_path = get_active_db()
    init_db(db_path)

    existing = get_savings_goal_by_id(goal_id=goal_id, user_id=payload.user_id, db_path=db_path)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Savings goal with ID {goal_id} not found")

    new_name = payload.goal_name if payload.goal_name is not None else existing["goal_name"]
    new_target = payload.target_amount if payload.target_amount is not None else existing["target_amount"]
    new_date = payload.target_date if payload.target_date is not None else existing["target_date"]
    new_saved = payload.current_saved_amount if payload.current_saved_amount is not None else existing["current_saved_amount"]

    is_valid, err = validate_goal_inputs(
        goal_name=new_name,
        target_amount=new_target,
        target_date=new_date,
        current_saved_amount=new_saved
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=err)

    updated = update_savings_goal(
        goal_id=goal_id,
        goal_name=payload.goal_name,
        target_amount=payload.target_amount,
        target_date=payload.target_date,
        description=payload.description,
        current_saved_amount=payload.current_saved_amount,
        user_id=payload.user_id,
        db_path=db_path
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Savings goal with ID {goal_id} not found")
    return updated


@app.delete("/api/savings-goals/{goal_id}")
def delete_savings_goal_endpoint(goal_id: int, user_id: str = Query("default_user")):
    """Delete a savings goal by ID, enforcing user privacy."""
    db_path = get_active_db()
    init_db(db_path)

    success = delete_savings_goal(goal_id=goal_id, user_id=user_id, db_path=db_path)
    if not success:
        raise HTTPException(status_code=404, detail=f"Savings goal with ID {goal_id} not found")
    return {"success": True, "deleted_id": goal_id}


@app.post("/api/savings-goals/{goal_id}/add-money")
def add_money_endpoint(goal_id: int, payload: AddMoneyPayload):
    """
    Deposit funds into a savings goal.
    Returns the updated goal and whether it was newly completed.
    """
    db_path = get_active_db()
    init_db(db_path)

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Contribution amount must be greater than ₹0.")
    if payload.amount > 50_000_000:
        raise HTTPException(status_code=400, detail="Contribution amount cannot exceed ₹5,00,00,000.")

    try:
        updated, just_completed = add_money_to_savings_goal(
            goal_id=goal_id,
            amount=payload.amount,
            user_id=payload.user_id,
            db_path=db_path
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail=f"Savings goal with ID {goal_id} not found")

    message = (
        f"🎉 Congratulations! You have completed your savings goal: '{updated['goal_name']}'!"
        if just_completed
        else f"Added ₹{payload.amount:,.2f} to '{updated['goal_name']}'."
    )

    return {
        **updated,
        "just_completed": just_completed,
        "message": message
    }


# ---------------------------------------------------------------------------
# SAMPLE DATA MANAGEMENT
# ---------------------------------------------------------------------------

@app.post("/api/sample-data/seed")
def seed_sample_data_endpoint():
    """Seed sample Indian college/student expenses, income, and budgets into SQLite."""
    db_path = get_active_db()
    init_db(db_path)
    counts = seed_sample_data(db_path=db_path)
    return {"success": True, "message": "Demo sample data loaded successfully", "counts": counts}


@app.post("/api/sample-data/clear")
def clear_sample_data_endpoint():
    """Clear all sample data rows (retains user-entered rows)."""
    db_path = get_active_db()
    init_db(db_path)
    counts = clear_sample_data(db_path=db_path)
    return {"success": True, "message": "Demo sample data cleared", "counts": counts}


@app.post("/api/reset")
def reset_database_endpoint():
    """Wipe all records from SQLite."""
    db_path = get_active_db()
    init_db(db_path)
    reset_all_data(db_path=db_path)
    return {"success": True, "message": "All data removed from SQLite database"}


# ---------------------------------------------------------------------------
# REPORT EXPORTS (CSV & PDF)
# ---------------------------------------------------------------------------

@app.get("/api/reports/csv")
def download_csv_endpoint(period: Optional[str] = Query(None)):
    """Generate and download a CSV financial report for the given period."""
    db_path = get_active_db()
    init_db(db_path)

    year, month = None, None
    if period:
        year, month = parse_period(period)

    if year and month:
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year:04d}-{month:02d}-01"
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"
        txs = get_unified_transactions(start_date=start_date, end_date=end_date, db_path=db_path)
    else:
        txs = get_unified_transactions(db_path=db_path)

    csv_text = generate_csv_report(txs, year=year, month=month, db_path=db_path)
    filename = f"pennypilot-report-{period or 'all'}.csv"

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/reports/pdf")
def download_pdf_endpoint(period: Optional[str] = Query(None)):
    """Generate and download a ReportLab PDF financial report."""
    db_path = get_active_db()
    init_db(db_path)

    today = date.today()
    if period:
        year, month = parse_period(period)
    else:
        year, month = today.year, today.month

    pdf_bytes = generate_pdf_report(year=year, month=month, db_path=db_path)
    filename = f"pennypilot-report-{year:04d}-{month:02d}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ---------------------------------------------------------------------------
# STATIC FRONTEND SERVING
# ---------------------------------------------------------------------------

FRONTEND_DIST = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend",
    "dist"
)

if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        # Serve static asset files if they exist in dist root (brand-mark.png, favicon.svg, etc.)
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)

        # Fallback to SPA index.html
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)

        return Response(content="PennyPilot Frontend dist index.html not found", status_code=404)
