import { useEffect, useMemo, useState } from 'react';
import { ArrowDownWideNarrow, ArrowUpDown, Download, Plus, Search, SlidersHorizontal, X } from 'lucide-react';
import type { AppData, EntryKind, PageKey, Transaction } from '../types';
import { CATEGORIES, INCOME_SOURCES } from '../types';
import { formatMoney, formatPeriod, getCategoryBreakdown, getCategoryMeta, getMonthTransactions, periodOf } from '../utils';
import { Button, IconButton, PageTitle, Panel } from '../components/ui';
import TransactionTable from '../components/TransactionTable';

export default function RecordsPage({
  page,
  data,
  period,
  onAdd,
  onEdit,
  onDelete,
}: {
  page: Extract<PageKey, 'Expenses' | 'Income' | 'Transactions'>;
  data: AppData;
  period: string;
  onAdd: (kind: EntryKind) => void;
  onEdit: (entry: Transaction) => void;
  onDelete: (entry: Transaction) => void;
}) {
  const [search, setSearch] = useState('');
  const [type, setType] = useState<'All' | EntryKind>(
    page === 'Expenses' ? 'expense' : page === 'Income' ? 'income' : 'All'
  );
  const [category, setCategory] = useState('All');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'amount'>('date');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  // Reset filters defensively whenever the active page changes
  useEffect(() => {
    setSearch('');
    setType(page === 'Expenses' ? 'expense' : page === 'Income' ? 'income' : 'All');
    setCategory('All');
    setFrom('');
    setTo('');
    setSortBy('date');
    setSortOrder('desc');
  }, [page]);

  // Derive distinct base records strictly per page type
  const base = useMemo((): Transaction[] => {
    if (page === 'Expenses') {
      const monthExpenses = data.expenses.filter((entry) => periodOf(entry.date) === period);
      return monthExpenses.map((entry): Transaction => ({
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
    }

    if (page === 'Income') {
      const monthIncome = data.income.filter((entry) => periodOf(entry.date) === period);
      return monthIncome.map((entry): Transaction => ({
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
    }

    // Default: Transactions page shows unified transactions
    return getMonthTransactions(data, period);
  }, [page, data, period]);

  // Distinct sources list for income filtering
  const incomeSources = useMemo(() => {
    const set = new Set<string>(INCOME_SOURCES);
    data.income.forEach((item) => set.add(item.source));
    return Array.from(set);
  }, [data.income]);

  const categories = useMemo(() => {
    if (page === 'Expenses' || (page === 'Transactions' && type === 'expense')) {
      return ['All', ...CATEGORIES];
    }
    if (page === 'Income' || (page === 'Transactions' && type === 'income')) {
      return ['All', ...incomeSources];
    }
    return ['All', ...CATEGORIES, ...incomeSources];
  }, [page, type, incomeSources]);

  // Filtered and sorted dataset
  const filtered = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return base
      .filter((entry) => {
        if (page === 'Transactions' && type !== 'All' && entry.kind !== type) {
          return false;
        }
        if (category !== 'All' && entry.categoryOrSource !== category) {
          return false;
        }
        if (from && entry.date < from) return false;
        if (to && entry.date > to) return false;
        if (query) {
          const matchTarget = [entry.name, entry.description, entry.paymentMethod, entry.categoryOrSource]
            .join(' ')
            .toLocaleLowerCase();
          if (!matchTarget.includes(query)) return false;
        }
        return true;
      })
      .sort((a, b) => {
        const comparison =
          sortBy === 'date'
            ? a.date.localeCompare(b.date) || a.entryId - b.entryId
            : a.amount - b.amount;
        return sortOrder === 'desc' ? -comparison : comparison;
      });
  }, [base, page, type, category, from, to, search, sortBy, sortOrder]);

  const clearFilters = () => {
    setSearch('');
    setType(page === 'Expenses' ? 'expense' : page === 'Income' ? 'income' : 'All');
    setCategory('All');
    setFrom('');
    setTo('');
  };

  const activeFilters =
    Number(Boolean(search)) +
    Number(type !== 'All' && page === 'Transactions') +
    Number(category !== 'All') +
    Number(Boolean(from)) +
    Number(Boolean(to));

  // Totals calculations
  const expenseTotal = filtered
    .filter((item) => item.kind === 'expense')
    .reduce((sum, item) => sum + item.amount, 0);

  const incomeTotal = filtered
    .filter((item) => item.kind === 'income')
    .reduce((sum, item) => sum + item.amount, 0);

  // Month base totals (for aggregate "All Categories" and "All Sources" chips)
  const baseExpenseTotal = useMemo(() => {
    return base.filter((item) => item.kind === 'expense').reduce((sum, item) => sum + item.amount, 0);
  }, [base]);

  const baseIncomeTotal = useMemo(() => {
    return base.filter((item) => item.kind === 'income').reduce((sum, item) => sum + item.amount, 0);
  }, [base]);

  // Category breakdown for Expenses page
  const expenseBreakdown = useMemo(() => {
    if (page !== 'Expenses') return [];
    return getCategoryBreakdown(data, period);
  }, [page, data, period]);

  // Source breakdown for Income page
  const incomeBreakdown = useMemo(() => {
    if (page !== 'Income') return [];
    const map = new Map<string, number>();
    base.forEach((item) => {
      map.set(item.categoryOrSource, (map.get(item.categoryOrSource) ?? 0) + item.amount);
    });
    const total = Array.from(map.values()).reduce((sum, v) => sum + v, 0);
    return Array.from(map.entries())
      .map(([source, amount]) => ({
        source,
        amount,
        percent: total > 0 ? (amount / total) * 100 : 0,
      }))
      .sort((a, b) => b.amount - a.amount);
  }, [page, base]);

  // Page titles and descriptions
  const title = page === 'Expenses' ? 'Expenses' : page === 'Income' ? 'Income' : 'Transactions';
  const eyebrow = page === 'Expenses' ? 'MONEY OUT' : page === 'Income' ? 'MONEY IN' : 'MONEY ACTIVITY';
  const subtitle =
    page === 'Expenses'
      ? 'Small details, clearer patterns.'
      : page === 'Income'
      ? 'Keep every inflow in the picture.'
      : 'Everything in and out, in one clear view.';

  // Export CSV handler tailored per page
  const handleExportCsv = () => {
    let rows: string[][];
    let filename: string;

    if (page === 'Expenses') {
      rows = [
        ['Date', 'Expense Name', 'Category', 'Amount (INR)', 'Payment Method', 'Notes'],
        ...filtered.map((item) => [
          item.date,
          item.name,
          item.categoryOrSource,
          item.amount.toFixed(2),
          item.paymentMethod,
          item.description,
        ]),
      ];
      filename = `pennypilot-expenses-${period}.csv`;
    } else if (page === 'Income') {
      rows = [
        ['Date', 'Income Source', 'Amount (INR)', 'Description / Notes'],
        ...filtered.map((item) => [
          item.date,
          item.name,
          item.amount.toFixed(2),
          item.description,
        ]),
      ];
      filename = `pennypilot-income-${period}.csv`;
    } else {
      rows = [
        ['Date', 'Name', 'Type', 'Category / Source', 'Amount (INR)', 'Payment Method', 'Notes'],
        ...filtered.map((item) => [
          item.date,
          item.name,
          item.kind,
          item.categoryOrSource,
          item.amount.toFixed(2),
          item.paymentMethod,
          item.description,
        ]),
      ];
      filename = `pennypilot-transactions-${period}.csv`;
    }

    const content = rows
      .map((row) => row.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
      .join('\r\n');

    const blob = new Blob([`\uFEFF${content}`], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="page-stack">
      <PageTitle
        eyebrow={eyebrow}
        title={title}
        description={`${subtitle} · ${formatPeriod(period)}`}
        actions={
          page === 'Transactions' ? (
            <>
              <Button onClick={() => onAdd('income')}>
                <Plus size={15} /> Add income
              </Button>
              <Button variant="primary" onClick={() => onAdd('expense')}>
                <Plus size={15} /> Add expense
              </Button>
            </>
          ) : page === 'Income' ? (
            <Button variant="primary" onClick={() => onAdd('income')}>
              <Plus size={16} /> Add income
            </Button>
          ) : (
            <Button variant="primary" onClick={() => onAdd('expense')}>
              <Plus size={16} /> Add expense
            </Button>
          )
        }
      />

      {/* Distinct Overview Strip */}
      <div className="record-overview-strip">
        {page === 'Expenses' && (
          <>
            <div>
              <span className="overview-dot overview-dot-out" />
              <span>Total Outflow</span>
              <strong>{formatMoney(expenseTotal)}</strong>
            </div>
            <i className="overview-separator" />
            <div>
              <span>Average</span>
              <strong>{filtered.length > 0 ? formatMoney(expenseTotal / filtered.length) : '₹0'}</strong>
            </div>
            <div className="overview-strip-tail">
              {filtered.length} {filtered.length === 1 ? 'expense' : 'expenses'} shown
            </div>
          </>
        )}

        {page === 'Income' && (
          <>
            <div>
              <span className="overview-dot overview-dot-in" />
              <span>Total Inflow</span>
              <strong>{formatMoney(incomeTotal)}</strong>
            </div>
            <i className="overview-separator" />
            <div>
              <span>Average Inflow</span>
              <strong>{filtered.length > 0 ? formatMoney(incomeTotal / filtered.length) : '₹0'}</strong>
            </div>
            <div className="overview-strip-tail">
              {filtered.length} {filtered.length === 1 ? 'income entry' : 'income entries'} shown
            </div>
          </>
        )}

        {page === 'Transactions' && (
          <>
            <div>
              <span className="overview-dot overview-dot-out" />
              <span>Outflow</span>
              <strong>{formatMoney(expenseTotal)}</strong>
            </div>
            <i className="overview-separator" />
            <div>
              <span className="overview-dot overview-dot-in" />
              <span>Inflow</span>
              <strong>{formatMoney(incomeTotal)}</strong>
            </div>
            <i className="overview-separator" />
            <div>
              <span className="overview-dot overview-dot-net" />
              <span>Net</span>
              <strong className={incomeTotal >= expenseTotal ? 'amount-positive' : 'amount-negative'}>
                {incomeTotal >= expenseTotal ? '+' : '−'}
                {formatMoney(Math.abs(incomeTotal - expenseTotal))}
              </strong>
            </div>
            <div className="overview-strip-tail">
              {filtered.length} {filtered.length === 1 ? 'transaction' : 'transactions'} shown
            </div>
          </>
        )}
      </div>

      {/* Category Breakdown (Expenses page) */}
      {page === 'Expenses' && expenseBreakdown.length > 0 && (
        <section className="records-breakdown-section" aria-label="Category breakdown">
          <div className="records-breakdown-header">
            <strong>Spending by Category</strong>
            <span>Click to filter table</span>
          </div>
          <div className="records-breakdown-chips">
            <button
              type="button"
              className={`breakdown-chip ${category === 'All' ? 'chip-active' : ''}`}
              onClick={() => setCategory('All')}
            >
              <span>All Categories</span>
              <strong>{formatMoney(baseExpenseTotal)}</strong>
            </button>
            {expenseBreakdown.map((item) => (
              <button
                key={item.category}
                type="button"
                className={`breakdown-chip ${category === item.category ? 'chip-active' : ''}`}
                onClick={() => setCategory(category === item.category ? 'All' : item.category)}
              >
                <i style={{ background: item.color ?? '#6366f1' }} />
                <span>{item.category}</span>
                <strong>{formatMoney(item.amount)}</strong>
                <small>({item.percent.toFixed(0)}%)</small>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Source Breakdown (Income page) */}
      {page === 'Income' && incomeBreakdown.length > 0 && (
        <section className="records-breakdown-section" aria-label="Income sources breakdown">
          <div className="records-breakdown-header">
            <strong>Income by Source</strong>
            <span>Click to filter table</span>
          </div>
          <div className="records-breakdown-chips">
            <button
              type="button"
              className={`breakdown-chip breakdown-chip-income ${category === 'All' ? 'chip-active' : ''}`}
              onClick={() => setCategory('All')}
            >
              <span>All Sources</span>
              <strong>{formatMoney(baseIncomeTotal)}</strong>
            </button>
            {incomeBreakdown.map((item) => {
              const meta = getCategoryMeta(item.source);
              return (
                <button
                  key={item.source}
                  type="button"
                  className={`breakdown-chip breakdown-chip-income ${category === item.source ? 'chip-active' : ''}`}
                  onClick={() => setCategory(category === item.source ? 'All' : item.source)}
                >
                  <i style={{ background: meta.color }} />
                  <span>{item.source}</span>
                  <strong>{formatMoney(item.amount)}</strong>
                  <small>({item.percent.toFixed(0)}%)</small>
                </button>
              );
            })}
          </div>
        </section>
      )}

      {/* Main Records Panel */}
      <Panel className="records-panel">
        <div className="filter-toolbar">
          <label className="search-control">
            <Search size={17} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={
                page === 'Expenses'
                  ? 'Search expense, note or payment…'
                  : page === 'Income'
                  ? 'Search income source or note…'
                  : 'Search transactions, notes or payment…'
              }
              aria-label={`Search ${title}`}
            />
            {search && (
              <IconButton label="Clear search" onClick={() => setSearch('')}>
                <X size={15} />
              </IconButton>
            )}
          </label>

          <div className="filters-right">
            {page === 'Transactions' && (
              <label className="filter-select">
                <span>Type</span>
                <select
                  value={type}
                  onChange={(event) => {
                    setType(event.target.value as 'All' | EntryKind);
                    setCategory('All');
                  }}
                >
                  <option value="All">All activity</option>
                  <option value="expense">Expenses</option>
                  <option value="income">Income</option>
                </select>
              </label>
            )}

            <label className="filter-select">
              <span>{page === 'Income' ? 'Source' : 'Category'}</span>
              <select value={category} onChange={(event) => setCategory(event.target.value)}>
                <option value="All">
                  {page === 'Income' ? 'All sources' : 'All categories'}
                </option>
                {categories
                  .filter((item) => item !== 'All')
                  .map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
              </select>
            </label>

            <button
              className="sort-button"
              type="button"
              onClick={() => setSortBy(sortBy === 'date' ? 'amount' : 'date')}
            >
              <ArrowUpDown size={14} /> {sortBy === 'date' ? 'Date' : 'Amount'}
            </button>

            <button
              className="sort-direction"
              type="button"
              aria-label={sortOrder === 'desc' ? 'Sort ascending' : 'Sort descending'}
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            >
              {sortOrder === 'desc' ? <ArrowDownWideNarrow size={15} /> : <SlidersHorizontal size={15} />}
            </button>
          </div>
        </div>

        <div className="date-filter-row">
          <span>Dates</span>
          <input
            aria-label="Start date"
            type="date"
            value={from}
            onChange={(event) => setFrom(event.target.value)}
          />
          <span className="date-range-separator">to</span>
          <input
            aria-label="End date"
            type="date"
            value={to}
            onChange={(event) => setTo(event.target.value)}
          />
          <span className="filter-period-note">Showing {formatPeriod(period)}</span>
          {activeFilters > 0 && (
            <button type="button" className="clear-filters" onClick={clearFilters}>
              Clear {activeFilters} filter{activeFilters > 1 ? 's' : ''} <X size={13} />
            </button>
          )}
        </div>

        <div className="table-results-bar">
          <div>
            <strong>{filtered.length}</strong>{' '}
            {page === 'Expenses'
              ? filtered.length === 1
                ? 'expense'
                : 'expenses'
              : page === 'Income'
              ? filtered.length === 1
                ? 'income entry'
                : 'income entries'
              : filtered.length === 1
              ? 'transaction'
              : 'transactions'}{' '}
            found
          </div>
          <button type="button" className="table-download" onClick={handleExportCsv}>
            <Download size={14} /> Export list
          </button>
        </div>

        <TransactionTable
          mode={page === 'Expenses' ? 'expenses' : page === 'Income' ? 'income' : 'all'}
          transactions={filtered}
          onEdit={onEdit}
          onDelete={onDelete}
          emptyTitle={
            search || activeFilters
              ? `No matching ${page === 'Expenses' ? 'expenses' : page === 'Income' ? 'income entries' : 'transactions'}`
              : page === 'Expenses'
              ? 'No expenses recorded this month'
              : page === 'Income'
              ? 'No income recorded this month'
              : 'No activity recorded this month'
          }
          emptyDetail={
            search || activeFilters
              ? 'Try adjusting your search query or filters.'
              : page === 'Expenses'
              ? 'Add an expense to start tracking where your money goes.'
              : page === 'Income'
              ? 'Add an income entry to track all your earnings.'
              : 'Add an expense or income entry to get started.'
          }
        />
      </Panel>
    </div>
  );
}
