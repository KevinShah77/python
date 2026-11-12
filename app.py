"""
Root Entrypoint for Personal Expenses & Smart Budget Management System
----------------------------------------------------------------------
Allows starting the Streamlit application from the repository root:
    streamlit run app.py
or
    streamlit run personal_expense_manager/app.py
"""

import os
import sys
import runpy

MODULE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "personal_expense_manager")
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

TARGET_APP_PATH = os.path.join(MODULE_DIR, "app.py")

if __name__ == "__main__":
    runpy.run_path(TARGET_APP_PATH, run_name="__main__")
