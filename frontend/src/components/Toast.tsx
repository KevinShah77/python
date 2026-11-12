import { useEffect } from 'react';
import { AlertCircle, CheckCircle2, X } from 'lucide-react';
import { IconButton } from './ui';

export default function Toast({ message, type = 'success', onClose }: { message: string; type?: 'success' | 'error' | 'info'; onClose: () => void }) {
  useEffect(() => {
    const timer = window.setTimeout(onClose, 3600);
    return () => window.clearTimeout(timer);
  }, [message, onClose]);
  const Icon = type === 'error' ? AlertCircle : CheckCircle2;
  return <div className={`toast toast-${type}`} role={type === 'error' ? 'alert' : 'status'}><Icon size={18} /><span>{message}</span><IconButton label="Dismiss notification" onClick={onClose}><X size={16} /></IconButton></div>;
}
