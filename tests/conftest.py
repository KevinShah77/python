import os
import sys

# Ensure personal_expense_manager is always the top priority on sys.path for all tests
MODULE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "personal_expense_manager")
if MODULE_DIR in sys.path:
    sys.path.remove(MODULE_DIR)
sys.path.insert(0, MODULE_DIR)
