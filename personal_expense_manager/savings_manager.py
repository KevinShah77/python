"""
Savings Goals Management Module for SpendWise / PennyPilot
----------------------------------------------------------
Academic & Engineering Concepts:
- Persistent SQLite storage with SQLAlchemy 2.x ORM
- User data isolation and privacy protection
- Strict input validation and edge case prevention
- Automated status evaluation: 'In Progress', 'Completed', 'Overdue'
- Mathematical calculations for progress percentage and remaining targets
"""

import os
import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    create_engine,
    select,
    update,
    delete
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Default database path from database module
DEFAULT_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "expenses.db")

Base = declarative_base()


class SavingsGoal(Base):
    """
    SQLAlchemy ORM Model for Savings Goals.
    Stores financial savings targets persistently in SQLite.
    """
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, default="default_user", index=True)
    goal_name = Column(String(150), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_saved_amount = Column(Float, nullable=False, default=0.0)
    target_date = Column(String(20), nullable=False)
    description = Column(Text, nullable=True, default="")
    created_date = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default="In Progress")
    is_sample = Column(Integer, default=0)


from sqlalchemy.pool import NullPool

# Engine cache keyed by normalized database file path
_engines: Dict[str, Engine] = {}


def get_engine(db_path: Optional[str] = None) -> Engine:
    """Return cached or new SQLAlchemy Engine for the target SQLite database path."""
    path = os.path.abspath(db_path or DEFAULT_DB_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    normalized = path.replace("\\", "/")
    url = f"sqlite:///{normalized}"
    if url not in _engines:
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=NullPool
        )
        _engines[url] = engine
    return _engines[url]


def get_db_session(db_path: Optional[str] = None) -> Session:
    """Return a new SQLAlchemy Session bound to the target database."""
    engine = get_engine(db_path)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_factory()


def init_savings_db(db_path: Optional[str] = None) -> None:
    """Initialize the savings_goals table in SQLite using SQLAlchemy metadata."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)


def validate_goal_inputs(
    goal_name: str,
    target_amount: float,
    target_date: str,
    current_saved_amount: float = 0.0
) -> Tuple[bool, str]:
    """
    Validate savings goal input fields.
    Returns (True, '') if valid, or (False, error_message) if invalid.
    """
    if not goal_name or not goal_name.strip():
        return False, "Goal name is required and cannot be empty."

    if len(goal_name.strip()) > 100:
        return False, "Goal name must not exceed 100 characters."

    try:
        t_amt = float(target_amount)
    except (ValueError, TypeError):
        return False, "Target amount must be a valid number."

    if t_amt <= 0:
        return False, "Target amount must be greater than ₹0."

    if t_amt > 100_000_000:
        return False, "Target amount cannot exceed ₹10,00,00,000 (10 Crores)."

    try:
        s_amt = float(current_saved_amount)
    except (ValueError, TypeError):
        return False, "Current saved amount must be a valid number."

    if s_amt < 0:
        return False, "Saved amount cannot be negative."

    if s_amt > 100_000_000:
        return False, "Saved amount cannot exceed ₹10,00,00,000 (10 Crores)."

    if not target_date or not isinstance(target_date, str):
        return False, "Target date is required in format YYYY-MM-DD."

    clean_date = target_date.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", clean_date):
        return False, "Target date must follow format YYYY-MM-DD (e.g. 2026-12-31)."

    try:
        parsed_date = datetime.strptime(clean_date, "%Y-%m-%d").date()
        if parsed_date.year < 2000 or parsed_date.year > 2100:
            return False, "Target date year must be between 2000 and 2100."
    except ValueError:
        return False, f"Invalid calendar date: '{target_date}'."

    return True, ""


def compute_goal_status(
    target_amount: float,
    current_saved_amount: float,
    target_date_str: str,
    reference_date: Optional[date] = None
) -> str:
    """
    Evaluate the status of a savings goal:
    - 'Completed': current_saved_amount >= target_amount
    - 'Overdue': current_saved_amount < target_amount and target_date < today
    - 'In Progress': current_saved_amount < target_amount and target_date >= today
    """
    if current_saved_amount >= target_amount:
        return "Completed"

    today_val = reference_date or date.today()
    try:
        target_dt = datetime.strptime(target_date_str.strip()[:10], "%Y-%m-%d").date()
        if target_dt < today_val:
            return "Overdue"
    except Exception:
        pass

    return "In Progress"


def compute_progress_and_remaining(
    target_amount: float,
    current_saved_amount: float
) -> Tuple[float, float]:
    """
    Calculate remaining amount and progress percentage.
    Returns (remaining_amount, progress_percentage).
    """
    remaining = max(0.0, round(float(target_amount) - float(current_saved_amount), 2))
    if target_amount > 0:
        progress = round((float(current_saved_amount) / float(target_amount)) * 100.0, 1)
    else:
        progress = 0.0
    return remaining, progress


def goal_to_dict(goal: SavingsGoal, reference_date: Optional[date] = None) -> Dict[str, Any]:
    """Serialize a SavingsGoal SQLAlchemy model into a clean JSON-serializable dictionary."""
    computed_status = compute_goal_status(
        goal.target_amount,
        goal.current_saved_amount,
        goal.target_date,
        reference_date=reference_date
    )
    remaining, progress = compute_progress_and_remaining(
        goal.target_amount,
        goal.current_saved_amount
    )
    return {
        "id": goal.id,
        "user_id": goal.user_id,
        "goal_name": goal.goal_name,
        "target_amount": float(goal.target_amount),
        "current_saved_amount": float(goal.current_saved_amount),
        "remaining_amount": remaining,
        "progress_percentage": progress,
        "target_date": goal.target_date,
        "description": goal.description or "",
        "created_date": goal.created_date,
        "status": computed_status,
        "is_sample": int(goal.is_sample or 0),
    }


def create_savings_goal(
    goal_name: str,
    target_amount: float,
    target_date: str,
    description: str = "",
    current_saved_amount: float = 0.0,
    user_id: str = "default_user",
    is_sample: int = 0,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Insert a new savings goal record into SQLite using SQLAlchemy."""
    init_savings_db(db_path)
    session = get_db_session(db_path)
    try:
        today_iso = date.today().isoformat()
        initial_status = compute_goal_status(
            float(target_amount),
            float(current_saved_amount),
            target_date
        )
        new_goal = SavingsGoal(
            user_id=(user_id or "default_user").strip(),
            goal_name=goal_name.strip(),
            target_amount=float(target_amount),
            current_saved_amount=float(current_saved_amount),
            target_date=target_date.strip(),
            description=(description or "").strip(),
            created_date=today_iso,
            status=initial_status,
            is_sample=int(is_sample)
        )
        session.add(new_goal)
        session.commit()
        session.refresh(new_goal)
        return goal_to_dict(new_goal)
    finally:
        session.close()


def get_all_savings_goals(
    user_id: Optional[str] = "default_user",
    status_filter: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve savings goals for a user, maintaining privacy.
    Ensures status is dynamically calculated relative to today.
    """
    init_savings_db(db_path)
    session = get_db_session(db_path)
    try:
        stmt = select(SavingsGoal)
        if user_id:
            stmt = stmt.where(SavingsGoal.user_id == user_id.strip())
        stmt = stmt.order_by(SavingsGoal.target_date.asc(), SavingsGoal.id.desc())
        results = session.execute(stmt).scalars().all()

        output = []
        for goal in results:
            d = goal_to_dict(goal)
            # Sync persisted status if it changed due to target_date passing
            if goal.status != d["status"]:
                goal.status = d["status"]
                session.add(goal)
            if status_filter:
                if d["status"].lower() == status_filter.strip().lower():
                    output.append(d)
            else:
                output.append(d)
        session.commit()
        return output
    finally:
        session.close()


def get_savings_goal_by_id(
    goal_id: int,
    user_id: Optional[str] = "default_user",
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Retrieve a single savings goal by ID, enforcing user privacy."""
    init_savings_db(db_path)
    session = get_db_session(db_path)
    try:
        stmt = select(SavingsGoal).where(SavingsGoal.id == int(goal_id))
        goal = session.execute(stmt).scalar_one_or_none()
        if not goal:
            return None
        # Enforce user privacy
        if user_id and goal.user_id != user_id.strip():
            return None
        return goal_to_dict(goal)
    finally:
        session.close()


def update_savings_goal(
    goal_id: int,
    goal_name: Optional[str] = None,
    target_amount: Optional[float] = None,
    target_date: Optional[str] = None,
    description: Optional[str] = None,
    current_saved_amount: Optional[float] = None,
    user_id: Optional[str] = "default_user",
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update an existing savings goal record, enforcing user privacy."""
    init_savings_db(db_path)
    session = get_db_session(db_path)
    try:
        stmt = select(SavingsGoal).where(SavingsGoal.id == int(goal_id))
        goal = session.execute(stmt).scalar_one_or_none()
        if not goal:
            return None
        if user_id and goal.user_id != user_id.strip():
            return None

        if goal_name is not None:
            goal.goal_name = goal_name.strip()
        if target_amount is not None:
            goal.target_amount = float(target_amount)
        if target_date is not None:
            goal.target_date = target_date.strip()
        if description is not None:
            goal.description = description.strip()
        if current_saved_amount is not None:
            goal.current_saved_amount = float(current_saved_amount)

        goal.status = compute_goal_status(
            goal.target_amount,
            goal.current_saved_amount,
            goal.target_date
        )
        session.add(goal)
        session.commit()
        session.refresh(goal)
        return goal_to_dict(goal)
    finally:
        session.close()


def delete_savings_goal(
    goal_id: int,
    user_id: Optional[str] = "default_user",
    db_path: Optional[str] = None
) -> bool:
    """Delete a savings goal by ID, enforcing user privacy."""
    init_savings_db(db_path)
    session = get_db_session(db_path)
    try:
        stmt = select(SavingsGoal).where(SavingsGoal.id == int(goal_id))
        goal = session.execute(stmt).scalar_one_or_none()
        if not goal:
            return False
        if user_id and goal.user_id != user_id.strip():
            return False
        session.delete(goal)
        session.commit()
        return True
    finally:
        session.close()


def add_money_to_savings_goal(
    goal_id: int,
    amount: float,
    user_id: Optional[str] = "default_user",
    db_path: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    Add money to an existing savings goal.
    Returns (updated_goal_dict, just_completed).
    - Prevents negative contributions.
    - Recalculates remaining amount and progress.
    - Identifies if this transaction completed the goal.
    """
    if float(amount) <= 0:
        raise ValueError("Contribution amount must be strictly greater than ₹0.")

    init_savings_db(db_path)
    session = get_db_session(db_path)
    try:
        stmt = select(SavingsGoal).where(SavingsGoal.id == int(goal_id))
        goal = session.execute(stmt).scalar_one_or_none()
        if not goal:
            return None, False
        if user_id and goal.user_id != user_id.strip():
            return None, False

        was_completed = goal.current_saved_amount >= goal.target_amount
        goal.current_saved_amount = round(float(goal.current_saved_amount) + float(amount), 2)
        goal.status = compute_goal_status(
            goal.target_amount,
            goal.current_saved_amount,
            goal.target_date
        )

        now_completed = goal.current_saved_amount >= goal.target_amount
        just_completed = (not was_completed) and now_completed

        session.add(goal)
        session.commit()
        session.refresh(goal)
        return goal_to_dict(goal), just_completed
    finally:
        session.close()


def get_savings_summary(
    user_id: Optional[str] = "default_user",
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate summary statistics across all savings goals for a user:
    - Total number of savings goals
    - Total amount targeted
    - Total amount saved
    - Overall savings progress percentage
    - Breakdown by status (Completed, In Progress, Overdue)
    """
    goals = get_all_savings_goals(user_id=user_id, db_path=db_path)
    total_goals = len(goals)
    total_target = round(sum(g["target_amount"] for g in goals), 2)
    total_saved = round(sum(g["current_saved_amount"] for g in goals), 2)
    overall_progress = (
        round((total_saved / total_target) * 100.0, 1) if total_target > 0 else 0.0
    )
    completed_count = sum(1 for g in goals if g["status"] == "Completed")
    in_progress_count = sum(1 for g in goals if g["status"] == "In Progress")
    overdue_count = sum(1 for g in goals if g["status"] == "Overdue")

    return {
        "total_goals": total_goals,
        "total_target_amount": total_target,
        "total_saved_amount": total_saved,
        "overall_progress_percentage": overall_progress,
        "completed_count": completed_count,
        "in_progress_count": in_progress_count,
        "overdue_count": overdue_count,
    }


def seed_sample_savings_goals(
    user_id: str = "default_user",
    db_path: Optional[str] = None,
    reference_date: Optional[date] = None
) -> int:
    """
    Seed realistic sample savings goals for demonstration.
    Flags rows with is_sample = 1 for clean removal later.
    """
    ref = reference_date or date.today()
    cur_year = ref.year
    cur_month = ref.month

    # Future dates
    target_1 = f"{cur_year + (1 if cur_month > 6 else 0):04d}-{(cur_month + 6 - 1) % 12 + 1:02d}-15"
    target_2 = f"{cur_year:04d}-{cur_month:02d}-28"
    target_3 = f"{cur_year + (1 if cur_month > 9 else 0):04d}-{(cur_month + 3 - 1) % 12 + 1:02d}-10"

    samples = [
        (
            "Emergency Fund",
            50000.0,
            35000.0,
            target_1,
            "3-month reserve for hostel, medical, and emergency living expenses.",
            1
        ),
        (
            "New Laptop / Tech Gear",
            65000.0,
            65000.0,
            target_2,
            "MacBook / ThinkPad upgrade for coding and software development.",
            1
        ),
        (
            "Goa Vacation Trip",
            20000.0,
            8500.0,
            target_3,
            "End of semester holiday trip with college friends.",
            1
        ),
    ]

    init_savings_db(db_path)
    session = get_db_session(db_path)
    inserted = 0
    try:
        for name, target, saved, t_date, desc, is_samp in samples:
            goal = SavingsGoal(
                user_id=user_id,
                goal_name=name,
                target_amount=target,
                current_saved_amount=saved,
                target_date=t_date,
                description=desc,
                created_date=ref.isoformat(),
                status=compute_goal_status(target, saved, t_date, reference_date=ref),
                is_sample=is_samp
            )
            session.add(goal)
            inserted += 1
        session.commit()
        return inserted
    finally:
        session.close()


def clear_sample_savings_goals(db_path: Optional[str] = None) -> int:
    """Remove all sample savings goals (is_sample = 1), preserving user-entered goals."""
    init_savings_db(db_path)
    session = get_db_session(db_path)
    try:
        stmt = delete(SavingsGoal).where(SavingsGoal.is_sample == 1)
        res = session.execute(stmt)
        session.commit()
        return res.rowcount or 0
    finally:
        session.close()


def reset_all_savings_goals(db_path: Optional[str] = None) -> None:
    """Wipe all savings goals from SQLite."""
    init_savings_db(db_path)
    session = get_db_session(db_path)
    try:
        session.execute(delete(SavingsGoal))
        session.commit()
    finally:
        session.close()
