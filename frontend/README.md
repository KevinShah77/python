# PennyPilot — Personal Finance

A responsive, backend-connected personal expense and budget management web application powered by **FastAPI**, **SQLite**, and **React 18 (TypeScript)**.

## Quick Start

### 1. Launch PennyPilot Full-Stack Web Application (FastAPI + React)

From the root project repository:

```bash
python run_web.py
```

Or:

```bash
python run.py --web
```

The application will be available at:
- **Web Application**: http://127.0.0.1:8000
- **Swagger REST API Docs**: http://127.0.0.1:8000/docs
- **SQLite Database**: `personal_expense_manager/data/expenses.db`

### 2. Frontend Development Server (Optional)

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` requests directly to `http://127.0.0.1:8000`.

### 3. Production Build

```bash
cd frontend
npm run build
```

## Features

- **Live SQLite Backend**: Connects directly to `expenses.db` with full CRUD for expenses, income, and tiered monthly budgets.
- **Monthly Dashboard**: Income, expenses, balance, budget utilization gauge, tiered threshold alerts (75%, 90%, 100%), category distribution, and recent activity feed.
- **Complete CRUD Flows**: Input validation, search, filter by category/date, sort chronologically or by amount.
- **Budget Guardrails**: Overall spending cap and category-specific budgets with progress bars and alerts.
- **Analytics & Visualizations**: Category breakdowns, 6-month cash flow trends, budget vs. actual comparisons.
- **Multi-Format Reports**: Instant CSV export and PDF downloads (both client-side jsPDF and server-side ReportLab supported).
- **Demo Data Controls**: Instant "Load demo" and "Clear demo" buttons to populate realistic student/young professional finances for testing.
