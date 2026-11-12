# TODO & Integration Status

> Source system: https://github.com/KevinShah77/python
> Backend status: Connected to live Python FastAPI REST API and SQLite database (`expenses.db`). Supports full CRUD operations, live state sync, sample data loading/clearing, and offline fallback.

## 1. Responsive personal-finance application shell
- [x] Provide clear navigation across Dashboard, Expenses, Income, Transactions, Budgets, Analytics, and Reports.
- [x] Optimize the application for desktop and mobile use.
- [x] Present the product as a personal expense and smart budget manager, with INR used throughout.

## 2. Dashboard overview and budget states
- [x] Show total income, total expenses, remaining balance, monthly budget, and budget utilization.
- [x] Show month-over-month comparison, category spending breakdown, and a recent transaction feed.
- [x] Show budget threshold alerts at 75%, 90%, and 100% utilization, including deficit and over-budget states.

## 3. Expense management
- [x] Support create, view, edit, and delete flows for expense name, INR amount, category, date, payment method, and optional notes.
- [x] Preserve the backend’s ten predefined expense categories: Food & Dining, Transportation, Shopping, Education, Healthcare, Entertainment, Bills & Utilities, Travel, Personal Care, and Others.
- [x] Preserve the backend’s payment methods: UPI / GPay / PhonePe, Cash, Debit Card, Credit Card, Net Banking, and Other.
- [x] Preserve expense validation: a non-empty name no longer than 100 characters; a numeric amount strictly greater than ₹0 and no more than ₹1,00,00,000; a predefined category; and a valid date.
- [x] Connect expenses CRUD directly to the SQLite backend via REST API (`POST /api/expenses`, `PUT /api/expenses/{id}`, `DELETE /api/expenses/{id}`).

## 4. Income tracking
- [x] Support income entries categorized as Allowance, Salary, Freelancing, Scholarship, or Other Income.
- [x] Support viewing, editing, and deleting income entries, and display income as positive cash flow.
- [x] Connect income CRUD directly to the SQLite backend via REST API (`POST /api/income`, `PUT /api/income/{id}`, `DELETE /api/income/{id}`).

## 5. Unified transaction ledger
- [x] Provide a unified transactions view with search, filters, sorting, and clear expense/income distinctions.
- [x] Search transaction name, description, or payment method; filter by date range, type, and category/source; sort chronologically or by transaction value.
- [x] Use readable responsive tables or mobile cards.

## 6. Budget management
- [x] Support both overall monthly limits and category-specific budgets.
- [x] Show allocated budget, actual spending, utilization, status, progress indicators, and remaining amounts.
- [x] Preserve tier states: below 75% normal, 75%–89.9% caution, 90%–99.9% warning, and 100% or more exceeded.
- [x] Connect budget limits to SQLite persistence via REST API (`POST /api/budgets`, `DELETE /api/budgets/{id}`).

## 7. Analytics and smart insights
- [x] Provide interactive visualizations for monthly expense trends, daily spending, income versus expenses, category comparisons, and budget versus actual spending.
- [x] Show spending averages, savings rate, deficit states, and rule-based financial insights.

## 8. Reports and downloads
- [x] Provide CSV and PDF report-generation controls with reporting-period selection and clear download states.
- [x] Provide report output for the selected month, with financial summary, category breakdown, and transaction details.
- [x] Support both client-side report rendering (jsPDF) and server-side ReportLab generation (`GET /api/reports/pdf`, `GET /api/reports/csv`).

## 9. Form, feedback, and backend connection
- [x] Live backend connection indicator in sidebar showing SQLite connection state (`expenses.db`).
- [x] One-click "Load demo" and "Clear demo" controls for evaluator testing.
- [x] Graceful fallback to browser local storage if backend server is unreachable.
