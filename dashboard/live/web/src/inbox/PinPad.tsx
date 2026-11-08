import { useEffect, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { Check, Delete, Loader2 } from 'lucide-react';
import { ICON } from './parts';
import { plainError } from './format';
import './inbox.css';

export type PinPadProps = {
  title: string;
  subtitle?: string;
  onSubmit: (pin: string) => Promise<void>;
  onCancel: () => void;
  compact?: boolean;
};

const MIN = 4, MAX = 8;
const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'del', '0', 'ok'] as const;

export function PinPad({ title, subtitle, onSubmit, onCancel, compact = false }: PinPadProps) {
  const [pin, setPin] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const root = useRef<HTMLDivElement>(null);
  const alive = useRef(true);
  useEffect(() => { alive.current = true; root.current?.focus(); return () => { alive.current = false; }; }, []);

  const add = (d: string) => { if (!pending) { setError(''); setPin((p) => (p.length < MAX ? p + d : p)); } };
  const del = () => { if (!pending) setPin((p) => p.slice(0, -1)); };
  const submit = async () => {
    if (pending) return;
    if (pin.length < MIN) { setError(`Enter at least ${MIN} digits.`); return; }
    setPending(true); setError('');
    try { await onSubmit(pin); }
    catch (err) { if (alive.current) { setError(plainError(err)); setPin(''); root.current?.focus(); } }
    finally { if (alive.current) setPending(false); }
  };

  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const onButton = (e.target as HTMLElement).tagName === 'BUTTON' && (e.key === 'Enter' || e.key === ' ');
    if (onButton) return;
    if (/^\d$/.test(e.key)) { add(e.key); }
    else if (e.key === 'Backspace') { del(); }
    else if (e.key === 'Enter') { void submit(); }
    else if (e.key === 'Escape') { onCancel(); }
    else return;
    e.preventDefault(); e.stopPropagation();
  };

  return (
    <div ref={root} tabIndex={-1} role="group" aria-label={title} onKeyDown={onKey}
      className={`inbox-pin${compact ? ' inbox-pin--compact' : ''}`}>
      <div className="inbox-pin__title">{title}</div>
      {subtitle && !compact && <div className="inbox-pin__sub">{subtitle}</div>}
      <div className="inbox-pin__dots" role="img" aria-label={`${pin.length} digits entered`}>
        {Array.from({ length: MAX }, (_, i) => <span key={i} className={`inbox-pin__dot${i < pin.length ? ' is-on' : ''}`} />)}
      </div>
      <div className="inbox-pin__error" role="alert" aria-live="polite">{error}</div>
      <div className="inbox-pin__keys">
        {KEYS.map((k) => {
          if (k === 'del') return <button key={k} type="button" tabIndex={-1} className="inbox-key" aria-label="Delete last digit" disabled={pending || !pin} onMouseDown={(e) => e.preventDefault()} onClick={del}><Delete {...ICON} /></button>;
          if (k === 'ok') return <button key={k} type="button" className="inbox-key inbox-key--ok" aria-label={pending ? 'Checking' : 'Submit PIN'} disabled={pending || pin.length < MIN} onMouseDown={(e) => e.preventDefault()} onClick={() => void submit()}>{pending ? <Loader2 {...ICON} className="inbox-spin" /> : <Check {...ICON} />}</button>;
          return <button key={k} type="button" tabIndex={-1} className="inbox-key" disabled={pending} onMouseDown={(e) => e.preventDefault()} onClick={() => add(k)}>{k}</button>;
        })}
      </div>
      <div className="inbox-pin__foot">
        {pending ? <span className="inbox-pin__pending">Checking</span> : <span className="inbox-pin__hint">{MIN} to {MAX} digits</span>}
        <button type="button" className="inbox-link" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}
