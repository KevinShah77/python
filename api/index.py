"""
Vercel Serverless Function Entrypoint for FastAPI
--------------------------------------------------
Exposes the SpendWise (PennyPilot) FastAPI ASGI app
for Vercel Serverless execution.
"""

import os
import sys

# Ensure root and module directories are in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

MODULE_DIR = os.path.join(ROOT_DIR, "personal_expense_manager")
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

# Import the FastAPI application
from personal_expense_manager.api import app
