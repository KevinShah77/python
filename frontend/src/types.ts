export const CATEGORIES = [
  'Food & Dining',
  'Transportation',
  'Shopping',
  'Education',
  'Healthcare',
  'Entertainment',
  'Bills & Utilities',
  'Travel',
  'Personal Care',
  'Others',
] as const;

export const PAYMENT_METHODS = [
  'UPI / GPay / PhonePe',
  'Cash',
  'Debit Card',
  'Credit Card',
  'Net Banking',
  'Other',
] as const;

export const INCOME_SOURCES = [
  'Allowance',
  'Salary',
  'Freelancing',
  'Scholarship',
  'Other Income',
] as const;

export type Category = (typeof CATEGORIES)[number];
export type PaymentMethod = (typeof PAYMENT_METHODS)[number];
export type IncomeSource = (typeof INCOME_SOURCES)[number];
export type EntryKind = 'expense' | 'income';
export type PageKey = 'Dashboard' | 'Expenses' | 'Income' | 'Transactions' | 'Budgets' | 'Savings Goals' | 'Analytics' | 'Reports';
export type GoalStatus = 'In Progress' | 'Completed' | 'Overdue';

export interface Expense {
  id: number;
  type: 'expense';
  name: string;
  amount: number;
  category: Category;
  date: string;
  paymentMethod: PaymentMethod;
  description: string;
}

export interface Income {
  id: number;
  type: 'income';
  source: IncomeSource;
  amount: number;
  date: string;
  description: string;
}

export interface Budget {
  id: number;
  category: 'Overall' | Category;
  amount: number;
  period: string;
}

export interface SavingsGoal {
  id: number;
  user_id: string;
  goal_name: string;
  target_amount: number;
  current_saved_amount: number;
  remaining_amount: number;
  progress_percentage: number;
  target_date: string;
  description: string;
  created_date: string;
  status: GoalStatus;
  is_sample?: number;
}

export interface SavingsSummary {
  total_goals: number;
  total_target_amount: number;
  total_saved_amount: number;
  overall_progress_percentage: number;
  completed_count?: number;
  in_progress_count?: number;
  overdue_count?: number;
}

export interface AppData {
  expenses: Expense[];
  income: Income[];
  budgets: Budget[];
  savings_goals: SavingsGoal[];
}

export interface Transaction {
  id: string;
  entryId: number;
  kind: EntryKind;
  name: string;
  categoryOrSource: string;
  amount: number;
  date: string;
  paymentMethod: string;
  description: string;
}

export interface RecordFormValue {
  kind: EntryKind;
  name: string;
  amount: number;
  categoryOrSource: string;
  date: string;
  paymentMethod: string;
  description: string;
}
