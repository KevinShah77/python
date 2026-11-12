import { useMemo } from 'react';
import {
  ArrowRight,
  ArrowUpRight,
  CircleDollarSign,
  Clock3,
  PiggyBank,
  Plus,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
  WalletCards,
} from 'lucide-react';
import type { AppData, EntryKind, SavingsGoal } from '../types';
import {
  budgetStatus,
  formatDate,
  formatMoney,
  formatPeriod,
  getBudgetRows,
  getCategoryBreakdown,
  getInsights,
  getMonthComparison,
  getMonthTransactions,
  getMonthlyTrend,
  getSummary,
  CATEGORY_META,
} from '../utils';
import { CategoryDonut, MonthlyCashflow } from '../components/Charts';
import { Button, EmptyState, Panel, ProgressBar, StatusPill } from '../components/ui';
import SavingsGoalCard from '../components/SavingsGoalCard';

export default function Dashboard({
  data,
  period,
  onAdd,
  goTo,
  onAddGoal,
  onEditGoal,
  onDeleteGoal,
  onAddMoney,
}: {
  data: AppData;
  period: string;
  onAdd: (kind: EntryKind) => void;
  goTo: (page: 'Transactions' | 'Budgets' | 'Analytics' | 'Savings Goals') => void;
  onAddGoal?: () => void;
  onEditGoal?: (goal: SavingsGoal) => void;
  onDeleteGoal?: (goal: SavingsGoal) => void;
  onAddMoney?: (goal: SavingsGoal) => void;
}) {
  const summary = getSummary(data, period);
  const compare = getMonthComparison(data, period);
  const breakdown = getCategoryBreakdown(data, period);
  const trend = getMonthlyTrend(data, period, 6);
  const transactions = getMonthTransactions(data, period).slice(0, 5);
  const categoryBudgets = getBudgetRows(data, period);
  const overallBudget = data.budgets.find((item) => item.period === period && item.category === 'Overall');
  const overallStatus = budgetStatus(summary.expenseTotal, overallBudget?.amount ?? 0);
  const budgetAlerts = useMemo(() => {
    const alerts = categoryBudgets.filter(
      (item) => item.amount > 0 && ['caution', 'warning', 'exceeded'].includes(item.tier)
    );
    if (overallBudget && ['caution', 'warning', 'exceeded'].includes(overallStatus.tier)) {
      alerts.unshift({
        ...overallStatus,
        category: 'Overall' as const,
        spent: summary.expenseTotal,
        amount: overallBudget.amount,
        id: overallBudget.id,
        period: overallBudget.period,
      });
    }
    return alerts;
  }, [categoryBudgets, overallBudget, overallStatus, summary.expenseTotal]);
  const insights = getInsights(data, period);
  const changedUp = compare.change > 0;
  const savingPositive = summary.balance >= 0;
  const greeting =
    new Date().getHours() < 12
      ? 'Good morning'
      : new Date().getHours() < 18
      ? 'Good afternoon'
      : 'Good evening';

  // Savings Goals Summary
  const goals = data.savings_goals || [];
  const savingsSummary = useMemo(() => {
    const totalGoals = goals.length;
    const totalTarget = goals.reduce((sum, g) => sum + g.target_amount, 0);
    const totalSaved = goals.reduce((sum, g) => sum + g.current_saved_amount, 0);
    const overallProgress = totalTarget > 0 ? (totalSaved / totalTarget) * 100 : 0;
    const completedCount = goals.filter((g) => g.status === 'Completed').length;
    return { totalGoals, totalTarget, totalSaved, overallProgress, completedCount };
  }, [goals]);

  const statCards = [
    {
      title: 'Total income',
      value: summary.incomeTotal,
      helper: 'Money in this month',
      icon: WalletCards,
      tone: 'green',
      sub: summary.income.length ? `${summary.income.length} income entries` : 'No income added yet',
    },
    {
      title: 'Total expenses',
      value: summary.expenseTotal,
      helper: 'Money out this month',
      icon: ArrowUpRight,
      tone: 'blue',
      sub: `${summary.expenses.length} expense entries`,
    },
    {
      title: 'Remaining balance',
      value: summary.balance,
      helper: savingPositive ? `${summary.savingsRate.toFixed(1)}% of income retained` : 'Expenses are above income',
      icon: CircleDollarSign,
      tone: savingPositive ? 'violet' : 'red',
      sub: savingPositive ? 'Available after expenses' : 'A deficit to address',
    },
    {
      title: 'Monthly budget',
      value: overallBudget?.amount ?? 0,
      helper: overallBudget ? `${overallStatus.utilization.toFixed(1)}% used` : 'Set a spending limit',
      icon: Target,
      tone: overallStatus.tier === 'exceeded' ? 'red' : 'amber',
      sub: overallBudget
        ? `${formatMoney(Math.max(overallStatus.remaining, 0))} left to plan`
        : 'No overall cap set',
    },
  ];

  return (
    <div className="page-stack">
      <div className="welcome-row">
        <div>
          <div className="eyebrow">YOUR MONEY, IN FOCUS</div>
          <h1>{greeting}.</h1>
          <p>
            Here’s your financial picture for <strong>{formatPeriod(period)}</strong>.
          </p>
        </div>
        <div className="welcome-actions">
          <Button variant="secondary" onClick={() => goTo('Analytics')}>
            <Sparkles size={16} /> See insights
          </Button>
          <Button variant="primary" onClick={() => onAdd('expense')}>
            <span className="plus-light">＋</span> Add transaction
          </Button>
        </div>
      </div>

      <section className="summary-grid" aria-label="Monthly summary">
        {statCards.map(({ title, value, helper, icon: Icon, tone, sub }) => (
          <article className={`summary-card summary-${tone}`} key={title}>
            <div className="summary-card-top">
              <span>{title}</span>
              <i>
                <Icon size={17} strokeWidth={1.9} />
              </i>
            </div>
            <strong className="summary-value">
              {title === 'Monthly budget' && !overallBudget ? 'Not set' : formatMoney(value)}
            </strong>
            <span className="summary-helper">{sub}</span>
            <div className="summary-card-bottom">
              <span>{helper}</span>
              {title === 'Total expenses' ? (
                <span className={`comparison-mini ${changedUp ? 'comparison-up' : 'comparison-down'}`}>
                  {changedUp ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                  {Math.abs(compare.percent).toFixed(1)}%
                </span>
              ) : (
                <span className="summary-mini-arrow">
                  <ArrowRight size={13} />
                </span>
              )}
            </div>
          </article>
        ))}
      </section>

      <section className="dashboard-highlight">
        <div className="highlight-copy">
          <div className="highlight-kicker">
            <span className="highlight-spark">✦</span> YOUR MONTHLY PACE
          </div>
          <h2>
            {overallBudget
              ? overallStatus.tier === 'exceeded'
                ? 'Your budget needs a reset.'
                : overallStatus.utilization >= 75
                ? 'You’re getting close to your limit.'
                : 'You’re on a steady track.'
              : 'Give your month a gentle guardrail.'}
          </h2>
          <p>
            {overallBudget
              ? `${formatMoney(summary.expenseTotal)} spent out of ${formatMoney(overallBudget.amount)}. ${
                  overallStatus.remaining >= 0
                    ? `${formatMoney(overallStatus.remaining)} remains in your plan.`
                    : `${formatMoney(Math.abs(overallStatus.remaining))} above your plan.`
                }`
              : 'Set an overall spending cap to see your monthly pace and get timely nudges.'}
          </p>
          <button type="button" className="highlight-link" onClick={() => goTo('Budgets')}>
            {overallBudget ? 'Review my budget' : 'Set a budget'} <ArrowRight size={15} />
          </button>
        </div>
        <div className="highlight-ring-wrap">
          <div
            className="highlight-ring"
            style={{ '--ring-value': `${Math.min(overallStatus.utilization, 100)}%` } as React.CSSProperties}
          >
            <div>
              <strong>{overallBudget ? `${Math.round(overallStatus.utilization)}%` : '—'}</strong>
              <span>of budget</span>
            </div>
          </div>
          <div className="highlight-ring-foot">
            <i /> {overallBudget ? overallStatus.label : 'Not set yet'}
          </div>
        </div>
        <div className="highlight-orb highlight-orb-one" />
        <div className="highlight-orb highlight-orb-two" />
      </section>

      {(budgetAlerts.length > 0 || summary.balance < 0) && (
        <div className="alert-strip">
          <div className="alert-symbol">{summary.balance < 0 ? '!' : '↗'}</div>
          <div>
            <strong>
              {summary.balance < 0
                ? 'Cash-flow heads-up'
                : `${budgetAlerts[0].category === 'Overall' ? 'Overall budget' : budgetAlerts[0].category} is ${
                    budgetAlerts[0].tier === 'exceeded'
                      ? 'over budget'
                      : budgetAlerts[0].tier === 'warning'
                      ? 'close to its limit'
                      : 'in the caution zone'
                  }`}
            </strong>
            <p>
              {summary.balance < 0
                ? `Outflow is ${formatMoney(Math.abs(summary.balance))} ahead of recorded income for ${formatPeriod(
                    period
                  )}.`
                : `${budgetAlerts[0].utilization.toFixed(0)}% used · ${
                    budgetAlerts[0].remaining >= 0
                      ? `${formatMoney(budgetAlerts[0].remaining)} left in the ${
                          budgetAlerts[0].category === 'Overall' ? 'overall' : budgetAlerts[0].category
                        } limit.`
                      : `${formatMoney(Math.abs(budgetAlerts[0].remaining))} over the ${
                          budgetAlerts[0].category === 'Overall' ? 'overall' : budgetAlerts[0].category
                        } limit.`
                  }`}
            </p>
          </div>
          <button type="button" onClick={() => goTo('Budgets')}>
            Review <ArrowRight size={14} />
          </button>
        </div>
      )}

      {/* Cash Flow and Category Breakdown */}
      <div className="dashboard-two-col">
        <Panel
          title="Cash flow"
          description="Income and expenses over the last six months"
          className="chart-panel"
          action={
            <button type="button" className="text-link" onClick={() => goTo('Analytics')}>
              Full report <ArrowRight size={14} />
            </button>
          }
        >
          <MonthlyCashflow data={trend} />
          <div className="chart-legend-note">
            <span>
              <i className="legend-dot legend-income" /> Income
            </span>
            <span>
              <i className="legend-dot legend-expense" /> Expenses
            </span>
            <small>INR · monthly totals</small>
          </div>
        </Panel>

        <Panel
          title="Where it goes"
          description={`${formatMoney(summary.expenseTotal)} across ${breakdown.length} categories`}
          className="chart-panel"
          action={
            <button type="button" className="text-link" onClick={() => goTo('Transactions')}>
              Details <ArrowRight size={14} />
            </button>
          }
        >
          {breakdown.length ? (
            <CategoryDonut data={breakdown} />
          ) : (
            <EmptyState
              icon="◌"
              title="No expenses to map"
              detail="Add an expense and your category mix will appear here."
              action={<Button size="sm" onClick={() => onAdd('expense')}>Add an expense</Button>}
            />
          )}
        </Panel>
      </div>

      {/* Dedicated Savings Goals Section */}
      <Panel
        title="Savings goals"
        description={
          goals.length > 0
            ? `${savingsSummary.completedCount} of ${savingsSummary.totalGoals} completed · ${formatMoney(savingsSummary.totalSaved)} saved`
            : 'Set financial targets and track your contributions'
        }
        action={
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {onAddGoal && (
              <Button size="sm" variant="secondary" onClick={onAddGoal}>
                <Plus size={14} /> New goal
              </Button>
            )}
            <button type="button" className="text-link" onClick={() => goTo('Savings Goals')}>
              View all ({goals.length}) <ArrowRight size={14} />
            </button>
          </div>
        }
      >
        {goals.length > 0 ? (
          <div>
            {/* Summary Mini-Strip */}
            <div className="record-overview-strip" style={{ marginBottom: '14px' }}>
              <div>
                <i className="overview-dot overview-dot-in" />
                <span>Total saved:</span>
                <strong>{formatMoney(savingsSummary.totalSaved)}</strong>
              </div>
              <div className="overview-separator" />
              <div>
                <i className="overview-dot overview-dot-out" />
                <span>Target:</span>
                <strong>{formatMoney(savingsSummary.totalTarget)}</strong>
              </div>
              <div className="overview-separator" />
              <div>
                <i className="overview-dot overview-dot-net" />
                <span>Progress:</span>
                <strong>{savingsSummary.overallProgress.toFixed(1)}%</strong>
              </div>
              <span className="overview-strip-tail">
                {savingsSummary.totalGoals} {savingsSummary.totalGoals === 1 ? 'goal' : 'goals'} tracked
              </span>
            </div>

            {/* Goals Grid on Dashboard */}
            <div className="budget-cards-grid">
              {goals.slice(0, 3).map((goal) => (
                <SavingsGoalCard
                  key={goal.id}
                  goal={goal}
                  onAddMoney={onAddMoney || (() => {})}
                  onEdit={onEditGoal || (() => {})}
                  onDelete={onDeleteGoal || (() => {})}
                />
              ))}
            </div>
          </div>
        ) : (
          <EmptyState
            icon={<PiggyBank size={24} />}
            title="No savings goals yet"
            detail="Create a savings goal for an emergency fund, gadget, or vacation and watch your money grow."
            action={
              onAddGoal && (
                <Button size="sm" onClick={onAddGoal}>
                  <Plus size={14} /> Set a savings goal
                </Button>
              )
            }
          />
        )}
      </Panel>

      {/* Category Budgets & Recent Activity */}
      <div className="dashboard-bottom-grid">
        <Panel
          title="Category budgets"
          description="A quick look at your category limits"
          action={
            <button type="button" className="text-link" onClick={() => goTo('Budgets')}>
              Manage <ArrowRight size={14} />
            </button>
          }
        >
          <div className="category-budget-list">
            {categoryBudgets
              .filter((item) => item.amount > 0)
              .slice(0, 4)
              .map((item) => (
                <div className="category-budget-row" key={item.category}>
                  <div className="category-budget-leading">
                    <span
                      className="category-mark"
                      style={
                        {
                          '--category-color': CATEGORY_META[item.category]?.color ?? '#9098ac',
                        } as React.CSSProperties
                      }
                    >
                      {CATEGORY_META[item.category]?.icon ?? '◌'}
                    </span>
                    <div>
                      <strong>{item.category}</strong>
                      <span>
                        {formatMoney(item.spent)} <i>of</i> {formatMoney(item.amount)}
                      </span>
                    </div>
                  </div>
                  <div className="category-budget-trailing">
                    <StatusPill tier={item.tier}>{item.utilization.toFixed(0)}%</StatusPill>
                    <ProgressBar value={item.progress} tier={item.tier} />
                  </div>
                </div>
              ))}
          </div>
          {categoryBudgets.filter((item) => item.amount > 0).length === 0 && (
            <EmptyState
              title="No category limits yet"
              detail="Add a category budget for a helpful spending guardrail."
              action={<Button size="sm" onClick={() => goTo('Budgets')}>Set limits</Button>}
            />
          )}
        </Panel>

        <Panel
          title="Recent activity"
          description={`Your latest entries in ${formatPeriod(period)}`}
          action={
            <button type="button" className="text-link" onClick={() => goTo('Transactions')}>
              View all <ArrowRight size={14} />
            </button>
          }
        >
          <div className="recent-list">
            {transactions.length ? (
              transactions.map((item) => (
                <div className="recent-item" key={item.id}>
                  <span
                    className={`recent-icon ${item.kind === 'income' ? 'recent-income' : ''}`}
                    style={
                      item.kind === 'expense'
                        ? ({
                            '--category-color': CATEGORY_META[item.categoryOrSource]?.color ?? '#9098ac',
                          } as React.CSSProperties)
                        : undefined
                    }
                  >
                    {item.kind === 'income' ? '↙' : CATEGORY_META[item.categoryOrSource]?.icon ?? '◌'}
                  </span>
                  <div className="recent-copy">
                    <strong>{item.name}</strong>
                    <span>
                      {item.categoryOrSource} · {formatDate(item.date)}
                    </span>
                  </div>
                  <strong className={`recent-amount ${item.kind === 'income' ? 'amount-positive' : ''}`}>
                    {item.kind === 'income' ? '+' : '−'}
                    {formatMoney(item.amount)}
                  </strong>
                </div>
              ))
            ) : (
              <EmptyState
                icon={<Clock3 size={23} />}
                title="Nothing recorded this month"
                detail="Once you start logging activity, it will show here."
                action={<Button size="sm" onClick={() => onAdd('expense')}>Add an entry</Button>}
              />
            )}
          </div>
        </Panel>
      </div>

      {insights.length > 0 && (
        <div className="insight-strip">
          <div className={`insight-icon insight-${insights[0].kind}`}>
            <Sparkles size={17} />
          </div>
          <div>
            <span className="eyebrow">A SMALL NUDGE</span>
            <strong>{insights[0].title}</strong>
            <p>
              {insights[0].detail} {insights[0].tip}
            </p>
          </div>
          <button type="button" onClick={() => goTo('Analytics')}>
            More insights <ArrowRight size={14} />
          </button>
        </div>
      )}

      <div className="dashboard-footnote">
        <span>
          <Clock3 size={14} /> Last updated just now
        </span>
        <button type="button" onClick={() => goTo('Transactions')}>
          All transactions <ArrowRight size={13} />
        </button>
      </div>
    </div>
  );
}
