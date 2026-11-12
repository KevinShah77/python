import { Pencil, Trash2 } from 'lucide-react';
import type { Transaction } from '../types';
import { formatDate, formatMoney, getCategoryMeta } from '../utils';
import { EmptyState, IconButton } from './ui';

export default function TransactionTable({
  transactions,
  mode = 'all',
  emptyTitle = 'No transactions found',
  emptyDetail = 'Try a different period or clear one of your filters.',
  onEdit,
  onDelete,
}: {
  transactions: Transaction[];
  mode?: 'expenses' | 'income' | 'all';
  emptyTitle?: string;
  emptyDetail?: string;
  onEdit?: (entry: Transaction) => void;
  onDelete?: (entry: Transaction) => void;
}) {
  if (!transactions.length) {
    return <EmptyState icon="◌" title={emptyTitle} detail={emptyDetail} />;
  }

  const isIncomeMode = mode === 'income';
  const isExpenseMode = mode === 'expenses';

  return (
    <>
      <div className="transaction-table-wrap">
        <table className="transaction-table">
          <thead>
            <tr>
              <th>{isIncomeMode ? 'Income Source' : isExpenseMode ? 'Expense' : 'Transaction'}</th>
              {!isIncomeMode && !isExpenseMode && <th>Type</th>}
              {!isIncomeMode && <th>{isExpenseMode ? 'Category' : 'Category / Source'}</th>}
              <th>Date</th>
              <th>{isIncomeMode ? 'Description / Notes' : isExpenseMode ? 'Payment Method' : 'Payment / Note'}</th>
              <th className="amount-column">Amount</th>
              {(onEdit || onDelete) && (
                <th className="actions-column">
                  <span className="sr-only">Actions</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {transactions.map((entry) => {
              const meta = getCategoryMeta(entry.categoryOrSource);
              const isIncome = entry.kind === 'income';

              return (
                <tr key={entry.id}>
                  <td>
                    <div className="transaction-name-cell">
                      <span
                        className={`transaction-type-icon ${isIncome ? 'transaction-type-income' : ''}`}
                        style={{ '--category-color': meta.color } as React.CSSProperties}
                      >
                        {isIncome ? (isIncomeMode ? meta.icon : '↙') : meta.icon}
                      </span>
                      <div>
                        <strong>{entry.name}</strong>
                        <span>
                          {isIncomeMode
                            ? 'Income inflow'
                            : isExpenseMode
                            ? 'Expense outflow'
                            : isIncome
                            ? 'Income'
                            : 'Expense'}
                          {entry.description && !isIncomeMode && <><i> · </i>{entry.description}</>}
                        </span>
                      </div>
                    </div>
                  </td>

                  {!isIncomeMode && !isExpenseMode && (
                    <td>
                      {isIncome ? (
                        <span className="type-badge type-badge-income">↙ Inflow</span>
                      ) : (
                        <span className="type-badge type-badge-expense">↗ Outflow</span>
                      )}
                    </td>
                  )}

                  {!isIncomeMode && (
                    <td>
                      <span className="table-category">
                        <i style={{ background: meta.color }} />
                        {entry.categoryOrSource}
                      </span>
                    </td>
                  )}

                  <td className="table-date">
                    {formatDate(entry.date, { day: 'numeric', month: 'short', year: 'numeric' })}
                  </td>

                  <td className={isIncomeMode ? 'table-description' : 'table-payment'}>
                    {isIncomeMode
                      ? entry.description || '—'
                      : isExpenseMode
                      ? entry.paymentMethod
                      : isIncome
                      ? entry.description || '—'
                      : entry.paymentMethod}
                  </td>

                  <td className={`table-amount ${isIncome ? 'amount-positive' : ''}`}>
                    {isIncome ? '+' : '−'}{formatMoney(entry.amount)}
                  </td>

                  {(onEdit || onDelete) && (
                    <td className="table-actions">
                      {onEdit && (
                        <IconButton label={`Edit ${entry.name}`} onClick={() => onEdit(entry)}>
                          <Pencil size={15} />
                        </IconButton>
                      )}
                      {onDelete && (
                        <IconButton
                          className="icon-button-danger"
                          label={`Delete ${entry.name}`}
                          onClick={() => onDelete(entry)}
                        >
                          <Trash2 size={15} />
                        </IconButton>
                      )}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="transaction-mobile-list">
        {transactions.map((entry) => {
          const meta = getCategoryMeta(entry.categoryOrSource);
          const isIncome = entry.kind === 'income';

          return (
            <article className="mobile-transaction-card" key={entry.id}>
              <div className="mobile-transaction-top">
                <span
                  className={`transaction-type-icon ${isIncome ? 'transaction-type-income' : ''}`}
                  style={{ '--category-color': meta.color } as React.CSSProperties}
                >
                  {isIncome ? (isIncomeMode ? meta.icon : '↙') : meta.icon}
                </span>
                <div className="mobile-transaction-title">
                  <strong>{entry.name}</strong>
                  <span>
                    {!isIncomeMode && !isExpenseMode && (
                      isIncome ? (
                        <span className="type-badge type-badge-income" style={{ marginRight: 6 }}>↙ Inflow</span>
                      ) : (
                        <span className="type-badge type-badge-expense" style={{ marginRight: 6 }}>↗ Outflow</span>
                      )
                    )}
                    {isIncomeMode ? `Inflow · ${formatDate(entry.date)}` : `${entry.categoryOrSource} · ${formatDate(entry.date)}`}
                  </span>
                </div>
                <b className={`table-amount ${isIncome ? 'amount-positive' : ''}`}>
                  {isIncome ? '+' : '−'}{formatMoney(entry.amount)}
                </b>
              </div>

              {entry.description && <p>{entry.description}</p>}

              <div className="mobile-transaction-bottom">
                <span>{isIncomeMode ? (entry.description || 'Income') : isIncome ? 'Income' : entry.paymentMethod}</span>
                <div>
                  {onEdit && (
                    <IconButton label={`Edit ${entry.name}`} onClick={() => onEdit(entry)}>
                      <Pencil size={14} />
                    </IconButton>
                  )}
                  {onDelete && (
                    <IconButton
                      className="icon-button-danger"
                      label={`Delete ${entry.name}`}
                      onClick={() => onDelete(entry)}
                    >
                      <Trash2 size={14} />
                    </IconButton>
                  )}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </>
  );
}
