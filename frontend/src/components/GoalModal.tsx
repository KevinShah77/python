import { useState, type FormEvent } from 'react';
import { CalendarDays, PiggyBank, X } from 'lucide-react';
import type { SavingsGoal } from '../types';
import { Button, IconButton } from './ui';

export default function GoalModal({
  editing,
  onClose,
  onSave,
}: {
  editing?: SavingsGoal;
  onClose: () => void;
  onSave: (
    goal: {
      goal_name: string;
      target_amount: number;
      target_date: string;
      description: string;
      current_saved_amount?: number;
    },
    goalId?: number
  ) => void;
}) {
  const [goalName, setGoalName] = useState(editing?.goal_name ?? '');
  const [targetAmount, setTargetAmount] = useState(editing ? String(editing.target_amount) : '');
  const [savedAmount, setSavedAmount] = useState(editing ? String(editing.current_saved_amount) : '0');
  const [targetDate, setTargetDate] = useState(
    editing?.target_date ??
      new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  );
  const [description, setDescription] = useState(editing?.description ?? '');
  const [error, setError] = useState('');

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanName = goalName.trim();
    if (!cleanName) {
      setError('Please provide a goal name.');
      return;
    }
    if (cleanName.length > 100) {
      setError('Goal name must be 100 characters or fewer.');
      return;
    }

    const tVal = Number(targetAmount);
    if (!Number.isFinite(tVal) || tVal <= 0) {
      setError('Target amount must be strictly greater than ₹0.');
      return;
    }
    if (tVal > 100_000_000) {
      setError('Target amount cannot exceed ₹10,00,00,000 (10 Crores).');
      return;
    }

    const sVal = Number(savedAmount || 0);
    if (!Number.isFinite(sVal) || sVal < 0) {
      setError('Current saved amount cannot be negative.');
      return;
    }
    if (sVal > 100_000_000) {
      setError('Saved amount cannot exceed ₹10,00,00,000 (10 Crores).');
      return;
    }

    if (!targetDate || !/^\d{4}-\d{2}-\d{2}$/.test(targetDate) || Number.isNaN(Date.parse(`${targetDate}T00:00:00`))) {
      setError('Please select a valid target date (YYYY-MM-DD).');
      return;
    }

    setError('');
    onSave(
      {
        goal_name: cleanName,
        target_amount: tVal,
        target_date: targetDate,
        description: description.trim(),
        current_saved_amount: sVal,
      },
      editing?.id
    );
  };

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section className="dialog budget-dialog" role="dialog" aria-modal="true" aria-labelledby="goal-dialog-title">
        <div className="dialog-topline">
          <div className="dialog-title-icon" style={{ background: '#ecf8f2', color: '#2a9a70' }}>
            <PiggyBank size={19} />
          </div>
          <IconButton label="Close dialog" onClick={onClose}>
            <X size={18} />
          </IconButton>
        </div>

        <div className="dialog-heading">
          <div className="eyebrow">{editing ? 'EDIT SAVINGS GOAL' : 'CREATE SAVINGS GOAL'}</div>
          <h2 id="goal-dialog-title">{editing ? 'Adjust your goal' : 'Set a savings target'}</h2>
          <p>
            {editing
              ? 'Update target amount, completion date, or notes.'
              : 'Every milestone starts with a plan. Define what you want to achieve.'}
          </p>
        </div>

        <form onSubmit={submit} noValidate>
          <label className="field">
            <span>
              Goal name <i>*</i>
            </span>
            <input
              autoFocus
              type="text"
              value={goalName}
              onChange={(e) => setGoalName(e.target.value)}
              placeholder="e.g. Emergency Fund, New Laptop, Goa Trip"
              maxLength={100}
            />
          </label>

          <div className="form-row">
            <label className="field">
              <span>
                Target amount <i>*</i>
              </span>
              <span className="amount-input">
                <span>₹</span>
                <input
                  type="number"
                  inputMode="decimal"
                  min="1"
                  max="100000000"
                  step="500"
                  value={targetAmount}
                  onChange={(e) => setTargetAmount(e.target.value)}
                  placeholder="50,000"
                />
              </span>
              <small>Up to ₹10 Crore</small>
            </label>

            <label className="field">
              <span>{editing ? 'Already saved' : 'Starting amount'}</span>
              <span className="amount-input">
                <span>₹</span>
                <input
                  type="number"
                  inputMode="decimal"
                  min="0"
                  max="100000000"
                  step="100"
                  value={savedAmount}
                  onChange={(e) => setSavedAmount(e.target.value)}
                  placeholder="0"
                />
              </span>
              <small>{editing ? 'Total saved to date' : 'Optional initial deposit'}</small>
            </label>
          </div>

          <label className="field">
            <span>
              Target completion date <i>*</i>
            </span>
            <span className="date-field">
              <CalendarDays size={15} />
              <input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
              />
            </span>
          </label>

          <label className="field">
            <span>
              Description / Notes <em>Optional</em>
            </span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Why are you saving for this? Add details, motivation, or milestones…"
              rows={2}
              maxLength={250}
            />
          </label>

          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}

          <div className="dialog-actions">
            <Button onClick={onClose}>Cancel</Button>
            <Button variant="primary" type="submit">
              {editing ? 'Save changes' : 'Create goal'}
            </Button>
          </div>
        </form>
      </section>
    </div>
  );
}
