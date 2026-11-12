import { useMemo, useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Coins,
  PiggyBank,
  Plus,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react';
import type { AppData, GoalStatus, SavingsGoal } from '../types';
import { formatMoney } from '../utils';
import { Button, EmptyState, PageTitle, Panel, ProgressBar } from '../components/ui';
import SavingsGoalCard from '../components/SavingsGoalCard';

export default function SavingsGoalsPage({
  data,
  onAddGoal,
  onEditGoal,
  onDeleteGoal,
  onAddMoney,
}: {
  data: AppData;
  onAddGoal: () => void;
  onEditGoal: (goal: SavingsGoal) => void;
  onDeleteGoal: (goal: SavingsGoal) => void;
  onAddMoney: (goal: SavingsGoal) => void;
}) {
  const [filter, setFilter] = useState<'All' | GoalStatus>('All');

  const goals = data.savings_goals || [];

  // Summary Metrics
  const summary = useMemo(() => {
    const totalGoals = goals.length;
    const totalTarget = goals.reduce((sum, g) => sum + g.target_amount, 0);
    const totalSaved = goals.reduce((sum, g) => sum + g.current_saved_amount, 0);
    const overallProgress = totalTarget > 0 ? (totalSaved / totalTarget) * 100 : 0;
    const completedCount = goals.filter((g) => g.status === 'Completed').length;
    const inProgressCount = goals.filter((g) => g.status === 'In Progress').length;
    const overdueCount = goals.filter((g) => g.status === 'Overdue').length;
    const remainingToTarget = Math.max(0, totalTarget - totalSaved);

    return {
      totalGoals,
      totalTarget,
      totalSaved,
      overallProgress,
      completedCount,
      inProgressCount,
      overdueCount,
      remainingToTarget,
    };
  }, [goals]);

  // Filtered Goals
  const filteredGoals = useMemo(() => {
    if (filter === 'All') return goals;
    return goals.filter((g) => g.status === filter);
  }, [goals, filter]);

  return (
    <div className="page-stack">
      <PageTitle
        eyebrow="DREAM & ACHIEVE"
        title="Savings Goals"
        description="Set financial targets, make contributions, and track your milestones"
        actions={
          <Button variant="primary" onClick={onAddGoal}>
            <Plus size={16} /> New savings goal
          </Button>
        }
      />

      {/* 4 Summary Cards */}
      <section className="summary-grid" aria-label="Savings Goals Summary">
        <article className="summary-card summary-violet">
          <div className="summary-card-top">
            <span>Total goals</span>
            <i>
              <Target size={17} strokeWidth={1.9} />
            </i>
          </div>
          <strong className="summary-value">{summary.totalGoals}</strong>
          <span className="summary-helper">
            {summary.completedCount} completed · {summary.inProgressCount} in progress
          </span>
          <div className="summary-card-bottom">
            <span>{summary.overdueCount > 0 ? `${summary.overdueCount} overdue` : 'All targets healthy'}</span>
            <span className="summary-mini-arrow">
              <ArrowRight size={13} />
            </span>
          </div>
        </article>

        <article className="summary-card summary-blue">
          <div className="summary-card-top">
            <span>Total target</span>
            <i>
              <PiggyBank size={17} strokeWidth={1.9} />
            </i>
          </div>
          <strong className="summary-value">{formatMoney(summary.totalTarget)}</strong>
          <span className="summary-helper">Across {summary.totalGoals} planned targets</span>
          <div className="summary-card-bottom">
            <span>{formatMoney(summary.remainingToTarget)} to go</span>
            <span className="summary-mini-arrow">
              <ArrowRight size={13} />
            </span>
          </div>
        </article>

        <article className="summary-card summary-green">
          <div className="summary-card-top">
            <span>Total saved</span>
            <i>
              <Coins size={17} strokeWidth={1.9} />
            </i>
          </div>
          <strong className="summary-value">{formatMoney(summary.totalSaved)}</strong>
          <span className="summary-helper">Explicitly contributed funds</span>
          <div className="summary-card-bottom">
            <span className="comparison-mini comparison-down">
              <TrendingUp size={13} />
              {summary.overallProgress.toFixed(1)}% of all targets
            </span>
            <span className="summary-mini-arrow">
              <ArrowRight size={13} />
            </span>
          </div>
        </article>

        <article className="summary-card summary-amber">
          <div className="summary-card-top">
            <span>Overall progress</span>
            <i>
              <Sparkles size={17} strokeWidth={1.9} />
            </i>
          </div>
          <strong className="summary-value">{summary.overallProgress.toFixed(1)}%</strong>
          <span className="summary-helper">
            {summary.completedCount} of {summary.totalGoals} goals achieved
          </span>
          <div className="summary-card-bottom" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '6px' }}>
            <ProgressBar value={summary.overallProgress} tier={summary.overallProgress >= 100 ? 'normal' : 'caution'} />
          </div>
        </article>
      </section>

      {/* Main Goals Panel */}
      <Panel
        title="Your savings milestones"
        description="Contribute towards individual goals whenever you save money"
        action={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="entry-kind-switch" style={{ margin: 0 }}>
              {(['All', 'In Progress', 'Completed', 'Overdue'] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={filter === tab ? 'entry-kind-active entry-kind-expense' : ''}
                  onClick={() => setFilter(tab)}
                  style={{ height: '30px', padding: '0 10px', fontSize: '11px' }}
                >
                  {tab === 'Completed' && <CheckCircle2 size={13} />}
                  {tab === 'Overdue' && <AlertCircle size={13} />}
                  {tab}
                  <small style={{ marginLeft: '4px', opacity: 0.75 }}>
                    (
                    {tab === 'All'
                      ? goals.length
                      : goals.filter((g) => g.status === tab).length}
                    )
                  </small>
                </button>
              ))}
            </div>
          </div>
        }
      >
        {filteredGoals.length > 0 ? (
          <div className="budget-cards-grid" style={{ marginTop: '12px' }}>
            {filteredGoals.map((goal) => (
              <SavingsGoalCard
                key={goal.id}
                goal={goal}
                onAddMoney={onAddMoney}
                onEdit={onEditGoal}
                onDelete={onDeleteGoal}
              />
            ))}
          </div>
        ) : (
          <div className="budget-empty-card" style={{ marginTop: '12px' }}>
            <EmptyState
              icon={<PiggyBank size={24} />}
              title={
                filter === 'All'
                  ? 'No savings goals created yet'
                  : `No ${filter.toLowerCase()} savings goals`
              }
              detail={
                filter === 'All'
                  ? 'Set a target for an emergency fund, new laptop, or vacation trip and start adding funds.'
                  : `You currently have no savings goals marked as ${filter}.`
              }
              action={
                <Button size="sm" onClick={onAddGoal}>
                  <Plus size={14} /> Create a savings goal
                </Button>
              }
            />
          </div>
        )}
      </Panel>
    </div>
  );
}
