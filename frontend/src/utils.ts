import { CATEGORIES, type AppData, type Budget, type Transaction } from './types';

export const CATEGORY_META: Record<string, { icon: string; color: string }> = {
  'Food & Dining': { icon: '🍽️', color: '#f4a261' },
  Transportation: { icon: '↗', color: '#528bff' },
  Shopping: { icon: '✦', color: '#e6b84a' },
  Education: { icon: '▤', color: '#38a78f' },
  Healthcare: { icon: '＋', color: '#e77992' },
  Entertainment: { icon: '▷', color: '#9976dc' },
  'Bills & Utilities': { icon: '⌁', color: '#d58d51' },
  Travel: { icon: '✈', color: '#43a5bb' },
  'Personal Care': { icon: '✿', color: '#d47eb3' },
  Others: { icon: '◌', color: '#8790a4' },
  Allowance: { icon: '◉', color: '#6886dd' },
  Salary: { icon: '▣', color: '#38a78f' },
  Freelancing: { icon: '⌘', color: '#9976dc' },
  Scholarship: { icon: '✧', color: '#d9a944' },
  'Other Income': { icon: '＋', color: '#8790a4' },
};

export function getCategoryMeta(key?: string): { icon: string; color: string } {
  if (!key) return { icon: '◌', color: '#8790a4' };
  if (CATEGORY_META[key]) return CATEGORY_META[key];
  const lower = key.toLowerCase();
  for (const [cat, meta] of Object.entries(CATEGORY_META)) {
    if (lower.includes(cat.toLowerCase())) {
      return meta;
    }
  }
  return { icon: '◌', color: '#8790a4' };
}

export const PERIODS = Array.from({ length: 12 }, (_, index) => {
  const now = new Date();
  const date = new Date(now.getFullYear(), now.getMonth() - index, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
});

export function formatMoney(value: number, decimals = 0) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(Number.isFinite(value) ? value : 0);
}

export function formatCompactMoney(value: number) {
  const absolute = Math.abs(value);
  if (absolute >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
  if (absolute >= 1000) return `₹${(value / 1000).toFixed(1)}k`;
  return formatMoney(value);
}

export function formatPeriod(period: string, short = false) {
  const [year, month] = period.split('-').map(Number);
  return new Intl.DateTimeFormat('en-IN', { month: short ? 'short' : 'long', year: 'numeric' }).format(new Date(year, month - 1, 1));
}

export function formatDate(value: string, options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }) {
  if (!value) return '';
  const [year, month, day] = value.split('-').map(Number);
  return new Intl.DateTimeFormat('en-IN', options).format(new Date(year, month - 1, day));
}

export function periodOf(value: string) {
  return value.slice(0, 7);
}

export function getTransactions(data: AppData): Transaction[] {
  const expenses: Transaction[] = data.expenses.map((entry) => ({
    id: `expense-${entry.id}`,
    entryId: entry.id,
    kind: 'expense',
    name: entry.name,
    categoryOrSource: entry.category,
    amount: entry.amount,
    date: entry.date,
    paymentMethod: entry.paymentMethod,
    description: entry.description,
  }));
  const income: Transaction[] = data.income.map((entry) => ({
    id: `income-${entry.id}`,
    entryId: entry.id,
    kind: 'income',
    name: entry.source,
    categoryOrSource: entry.source,
    amount: entry.amount,
    date: entry.date,
    paymentMethod: 'N/A',
    description: entry.description,
  }));
  return [...expenses, ...income].sort((a, b) => b.date.localeCompare(a.date) || b.entryId - a.entryId);
}

export function getMonthTransactions(data: AppData, period: string) {
  return getTransactions(data).filter((entry) => periodOf(entry.date) === period);
}

export function getSummary(data: AppData, period: string) {
  const expenses = data.expenses.filter((entry) => periodOf(entry.date) === period);
  const income = data.income.filter((entry) => periodOf(entry.date) === period);
  const expenseTotal = expenses.reduce((sum, item) => sum + item.amount, 0);
  const incomeTotal = income.reduce((sum, item) => sum + item.amount, 0);
  const overallBudget = data.budgets.find((item) => item.period === period && item.category === 'Overall');
  return {
    expenses,
    income,
    expenseTotal,
    incomeTotal,
    balance: incomeTotal - expenseTotal,
    savingsRate: incomeTotal > 0 ? ((incomeTotal - expenseTotal) / incomeTotal) * 100 : 0,
    overallBudget: overallBudget?.amount ?? 0,
    transactionCount: expenses.length + income.length,
  };
}

export function getCategoryBreakdown(data: AppData, period: string) {
  const expenses = data.expenses.filter((entry) => periodOf(entry.date) === period);
  const totals = CATEGORIES.map((category) => {
    const amount = expenses.filter((entry) => entry.category === category).reduce((sum, item) => sum + item.amount, 0);
    return { category, amount, count: expenses.filter((entry) => entry.category === category).length };
  }).filter((item) => item.amount > 0).sort((a, b) => b.amount - a.amount);
  const total = totals.reduce((sum, item) => sum + item.amount, 0);
  return totals.map((item) => ({ ...item, percent: total > 0 ? (item.amount / total) * 100 : 0, ...(CATEGORY_META[item.category] ?? {}) }));
}

export type BudgetTier = 'none' | 'normal' | 'caution' | 'warning' | 'exceeded';
export function budgetStatus(spent: number, limit: number) {
  const utilization = limit > 0 ? (spent / limit) * 100 : 0;
  const tier: BudgetTier = limit <= 0 ? 'none' : utilization < 75 ? 'normal' : utilization < 90 ? 'caution' : utilization < 100 ? 'warning' : 'exceeded';
  const labels: Record<BudgetTier, string> = {
    none: 'No limit set', normal: 'On track', caution: 'Caution', warning: 'Near limit', exceeded: 'Over budget',
  };
  const messages: Record<BudgetTier, string> = {
    none: 'Add a limit to start tracking this budget.',
    normal: 'Spending is within a healthy range.',
    caution: 'Keep an eye on spending as you approach the limit.',
    warning: 'You are close to the budget limit.',
    exceeded: `Over budget by ${formatMoney(Math.max(spent - limit, 0))}.`,
  };
  return {
    tier,
    label: labels[tier],
    message: messages[tier],
    utilization,
    remaining: limit - spent,
    progress: limit > 0 ? Math.min(spent / limit, 1) * 100 : 0,
  };
}

export function getBudgetRows(data: AppData, period: string) {
  const expenses = data.expenses.filter((entry) => periodOf(entry.date) === period);
  const budgets = data.budgets.filter((item) => item.period === period && item.category !== 'Overall');
  return budgets
    .map((budget) => {
      const spent = expenses.filter((item) => item.category === budget.category).reduce((sum, item) => sum + item.amount, 0);
      return { ...budget, spent, ...budgetStatus(spent, budget.amount) };
    })
    .sort((a, b) => b.utilization - a.utilization);
}

export function getMonthComparison(data: AppData, period: string) {
  const [year, month] = period.split('-').map(Number);
  const previous = new Date(year, month - 2, 1);
  const previousPeriod = `${previous.getFullYear()}-${String(previous.getMonth() + 1).padStart(2, '0')}`;
  const current = getSummary(data, period).expenseTotal;
  const prior = getSummary(data, previousPeriod).expenseTotal;
  return { current, prior, previousPeriod, change: current - prior, percent: prior > 0 ? ((current - prior) / prior) * 100 : current > 0 ? 100 : 0 };
}

export function getMonthlyTrend(data: AppData, period: string, count = 6) {
  const [year, month] = period.split('-').map(Number);
  return Array.from({ length: count }, (_, index) => {
    const date = new Date(year, month - 1 - (count - 1 - index), 1);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const label = new Intl.DateTimeFormat('en-IN', { month: 'short' }).format(date);
    const summary = getSummary(data, key);
    return { period: key, month: label, income: summary.incomeTotal, expenses: summary.expenseTotal, balance: summary.balance };
  });
}

export function getDailyTrend(data: AppData, period: string) {
  const [, monthValue] = period.split('-');
  const month = Number(monthValue);
  const year = Number(period.slice(0, 4));
  const days = new Date(year, month, 0).getDate();
  const monthExpenses = data.expenses.filter((item) => periodOf(item.date) === period);
  let cumulative = 0;
  return Array.from({ length: days }, (_, index) => {
    const day = index + 1;
    const spend = monthExpenses.filter((item) => Number(item.date.slice(8, 10)) === day).reduce((sum, item) => sum + item.amount, 0);
    cumulative += spend;
    return { day: String(day), spend, cumulative };
  });
}

export function getAverageStats(data: AppData, period: string) {
  const summary = getSummary(data, period);
  const allPeriods = new Set(data.expenses.map((entry) => periodOf(entry.date)));
  const historyTotal = data.expenses.reduce((sum, entry) => sum + entry.amount, 0);
  const date = new Date(Number(period.slice(0, 4)), Number(period.slice(5, 7)), 0);
  const elapsed = period === new Date().toISOString().slice(0, 7) ? new Date().getDate() : date.getDate();
  return {
    daily: summary.expenseTotal / Math.max(elapsed, 1),
    perTransaction: summary.expenses.length ? summary.expenseTotal / summary.expenses.length : 0,
    monthly: allPeriods.size ? historyTotal / allPeriods.size : 0,
    count: summary.expenses.length,
  };
}

export interface Insight {
  kind: 'positive' | 'warning' | 'info';
  icon: string;
  title: string;
  detail: string;
  tip: string;
}

export function getInsights(data: AppData, period: string): Insight[] {
  const summary = getSummary(data, period);
  const breakdown = getCategoryBreakdown(data, period);
  const comparison = getMonthComparison(data, period);
  const insights: Insight[] = [];
  if (!summary.transactionCount) {
    return [{ kind: 'info', icon: '✦', title: 'A fresh start', detail: `No activity recorded for ${formatPeriod(period)} yet.`, tip: 'Add your first transaction to see your spending patterns take shape.' }];
  }
  if (breakdown.length) {
    const top = breakdown[0];
    insights.push({
      kind: top.percent >= 35 ? 'warning' : 'info',
      icon: top.icon,
      title: `${top.category} leads your spending`,
      detail: `${top.percent.toFixed(1)}% of this month’s outflow, or ${formatMoney(top.amount)}.`,
      tip: top.percent >= 35 ? 'Consider setting a category limit to keep this area in view.' : 'Keep reviewing this category as you plan the rest of the month.',
    });
    const concentration = breakdown.find((item) => item.percent >= 35 && item.category !== top.category);
    if (concentration) insights.push({ kind: 'warning', icon: '!', title: `${concentration.category} is a large share`, detail: `${concentration.percent.toFixed(1)}% of monthly outflow is concentrated here.`, tip: 'A category budget can help make this spending easier to manage.' });
  }
  if (comparison.prior > 0 && Math.abs(comparison.percent) >= 20) {
    const up = comparison.change > 0;
    insights.push({ kind: up ? 'warning' : 'positive', icon: up ? '↗' : '↘', title: up ? 'Spending is up month over month' : 'Spending is down from last month', detail: `${Math.abs(comparison.percent).toFixed(1)}% ${up ? 'higher' : 'lower'} than ${formatPeriod(comparison.previousPeriod)}.`, tip: up ? 'Review the categories that shifted most before adding new discretionary purchases.' : 'Keep up the steady habits and consider directing the difference toward savings.' });
  }
  const overall = data.budgets.find((item) => item.period === period && item.category === 'Overall');
  if (overall) {
    const status = budgetStatus(summary.expenseTotal, overall.amount);
    if (status.tier === 'warning' || status.tier === 'exceeded' || status.tier === 'caution') {
      insights.push({ kind: status.tier === 'exceeded' ? 'warning' : 'info', icon: status.tier === 'exceeded' ? '!' : '◷', title: status.tier === 'exceeded' ? 'Monthly cap exceeded' : `Budget ${status.tier === 'warning' ? 'nearly reached' : 'in caution range'}`, detail: `${status.utilization.toFixed(1)}% of the ${formatMoney(overall.amount)} overall budget has been used.`, tip: status.tier === 'exceeded' ? 'Pause non-essential spending and revisit your category limits.' : 'Check the remaining days of the month before committing to larger purchases.' });
    }
  }
  if (summary.incomeTotal > 0 && summary.balance < 0) {
    insights.push({ kind: 'warning', icon: '−', title: 'Outflow is ahead of income', detail: `Expenses exceed recorded income by ${formatMoney(Math.abs(summary.balance))}.`, tip: 'Prioritize essential expenses and review flexible spending.' });
  } else if (summary.incomeTotal > 0 && summary.savingsRate >= 25) {
    insights.push({ kind: 'positive', icon: '✦', title: 'Strong savings month', detail: `${summary.savingsRate.toFixed(1)}% of recorded income remains after expenses.`, tip: 'Consider keeping a portion of this buffer for upcoming goals.' });
  } else if (summary.incomeTotal > 0 && summary.savingsRate < 15) {
    insights.push({ kind: 'info', icon: '◉', title: 'Savings buffer is building', detail: `${summary.savingsRate.toFixed(1)}% of recorded income remains after expenses.`, tip: 'Small recurring changes can help grow your monthly buffer.' });
  }
  return insights.slice(0, 5);
}

export function createBudgetRows(data: AppData, period: string) {
  const expenses = data.expenses.filter((entry) => periodOf(entry.date) === period);
  return CATEGORIES.map((category) => {
    const budget = data.budgets.find((item) => item.period === period && item.category === category);
    const spent = expenses.filter((item) => item.category === category).reduce((sum, item) => sum + item.amount, 0);
    return { category, budget: budget?.amount ?? 0, spent, ...budgetStatus(spent, budget?.amount ?? 0) };
  });
}

function csvCell(value: string | number) {
  const text = String(value ?? '');
  return `"${text.replace(/"/g, '""')}"`;
}

export function downloadCsv(data: AppData, period: string, transactions: Transaction[] = getMonthTransactions(data, period)) {
  const summary = getSummary(data, period);
  const categoryRows = getCategoryBreakdown(data, period);
  const rows: Array<Array<string | number>> = [
    ['PENNYPILOT — MONTHLY FINANCIAL REPORT'],
    [formatPeriod(period)],
    [],
    ['Executive summary'],
    ['Total income (INR)', summary.incomeTotal],
    ['Total expenses (INR)', summary.expenseTotal],
    ['Remaining balance (INR)', summary.balance],
    ['Savings rate (%)', summary.savingsRate.toFixed(1)],
    ['Overall budget (INR)', summary.overallBudget || 'Not set'],
    [],
    ['Category', 'Transactions', 'Total spent (INR)', 'Share (%)'],
    ...categoryRows.map((item) => [item.category, item.count, item.amount.toFixed(2), item.percent.toFixed(1)]),
    [],
    ['Date', 'Name / source', 'Type', 'Category / source', 'Amount (INR)', 'Payment method', 'Notes'],
    ...transactions.map((item) => [item.date, item.name, item.kind === 'income' ? 'Income' : 'Expense', item.categoryOrSource, item.amount.toFixed(2), item.paymentMethod, item.description]),
  ];
  const content = `\uFEFF${rows.map((row) => row.map((cell) => csvCell(cell)).join(',')).join('\r\n')}`;
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `pennypilot-report-${period}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function downloadPdf(data: AppData, period: string) {
  const { jsPDF } = await import('jspdf');
  const pdf = new jsPDF({ unit: 'mm', format: 'a4' });
  const margin = 15;
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const summary = getSummary(data, period);
  const categories = getCategoryBreakdown(data, period);
  const transactions = getMonthTransactions(data, period);
  let y = 19;
  const money = (value: number) => `INR ${new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(value)}`;
  const line = (color: [number, number, number], width = 0.25) => { pdf.setDrawColor(...color); pdf.setLineWidth(width); };
  const ensureSpace = (height: number) => {
    if (y + height > pageHeight - margin) { pdf.addPage(); y = margin; }
  };
  const title = 'PennyPilot';
  pdf.setFillColor(63, 92, 232);
  pdf.roundedRect(margin, y - 4, 9, 9, 2, 2, 'F');
  pdf.setFillColor(200, 238, 106);
  pdf.circle(margin + 6.6, y + 2.2, 1.1, 'F');
  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(20);
  pdf.setTextColor(30, 42, 74);
  pdf.text(title, margin + 13, y + 2);
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(10);
  pdf.setTextColor(100, 110, 132);
  pdf.text(`Monthly financial report  ·  ${formatPeriod(period)}`, margin + 13, y + 8);
  y += 20;
  line([226, 230, 240], 0.4);
  pdf.line(margin, y, pageWidth - margin, y);
  y += 10;

  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(11);
  pdf.setTextColor(30, 42, 74);
  pdf.text('Executive overview', margin, y);
  y += 7;
  const summaryRows = [
    ['Total income', money(summary.incomeTotal)],
    ['Total expenses', money(summary.expenseTotal)],
    ['Remaining balance', money(summary.balance)],
    ['Savings rate', `${summary.savingsRate.toFixed(1)}%`],
    ['Monthly budget', summary.overallBudget ? money(summary.overallBudget) : 'Not set'],
  ];
  summaryRows.forEach(([label, value], index) => {
    ensureSpace(9);
    if (index % 2 === 0) { pdf.setFillColor(247, 248, 251); pdf.rect(margin, y - 5, pageWidth - margin * 2, 8, 'F'); }
    pdf.setFont('helvetica', 'normal'); pdf.setFontSize(9); pdf.setTextColor(68, 77, 98);
    pdf.text(label, margin + 2, y);
    pdf.setFont('helvetica', 'bold'); pdf.setTextColor(30, 42, 74);
    pdf.text(value, pageWidth - margin - 2, y, { align: 'right' });
    y += 8;
  });
  y += 8;

  ensureSpace(15);
  pdf.setFont('helvetica', 'bold'); pdf.setFontSize(11); pdf.setTextColor(30, 42, 74);
  pdf.text('Category spending', margin, y); y += 7;
  pdf.setFillColor(63, 92, 232); pdf.rect(margin, y - 5, pageWidth - margin * 2, 8, 'F');
  pdf.setFont('helvetica', 'bold'); pdf.setFontSize(8); pdf.setTextColor(255, 255, 255);
  pdf.text('CATEGORY', margin + 2, y); pdf.text('TXNS', pageWidth - margin - 48, y, { align: 'right' });
  pdf.text('SPENT', pageWidth - margin - 2, y, { align: 'right' }); y += 8;
  categories.forEach((item, index) => {
    ensureSpace(8);
    if (index % 2 === 0) { pdf.setFillColor(247, 248, 251); pdf.rect(margin, y - 5, pageWidth - margin * 2, 8, 'F'); }
    pdf.setFont('helvetica', 'normal'); pdf.setFontSize(8.5); pdf.setTextColor(57, 66, 86);
    pdf.text(item.category, margin + 2, y);
    pdf.text(String(item.count), pageWidth - margin - 48, y, { align: 'right' });
    pdf.text(money(item.amount), pageWidth - margin - 2, y, { align: 'right' }); y += 8;
  });
  y += 7;

  ensureSpace(17);
  pdf.setFont('helvetica', 'bold'); pdf.setFontSize(11); pdf.setTextColor(30, 42, 74);
  pdf.text('Transaction activity', margin, y); y += 7;
  pdf.setFillColor(63, 92, 232); pdf.rect(margin, y - 5, pageWidth - margin * 2, 8, 'F');
  pdf.setFont('helvetica', 'bold'); pdf.setFontSize(7); pdf.setTextColor(255, 255, 255);
  pdf.text('DATE', margin + 2, y);
  pdf.text('DETAIL', margin + 23, y);
  pdf.text('TYPE', margin + 59, y);
  pdf.text('CATEGORY / SOURCE', margin + 76, y);
  pdf.text('METHOD', margin + 113, y);
  pdf.text('AMOUNT', pageWidth - margin - 2, y, { align: 'right' });
  y += 8;
  transactions.forEach((item, index) => {
    ensureSpace(9);
    if (index % 2 === 0) { pdf.setFillColor(247, 248, 251); pdf.rect(margin, y - 5, pageWidth - margin * 2, 9, 'F'); }
    pdf.setFont('helvetica', 'normal'); pdf.setFontSize(7.3); pdf.setTextColor(57, 66, 86);
    pdf.text(formatDate(item.date), margin + 2, y);
    const detail = pdf.splitTextToSize(item.name, 34)[0] ?? item.name;
    pdf.text(detail, margin + 23, y);
    pdf.text(item.kind === 'income' ? 'Income' : 'Expense', margin + 59, y);
    pdf.text(item.categoryOrSource, margin + 76, y);
    pdf.text(item.paymentMethod || 'N/A', margin + 113, y);
    pdf.setFont('helvetica', 'bold');
    pdf.setTextColor(item.kind === 'income' ? 44 : 52, item.kind === 'income' ? 145 : 65, item.kind === 'income' ? 113 : 81);
    pdf.text(`${item.kind === 'income' ? '+' : '−'} ${money(item.amount)}`, pageWidth - margin - 2, y, { align: 'right' });
    y += 9;
  });
  const pages = pdf.getNumberOfPages();
  for (let page = 1; page <= pages; page += 1) {
    pdf.setPage(page);
    pdf.setFont('helvetica', 'normal'); pdf.setFontSize(7); pdf.setTextColor(139, 146, 162);
    pdf.text(`Generated ${new Date().toLocaleDateString('en-IN')}  ·  PennyPilot`, margin, pageHeight - 8);
    pdf.text(`${page} / ${pages}`, pageWidth - margin, pageHeight - 8, { align: 'right' });
  }
  pdf.save(`pennypilot-report-${period}.pdf`);
}

export function getBudgetFor(data: AppData, category: Budget['category'], period: string) {
  return data.budgets.find((item) => item.period === period && item.category === category);
}
