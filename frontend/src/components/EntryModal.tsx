import { useState, type FormEvent } from 'react';
import { ArrowDownLeft, ArrowUpRight, CalendarDays, ChevronDown, X } from 'lucide-react';
import { CATEGORIES, INCOME_SOURCES, PAYMENT_METHODS, type EntryKind, type IncomeSource, type RecordFormValue, type Transaction } from '../types';
import { formatDate } from '../utils';
import { Button, IconButton } from './ui';

export default function EntryModal({ initialKind, editing, onClose, onSave }: {
  initialKind: EntryKind;
  editing?: Transaction;
  onClose: () => void;
  onSave: (value: RecordFormValue, entryId?: number) => void;
}) {
  const [kind, setKind] = useState<EntryKind>(editing?.kind ?? initialKind);
  const resolveInitialIncomeSource = (val?: string): IncomeSource => {
    if (!val) return INCOME_SOURCES[0];
    if (INCOME_SOURCES.includes(val as IncomeSource)) return val as IncomeSource;
    const match = INCOME_SOURCES.find((s) => val.toLowerCase().includes(s.toLowerCase()));
    return match ?? 'Other Income';
  };

  const initialSource = resolveInitialIncomeSource(editing?.categoryOrSource);
  const [name, setName] = useState(editing?.name ?? (kind === 'income' ? initialSource : ''));
  const [amount, setAmount] = useState(editing ? String(editing.amount) : '');
  const [category, setCategory] = useState(
    editing
      ? (kind === 'income' ? initialSource : editing.categoryOrSource)
      : (kind === 'income' ? INCOME_SOURCES[0] : CATEGORIES[0])
  );
  const [date, setDate] = useState(editing?.date ?? new Date().toISOString().slice(0, 10));
  const [paymentMethod, setPaymentMethod] = useState(editing?.paymentMethod && editing.paymentMethod !== 'N/A' ? editing.paymentMethod : PAYMENT_METHODS[0]);
  const [description, setDescription] = useState(editing?.description ?? '');
  const [error, setError] = useState('');

  const switchKind = (next: EntryKind) => {
    if (editing || next === kind) return;
    setKind(next);
    if (next === 'income') { setCategory(INCOME_SOURCES[0]); setName(INCOME_SOURCES[0]); }
    else { setCategory(CATEGORIES[0]); setName(''); }
    setError('');
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const numericAmount = Number(amount);
    if (!name.trim()) { setError(kind === 'income' ? 'Choose an income source.' : 'An expense name is required.'); return; }
    if (name.trim().length > 100) { setError('Name must be 100 characters or fewer.'); return; }
    if (!Number.isFinite(numericAmount) || numericAmount <= 0) { setError('Enter an amount greater than ₹0.'); return; }
    if (kind === 'expense' && numericAmount > 10_000_000) { setError('Expense amount cannot exceed ₹1,00,00,000.'); return; }
    if (kind === 'income' && numericAmount > 50_000_000) { setError('Income amount cannot exceed ₹5,00,00,000.'); return; }
    if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date) || Number.isNaN(Date.parse(`${date}T00:00:00`))) { setError('Select a valid date.'); return; }
    if (kind === 'expense' && !CATEGORIES.includes(category as (typeof CATEGORIES)[number])) { setError('Select a valid expense category.'); return; }
    if (kind === 'income' && !INCOME_SOURCES.includes(category as (typeof INCOME_SOURCES)[number])) { setError('Select a valid income source.'); return; }
    setError('');
    onSave({ kind, name: kind === 'income' ? category : name.trim(), amount: numericAmount, categoryOrSource: category, date, paymentMethod, description: description.trim() }, editing?.entryId);
  };

  return <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section className="dialog entry-dialog" role="dialog" aria-modal="true" aria-labelledby="entry-title"><div className="dialog-topline"><div className="dialog-title-icon">{kind === 'income' ? <ArrowDownLeft size={19} /> : <ArrowUpRight size={19} />}</div><IconButton label="Close dialog" onClick={onClose}><X size={18} /></IconButton></div><div className="dialog-heading"><div className="eyebrow">{editing ? 'EDIT ENTRY' : 'NEW ENTRY'}</div><h2 id="entry-title">{editing ? `Edit ${kind}` : 'Add to your story'}</h2><p>{editing ? `Update the details for ${formatDate(editing.date, { day: 'numeric', month: 'long', year: 'numeric' })}.` : 'Capture it now. You can always adjust it later.'}</p></div>
    {!editing && <div className="entry-kind-switch" role="tablist" aria-label="Entry type"><button type="button" role="tab" aria-selected={kind === 'expense'} className={kind === 'expense' ? 'entry-kind-active entry-kind-expense' : ''} onClick={() => switchKind('expense')}>{kind === 'expense' && <ArrowUpRight size={15} />} Expense</button><button type="button" role="tab" aria-selected={kind === 'income'} className={kind === 'income' ? 'entry-kind-active entry-kind-income' : ''} onClick={() => switchKind('income')}>{kind === 'income' && <ArrowDownLeft size={15} />} Income</button></div>}
    <form onSubmit={submit} noValidate>
      {kind === 'expense' ? <label className="field"><span>What was it for? <i>*</i></span><input autoFocus value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Lunch with friends" maxLength={110} /></label> : <label className="field"><span>Income source <i>*</i></span><span className="select-wrap"><select value={category} onChange={(event) => { setCategory(event.target.value); setName(event.target.value); }} autoFocus>{INCOME_SOURCES.map((source) => <option key={source} value={source}>{source}</option>)}</select><ChevronDown size={15} /></span></label>}
      {kind === 'expense' && <label className="field"><span>Category <i>*</i></span><span className="select-wrap"><select value={category} onChange={(event) => setCategory(event.target.value)}>{CATEGORIES.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={15} /></span></label>}
      <div className="form-row"><label className="field"><span>Amount <i>*</i></span><span className="amount-input"><span>₹</span><input type="number" inputMode="decimal" min="0.01" step="0.01" max={kind === 'income' ? 50000000 : 10000000} value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="0.00" /></span><small>{kind === 'income' ? 'Up to ₹5 crore' : 'Up to ₹1 crore'}</small></label><label className="field"><span>{kind === 'income' ? 'Received on' : 'Date'} <i>*</i></span><span className="date-field"><CalendarDays size={15} /><input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></span></label></div>
      {kind === 'expense' && <label className="field"><span>Payment method</span><span className="select-wrap"><select value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}>{PAYMENT_METHODS.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={15} /></span></label>}
      <label className="field"><span>Notes <em>Optional</em></span><textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Add a little context…" rows={2} maxLength={250} /></label>
      {error && <div className="form-error" role="alert">{error}</div>}
      <div className="dialog-actions"><Button onClick={onClose}>Cancel</Button><Button variant="primary" type="submit">{editing ? 'Save changes' : kind === 'income' ? 'Add income' : 'Add expense'}</Button></div>
    </form>
  </section></div>;
}
