import { useState } from 'react';
import { Download, FileDown, FileSpreadsheet, Printer, Server } from 'lucide-react';
import type { AppData } from '../types';
import { downloadCsv, downloadPdf, formatMoney, formatPeriod, getCategoryBreakdown, getMonthTransactions, getSummary } from '../utils';
import { downloadServerReport } from '../api';
import { Button, PageTitle, Panel } from '../components/ui';
import TransactionTable from '../components/TransactionTable';

export default function ReportsPage({
  data,
  period,
  notify,
  backendConnected = false,
}: {
  data: AppData;
  period: string;
  notify: (message: string) => void;
  backendConnected?: boolean;
}) {
  const [downloading, setDownloading] = useState<boolean>(false);
  const summary = getSummary(data, period);
  const categories = getCategoryBreakdown(data, period);
  const transactions = getMonthTransactions(data, period);

  const exportCsv = async () => {
    if (backendConnected) {
      try {
        setDownloading(true);
        await downloadServerReport('csv', period);
        notify('CSV report downloaded from SQLite backend.');
        return;
      } catch {
        /* Fallback to client CSV if server request fails */
      } finally {
        setDownloading(false);
      }
    }
    downloadCsv(data, period, transactions);
    notify('CSV report generated and downloaded.');
  };

  const exportPdf = async () => {
    if (backendConnected) {
      try {
        setDownloading(true);
        await downloadServerReport('pdf', period);
        notify('Official ReportLab PDF report downloaded from backend.');
        return;
      } catch {
        /* Fallback to client jsPDF if server request fails */
      } finally {
        setDownloading(false);
      }
    }
    await downloadPdf(data, period);
    notify('PDF report rendered in browser and downloaded.');
  };

  const exportClientPdf = async () => {
    setDownloading(true);
    try {
      await downloadPdf(data, period);
      notify('Client jsPDF report downloaded.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="page-stack">
      <PageTitle
        eyebrow="READY WHEN YOU ARE"
        title="Reports"
        description={`A tidy monthly record for ${formatPeriod(period)}.`}
        actions={
          <>
            <Button onClick={exportCsv} disabled={downloading}>
              <FileSpreadsheet size={16} /> Export CSV
            </Button>
            <Button variant="primary" onClick={exportPdf} disabled={downloading}>
              <FileDown size={16} /> Download PDF
            </Button>
          </>
        }
      />
      <div className="report-intro">
        <div className="report-intro-icon">
          <FileDown size={21} />
        </div>
        <div>
          <span className="eyebrow">MONTHLY FINANCIAL REPORT</span>
          <h2>{formatPeriod(period)}</h2>
          <p>Executive summary, category breakdown, and transaction activity in one place.</p>
        </div>
        <div className="report-intro-actions">
          <Button size="sm" onClick={exportCsv} disabled={downloading}>
            <Download size={14} /> CSV
          </Button>
          <Button size="sm" variant="primary" onClick={exportPdf} disabled={downloading}>
            <FileDown size={14} /> Save PDF
          </Button>
          {backendConnected && (
            <Button size="sm" variant="secondary" onClick={exportClientPdf} title="Generate PDF using client-side jsPDF">
              <Printer size={14} /> Browser PDF
            </Button>
          )}
        </div>
      </div>
      <div className="report-summary-grid">
        <article>
          <span>Income</span>
          <strong className="amount-positive">{formatMoney(summary.incomeTotal)}</strong>
          <small>{summary.income.length} inflow records</small>
        </article>
        <article>
          <span>Expenses</span>
          <strong>{formatMoney(summary.expenseTotal)}</strong>
          <small>{summary.expenses.length} outflow records</small>
        </article>
        <article>
          <span>Balance</span>
          <strong className={summary.balance < 0 ? 'amount-negative' : 'amount-positive'}>
            {formatMoney(summary.balance)}
          </strong>
          <small>{summary.balance < 0 ? 'Deficit' : `${summary.savingsRate.toFixed(1)}% savings rate`}</small>
        </article>
        <article>
          <span>Budget</span>
          <strong>{summary.overallBudget ? formatMoney(summary.overallBudget) : 'Not set'}</strong>
          <small>Overall monthly limit</small>
        </article>
      </div>
      <Panel title="Category breakdown" description="A focused view of monthly expense distribution">
        <div className="report-category-table">
          <div className="report-category-head">
            <span>Category</span>
            <span>Transactions</span>
            <span>Share</span>
            <strong>Amount</strong>
          </div>
          {categories.length ? (
            categories.map((item) => (
              <div className="report-category-row" key={item.category}>
                <span>
                  <i style={{ background: item.color ?? '#9aa2b4' }} />
                  {item.category}
                </span>
                <span>{item.count}</span>
                <span>{item.percent.toFixed(1)}%</span>
                <strong>{formatMoney(item.amount)}</strong>
              </div>
            ))
          ) : (
            <div className="report-empty">No expenses recorded for this period yet.</div>
          )}
        </div>
      </Panel>
      <Panel title="Transaction activity" description={`${transactions.length} entries · ${formatPeriod(period)}`}>
        <TransactionTable
          transactions={transactions}
          emptyTitle="No report activity yet"
          emptyDetail="Once you add an income or expense, it will appear in the monthly report."
        />
      </Panel>
      <div className="report-footnote">
        {backendConnected ? <Server size={14} /> : <Printer size={14} />}
        <span>
          {backendConnected
            ? 'Connected to SQLite backend: ReportLab PDF and CSV compiled with live server metrics; local jsPDF rendering also available.'
            : 'Your PDF report is generated locally in your browser and saved directly to your device.'}
        </span>
      </div>
    </div>
  );
}

