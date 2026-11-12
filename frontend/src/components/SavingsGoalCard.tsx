import { CalendarDays, Coins, CheckCircle2, AlertCircle, Pencil, PiggyBank, Trash2 } from 'lucide-react';
import type { SavingsGoal } from '../types';
import { formatDate, formatMoney } from '../utils';
import { Button, IconButton, ProgressBar, StatusPill } from './ui';

export default function SavingsGoalCard({
  goal,
  onAddMoney,
  onEdit,
  onDelete,
}: {
  goal: SavingsGoal;
  onAddMoney: (goal: SavingsGoal) => void;
  onEdit: (goal: SavingsGoal) => void;
  onDelete: (goal: SavingsGoal) => void;
}) {
  const isCompleted = goal.status === 'Completed';
  const isOverdue = goal.status === 'Overdue';

  const tier = isCompleted ? 'normal' : isOverdue ? 'exceeded' : goal.progress_percentage >= 75 ? 'caution' : 'normal';

  const iconBg = isCompleted ? '#ecf8f2' : isOverdue ? '#fbefef' : '#eff4ff';
  const iconColor = isCompleted ? '#2a9a70' : isOverdue ? '#cc5f70' : '#3f5ce8';

  return (
    <article
      className="category-budget-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        minHeight: '215px',
        border: isCompleted ? '1px solid #ccebd7' : isOverdue ? '1px solid #f6d1d4' : undefined,
      }}
    >
      <div>
        {/* Top Header */}
        <div className="category-budget-card-top" style={{ marginBottom: '10px' }}>
          <span
            className="category-mark"
            style={{
              background: iconBg,
              color: iconColor,
              borderColor: 'transparent',
            }}
          >
            {isCompleted ? <CheckCircle2 size={17} /> : isOverdue ? <AlertCircle size={17} /> : <PiggyBank size={17} />}
          </span>

          <div className="category-budget-card-heading" style={{ flex: 1, minWidth: 0 }}>
            <strong style={{ fontSize: '13px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {goal.goal_name}
            </strong>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px' }}>
              <CalendarDays size={12} />
              Target: {formatDate(goal.target_date, { day: 'numeric', month: 'short', year: 'numeric' })}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <StatusPill tier={tier}>{goal.status}</StatusPill>
            <IconButton label={`Edit ${goal.goal_name}`} onClick={() => onEdit(goal)}>
              <Pencil size={13} />
            </IconButton>
            <IconButton className="icon-button-danger" label={`Delete ${goal.goal_name}`} onClick={() => onDelete(goal)}>
              <Trash2 size={13} />
            </IconButton>
          </div>
        </div>

        {/* Description if present */}
        {goal.description && (
          <p
            style={{
              margin: '0 0 10px',
              color: '#828ba0',
              fontSize: '11px',
              lineHeight: 1.4,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {goal.description}
          </p>
        )}

        {/* Financial Amounts */}
        <div className="category-budget-numbers" style={{ marginBottom: '8px' }}>
          <strong>
            {formatMoney(goal.current_saved_amount)} <i>saved</i>
          </strong>
          <span>of {formatMoney(goal.target_amount)}</span>
        </div>

        {/* Progress Bar */}
        <ProgressBar value={goal.progress_percentage} tier={tier} />

        {/* Status Foot */}
        <div className="category-budget-foot" style={{ marginTop: '8px', marginBottom: '14px' }}>
          <span style={{ fontWeight: 700, color: iconColor }}>
            {goal.progress_percentage.toFixed(1)}% completed
          </span>
          <span className={goal.remaining_amount <= 0 ? 'amount-positive' : isOverdue ? 'amount-negative' : ''}>
            {goal.remaining_amount <= 0
              ? '✓ Target reached!'
              : `${formatMoney(goal.remaining_amount)} remaining`}
          </span>
        </div>
      </div>

      {/* Action Button */}
      <div style={{ paddingTop: '10px', borderTop: '1px solid #f1f2f6' }}>
        <Button
          variant={isCompleted ? 'secondary' : 'primary'}
          size="sm"
          style={{ width: '100%' }}
          onClick={() => onAddMoney(goal)}
        >
          <Coins size={14} />
          {isCompleted ? 'Add extra savings' : 'Add money'}
        </Button>
      </div>
    </article>
  );
}
