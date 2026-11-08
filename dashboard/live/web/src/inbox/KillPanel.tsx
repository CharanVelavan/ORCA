import { useState } from 'react';
import { api } from '../api';
import { useLiveStore } from '../store';
import { ConfirmButton } from './ConfirmButton';
import './inbox.css';

export function useKilled(): boolean {
  return (useLiveStore((s) => s.kill) as Record<string, unknown> | null)?.engaged === true;
}

export function KillPanel({ onDone }: { onDone: () => void }) {
  const killed = useKilled();
  const [reason, setReason] = useState('');
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
      <ConfirmButton label={killed ? 'Release' : 'Engage'} confirmLabel={killed ? 'Confirm release' : 'Confirm engage'} tone={killed ? 'primary' : 'danger'}
        hint={killed ? 'Execution stays manual until a mode is set again.' : 'Revokes tokens and refuses all execution.'}
        onConfirm={async () => {
          const res = killed ? await api.releaseKill({ pin: 'click' }) : await api.kill({ pin: 'click', reason: reason.trim() || 'Engaged by commander' });
          if (res && (res as Record<string, unknown>).ok === false) throw new Error(String((res as Record<string, unknown>).error ?? 'The console did not accept that.'));
          onDone();
        }} />
    </div>
  );
}
