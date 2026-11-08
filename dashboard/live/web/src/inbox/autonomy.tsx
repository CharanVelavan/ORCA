import { useState } from 'react';
import { api } from '../api';
import { useLiveStore } from '../store';
import { ConfirmButton } from './ConfirmButton';
import { istTime, toMs } from './format';
import { getSimNowMs } from './simClock';
import './inbox.css';

export type Mode = 'MANUAL' | 'ASSISTED' | 'AUTO';
export const MODES: Mode[] = ['MANUAL', 'ASSISTED', 'AUTO'];
const MINUTES = [5, 10, 20, 60];

export function useAutonomy(): { mode: Mode; expires: string; downgraded: string; killed: boolean } {
  const a = useLiveStore((s) => s.autonomy) as Record<string, unknown> | null;
  const kill = useLiveStore((s) => s.kill) as Record<string, unknown> | null;
  const killed = kill?.engaged === true;
  let mode = String(a?.mode ?? a?.to ?? 'MANUAL') as Mode;
  const expires = String(a?.expires ?? a?.expires_at ?? '');
  const exp = toMs(expires);
  if (!MODES.includes(mode) || killed || (mode !== 'MANUAL' && Number.isFinite(exp) && exp <= getSimNowMs())) mode = 'MANUAL';
  const downgraded = a?.cause && a?.from ? `Downgraded from ${String(a.from)}: ${String(a.cause)}` : '';
  return { mode, expires, downgraded, killed };
}

export function AutonomyPanel({ onDone }: { onDone: () => void }) {
  const cur = useAutonomy();
  const [pick, setPick] = useState<Mode | null>(null);
  const [minutes, setMinutes] = useState(20);

  if (cur.killed) {
    return <div className="inbox-pop"><div className="inbox-pop__title">Autonomy</div><p className="inbox-body">The kill switch is engaged. Release it before changing the mode.</p></div>;
  }
  if (pick) {
    return (
      <div className="inbox-pop">
        <div className="inbox-pop__title">{`Set ${pick}`}</div>
        <p className="inbox-body inbox-body--muted">{`${pick} for ${minutes} min, all sites and playbooks.`}</p>
        <ConfirmButton label={`Set ${pick}`} confirmLabel="Confirm" onConfirm={async () => {
          const res = await api.autonomy({ mode: pick, sites: '*', playbooks: '*', minutes, pin: 'click' });
          if (res && (res as Record<string, unknown>).ok === false) throw new Error(String((res as Record<string, unknown>).error ?? 'The console did not accept that.'));
          onDone();
        }} />
        <button type="button" className="inbox-link" onClick={() => setPick(null)}>Back</button>
      </div>
    );
  }
  return (
    <div className="inbox-pop">
      <div className="inbox-pop__title">Autonomy mode</div>
      <p className="inbox-body inbox-body--muted">
        Now {cur.mode}{cur.expires && cur.mode !== 'MANUAL' ? `, until ${istTime(cur.expires)} IST` : ''}.
        {cur.downgraded && ` ${cur.downgraded}.`}
      </p>
      <div className="inbox-seg" role="radiogroup" aria-label="Mode">
        {MODES.map((m) => (
          <button key={m} type="button" role="radio" aria-checked={cur.mode === m} className={`inbox-seg__opt${cur.mode === m ? ' is-on' : ''}`} onClick={() => setPick(m)}>{m}</button>
        ))}
      </div>
      <label className="inbox-field">For
        <select value={minutes} onChange={(e) => setMinutes(Number(e.target.value))}>
          {MINUTES.map((m) => <option key={m} value={m}>{m} minutes</option>)}
        </select>
      </label>
      <p className="inbox-body inbox-body--muted">Choosing a mode asks you to confirm.</p>
    </div>
  );
}
