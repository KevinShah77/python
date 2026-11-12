"""
Database Module for Personal Expenses & Smart Budget Management System
----------------------------------------------------------------------
Academic Demonstration Concepts:
- SQLite3 database connection and cursor handling
- Context managers ('with' statement) for automatic commit/rollback
- Parameterized SQL queries to prevent SQL injection
- Data integrity constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE)
- Exception handling with sqlite3.Error
- CRUD operations (Create, Read, Update, Delete)
"""

import os
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

# Default database path inside data/ directory
DEFAULT_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "expenses.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Establish and return a connection to the SQLite database.
    Ensures directory exists and enables foreign keys, WAL mode, and dictionary row access.
    """
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enables column-by-name access
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
    except Exception:
        pass
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initialize SQLite database tables if they do not exist.
    Creates tables: expenses, income, budgets.
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()

            # Table 1: Expenses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_name TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    payment_method TEXT,
                    description TEXT,
                    is_sample INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Table 2: Income
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS income (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    income_source TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    date TEXT NOT NULL,
                    description TEXT,
                    is_sample INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Table 3: Budgets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    budget_amount REAL NOT NULL CHECK(budget_amount >= 0),
                    month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
                    year INTEGER NOT NULL CHECK(year >= 2000),
                    is_sample INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, month, year)
                );
            """)

            # Table 4: Savings Goals
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS savings_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    goal_name TEXT NOT NULL,
                    target_amount REAL NOT NULL CHECK(target_amount > 0),
                    current_saved_amount REAL NOT NULL DEFAULT 0.0 CHECK(current_saved_amount >= 0),
                    target_date TEXT NOT NULL,
                    description TEXT,
                    created_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'In Progress',
                    is_sample INTEGER DEFAULT 0
                );
            """)

            # Create indices for query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_income_date ON income(date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_my ON budgets(month, year);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_savings_goals_user ON savings_goals(user_id);")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# EXPENSE CRUD OPERATIONS
# ---------------------------------------------------------------------------

def add_expense(
    expense_name: str,
    amount: float,
    category: str,
    date_str: str,
    payment_method: str = "Cash",
    description: str = "",
    is_sample: int = 0,
    db_path: Optional[str] = None
) -> int:
    """
    Add a new expense record to the database.
    Returns the newly inserted row ID.
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (expense_name, amount, category, date, payment_method, description, is_sample)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                expense_name.strip(),
                float(amount),
                category.strip(),
                date_str.strip(),
                (payment_method or "").strip(),
                (description or "").strip(),
                int(is_sample)
            ))
            return cursor.lastrowid
    finally:
        conn.close()


def get_all_expenses(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all expenses ordered by date descending."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC, id DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_expenses_by_month(year: int, month: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all expenses for a specific year and month."""
    month_str = f"{year:04d}-{month:02d}-%"
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM expenses 
            WHERE date LIKE ? 
            ORDER BY date DESC, id DESC
        """, (month_str,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_expense_by_id(expense_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single expense record by ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_expense(
    expense_id: int,
    expense_name: str,
    amount: float,
    category: str,
    date_str: str,
    payment_method: str = "Cash",
    description: str = "",
    db_path: Optional[str] = None
) -> bool:
    """Update an existing expense record."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE expenses
                SET expense_name = ?, amount = ?, category = ?, date = ?, payment_method = ?, description = ?
                WHERE id = ?
            """, (
                expense_name.strip(),
                float(amount),
                category.strip(),
                date_str.strip(),
                (payment_method or "").strip(),
                (description or "").strip(),
                expense_id
            ))
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_expense(expense_id: int, db_path: Optional[str] = None) -> bool:
    """Delete an expense record by ID."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# INCOME CRUD OPERATIONS
# ---------------------------------------------------------------------------

def add_income(
    income_source: str,
    amount: float,
    date_str: str,
    description: str = "",
    is_sample: int = 0,
    db_path: Optional[str] = None
) -> int:
    """
    Add a new income record.
    Returns the newly inserted row ID.
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO income (income_source, amount, date, description, is_sample)
                VALUES (?, ?, ?, ?, ?)
            """, (
                income_source.strip(),
                float(amount),
                date_str.strip(),
                (description or "").strip(),
                int(is_sample)
            ))
            return cursor.lastrowid
    finally:
        conn.close()


def get_all_income(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all income records ordered by date descending."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM income ORDER BY date DESC, id DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_income_by_month(year: int, month: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all income for a specific year and month."""
    month_str = f"{year:04d}-{month:02d}-%"
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM income 
            WHERE date LIKE ? 
            ORDER BY date DESC, id DESC
        """, (month_str,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_income_by_id(income_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single income record by ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM income WHERE id = ?", (income_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_income(
    income_id: int,
    income_source: str,
    amount: float,
    date_str: str,
    description: str = "",
    db_path: Optional[str] = None
) -> bool:
    """Update an existing income record."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE income
                SET income_source = ?, amount = ?, date = ?, description = ?
                WHERE id = ?
            """, (
                income_source.strip(),
                float(amount),
                date_str.strip(),
                (description or "").strip(),
                income_id
            ))
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_income(income_id: int, db_path: Optional[str] = None) -> bool:
    """Delete an income record by ID."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM income WHERE id = ?", (income_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# BUDGET CRUD OPERATIONS
# ---------------------------------------------------------------------------

def set_budget(
    category: str,
    budget_amount: float,
    month: int,
    year: int,
    is_sample: int = 0,
    db_path: Optional[str] = None
) -> int:
    """
    Insert or update (upsert) a budget limit for a category in a given month and year.
    'Overall' is used for overall monthly budget limit.
    """
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO budgets (category, budget_amount, month, year, is_sample)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(category, month, year) DO UPDATE SET
                    budget_amount = excluded.budget_amount,
                    is_sample = excluded.is_sample
            """, (
                category.strip(),
                float(budget_amount),
                int(month),
                int(year),
                int(is_sample)
            ))
            return cursor.lastrowid
    finally:
        conn.close()


def get_budgets_by_month(year: int, month: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all budget allocations for a specific month and year."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM budgets 
            WHERE month = ? AND year = ?
            ORDER BY CASE WHEN category = 'Overall' THEN 0 ELSE 1 END, category ASC
        """, (int(month), int(year)))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_budgets(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all budget records ordered by year DESC, month DESC, category ASC."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM budgets 
            ORDER BY year DESC, month DESC, CASE WHEN category = 'Overall' THEN 0 ELSE 1 END, category ASC
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_budget_by_id(budget_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single budget record by ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets WHERE id = ?", (int(budget_id),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_budget_by_category(category: str, year: int, month: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get budget for a specific category in a month/year."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM budgets 
            WHERE category = ? AND month = ? AND year = ?
        """, (category.strip(), int(month), int(year)))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_budget(budget_id: int, db_path: Optional[str] = None) -> bool:
    """Delete a budget entry by ID."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_budget_by_category(category: str, year: int, month: int, db_path: Optional[str] = None) -> bool:
    """Delete budget limit for a category in a specific month and year."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM budgets 
                WHERE category = ? AND month = ? AND year = ?
            """, (category.strip(), int(month), int(year)))
            return cursor.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# UNIFIED TRANSACTIONS AND REPORT QUERIES
# ---------------------------------------------------------------------------

def get_unified_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    tx_type: Optional[str] = None,  # 'Expense', 'Income', or None (Both)
    search_query: Optional[str] = None,
    sort_by: str = "date",          # "date" or "amount"
    sort_order: str = "DESC",       # "ASC" or "DESC"
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve unified transaction stream (both income and expenses) with flexible
    filtering and sorting for the Transaction History page.
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()

        # Build UNION query
        # Standardizing columns:
        # id, name, type, category_or_source, amount, date, payment_method, description, is_sample
        query = """
            SELECT 
                id,
                expense_name AS name,
                'Expense' AS type,
                category AS category_or_source,
                amount,
                date,
                payment_method,
                description,
                is_sample
            FROM expenses
            UNION ALL
            SELECT 
                id,
                income_source AS name,
                'Income' AS type,
                income_source AS category_or_source,
                amount,
                date,
                'N/A' AS payment_method,
                description,
                is_sample
            FROM income
        """

        # Wrap in outer query for filtering
        outer_query = f"SELECT * FROM ({query}) WHERE 1=1"
        params: List[Any] = []

        if start_date:
            outer_query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            outer_query += " AND date <= ?"
            params.append(end_date)

        if tx_type and tx_type in ("Expense", "Income"):
            outer_query += " AND type = ?"
            params.append(tx_type)

        if category and category != "All":
            outer_query += " AND category_or_source = ?"
            params.append(category)

        if search_query:
            wildcard = f"%{search_query.strip()}%"
            outer_query += " AND (name LIKE ? OR description LIKE ? OR payment_method LIKE ?)"
            params.extend([wildcard, wildcard, wildcard])

        # Sorting validation
        valid_sort_cols = {"date": "date", "amount": "amount"}
        order_col = valid_sort_cols.get(sort_by.lower(), "date")
        order_dir = "ASC" if sort_order.upper() == "ASC" else "DESC"

        outer_query += f" ORDER BY {order_col} {order_dir}, id DESC"

        cursor.execute(outer_query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_available_months_and_years(db_path: Optional[str] = None) -> List[Tuple[int, int]]:
    """
    Returns a distinct sorted list of (year, month) tuples from existing
    income, expense, and budget records. Always includes current month/year.
    """
    conn = get_connection(db_path)
    periods = set()
    today = date.today()
    periods.add((today.year, today.month))
    # Include next month and previous month so users can establish future budgets or review history
    next_m = today.month + 1 if today.month < 12 else 1
    next_y = today.year if today.month < 12 else today.year + 1
    periods.add((next_y, next_m))
    prev_m = today.month - 1 if today.month > 1 else 12
    prev_y = today.year if today.month > 1 else today.year - 1
    periods.add((prev_y, prev_m))

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT substr(date, 1, 7) AS ym FROM expenses WHERE date IS NOT NULL")
        for row in cursor.fetchall():
            if row["ym"] and len(row["ym"]) == 7:
                try:
                    y, m = map(int, row["ym"].split("-"))
                    periods.add((y, m))
                except ValueError:
                    pass

        cursor.execute("SELECT DISTINCT substr(date, 1, 7) AS ym FROM income WHERE date IS NOT NULL")
        for row in cursor.fetchall():
            if row["ym"] and len(row["ym"]) == 7:
                try:
                    y, m = map(int, row["ym"].split("-"))
                    periods.add((y, m))
                except ValueError:
                    pass

        cursor.execute("SELECT DISTINCT year, month FROM budgets")
        for row in cursor.fetchall():
            periods.add((int(row["year"]), int(row["month"])))

        sorted_periods = sorted(list(periods), key=lambda x: (x[0], x[1]), reverse=True)
        return sorted_periods
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# SAMPLE DATA MANAGEMENT
# ---------------------------------------------------------------------------

def seed_sample_data(reference_date: Optional[date] = None, db_path: Optional[str] = None) -> Dict[str, int]:
    """
    Seed realistic sample transactions and budgets for Indian college / young professional scenario.
    Spans 3 months: current month, previous month, and month before that.
    Flags rows with is_sample = 1 for clean removal later.
    """
    if reference_date is None:
        reference_date = date.today()

    cur_year = reference_date.year
    cur_month = reference_date.month

    # Calculate previous month and month-2
    prev_m = cur_month - 1 if cur_month > 1 else 12
    prev_y = cur_year if cur_month > 1 else cur_year - 1

    prev2_m = prev_m - 1 if prev_m > 1 else 12
    prev2_y = prev_y if prev_m > 1 else prev_y - 1

    sample_income = [
        # Current month
        ("Monthly Allowance", 18000.0, f"{cur_year:04d}-{cur_month:02d}-01", "Parental monthly college allowance", 1),
        ("Freelancing Web Design", 12500.0, f"{cur_year:04d}-{cur_month:02d}-10", "Frontend client project payout", 1),
        ("Merit Scholarship", 5000.0, f"{cur_year:04d}-{cur_month:02d}-15", "College semester academic merit reward", 1),
        # Previous month
        ("Monthly Allowance", 18000.0, f"{prev_y:04d}-{prev_m:02d}-01", "Parental monthly college allowance", 1),
        ("Freelancing Web Design", 15000.0, f"{prev_y:04d}-{prev_m:02d}-12", "Python web development freelance work", 1),
        # Two months ago
        ("Monthly Allowance", 18000.0, f"{prev2_y:04d}-{prev2_m:02d}-01", "Parental monthly college allowance", 1),
        ("Tutoring Junior Students", 6000.0, f"{prev2_y:04d}-{prev2_m:02d}-18", "Data Structures peer tutoring stipend", 1),
    ]

    sample_expenses = [
        # Current Month Expenses
        ("Campus Canteen Lunch", 180.0, "Food & Dining", f"{cur_year:04d}-{cur_month:02d}-02", "UPI / GPay / PhonePe", "Lunch with project team", 1),
        ("Metro Monthly Smartcard Recharge", 900.0, "Transportation", f"{cur_year:04d}-{cur_month:02d}-03", "Debit Card", "Daily college commute card topup", 1),
        ("Python Programming Book", 1150.0, "Education", f"{cur_year:04d}-{cur_month:02d}-04", "UPI / GPay / PhonePe", "Reference book for CSE semester 5", 1),
        ("Weekly Grocery & Snacks", 1450.0, "Food & Dining", f"{cur_year:04d}-{cur_month:02d}-05", "UPI / GPay / PhonePe", "Hostel room essentials and fruits", 1),
        ("Mobile Postpaid & Fiber Bill", 1299.0, "Bills & Utilities", f"{cur_year:04d}-{cur_month:02d}-06", "Net Banking", "Jio Fiber broadband & mobile recharge", 1),
        ("Semester Exam & Lab Fees", 3200.0, "Education", f"{cur_year:04d}-{cur_month:02d}-08", "Net Banking", "University term examination enrollment", 1),
        ("Weekend Movie & Popcorn", 650.0, "Entertainment", f"{cur_year:04d}-{cur_month:02d}-09", "UPI / GPay / PhonePe", "Watched new sci-fi movie at PVR", 1),
        ("Pharmacy & Multivitamins", 480.0, "Healthcare", f"{cur_year:04d}-{cur_month:02d}-11", "Cash", "Cough syrup and vitamin C supplements", 1),
        ("Denim Jeans & T-Shirt", 2499.0, "Shopping", f"{cur_year:04d}-{cur_month:02d}-13", "Credit Card", "Myntra festive season sale", 1),
        ("Haircut and Grooming Kit", 450.0, "Personal Care", f"{cur_year:04d}-{cur_month:02d}-14", "UPI / GPay / PhonePe", "Salon haircut and face wash", 1),
        ("Cafe Coffee Day Outing", 340.0, "Food & Dining", f"{cur_year:04d}-{cur_month:02d}-16", "UPI / GPay / PhonePe", "Group study session coffee", 1),
        ("Cab Ride to Railway Station", 420.0, "Transportation", f"{cur_year:04d}-{cur_month:02d}-18", "UPI / GPay / PhonePe", "Uber ride during rainy day", 1),
        ("Cloud Server Hosting", 780.0, "Bills & Utilities", f"{cur_year:04d}-{cur_month:02d}-20", "Credit Card", "AWS student server instance for project", 1),
        ("Weekend Road Trip Petrol", 1600.0, "Travel", f"{cur_year:04d}-{cur_month:02d}-22", "UPI / GPay / PhonePe", "Shared bike petrol expense to hill station", 1),
        ("Wireless Earbuds Replacement", 1999.0, "Shopping", f"{cur_year:04d}-{cur_month:02d}-24", "Debit Card", "Noise earbuds from Amazon sale", 1),
        ("Dinner with Roommates", 890.0, "Food & Dining", f"{cur_year:04d}-{cur_month:02d}-26", "UPI / GPay / PhonePe", "Celebrated mini project completion", 1),
        
        # Previous Month Expenses
        ("Campus Canteen & Snacks", 2800.0, "Food & Dining", f"{prev_y:04d}-{prev_m:02d}-03", "UPI / GPay / PhonePe", "Monthly mess & snacks expenses", 1),
        ("Metro Smartcard Recharge", 850.0, "Transportation", f"{prev_y:04d}-{prev_m:02d}-04", "Debit Card", "Metro travel", 1),
        ("Online Certification Course", 1899.0, "Education", f"{prev_y:04d}-{prev_m:02d}-08", "Credit Card", "Coursera Python specialization certificate", 1),
        ("Hostel Wi-Fi Contribution", 600.0, "Bills & Utilities", f"{prev_y:04d}-{prev_m:02d}-10", "Cash", "Monthly shared broadband", 1),
        ("Dentist Consultation & Cleaning", 1200.0, "Healthcare", f"{prev_y:04d}-{prev_m:02d}-14", "UPI / GPay / PhonePe", "Routine dental checkup", 1),
        ("Running Shoes", 2999.0, "Shopping", f"{prev_y:04d}-{prev_m:02d}-18", "Credit Card", "Puma running sneakers", 1),
        ("Gaming Subscription & Streaming", 799.0, "Entertainment", f"{prev_y:04d}-{prev_m:02d}-20", "Debit Card", "Netflix & Spotify premium student plan", 1),
        ("Weekend Train Ticket Home", 650.0, "Travel", f"{prev_y:04d}-{prev_m:02d}-24", "Net Banking", "IRCTC sleeper ticket to hometown", 1),
        ("Stationery & Project Printouts", 380.0, "Education", f"{prev_y:04d}-{prev_m:02d}-26", "Cash", "Spiral binding & record printouts", 1),
        ("Skin Care Products", 550.0, "Personal Care", f"{prev_y:04d}-{prev_m:02d}-28", "UPI / GPay / PhonePe", "Moisturizer & sunscreen", 1),

        # Two Months Ago Expenses
        ("Food & Daily Meals", 3400.0, "Food & Dining", f"{prev2_y:04d}-{prev2_m:02d}-04", "UPI / GPay / PhonePe", "Monthly meal total", 1),
        ("Transportation Expenses", 950.0, "Transportation", f"{prev2_y:04d}-{prev2_m:02d}-07", "Debit Card", "Bicycle repair & bus passes", 1),
        ("Textbooks & Lab Manuals", 1450.0, "Education", f"{prev2_y:04d}-{prev2_m:02d}-11", "Cash", "Academic notebooks and syllabus book", 1),
        ("Electricity & Maintenance", 800.0, "Bills & Utilities", f"{prev2_y:04d}-{prev2_m:02d}-15", "Net Banking", "Hostel room power share", 1),
        ("Festival Shopping & Gifts", 3500.0, "Shopping", f"{prev2_y:04d}-{prev2_m:02d}-20", "Credit Card", "Festival ethnic wear and gifts", 1),
        ("Concert & Fest Tickets", 1000.0, "Entertainment", f"{prev2_y:04d}-{prev2_m:02d}-25", "UPI / GPay / PhonePe", "College cultural annual fest pass", 1),
    ]

    sample_budgets = [
        # Current month budgets
        ("Overall", 25000.0, cur_month, cur_year, 1),
        ("Food & Dining", 6000.0, cur_month, cur_year, 1),
        ("Transportation", 2000.0, cur_month, cur_year, 1),
        ("Shopping", 4000.0, cur_month, cur_year, 1),
        ("Education", 5000.0, cur_month, cur_year, 1),
        ("Healthcare", 1500.0, cur_month, cur_year, 1),
        ("Entertainment", 2000.0, cur_month, cur_year, 1),
        ("Bills & Utilities", 2500.0, cur_month, cur_year, 1),
        ("Travel", 2500.0, cur_month, cur_year, 1),
        ("Personal Care", 1000.0, cur_month, cur_year, 1),

        # Previous month budgets
        ("Overall", 22000.0, prev_m, prev_y, 1),
        ("Food & Dining", 5500.0, prev_m, prev_y, 1),
        ("Transportation", 1800.0, prev_m, prev_y, 1),
        ("Education", 4000.0, prev_m, prev_y, 1),
        ("Shopping", 3500.0, prev_m, prev_y, 1),
    ]

    # Future target dates for sample savings goals
    target_1 = f"{cur_year + (1 if cur_month > 6 else 0):04d}-{(cur_month + 6 - 1) % 12 + 1:02d}-15"
    target_2 = f"{cur_year:04d}-{cur_month:02d}-28"
    target_3 = f"{cur_year + (1 if cur_month > 9 else 0):04d}-{(cur_month + 3 - 1) % 12 + 1:02d}-10"
    sample_savings_goals = [
        ("default_user", "Emergency Fund", 50000.0, 35000.0, target_1, "3-month reserve for hostel, medical, and emergency living expenses.", reference_date.isoformat(), "In Progress", 1),
        ("default_user", "New Laptop / Tech Gear", 65000.0, 65000.0, target_2, "MacBook / ThinkPad upgrade for coding and software development.", reference_date.isoformat(), "Completed", 1),
        ("default_user", "Goa Vacation Trip", 20000.0, 8500.0, target_3, "End of semester holiday trip with college friends.", reference_date.isoformat(), "In Progress", 1),
    ]

    conn = get_connection(db_path)
    inserted_counts = {"income": 0, "expenses": 0, "budgets": 0, "savings_goals": 0}

    try:
        with conn:
            cursor = conn.cursor()

            # Insert Income
            for item in sample_income:
                cursor.execute("""
                    INSERT INTO income (income_source, amount, date, description, is_sample)
                    VALUES (?, ?, ?, ?, ?)
                """, item)
                inserted_counts["income"] += 1

            # Insert Expenses
            for item in sample_expenses:
                cursor.execute("""
                    INSERT INTO expenses (expense_name, amount, category, date, payment_method, description, is_sample)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, item)
                inserted_counts["expenses"] += 1

            # Insert Budgets (using upsert)
            for item in sample_budgets:
                cursor.execute("""
                    INSERT INTO budgets (category, budget_amount, month, year, is_sample)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(category, month, year) DO UPDATE SET
                        budget_amount = excluded.budget_amount,
                        is_sample = excluded.is_sample
                """, item)
                inserted_counts["budgets"] += 1

            # Insert Savings Goals
            for item in sample_savings_goals:
                cursor.execute("""
                    INSERT INTO savings_goals (user_id, goal_name, target_amount, current_saved_amount, target_date, description, created_date, status, is_sample)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, item)
                inserted_counts["savings_goals"] += 1

        return inserted_counts
    finally:
        conn.close()


def clear_sample_data(db_path: Optional[str] = None) -> Dict[str, int]:
    """
    Remove all records flagged with is_sample = 1.
    Retains all user-entered records and schema intact.
    """
    conn = get_connection(db_path)
    counts = {"income": 0, "expenses": 0, "budgets": 0, "savings_goals": 0}
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE is_sample = 1")
            counts["expenses"] = cursor.rowcount
            cursor.execute("DELETE FROM income WHERE is_sample = 1")
            counts["income"] = cursor.rowcount
            cursor.execute("DELETE FROM budgets WHERE is_sample = 1")
            counts["budgets"] = cursor.rowcount
            cursor.execute("DELETE FROM savings_goals WHERE is_sample = 1")
            counts["savings_goals"] = cursor.rowcount
        return counts
    finally:
        conn.close()


def reset_all_data(db_path: Optional[str] = None) -> None:
    """Clear all data from all tables (expenses, income, budgets, savings_goals)."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses")
            cursor.execute("DELETE FROM income")
            cursor.execute("DELETE FROM budgets")
            cursor.execute("DELETE FROM savings_goals")
    finally:
        conn.close()


def has_data(db_path: Optional[str] = None) -> bool:
    """Return True if there are any expense or income records in the database."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT (SELECT COUNT(*) FROM expenses) + (SELECT COUNT(*) FROM income) AS total")
        row = cursor.fetchone()
        return bool(row and row["total"] > 0)
    finally:
        conn.close()


def has_sample_data(db_path: Optional[str] = None) -> bool:
    """Return True if any sample data exists in the database."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT (SELECT COUNT(*) FROM expenses WHERE is_sample = 1) + (SELECT COUNT(*) FROM income WHERE is_sample = 1) AS total")
        row = cursor.fetchone()
        return bool(row and row["total"] > 0)
    finally:
        conn.close()
