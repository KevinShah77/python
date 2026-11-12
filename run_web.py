"""
PennyPilot Web Application Launcher
-----------------------------------
Starts the FastAPI web server hosting the modern PennyPilot frontend
connected to the SQLite database.

Usage:
    python run_web.py
"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)
    MODULE_DIR = os.path.join(ROOT_DIR, "personal_expense_manager")
    if MODULE_DIR not in sys.path:
        sys.path.insert(0, MODULE_DIR)

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    print("=" * 60)
    print("   PennyPilot Personal Finance & Budget Management System   ")
    print("=" * 60)
    print(f" -> Modern Web App:   http://{host}:{port}")
    print(f" -> Swagger REST API: http://{host}:{port}/docs")
    print(f" -> SQLite Database:  personal_expense_manager/data/expenses.db")
    print("=" * 60)
    print("Press Ctrl+C to stop the server.\n")

    uvicorn.run("personal_expense_manager.api:app", host=host, port=port, log_level="info")
