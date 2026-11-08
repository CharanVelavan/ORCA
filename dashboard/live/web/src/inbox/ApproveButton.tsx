import { useEffect, useRef, useState } from 'react';
import { Loader2, ShieldAlert } from 'lucide-react';
import { api } from '../api';
import { usePipeline } from '../pipeline/pipelineStore';
import { ICON } from './parts';
import { plainError } from './format';
import './inbox.css';

/** One-click approval. The server may still refuse (clone test, path not clean); that text shows inline as a refusal. */
export function ApproveButton({ hash, variant = 'inbox', label = 'Approve', onDone }: { hash: string; variant?: 'inbox' | 'node'; label?: string; onDone?: () => void }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  // Hide the request at once: the paced stream (stage/presenter.ts) may show the engine's 'approved' event a little later.
  const drop = () => usePipeline.setState((st) => ({ pending: st.pending.filter((p) => p.hash !== hash) }));
  const go = async () => {
    if (pending) return;
    setPending(true); setError('');
    try {
      const res = (await api.approve({ hash, pin: 'click' })) as Record<string, unknown> | null;
      if (res && res.ok === false) throw new Error(String(res.error ?? 'The console refused this approval.'));
      drop();
      onDone?.();
    } catch (err) {
      const msg = plainError(err);
      if (/already run/i.test(msg)) { drop(); return; } // decided a moment ago; the paced stream just has not shown it yet
      if (alive.current) setError(msg);
    }
    finally { if (alive.current) setPending(false); }
  };
  const node = variant === 'node';
  return (
    <>
      <button type="button" className={node ? 'fc-btn' : 'inbox-btn inbox-btn--primary'} disabled={pending} aria-busy={pending} onClick={() => void go()}>
        {pending ? <><Loader2 {...ICON} className="inbox-spin" aria-hidden /> Approving</> : label}
      </button>
      {error && (
        <p className={node ? 'fc-ask__refusal' : 'inbox-refusal'} role="alert">
          <ShieldAlert {...ICON} aria-hidden /><span><strong>Refused.</strong> {error}</span>
        </p>
      )}
    </>
  );
}
