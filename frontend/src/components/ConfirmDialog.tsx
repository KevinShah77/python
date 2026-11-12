import { AlertTriangle, X } from 'lucide-react';
import { Button, IconButton } from './ui';

export default function ConfirmDialog({ title, detail, confirmLabel = 'Delete entry', onConfirm, onCancel }: { title: string; detail: string; confirmLabel?: string; onConfirm: () => void; onCancel: () => void }) {
  return <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onCancel(); }}><section className="dialog confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title"><div className="dialog-topline"><span className="dialog-icon dialog-icon-danger"><AlertTriangle size={20} /></span><IconButton label="Close" onClick={onCancel}><X size={17} /></IconButton></div><h2 id="confirm-title">{title}</h2><p>{detail}</p><div className="dialog-actions"><Button onClick={onCancel}>Keep it</Button><Button variant="danger" onClick={onConfirm}>{confirmLabel}</Button></div></section></div>;
}
