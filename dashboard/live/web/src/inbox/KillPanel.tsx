import { useState } from 'react';
import { api } from '../api';
import { useLiveStore } from '../store';
import { PinPad } from './PinPad';
import './inbox.css';

export function useKilled(): boolean {
  return (useLiveStore((s) => s.kill) as Record<string, unknown> | null)?.engaged === true;
}

export function KillPanel({ onDone }: { onDone: () => void }) {
  const killed = useKilled();
  const [reason, setReason] = useState('');
  const [asking, setAsking] = useState(false);

  if (asking) {
    return (
      <PinPad title={killed ? 'Release kill switch' : 'Engage kill switch'}
        subtitle={killed ? 'Execution stays manual until a mode is set again' : 'Revokes tokens and refuses all execution'}
        onCancel={() => setAsking(false)}
        onSubmit={async (pin) => {
          const res = killed ? await api.releaseKill({ pin }) : await api.kill({ pin, reason: reason.trim() || 'Engaged by commander' });
          if (res && (res as Record<string, unknown>).ok === false) throw new Error('API 400: kill');
          onDone();
        }} />
    );
  }
  return (
    <div className="inbox-pop">
      <div className="inbox-pop__title">{killed ? 'Kill switch engaged' : 'Kill switch armed'}</div>
      <p className="inbox-body inbox-body--muted">
        {killed ? 'All tokens are revoked and no playbook can execute.' : 'Engaging revokes every unused token, drops all autonomy grants, and refuses execution.'}
      </p>
      {!killed && (
        <label className="inbox-field">Reason
          <input value={reason} maxLength={160} onChange={(e) => setReason(e.target.value)} placeholder="Short reason" />
        </label>
      )}
      <button type="button" className={`inbox-btn ${killed ? 'inbox-btn--primary' : 'inbox-btn--danger'}`} onClick={() => setAsking(true)}>
        {killed ? 'Release' : 'Engage'}
      </button>
    </div>
  );
}
