"""
Launcher Script for Personal Expenses & Smart Budget Management System
----------------------------------------------------------------------
Allows starting either interface:
    python run.py             # Streamlit application (default)
    python run.py --web       # PennyPilot Modern Web application
    python run_web.py         # Direct launcher for PennyPilot Web
"""

import sys
import subprocess
import os

if __name__ == "__main__":
    if "--web" in sys.argv:
        import uvicorn
        root_dir = os.path.dirname(os.path.abspath(__file__))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        pem_dir = os.path.join(root_dir, "personal_expense_manager")
        if pem_dir not in sys.path:
            sys.path.insert(0, pem_dir)
        print("=" * 60)
        print("Launching PennyPilot Web Application on http://127.0.0.1:8000")
        print("=" * 60)
        uvicorn.run("personal_expense_manager.api:app", host="127.0.0.1", port=8000, log_level="info")
    else:
        app_target = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "personal_expense_manager",
            "app.py"
        )
        cmd = [sys.executable, "-m", "streamlit", "run", app_target]
        print(f"Launching Personal Expenses System: {' '.join(cmd)}")
        print("Tip: To launch the modern PennyPilot web interface, run: python run_web.py or python run.py --web")
        subprocess.run(cmd)
