"""
PennyPilot Server Runner
------------------------
Allows running the PennyPilot backend and web server directly:
    python -m personal_expense_manager.server
"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(MODULE_DIR)
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)
    if MODULE_DIR not in sys.path:
        sys.path.insert(0, MODULE_DIR)

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"Starting PennyPilot Web Server on http://{host}:{port}")
    uvicorn.run("personal_expense_manager.api:app", host=host, port=port, log_level="info")
