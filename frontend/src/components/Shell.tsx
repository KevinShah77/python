import { useState } from 'react';
import {
  ArrowUpRight, Bell, CalendarDays, ChartNoAxesCombined, ChevronDown,
  CreditCard, FileText, LayoutDashboard, Menu, PiggyBank, Plus, ReceiptText,
  RotateCcw, Sparkles, Target, WalletCards, X,
} from 'lucide-react';
import type { EntryKind, PageKey } from '../types';
import { formatPeriod, PERIODS } from '../utils';
import { IconButton } from './ui';

const navigation: Array<{ label: PageKey; icon: typeof LayoutDashboard; section: string }> = [
  { label: 'Dashboard', icon: LayoutDashboard, section: 'Overview' },
  { label: 'Expenses', icon: ArrowUpRight, section: 'Money' },
  { label: 'Income', icon: WalletCards, section: 'Money' },
  { label: 'Transactions', icon: CreditCard, section: 'Money' },
  { label: 'Budgets', icon: Target, section: 'Planning' },
  { label: 'Savings Goals', icon: PiggyBank, section: 'Planning' },
  { label: 'Analytics', icon: ChartNoAxesCombined, section: 'Planning' },
  { label: 'Reports', icon: FileText, section: 'Planning' },
];

export function BrandMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span className="brand-mark-line brand-mark-line-one" />
      <span className="brand-mark-line brand-mark-line-two" />
      <span className="brand-mark-line brand-mark-line-three" />
      <i />
    </div>
  );
}

export default function Shell({
  activePage,
  setActivePage,
  period,
  setPeriod,
  onAdd,
  children,
  alertCount = 0,
  backendConnected = false,
  onSeedSampleData,
  onClearSampleData,
}: {
  activePage: PageKey;
  setActivePage: (page: PageKey) => void;
  period: string;
  setPeriod: (period: string) => void;
  onAdd: (kind: EntryKind) => void;
  children: React.ReactNode;
  alertCount?: number;
  backendConnected?: boolean;
  onSeedSampleData?: () => void;
  onClearSampleData?: () => void;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [periodOpen, setPeriodOpen] = useState(false);
  const move = (page: PageKey) => {
    setActivePage(page);
    setMobileOpen(false);
  };

  const navContent = (
    <>
      <div className="brand-lockup">
        <BrandMark />
        <div>
          <strong>PennyPilot</strong>
          <span>PERSONAL FINANCE</span>
        </div>
      </div>
      <div className="sidebar-label">WORKSPACE</div>
      {['Overview', 'Money', 'Planning'].map((section) => (
        <div className="nav-group" key={section}>
          <div className="sidebar-section-label">{section}</div>
          {navigation
            .filter((item) => item.section === section)
            .map(({ label, icon: Icon }) => (
              <button
                key={label}
                type="button"
                className={`nav-item ${activePage === label ? 'nav-item-active' : ''}`}
                onClick={() => move(label)}
              >
                <Icon size={18} strokeWidth={1.9} />
                <span>{label}</span>
                {label === 'Budgets' && alertCount > 0 && <b className="nav-badge">{alertCount}</b>}
              </button>
            ))}
        </div>
      ))}
      <div className="sidebar-bottom">
        <div className="sidebar-note">
          <div className="sidebar-note-icon">
            <CalendarDays size={17} />
          </div>
          <div>
            <strong>A little more clarity</strong>
            <span>One good habit at a time.</span>
          </div>
        </div>

        <div
          className={`local-status ${backendConnected ? 'local-status-connected' : 'local-status-offline'}`}
          title={
            backendConnected
              ? 'Connected to live SQLite backend (expenses.db)'
              : 'Running in browser-local offline mode'
          }
        >
          <span className={`local-status-dot ${backendConnected ? 'dot-connected' : 'dot-offline'}`} />
          <span>{backendConnected ? 'Live SQLite Backend' : 'Browser-local (Offline)'}</span>
        </div>

        <div className="demo-data-actions">
          {onSeedSampleData && (
            <button
              type="button"
              className="sidebar-action-btn"
              onClick={onSeedSampleData}
              title="Load realistic Indian college/student demo records"
            >
              <Sparkles size={11} /> Load demo
            </button>
          )}
          {onClearSampleData && (
            <button
              type="button"
              className="sidebar-action-btn-subtle"
              onClick={onClearSampleData}
              title="Clear demo records"
            >
              <RotateCcw size={11} /> Clear
            </button>
          )}
        </div>
      </div>
    </>
  );

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>{navContent}</aside>
      {mobileOpen && (
        <button
          type="button"
          className="mobile-scrim"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <main className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <IconButton
              className="mobile-menu-button"
              label={mobileOpen ? 'Close menu' : 'Open menu'}
              onClick={() => setMobileOpen(!mobileOpen)}
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </IconButton>
            <div className="breadcrumb">
              <span>Workspace</span>
              <span className="breadcrumb-slash">/</span>
              <strong>{activePage}</strong>
            </div>
          </div>
          <div className="topbar-actions">
            <div className="period-control-wrap">
              <button
                className={`period-control ${periodOpen ? 'period-control-open' : ''}`}
                type="button"
                onClick={() => setPeriodOpen(!periodOpen)}
              >
                <CalendarDays size={17} />
                <span>{formatPeriod(period, true)}</span>
                <ChevronDown size={15} />
              </button>
              {periodOpen && (
                <>
                  <button
                    className="popover-scrim"
                    aria-label="Close period menu"
                    type="button"
                    onClick={() => setPeriodOpen(false)}
                  />
                  <div className="period-popover">
                    <div className="popover-title">Reporting period</div>
                    {PERIODS.map((item) => (
                      <button
                        type="button"
                        key={item}
                        className={`period-option ${item === period ? 'period-option-active' : ''}`}
                        onClick={() => {
                          setPeriod(item);
                          setPeriodOpen(false);
                        }}
                      >
                        {formatPeriod(item)}
                        {item === period && <span>Current view</span>}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
            <div className="topbar-divider" />
            <button
              type="button"
              className="notification-button"
              aria-label={`${alertCount} budget alerts`}
              onClick={() => move('Budgets')}
            >
              <Bell size={18} />
              {alertCount > 0 && <i />}
            </button>
            <button
              type="button"
              className="button button-primary topbar-add"
              onClick={() => onAdd(activePage === 'Income' ? 'income' : 'expense')}
            >
              <Plus size={16} /> <span>New entry</span>
            </button>
            <button
              type="button"
              className="topbar-add-compact"
              aria-label="Add transaction"
              onClick={() => onAdd(activePage === 'Income' ? 'income' : 'expense')}
            >
              <Plus size={18} />
            </button>
          </div>
        </header>
        <div className="page-content">{children}</div>
        <footer className="main-footer">
          <span>Made for a clearer relationship with money.</span>
          <span>
            <ReceiptText size={13} /> PennyPilot
          </span>
        </footer>
      </main>
    </div>
  );
}
