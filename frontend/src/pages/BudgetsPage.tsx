import { useMemo } from 'react';
import { ArrowRight, Pencil, Plus, Target, Trash2, WalletCards } from 'lucide-react';
import type { AppData, Budget, Category } from '../types';
import { Button, EmptyState, IconButton, PageTitle, Panel, ProgressBar, StatusPill } from '../components/ui';
import { BudgetComparison } from '../components/Charts';
import { budgetStatus, createBudgetRows, formatMoney, formatPeriod, getSummary, CATEGORY_META } from '../utils';

export default function BudgetsPage({ data, period, onAdd, onEdit, onDelete, onCreate }: {
  data: AppData;
  period: string;
  onAdd: () => void;
  onEdit: (budget: Budget) => void;
  onDelete: (budget: Budget) => void;
  onCreate: (category: 'Overall' | Category, amount: number) => void;
}) {
  const summary = getSummary(data, period);
  const overall = data.budgets.find((item) => item.period === period && item.category === 'Overall');
  const overallStatus = budgetStatus(summary.expenseTotal, overall?.amount ?? 0);
  const categoryBudgets = data.budgets.filter((item) => item.period === period && item.category !== 'Overall').sort((a, b) => a.category.localeCompare(b.category));
  const chartData = useMemo(() => createBudgetRows(data, period).filter((item) => item.budget > 0 || item.spent > 0), [data, period]);
  const alerts = categoryBudgets.map((item) => {
    const spent = data.expenses.filter((entry) => entry.date.startsWith(period) && entry.category === item.category).reduce((sum, entry) => sum + entry.amount, 0);
    return { ...item, spent, ...budgetStatus(spent, item.amount) };
  }).filter((item) => ['caution', 'warning', 'exceeded'].includes(item.tier));
  if (overall && ['caution', 'warning', 'exceeded'].includes(overallStatus.tier)) alerts.unshift({ ...overall, spent: summary.expenseTotal, ...overallStatus });

  return <div className="page-stack">
    <PageTitle eyebrow="PLAN WITH INTENTION" title="Budgets" description={`Your monthly guardrails · ${formatPeriod(period)}`} actions={<Button variant="primary" onClick={onAdd}><Plus size={16} /> Set a limit</Button>} />
    <div className="budget-overview-grid"><section className={`overall-budget-card ${overallStatus.tier === 'exceeded' ? 'overall-budget-danger' : ''}`}><div className="overall-budget-top"><span className="overall-budget-icon"><Target size={19} /></span><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><StatusPill tier={overall?.amount ? overallStatus.tier : 'none'}>{overall?.amount ? overallStatus.label : 'No limit set'}</StatusPill>{overall?.amount ? <IconButton className="icon-button-danger" label="Remove overall budget" onClick={() => onDelete(overall)}><Trash2 size={14} /></IconButton> : null}</div></div><div className="eyebrow">OVERALL MONTHLY BUDGET</div><div className="overall-budget-amount">{overall?.amount ? formatMoney(overall.amount) : 'Set a monthly cap'}</div><p>{overall?.amount ? `${formatMoney(summary.expenseTotal)} spent so far` : 'Give your total monthly spending a simple guardrail.'}</p>{overall?.amount ? <><ProgressBar value={overallStatus.progress} tier={overallStatus.tier} /><div className="overall-budget-foot"><span>{overallStatus.utilization.toFixed(1)}% used</span><strong className={overallStatus.remaining < 0 ? 'amount-negative' : ''}>{overallStatus.remaining >= 0 ? `${formatMoney(overallStatus.remaining)} left` : `${formatMoney(Math.abs(overallStatus.remaining))} over`}</strong></div><button type="button" className="text-link" onClick={() => onEdit(overall)}>Adjust monthly cap <ArrowRight size={14} /></button></> : <Button variant="primary" size="sm" onClick={() => onCreate('Overall', 25000)}>Create overall cap</Button>}</section>
      <section className="budget-overview-note"><div className="budget-note-icon"><WalletCards size={20} /></div><div><span className="eyebrow">A HELPFUL RHYTHM</span><h3>Build a plan that feels like yours.</h3><p>Budget alerts show up as you reach 75%, 90%, and 100% of your chosen limit. Adjust them whenever life changes.</p></div><div className="budget-thresholds"><span className="threshold-normal"><i /> Under 75% <small>On track</small></span><span className="threshold-caution"><i /> 75%+ <small>Pay attention</small></span><span className="threshold-warning"><i /> 90%+ <small>Getting close</small></span><span className="threshold-exceeded"><i /> 100%+ <small>Over budget</small></span></div></section></div>
    {alerts.length > 0 && <section className="budget-alert-list"><div className="budget-alert-heading"><span className="alert-dot" /><strong>{alerts.length} budget {alerts.length === 1 ? 'nudge' : 'nudges'} for this month</strong></div>{alerts.slice(0, 3).map((item) => <div className={`budget-alert-row alert-tier-${item.tier}`} key={`${item.category}-${item.id}`}><span className="budget-alert-category">{item.category === 'Overall' ? '◉' : CATEGORY_META[item.category]?.icon ?? '◌'} {item.category === 'Overall' ? 'Overall budget' : item.category}</span><span>{item.utilization.toFixed(0)}% used</span><strong>{item.tier === 'exceeded' ? `${formatMoney(Math.abs(item.remaining))} over` : `${formatMoney(Math.max(item.remaining, 0))} left`}</strong></div>)}</section>}
    <Panel title="Category budgets" description="Compare limits with actual spending. Limits are specific to the selected month." action={<span className="budget-count">{categoryBudgets.length} {categoryBudgets.length === 1 ? 'limit' : 'limits'}</span>}><div className="budget-cards-grid">{categoryBudgets.map((item) => {
      const spent = data.expenses.filter((entry) => entry.date.startsWith(period) && entry.category === item.category).reduce((sum, entry) => sum + entry.amount, 0);
      const status = budgetStatus(spent, item.amount);
      return <article className="category-budget-card" key={item.id}><div className="category-budget-card-top"><span className="category-mark" style={{ '--category-color': CATEGORY_META[item.category]?.color ?? '#9098ac' } as React.CSSProperties}>{CATEGORY_META[item.category]?.icon ?? '◌'}</span><div className="category-budget-card-heading"><strong>{item.category}</strong><span>{status.label}</span></div><div className="category-budget-actions"><IconButton label={`Edit ${item.category} budget`} onClick={() => onEdit(item)}><Pencil size={14} /></IconButton><IconButton className="icon-button-danger" label={`Delete ${item.category} budget`} onClick={() => onDelete(item)}><Trash2 size={14} /></IconButton></div></div><div className="category-budget-numbers"><strong>{formatMoney(spent)} <i>spent</i></strong><span>of {formatMoney(item.amount)}</span></div><ProgressBar value={status.progress} tier={status.tier} /><div className="category-budget-foot"><StatusPill tier={status.tier}>{status.utilization.toFixed(0)}%</StatusPill><span className={status.remaining < 0 ? 'amount-negative' : ''}>{status.remaining >= 0 ? `${formatMoney(status.remaining)} left` : `${formatMoney(Math.abs(status.remaining))} over`}</span></div></article>;
    })}{categoryBudgets.length === 0 && <div className="budget-empty-card"><EmptyState icon={<Target size={22} />} title="No category limits yet" detail="Start with one category you want to keep in view." action={<Button size="sm" onClick={onAdd}><Plus size={14} /> Add category limit</Button>} /></div>}</div></Panel>
    <Panel title="Budget versus actual" description="A side-by-side view of your category plan and spend"><BudgetComparison data={chartData} /></Panel>
  </div>;
}
