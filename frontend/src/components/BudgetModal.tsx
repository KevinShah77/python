import { useState, type FormEvent } from 'react';
import { ChevronDown, Target, X } from 'lucide-react';
import { CATEGORIES, type Budget, type Category } from '../types';
import { formatPeriod } from '../utils';
import { Button, IconButton } from './ui';

export default function BudgetModal({ period, editing, onClose, onSave }: {
  period: string;
  editing?: Budget;
  onClose: () => void;
  onSave: (category: 'Overall' | Category, amount: number) => void;
}) {
  const [category, setCategory] = useState<'Overall' | Category>(editing?.category ?? 'Overall');
  const [amount, setAmount] = useState(editing ? String(editing.amount) : '');
  const [error, setError] = useState('');
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = Number(amount);
    if (!Number.isFinite(value) || value <= 0) { setError('Budget limit must be greater than ₹0.'); return; }
    if (value > 100_000_000) { setError('Budget amount cannot exceed ₹10,00,00,000.'); return; }
    onSave(category, value);
  };
  return <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section className="dialog budget-dialog" role="dialog" aria-modal="true" aria-labelledby="budget-title"><div className="dialog-topline"><div className="dialog-title-icon dialog-title-icon-budget"><Target size={19} /></div><IconButton label="Close dialog" onClick={onClose}><X size={18} /></IconButton></div><div className="dialog-heading"><div className="eyebrow">MONTHLY PLAN</div><h2 id="budget-title">{editing ? 'Adjust a limit' : 'Set a spending limit'}</h2><p>Your guardrail for <strong>{formatPeriod(period)}</strong>.</p></div><form onSubmit={submit} noValidate><label className="field"><span>Budget scope <i>*</i></span><span className="select-wrap"><select value={category} onChange={(event) => setCategory(event.target.value as 'Overall' | Category)}><option value="Overall">Overall monthly budget</option>{CATEGORIES.map((item) => <option key={item} value={item}>{item}</option>)}</select><ChevronDown size={15} /></span></label><label className="field"><span>{category === 'Overall' ? 'Monthly spending cap' : `${category} limit`} <i>*</i></span><span className="amount-input"><span>₹</span><input autoFocus type="number" min="0.01" max="100000000" step="500" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="e.g. 25,000" /></span><small>Choose an amount greater than ₹0 · Maximum ₹10 crore</small></label>{error && <div className="form-error" role="alert">{error}</div>}<div className="dialog-actions"><Button onClick={onClose}>Cancel</Button><Button variant="primary" type="submit">{editing ? 'Save limit' : 'Create limit'}</Button></div></form></section></div>;
}
