import { useCallback, useEffect, useMemo, useState } from 'react';
import type {
  AppData,
  Budget,
  Category,
  EntryKind,
  IncomeSource,
  PageKey,
  PaymentMethod,
  RecordFormValue,
  SavingsGoal,
  Transaction,
} from './types';
import { createSeedData } from './data';
import { budgetStatus, getBudgetRows, getSummary } from './utils';
import {
  checkBackendStatus,
  fetchAppData,
  createExpenseApi,
  updateExpenseApi,
  deleteExpenseApi,
  createIncomeApi,
  updateIncomeApi,
  deleteIncomeApi,
  saveBudgetApi,
  deleteBudgetApi,
  createSavingsGoalApi,
  updateSavingsGoalApi,
  deleteSavingsGoalApi,
  addMoneyToSavingsGoalApi,
  seedSampleDataApi,
  clearSampleDataApi,
} from './api';
import Shell from './components/Shell';
import EntryModal from './components/EntryModal';
import BudgetModal from './components/BudgetModal';
import GoalModal from './components/GoalModal';
import AddMoneyModal from './components/AddMoneyModal';
import ConfirmDialog from './components/ConfirmDialog';
import Toast from './components/Toast';
import Dashboard from './pages/Dashboard';
import RecordsPage from './pages/RecordsPage';
import BudgetsPage from './pages/BudgetsPage';
import SavingsGoalsPage from './pages/SavingsGoalsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ReportsPage from './pages/ReportsPage';

const STORAGE_KEY = 'pennypilot-v1';
type DeleteTarget =
  | { kind: 'record'; entry: Transaction }
  | { kind: 'budget'; budget: Budget }
  | { kind: 'goal'; goal: SavingsGoal };

function loadLocalData(): AppData {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved) as AppData;
      if (
        Array.isArray(parsed.expenses) &&
        Array.isArray(parsed.income) &&
        Array.isArray(parsed.budgets)
      ) {
        if (!Array.isArray(parsed.savings_goals)) {
          parsed.savings_goals = createSeedData().savings_goals;
        }
        return parsed;
      }
    }
  } catch {
    /* Re-seed if stored browser data was invalid or unavailable. */
  }
  return createSeedData();
}

export default function App() {
  const [data, setData] = useState<AppData>(loadLocalData);
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [page, setPage] = useState<PageKey>('Dashboard');
  const [period, setPeriod] = useState(() => new Date().toISOString().slice(0, 7));
  const [entryDialog, setEntryDialog] = useState<{ kind: EntryKind; editing?: Transaction } | null>(null);
  const [budgetDialog, setBudgetDialog] = useState<{ editing?: Budget } | null>(null);
  const [goalDialog, setGoalDialog] = useState<{ editing?: SavingsGoal } | null>(null);
  const [addMoneyDialog, setAddMoneyDialog] = useState<{ goal: SavingsGoal } | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Synchronize with local storage as offline cache
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch {
      /* Continue in-memory if browser storage is full. */
    }
  }, [data]);

  // Connect to Python FastAPI / SQLite backend on mount
  useEffect(() => {
    let isMounted = true;
    async function initBackend() {
      const status = await checkBackendStatus();
      if (!isMounted) return;

      if (status && status.db_connected) {
        setBackendConnected(true);
        try {
          // If database is completely empty on first launch, auto_seed=true populates demo data
          const remoteData = await fetchAppData(true);
          if (isMounted) {
            setData(remoteData);
          }
        } catch {
          // If remote load fails, keep local data
        }
      } else {
        setBackendConnected(false);
      }
    }

    initBackend();
    return () => {
      isMounted = false;
    };
  }, []);

  const notify = useCallback((message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type });
  }, []);

  const openAdd = useCallback((kind: EntryKind) => setEntryDialog({ kind }), []);
  const openEdit = useCallback((entry: Transaction) => setEntryDialog({ kind: entry.kind, editing: entry }), []);

  const saveEntry = async (value: RecordFormValue, entryId?: number) => {
    if (backendConnected) {
      try {
        if (value.kind === 'expense') {
          const payload = {
            name: value.name,
            amount: value.amount,
            category: value.categoryOrSource as Category,
            date: value.date,
            paymentMethod: value.paymentMethod as PaymentMethod,
            description: value.description,
          };
          if (entryId) {
            const updated = await updateExpenseApi(entryId, payload);
            setData((current) => ({
              ...current,
              expenses: current.expenses.map((entry) => (entry.id === entryId ? updated : entry)),
            }));
            notify('Expense updated.');
          } else {
            const created = await createExpenseApi(payload);
            setData((current) => ({
              ...current,
              expenses: [created, ...current.expenses],
            }));
            notify('Expense added.');
          }
        } else {
          const payload = {
            source: value.categoryOrSource as IncomeSource,
            amount: value.amount,
            date: value.date,
            description: value.description,
          };
          if (entryId) {
            const updated = await updateIncomeApi(entryId, payload);
            setData((current) => ({
              ...current,
              income: current.income.map((entry) => (entry.id === entryId ? updated : entry)),
            }));
            notify('Income updated.');
          } else {
            const created = await createIncomeApi(payload);
            setData((current) => ({
              ...current,
              income: [created, ...current.income],
            }));
            notify('Income added.');
          }
        }
        setEntryDialog(null);
        return;
      } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : 'Error saving to backend';
        notify(errorMsg, 'error');
        return;
      }
    }

    // Fallback: Local storage persistence when offline
    setData((current) => {
      if (value.kind === 'expense') {
        const expense = {
          id: entryId ?? Math.max(0, ...current.expenses.map((entry) => entry.id)) + 1,
          type: 'expense' as const,
          name: value.name,
          amount: value.amount,
          category: value.categoryOrSource as Category,
          date: value.date,
          paymentMethod: value.paymentMethod as PaymentMethod,
          description: value.description,
        };
        return {
          ...current,
          expenses: entryId
            ? current.expenses.map((entry) => (entry.id === entryId ? expense : entry))
            : [expense, ...current.expenses],
        };
      }
      const income = {
        id: entryId ?? Math.max(0, ...current.income.map((entry) => entry.id)) + 1,
        type: 'income' as const,
        source: value.categoryOrSource as IncomeSource,
        amount: value.amount,
        date: value.date,
        description: value.description,
      };
      return {
        ...current,
        income: entryId
          ? current.income.map((entry) => (entry.id === entryId ? income : entry))
          : [income, ...current.income],
      };
    });
    setEntryDialog(null);
    notify(
      entryId
        ? `${value.kind === 'expense' ? 'Expense' : 'Income'} updated.`
        : `${value.kind === 'expense' ? 'Expense' : 'Income'} added.`
    );
  };

  const saveBudget = async (category: 'Overall' | Category, amount: number) => {
    if (backendConnected) {
      try {
        const saved = await saveBudgetApi({ category, amount, period });
        setData((current) => {
          const existing = current.budgets.find(
            (item) => item.period === period && item.category === category
          );
          return {
            ...current,
            budgets: existing
              ? current.budgets.map((item) => (item.id === existing.id ? saved : item))
              : [saved, ...current.budgets],
          };
        });
        setBudgetDialog(null);
        notify(`${category === 'Overall' ? 'Overall monthly' : category} budget saved.`);
        return;
      } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : 'Error saving budget';
        notify(errorMsg, 'error');
        return;
      }
    }

    // Fallback: Local storage persistence when offline
    setData((current) => {
      const existing = current.budgets.find(
        (item) => item.period === period && item.category === category
      );
      const budget = {
        id: existing?.id ?? Math.max(0, ...current.budgets.map((item) => item.id)) + 1,
        category,
        amount,
        period,
      };
      return {
        ...current,
        budgets: existing
          ? current.budgets.map((item) => (item.id === existing.id ? budget : item))
          : [budget, ...current.budgets],
      };
    });
    setBudgetDialog(null);
    notify(`${category === 'Overall' ? 'Overall monthly' : category} budget saved.`);
  };

  const saveGoal = async (
    goalData: {
      goal_name: string;
      target_amount: number;
      target_date: string;
      description: string;
      current_saved_amount?: number;
    },
    goalId?: number
  ) => {
    if (backendConnected) {
      try {
        if (goalId) {
          const updated = await updateSavingsGoalApi(goalId, goalData);
          setData((current) => ({
            ...current,
            savings_goals: (current.savings_goals || []).map((g) => (g.id === goalId ? updated : g)),
          }));
          notify('Savings goal updated.');
        } else {
          const created = await createSavingsGoalApi(goalData);
          setData((current) => ({
            ...current,
            savings_goals: [created, ...(current.savings_goals || [])],
          }));
          notify('Savings goal created.');
        }
        setGoalDialog(null);
        return;
      } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : 'Error saving savings goal';
        notify(errorMsg, 'error');
        return;
      }
    }

    // Local offline fallback
    setData((current) => {
      const existingList = current.savings_goals || [];
      const id = goalId ?? Math.max(0, ...existingList.map((g) => g.id)) + 1;
      const saved = Number(goalData.current_saved_amount || 0);
      const target = Number(goalData.target_amount);
      const remaining = Math.max(0, target - saved);
      const progress = target > 0 ? (saved / target) * 100 : 0;
      const isCompleted = saved >= target;
      const isOverdue = !isCompleted && goalData.target_date < new Date().toISOString().slice(0, 10);
      const status = isCompleted ? 'Completed' : isOverdue ? 'Overdue' : 'In Progress';

      const newGoal: SavingsGoal = {
        id,
        user_id: 'default_user',
        goal_name: goalData.goal_name,
        target_amount: target,
        current_saved_amount: saved,
        remaining_amount: remaining,
        progress_percentage: Math.round(progress * 10) / 10,
        target_date: goalData.target_date,
        description: goalData.description,
        created_date: new Date().toISOString().slice(0, 10),
        status,
      };

      return {
        ...current,
        savings_goals: goalId
          ? existingList.map((g) => (g.id === goalId ? newGoal : g))
          : [newGoal, ...existingList],
      };
    });
    setGoalDialog(null);
    notify(goalId ? 'Savings goal updated.' : 'Savings goal created.');
  };

  const handleAddMoney = async (goalId: number, amount: number) => {
    if (backendConnected) {
      try {
        const res = await addMoneyToSavingsGoalApi(goalId, amount);
        setData((current) => ({
          ...current,
          savings_goals: (current.savings_goals || []).map((g) => (g.id === goalId ? res : g)),
        }));
        if (res.just_completed) {
          notify(`🎉 Goal Completed! Congratulations, you reached your target for "${res.goal_name}"!`, 'success');
        } else {
          notify(`Added ₹${amount.toLocaleString('en-IN')} to "${res.goal_name}".`, 'success');
        }
        return;
      } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : 'Error adding money';
        notify(errorMsg, 'error');
        throw err;
      }
    }

    // Local offline fallback
    setData((current) => {
      const existingList = current.savings_goals || [];
      const targetGoal = existingList.find((g) => g.id === goalId);
      if (!targetGoal) return current;

      const newSaved = targetGoal.current_saved_amount + amount;
      const target = targetGoal.target_amount;
      const remaining = Math.max(0, target - newSaved);
      const progress = target > 0 ? (newSaved / target) * 100 : 0;
      const wasCompleted = targetGoal.status === 'Completed';
      const nowCompleted = newSaved >= target;
      const isOverdue = !nowCompleted && targetGoal.target_date < new Date().toISOString().slice(0, 10);
      const status = nowCompleted ? 'Completed' : isOverdue ? 'Overdue' : 'In Progress';

      const updated: SavingsGoal = {
        ...targetGoal,
        current_saved_amount: newSaved,
        remaining_amount: remaining,
        progress_percentage: Math.round(progress * 10) / 10,
        status,
      };

      if (!wasCompleted && nowCompleted) {
        notify(`🎉 Goal Completed! Congratulations, you reached your target for "${targetGoal.goal_name}"!`, 'success');
      } else {
        notify(`Added ₹${amount.toLocaleString('en-IN')} to "${targetGoal.goal_name}".`, 'success');
      }

      return {
        ...current,
        savings_goals: existingList.map((g) => (g.id === goalId ? updated : g)),
      };
    });
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;

    if (backendConnected) {
      try {
        if (deleteTarget.kind === 'record') {
          const entry = deleteTarget.entry;
          if (entry.kind === 'expense') {
            await deleteExpenseApi(entry.entryId);
            setData((current) => ({
              ...current,
              expenses: current.expenses.filter((item) => item.id !== entry.entryId),
            }));
            notify('Expense removed.');
          } else {
            await deleteIncomeApi(entry.entryId);
            setData((current) => ({
              ...current,
              income: current.income.filter((item) => item.id !== entry.entryId),
            }));
            notify('Income removed.');
          }
        } else if (deleteTarget.kind === 'budget') {
          await deleteBudgetApi(deleteTarget.budget.id);
          setData((current) => ({
            ...current,
            budgets: current.budgets.filter((item) => item.id !== deleteTarget.budget.id),
          }));
          notify('Budget limit removed.');
        } else if (deleteTarget.kind === 'goal') {
          await deleteSavingsGoalApi(deleteTarget.goal.id);
          setData((current) => ({
            ...current,
            savings_goals: (current.savings_goals || []).filter((g) => g.id !== deleteTarget.goal.id),
          }));
          notify('Savings goal removed.');
        }
        setDeleteTarget(null);
        return;
      } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to delete item';
        notify(errorMsg, 'error');
        return;
      }
    }

    // Fallback: Local delete
    if (deleteTarget.kind === 'record') {
      const entry = deleteTarget.entry;
      setData((current) =>
        entry.kind === 'expense'
          ? { ...current, expenses: current.expenses.filter((item) => item.id !== entry.entryId) }
          : { ...current, income: current.income.filter((item) => item.id !== entry.entryId) }
      );
      notify(`${entry.kind === 'expense' ? 'Expense' : 'Income'} removed.`);
    } else if (deleteTarget.kind === 'budget') {
      setData((current) => ({
        ...current,
        budgets: current.budgets.filter((item) => item.id !== deleteTarget.budget.id),
      }));
      notify('Budget limit removed.');
    } else if (deleteTarget.kind === 'goal') {
      setData((current) => ({
        ...current,
        savings_goals: (current.savings_goals || []).filter((g) => g.id !== deleteTarget.goal.id),
      }));
      notify('Savings goal removed.');
    }
    setDeleteTarget(null);
  };

  const handleSeedDemo = async () => {
    if (!backendConnected) {
      setData(createSeedData());
      notify('Loaded demo sample data.');
      return;
    }
    try {
      const remote = await seedSampleDataApi();
      setData(remote);
      notify('Demo records loaded into SQLite database.');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to seed demo data';
      notify(errorMsg, 'error');
    }
  };

  const handleClearDemo = async () => {
    if (!backendConnected) {
      setData({ expenses: [], income: [], budgets: [], savings_goals: [] });
      notify('Cleared demo data.');
      return;
    }
    try {
      const remote = await clearSampleDataApi();
      setData(remote);
      notify('Demo records removed from SQLite database.');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to clear demo data';
      notify(errorMsg, 'error');
    }
  };

  const budgetAlerts = useMemo(() => {
    const rows = getBudgetRows(data, period).filter(
      (item) => item.amount > 0 && ['caution', 'warning', 'exceeded'].includes(item.tier)
    );
    const summary = getSummary(data, period);
    const overall = data.budgets.find(
      (item) => item.period === period && item.category === 'Overall'
    );
    const overallStatus = budgetStatus(summary.expenseTotal, overall?.amount ?? 0);
    return rows.length + (overall && ['caution', 'warning', 'exceeded'].includes(overallStatus.tier) ? 1 : 0);
  }, [data, period]);

  return (
    <Shell
      activePage={page}
      setActivePage={setPage}
      period={period}
      setPeriod={setPeriod}
      onAdd={openAdd}
      alertCount={budgetAlerts}
      backendConnected={backendConnected}
      onSeedSampleData={handleSeedDemo}
      onClearSampleData={handleClearDemo}
    >
      {page === 'Dashboard' && (
        <Dashboard
          data={data}
          period={period}
          onAdd={openAdd}
          goTo={setPage}
          onAddGoal={() => setGoalDialog({})}
          onEditGoal={(goal) => setGoalDialog({ editing: goal })}
          onDeleteGoal={(goal) => setDeleteTarget({ kind: 'goal', goal })}
          onAddMoney={(goal) => setAddMoneyDialog({ goal })}
        />
      )}
      {(page === 'Expenses' || page === 'Income' || page === 'Transactions') && (
        <RecordsPage
          key={page}
          page={page}
          data={data}
          period={period}
          onAdd={openAdd}
          onEdit={openEdit}
          onDelete={(entry) => setDeleteTarget({ kind: 'record', entry })}
        />
      )}
      {page === 'Budgets' && (
        <BudgetsPage
          data={data}
          period={period}
          onAdd={() => setBudgetDialog({})}
          onCreate={saveBudget}
          onEdit={(budget) => setBudgetDialog({ editing: budget })}
          onDelete={(budget) => setDeleteTarget({ kind: 'budget', budget })}
        />
      )}
      {page === 'Savings Goals' && (
        <SavingsGoalsPage
          data={data}
          onAddGoal={() => setGoalDialog({})}
          onEditGoal={(goal) => setGoalDialog({ editing: goal })}
          onDeleteGoal={(goal) => setDeleteTarget({ kind: 'goal', goal })}
          onAddMoney={(goal) => setAddMoneyDialog({ goal })}
        />
      )}
      {page === 'Analytics' && <AnalyticsPage data={data} period={period} />}
      {page === 'Reports' && (
        <ReportsPage
          data={data}
          period={period}
          notify={(message) => notify(message, 'success')}
          backendConnected={backendConnected}
        />
      )}
      {entryDialog && (
        <EntryModal
          key={`${entryDialog.kind}-${entryDialog.editing?.id ?? 'new'}`}
          initialKind={entryDialog.kind}
          editing={entryDialog.editing}
          onClose={() => setEntryDialog(null)}
          onSave={saveEntry}
        />
      )}
      {budgetDialog && (
        <BudgetModal
          key={budgetDialog.editing?.id ?? 'new-budget'}
          period={period}
          editing={budgetDialog.editing}
          onClose={() => setBudgetDialog(null)}
          onSave={saveBudget}
        />
      )}
      {goalDialog && (
        <GoalModal
          key={goalDialog.editing?.id ?? 'new-goal'}
          editing={goalDialog.editing}
          onClose={() => setGoalDialog(null)}
          onSave={saveGoal}
        />
      )}
      {addMoneyDialog && (
        <AddMoneyModal
          key={`add-${addMoneyDialog.goal.id}`}
          goal={addMoneyDialog.goal}
          onClose={() => setAddMoneyDialog(null)}
          onAddMoney={handleAddMoney}
        />
      )}
      {deleteTarget && (
        <ConfirmDialog
          title={
            deleteTarget.kind === 'record'
              ? `Delete this ${deleteTarget.entry.kind}?`
              : deleteTarget.kind === 'budget'
              ? 'Remove this budget limit?'
              : `Delete goal "${deleteTarget.goal.goal_name}"?`
          }
          detail={
            deleteTarget.kind === 'record'
              ? `“${deleteTarget.entry.name}” will be removed from your database. This cannot be undone.`
              : deleteTarget.kind === 'budget'
              ? `The ${
                  deleteTarget.budget.category === 'Overall' ? 'overall' : deleteTarget.budget.category
                } limit for ${deleteTarget.budget.period} will be removed. Your transactions will stay as they are.`
              : `“${deleteTarget.goal.goal_name}” and all recorded progress will be removed. This cannot be undone.`
          }
          onCancel={() => setDeleteTarget(null)}
          onConfirm={confirmDelete}
        />
      )}
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </Shell>
  );
}
