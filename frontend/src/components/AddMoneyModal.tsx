import { useState, type FormEvent } from 'react';
import { Coins, Sparkles, X } from 'lucide-react';
import type { SavingsGoal } from '../types';
import { formatMoney } from '../utils';
import { Button, IconButton, ProgressBar, StatusPill } from './ui';

export default function AddMoneyModal({
  goal,
  onClose,
  onAddMoney,
}: {
  goal: SavingsGoal;
  onClose: () => void;
  onAddMoney: (goalId: number, amount: number) => Promise<void> | void;
}) {
  const [amount, setAmount] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const remaining = Math.max(0, goal.remaining_amount);
  const isAlreadyCompleted = goal.status === 'Completed';

  const quickAmounts = [500, 1000, 2000, 5000].filter((val) => val <= (remaining || 10000));

  const handleChipClick = (val: number) => {
    setAmount(String(val));
    setError('');
  };

  const handleFillRemaining = () => {
    if (remaining > 0) {
      setAmount(String(remaining));
      setError('');
    }
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const val = Number(amount);
    if (!Number.isFinite(val) || val <= 0) {
      setError('Please enter an amount strictly greater than ₹0.');
      return;
    }
    if (val > 50_000_000) {
      setError('Deposit amount cannot exceed ₹5,00,00,000.');
      return;
    }

    setError('');
    setSubmitting(true);
    try {
      await onAddMoney(goal.id, val);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add money.';
      setError(msg);
      setSubmitting(false);
    }
  };

  // Preview projected progress
  const inputNum = Number(amount) || 0;
  const projectedSaved = goal.current_saved_amount + inputNum;
  const projectedProgress = Math.min(
    100,
    goal.target_amount > 0 ? (projectedSaved / goal.target_amount) * 100 : 0
  );
  const willComplete = !isAlreadyCompleted && projectedSaved >= goal.target_amount;

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !submitting) onClose();
      }}
    >
      <section className="dialog budget-dialog" role="dialog" aria-modal="true" aria-labelledby="add-money-title">
        <div className="dialog-topline">
          <div className="dialog-title-icon" style={{ background: '#ecf8f2', color: '#2a9a70' }}>
            <Coins size={19} />
          </div>
          <IconButton label="Close dialog" onClick={onClose} disabled={submitting}>
            <X size={18} />
          </IconButton>
        </div>

        <div className="dialog-heading">
          <div className="eyebrow">SAVINGS CONTRIBUTION</div>
          <h2 id="add-money-title">Add money to “{goal.goal_name}”</h2>
          <p>Record your explicit contribution toward this savings goal.</p>
        </div>

        {/* Current Goal Status Card */}
        <div
          style={{
            padding: '12px 14px',
            borderRadius: '9px',
            background: '#f8fafc',
            border: '1px solid #eef2f6',
            marginBottom: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#334155' }}>{goal.goal_name}</span>
            <StatusPill tier={goal.status === 'Completed' ? 'normal' : goal.status === 'Overdue' ? 'exceeded' : 'caution'}>
              {goal.status}
            </StatusPill>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', fontSize: '11px' }}>
            <div>
              <span style={{ display: 'block', color: '#94a3b8', fontSize: '10px' }}>Target</span>
              <strong style={{ color: '#1e293b' }}>{formatMoney(goal.target_amount)}</strong>
            </div>
            <div>
              <span style={{ display: 'block', color: '#94a3b8', fontSize: '10px' }}>Current</span>
              <strong style={{ color: '#2563eb' }}>{formatMoney(goal.current_saved_amount)}</strong>
            </div>
            <div>
              <span style={{ display: 'block', color: '#94a3b8', fontSize: '10px' }}>Remaining</span>
              <strong style={{ color: remaining > 0 ? '#d97706' : '#16a34a' }}>
                {remaining > 0 ? formatMoney(remaining) : 'Goal Reached!'}
              </strong>
            </div>
          </div>

          <div style={{ marginTop: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748b', marginBottom: '4px' }}>
              <span>Progress</span>
              <strong>{inputNum > 0 ? `${projectedProgress.toFixed(1)}% (projected)` : `${goal.progress_percentage.toFixed(1)}%`}</strong>
            </div>
            <ProgressBar
              value={inputNum > 0 ? projectedProgress : goal.progress_percentage}
              tier={willComplete || isAlreadyCompleted ? 'normal' : 'caution'}
            />
          </div>
        </div>

        {willComplete && (
          <div
            style={{
              padding: '9px 12px',
              borderRadius: '8px',
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              color: '#15803d',
              fontSize: '11px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginBottom: '14px',
            }}
          >
            <Sparkles size={16} />
            <span>This contribution will complete your savings goal!</span>
          </div>
        )}

        <form onSubmit={submit} noValidate>
          <label className="field">
            <span>
              Amount to contribute <i>*</i>
            </span>
            <span className="amount-input">
              <span>₹</span>
              <input
                autoFocus
                type="number"
                inputMode="decimal"
                min="1"
                max="50000000"
                step="50"
                value={amount}
                onChange={(e) => {
                  setAmount(e.target.value);
                  setError('');
                }}
                placeholder="e.g. 5,000"
                disabled={submitting}
              />
            </span>
          </label>

          {/* Quick preset chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' }}>
            {quickAmounts.map((q) => (
              <button
                key={q}
                type="button"
                className="button button-secondary button-sm"
                style={{ fontSize: '10px', padding: '0 8px', height: '28px' }}
                onClick={() => handleChipClick(q)}
                disabled={submitting}
              >
                +₹{q.toLocaleString('en-IN')}
              </button>
            ))}
            {remaining > 0 && (
              <button
                type="button"
                className="button button-secondary button-sm"
                style={{
                  fontSize: '10px',
                  padding: '0 8px',
                  height: '28px',
                  borderColor: '#bbf7d0',
                  color: '#16a34a',
                }}
                onClick={handleFillRemaining}
                disabled={submitting}
              >
                Complete Goal ({formatMoney(remaining)})
              </button>
            )}
          </div>

          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}

          <div className="dialog-actions">
            <Button onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? 'Adding...' : 'Add money'}
            </Button>
          </div>
        </form>
      </section>
    </div>
  );
}
