import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from 'react';

export function IconButton({ label, className = '', children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return <button type="button" aria-label={label} title={label} className={`icon-button ${className}`} {...props}>{children}</button>;
}

export function Button({ variant = 'secondary', size = 'md', className = '', children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger'; size?: 'sm' | 'md' }) {
  return <button type="button" className={`button button-${variant} button-${size} ${className}`} {...props}>{children}</button>;
}

export function PageTitle({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <div className="page-title-row"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{actions && <div className="page-title-actions">{actions}</div>}</div>;
}

export function Panel({ title, description, action, children, className = '', ...props }: HTMLAttributes<HTMLElement> & { title?: string; description?: string; action?: ReactNode }) {
  return <section className={`panel ${className}`} {...props}>{(title || description || action) && <div className="panel-head"><div>{title && <h2>{title}</h2>}{description && <p>{description}</p>}</div>{action && <div className="panel-action">{action}</div>}</div>}{children}</section>;
}

export function EmptyState({ icon = '◌', title, detail, action }: { icon?: ReactNode; title: string; detail: string; action?: ReactNode }) {
  return <div className="empty-state"><div className="empty-state-icon">{icon}</div><strong>{title}</strong><p>{detail}</p>{action}</div>;
}

export function StatusPill({ tier, children }: { tier: string; children: ReactNode }) {
  return <span className={`status-pill status-${tier}`}>{children}</span>;
}

export function ProgressBar({ value, tier = 'normal' }: { value: number; tier?: string }) {
  return <div className={`progress-track progress-${tier}`}><div className="progress-fill" style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} /></div>;
}
