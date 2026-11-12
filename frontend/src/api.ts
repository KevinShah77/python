import type { AppData, Budget, Category, Expense, Income, IncomeSource, PaymentMethod, SavingsGoal, SavingsSummary } from './types';

const API_BASE = '/api';

export interface ApiStatus {
  status: string;
  app: string;
  version: string;
  db_connected: boolean;
  has_data: boolean;
  has_sample_data: boolean;
  counts: {
    expenses: number;
    income: number;
    budgets: number;
  };
}

/** Check if the Python FastAPI / SQLite backend is reachable */
export async function checkBackendStatus(): Promise<ApiStatus | null> {
  try {
    const res = await fetch(`${API_BASE}/status`, {
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) return null;
    return (await res.json()) as ApiStatus;
  } catch {
    return null;
  }
}

/** Fetch all expenses, income, and budgets from the SQLite backend */
export async function fetchAppData(autoSeed = false): Promise<AppData> {
  const url = autoSeed ? `${API_BASE}/data?auto_seed=true` : `${API_BASE}/data`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) {
    throw new Error(`Failed to fetch application data (${res.status} ${res.statusText})`);
  }
  return (await res.json()) as AppData;
}

/** Create a new expense entry in SQLite */
export async function createExpenseApi(entry: {
  name: string;
  amount: number;
  category: Category;
  date: string;
  paymentMethod: PaymentMethod;
  description: string;
}): Promise<Expense> {
  const res = await fetch(`${API_BASE}/expenses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(entry),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save expense');
  }
  return (await res.json()) as Expense;
}

/** Update an existing expense entry in SQLite */
export async function updateExpenseApi(
  id: number,
  entry: {
    name: string;
    amount: number;
    category: Category;
    date: string;
    paymentMethod: PaymentMethod;
    description: string;
  }
): Promise<Expense> {
  const res = await fetch(`${API_BASE}/expenses/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(entry),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to update expense');
  }
  return (await res.json()) as Expense;
}

/** Delete an expense entry from SQLite */
export async function deleteExpenseApi(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/expenses/${id}`, {
    method: 'DELETE',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error('Failed to delete expense record');
  }
}

/** Create a new income entry in SQLite */
export async function createIncomeApi(entry: {
  source: IncomeSource;
  amount: number;
  date: string;
  description: string;
}): Promise<Income> {
  const res = await fetch(`${API_BASE}/income`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(entry),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save income');
  }
  return (await res.json()) as Income;
}

/** Update an existing income entry in SQLite */
export async function updateIncomeApi(
  id: number,
  entry: {
    source: IncomeSource;
    amount: number;
    date: string;
    description: string;
  }
): Promise<Income> {
  const res = await fetch(`${API_BASE}/income/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(entry),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to update income');
  }
  return (await res.json()) as Income;
}

/** Delete an income entry from SQLite */
export async function deleteIncomeApi(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/income/${id}`, {
    method: 'DELETE',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error('Failed to delete income record');
  }
}

/** Save or update a budget limit in SQLite */
export async function saveBudgetApi(budget: {
  category: 'Overall' | Category;
  amount: number;
  period: string;
}): Promise<Budget> {
  const res = await fetch(`${API_BASE}/budgets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(budget),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save budget limit');
  }
  return (await res.json()) as Budget;
}

/** Delete a budget limit from SQLite */
export async function deleteBudgetApi(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/budgets/${id}`, {
    method: 'DELETE',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error('Failed to delete budget limit');
  }
}

/** Seed realistic demo sample data into SQLite */
export async function seedSampleDataApi(): Promise<AppData> {
  const res = await fetch(`${API_BASE}/sample-data/seed`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error('Failed to seed sample data');
  }
  return await fetchAppData();
}

/** Clear sample data rows from SQLite (retains custom user entries) */
export async function clearSampleDataApi(): Promise<AppData> {
  const res = await fetch(`${API_BASE}/sample-data/clear`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error('Failed to clear sample data');
  }
  return await fetchAppData();
}

/** Fetch all savings goals from the SQLite backend */
export async function fetchSavingsGoalsApi(status?: string): Promise<SavingsGoal[]> {
  const url = status ? `${API_BASE}/savings-goals?status=${encodeURIComponent(status)}` : `${API_BASE}/savings-goals`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) {
    throw new Error(`Failed to fetch savings goals (${res.status} ${res.statusText})`);
  }
  return (await res.json()) as SavingsGoal[];
}

/** Fetch summary stats across savings goals from backend */
export async function fetchSavingsSummaryApi(): Promise<SavingsSummary> {
  const res = await fetch(`${API_BASE}/savings-goals/summary`, { headers: { Accept: 'application/json' } });
  if (!res.ok) {
    throw new Error(`Failed to fetch savings goals summary (${res.status} ${res.statusText})`);
  }
  return (await res.json()) as SavingsSummary;
}

/** Create a new savings goal in SQLite */
export async function createSavingsGoalApi(goal: {
  goal_name: string;
  target_amount: number;
  target_date: string;
  description?: string;
  current_saved_amount?: number;
}): Promise<SavingsGoal> {
  const res = await fetch(`${API_BASE}/savings-goals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(goal),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to create savings goal');
  }
  return (await res.json()) as SavingsGoal;
}

/** Update an existing savings goal in SQLite */
export async function updateSavingsGoalApi(
  id: number,
  goal: {
    goal_name?: string;
    target_amount?: number;
    target_date?: string;
    description?: string;
    current_saved_amount?: number;
  }
): Promise<SavingsGoal> {
  const res = await fetch(`${API_BASE}/savings-goals/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(goal),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to update savings goal');
  }
  return (await res.json()) as SavingsGoal;
}

/** Delete a savings goal from SQLite */
export async function deleteSavingsGoalApi(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/savings-goals/${id}`, {
    method: 'DELETE',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error('Failed to delete savings goal');
  }
}

/** Add money (deposit) to an existing savings goal */
export async function addMoneyToSavingsGoalApi(
  id: number,
  amount: number
): Promise<SavingsGoal & { just_completed?: boolean; message?: string }> {
  const res = await fetch(`${API_BASE}/savings-goals/${id}/add-money`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ amount }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to add money to savings goal');
  }
  return (await res.json()) as SavingsGoal & { just_completed?: boolean; message?: string };
}

/** Get the direct download URL for server-generated PDF report */
export function getServerPdfUrl(period: string): string {
  return `${API_BASE}/reports/pdf?period=${encodeURIComponent(period)}`;
}

/** Get the direct download URL for server-generated CSV report */
export function getServerCsvUrl(period: string): string {
  return `${API_BASE}/reports/csv?period=${encodeURIComponent(period)}`;
}

/** Download a server-generated report (PDF or CSV) directly via blob download */
export async function downloadServerReport(type: 'pdf' | 'csv', period: string): Promise<boolean> {
  const url = type === 'pdf' ? getServerPdfUrl(period) : getServerCsvUrl(period);
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to download server ${type.toUpperCase()} report (${res.status} ${res.statusText})`);
  }
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = blobUrl;
  anchor.download = `pennypilot-report-${period}.${type}`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(blobUrl);
  return true;
}

