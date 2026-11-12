# 💰 Personal Expenses & Smart Budget Management System

A full-stack, production-ready personal finance and budget management web application engineered primarily in **Python**, built as a **BTech CSE Python Programming Mini Project**.

Designed with a modern SaaS aesthetic (navy/blue & white theme), the system allows users to record daily expenses, track multiple income streams, monitor monthly budgets with automated tiered threshold alerts, uncover rule-based spending heuristics, and export audit-ready CSV and PDF reports.

---

## 🌟 Highlights & Key Features

### 1. 📊 User Dashboard
- **Executive Summary Cards**: Real-time KPI metrics for Total Income, Total Expenses, Remaining Balance (with deficit handling), Monthly Budget, and Budget Utilization %.
- **Active Budget Alerts**: Automated banners triggered when overall or category budgets enter Caution (75%), Warning (90%), or Exceeded (≥100%) states.
- **Visual Budget Progress**: Dynamic progress bar indicating exact utilization and remaining allowance.
- **Month-over-Month (MoM) Overview**: Delta change indicators comparing current month against the preceding month.
- **Category-wise Spending Breakdown**: Mini progress bars and percentages for all active categories.
- **Recent Transactions Ledger**: Instant feed of recent inflows and outflows with category icons and color-coded amount badges.

### 2. 💸 Add & Manage Expenses
- Input fields: Expense Name, Amount (INR ₹), Category, Transaction Date, Payment Method, and Notes.
- Strict defensive validation: Rejects negative or zero amounts, non-numeric values, missing fields, or invalid dates.
- Complete CRUD operations: Add new expenses, edit past entries, and safely delete with confirmation.

### 3. 🏷️ Standardized Expense Categorization
- 10 Predefined Categories:
  - 🍔 Food & Dining
  - 🚗 Transportation
  - 🛍️ Shopping
  - 🎓 Education
  - 🏥 Healthcare
  - 🎬 Entertainment
  - 💡 Bills & Utilities
  - ✈️ Travel
  - 💅 Personal Care
  - 📦 Others
- Distinct color palette and Unicode emojis mapped uniformly across tables, cards, and charts.

### 4. 💰 Income Tracking
- Track multiple income sources: Allowance, Salary, Freelancing, Scholarship, and Other Income.
- Record, edit, and delete income entries.
- Real-time net balance calculation: `Remaining Balance = Total Income - Total Expenses`.

### 5. 🗓️ Monthly Expense Tracking
- Multi-month historical data navigation via active period selector.
- Automatic aggregation of monthly income and expenditure.
- Month-over-month (MoM) delta analysis with directional indicators (🔺 Increased, 🔻 Decreased, ➖ Unchanged).

### 6. 🎯 Budget Setting & Management
- Establish an **Overall Monthly Spending Cap** as well as **Individual Category-wise Budgets**.
- Real-time variance tracking: Allocated Budget, Amount Spent, Remaining Budget, and Utilization %.
- Persistent SQLite storage: Retains budget parameters across application restarts.

### 7. 🔔 Tiered Budget Alerts & Notifications
- Automated four-tier monitoring state machine:
  - **< 75%**: 🟢 *Normal Status* &mdash; Spending within healthy limits.
  - **75% – 89.9%**: 🟡 *Budget Caution* &mdash; High utilization approaching warning threshold.
  - **90% – 99.9%**: 🟠 *High Spending Warning* &mdash; Nearing critical budget cap.
  - **≥ 100%**: 🔴 *Budget Exceeded* &mdash; Overspending alert with exact deficit amount.
- Alerts trigger independently for overall and category-level budgets.

### 8. 📈 Interactive Analytics & Visualizations (Plotly)
1. **Donut Chart**: Category-wise expense distribution with hover tooltips in INR.
2. **Bar Chart**: Monthly expense trends across the calendar year.
3. **Dual-Axis Line & Bar Chart**: Daily spending timeline with cumulative expense progression.
4. **Grouped Bar Chart**: Income vs. Expenses comparison across all months.
5. **Horizontal Bar Chart**: Budget vs. Actual spending comparison across categories.

### 9. 📐 Statistical Spending Averages
- Average Daily Expenditure (accounting for calendar month days and elapsed days).
- Average Monthly Expenditure across all recorded historical months.
- Average Expenditure per Transaction.
- Category-wise Average Spending per transaction.
- Comprehensive zero-division safeguards across all calculations.

### 10. 🧠 Smart Spending Insights (Rule-Based Heuristics)
- Identifies the highest spending category and its share of total expenses.
- Flags concentration risks when any single category consumes >35% of monthly outflow.
- Detects significant month-over-month cost jumps (>20% increase).
- Evaluates budget pacing against the calendar.
- Generates actionable, category-specific recommendations to curb impulse buys and save money.

### 11. 🪙 Savings Tracker & Net Cash Flow
- Real-time savings formula calculation: `Savings = Total Income - Total Expenses`.
- Interactive Plotly gauge meter displaying user's savings rate percentage against the 20% healthy savings benchmark.
- Explicit deficit alerts when expenses surpass income.

### 12. 📜 Unified Transactions & Multi-Format Reports
- Search transactions by name, description, or payment method.
- Filter by date range, transaction type (All, Expense, Income), and category/source.
- Sort chronologically or by transaction value.
- **CSV Export**: Instant download of filtered or monthly transaction ledgers.
- **PDF Report Generation**: Professional, publication-ready PDF documents generated via **ReportLab**, featuring executive financial summary tables, category breakdowns, and transaction history.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Language** | Python 3.12+ | Core programming and business logic |
| **Web API Backend** | FastAPI & Uvicorn | High-performance asynchronous REST API server |
| **Modern Frontend** | React 18, TypeScript & Vite | PennyPilot responsive SaaS interface |
| **Streamlit UI** | Streamlit | Classic Python-native interactive dashboard |
| **Database** | SQLite3 | Local relational storage with foreign keys and constraints |
| **Data Processing** | Pandas & NumPy | Reshaping, aggregations, and grouped calculations |
| **Data Visualization** | Plotly & Recharts | Dynamic, responsive HTML5 & SVG charts |
| **PDF Generation** | ReportLab 5.x & jsPDF | Publication-grade server & client PDF generation |
| **Image Processing** | Pillow (PIL) | Dynamic asset generation |

---

## 📂 Project Architecture

```
Python/
│
├── run_web.py                  # Main entrypoint: Launches FastAPI + PennyPilot Web UI
├── run.py                      # Dual runner: starts web UI (--web) or Streamlit
├── app.py                      # Streamlit application entrypoint
├── start.bat                   # One-click Windows runner
├── push_to_github.bat          # One-click Git push script
├── requirements.txt            # Python dependencies manifest
├── pytest.ini                  # Pytest configuration
├── README.md                   # Full documentation & viva guide
│
├── personal_expense_manager/   # Core Python Backend & Analytics Engine
│   ├── api.py                  # FastAPI REST API & static web serving
│   ├── database.py             # SQLite WAL-mode connection, schemas & CRUD
│   ├── expense_manager.py      # Expense validation, categorization & math
│   ├── income_manager.py       # Income validation, source tracking & cashflow
│   ├── budget_manager.py       # Budget limits, 4-tier alert engine
│   ├── analytics.py            # Statistical averages & 5 Plotly visualizations
│   ├── insights.py             # Rule-based spending heuristics & recommendations
│   ├── reports.py              # CSV serialization & ReportLab PDF generator
│   ├── data/
│   │   └── expenses.db         # Persistent SQLite database
│   └── assets/
│       └── logo.png            # Application branding logo
│
├── frontend/                   # Modern PennyPilot React 18 Frontend
│   ├── src/                    # TypeScript + React components, pages & state
│   ├── public/                 # Static branding assets & favicon
│   ├── dist/                   # Production compiled web assets (served by FastAPI)
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.ts          # Vite build configuration
│   └── tsconfig.json           # TypeScript configuration
│
└── tests/                      # Automated Test Suite (45 Passing Tests)
    ├── test_api.py             # FastAPI REST endpoints & report download tests
    ├── test_section_display_and_filtering.py # Dedicated section display tests
    ├── test_system.py          # Core system & CRUD test suite
    ├── test_edge_cases.py      # Edge cases (leap years, boundaries, SQL injection)
    └── test_fixes_and_robustness.py # PDF XML escaping & insight robustness
```

---

## 🎓 Core Python Programming Concepts Demonstrated

This project is tailored for academic evaluation, showcasing:
1. **Variables & Data Types**: Floats, integers, strings, booleans, datetime objects.
2. **Data Structures**: Lists, tuples, dictionaries, sets, and Pandas DataFrames.
3. **Control Flow**: Conditional branching (`if/elif/else`), list comprehensions, and iteration (`for/while`).
4. **Functions & Modular Programming**: Single-responsibility architecture across 8 specialized modules.
5. **Defensive Programming & Validation**: Boundary checks, type validation, sanitized inputs.
6. **Exception Handling**: Robust `try/except/finally` blocks preventing unexpected application crashes.
7. **Database Operations (SQL)**: Parameterized queries (`?`), transactions with context managers (`with conn:`), index optimization, and `ON CONFLICT` upserts.
8. **File & Stream I/O**: In-memory byte and string buffers (`io.StringIO`, `io.BytesIO`), dynamic CSV writing, binary PDF rendering.
9. **Mathematical & Statistical Computations**: Averages, percentage shares, variance analysis, zero-division error handling.

---

## 🚀 Installation & Windows Execution Guide

### Prerequisites
- Python 3.10, 3.11, or 3.12 installed on Windows.
- Ensure Python and `pip` are added to your system `PATH`.

### Step 1: Clone or Navigate to the Repository
```powershell
cd "c:\Users\<YourUser>\OneDrive\Desktop\Python"
```

### Step 2: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Application
You can run the application directly using any of the following options:

**Option 1: Modern PennyPilot Web Application (FastAPI + React 18)**
```powershell
python run_web.py
```
or
```powershell
python run.py --web
```
- Web Application: **http://127.0.0.1:8000**
- REST API Documentation: **http://127.0.0.1:8000/docs**

**Option 2: Streamlit Interactive Dashboard**
```powershell
python run.py
```
or
```powershell
streamlit run app.py
```
- Streamlit Application: **http://localhost:8501**

---

## 🧪 Running the Automated Test Suite

To verify all system components, validations, calculations, and PDF generation:
```powershell
python -m pytest tests/test_system.py -v
```

---

## 💡 Quick Start Guide for College Project Demonstration

1. **Launch the Application**: Run `streamlit run app.py`.
2. **Load Demo Sample Data**: Click the **"🚀 Load Demo Sample Data"** button in the sidebar. This immediately seeds 35+ realistic Indian Rupee transactions (College allowances, freelancing, canteen meals, books, bills, and budgets) across multiple months.
3. **Explore Dashboard**: View summary KPI cards, active budget alerts, category breakdowns, and recent transactions.
4. **Test Adding an Expense**: Navigate to **"💸 Add Expense"**, fill in the form, and observe instant validation and updates.
5. **Inspect Budget Manager**: Navigate to **"🎯 Budget Manager"** to see color-coded budget status tiers (Normal, Caution, Warning, Exceeded) and test setting custom category caps.
6. **View Visual Analytics**: Open **"📈 Analytics & Reports"** to interact with the 5 Plotly charts, statistical averages, and automated rule-based smart insights.
7. **Download Reports**: Under **"📜 Transactions"**, click **"📄 Download Monthly Report as PDF"** to generate a clean, print-ready PDF summary.
8. **Clean Demo Data**: Click **"🧹 Clear Demo Sample Data"** in the sidebar to remove test records while preserving user data and database schema.

---

## 📜 License
Developed as an academic demonstration project under the MIT License.
