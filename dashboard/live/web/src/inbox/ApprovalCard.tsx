import { useState } from 'react';
import { motion } from 'framer-motion';
import { Ban, CheckCircle2, Clock, FlaskConical, Hourglass, Bot, XCircle } from 'lucide-react';
import { api } from '../api';
import { useUi } from '../stage/uiStore';
import type { Approval } from '../types';
import { PinPad } from './PinPad';
import { Chip, ICON, useCardMotion } from './parts';
import type { Tone } from './parts';
import { clockText, plainError, roleName, toMs } from './format';
import { useSimNow } from './simClock';
import './inbox.css';

type StatusKey = 'requested' | 'approved' | 'rejected' | 'auto' | 'expired';

const STATUS: Record<StatusKey, { tone: Tone; word: string; Icon: typeof Clock }> = {
  requested: { tone: 'warn', word: 'Requested', Icon: Hourglass },
  approved: { tone: 'ok', word: 'Approved', Icon: CheckCircle2 },
  rejected: { tone: 'critical', word: 'Rejected', Icon: XCircle },
  auto: { tone: 'accent', word: 'Auto', Icon: Bot },
  expired: { tone: 'unknown', word: 'Expired', Icon: Ban },
};

function firstSentence(v: unknown): string {
  const t = typeof v === 'string' ? v.trim() : '';
  const m = t.match(/^.*?[.!?](?=\s|$)/);
  return m ? m[0] : t;
}

function cloneTest(value: unknown): { state: 'pass' | 'fail' | 'none'; detail: string } {
  if (value == null || value === '') return { state: 'none', detail: 'Not run' };
  if (typeof value === 'string') return { state: /fail|refus|not/i.test(value) ? 'fail' : 'pass', detail: value };
  const v = value as Record<string, unknown>;
  return { state: v.passed === false ? 'fail' : 'pass', detail: String(v.detail ?? (v.passed === false ? 'Failed' : 'Passed on a cloned sandbox')) };
}

export function ApprovalCard({ approval }: { approval: Approval }) {
  const motionProps = useCardMotion();
  const now = useSimNow();
  const pinFor = useUi((s) => s.pinFor), pinAt = useUi((s) => s.pinAt), openPin = useUi((s) => s.openPin);
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const expMs = toMs(approval.expires_at), reqMs = toMs((approval as Record<string, unknown>).requested_at);
  const left = expMs - now;
  let status = (approval.status in STATUS ? approval.status : 'requested') as StatusKey;
  if (status === 'requested' && Number.isFinite(left) && left <= 0) status = 'expired';
  const S = STATUS[status];
  const open = status === 'requested';
  const title = typeof approval.title === 'string' ? approval.title : '';
  const ct = cloneTest(approval.clone_test);
  const total = Number.isFinite(reqMs) && Number.isFinite(expMs) && expMs > reqMs ? expMs - reqMs : 5 * 60000;
  const frac = Number.isFinite(left) ? Math.min(1, Math.max(0, left / total)) : 0;
  const pinHere = pinFor === approval.hash && pinAt === 'inbox';
  const pinElsewhere = pinFor === approval.hash && pinAt === 'node';

  const approve = async (pin: string) => {
    const res = await api.approve({ hash: approval.hash, pin });
    if (res && (res as Record<string, unknown>).ok === false) throw new Error('API 400: approve');
    openPin(null);
  };
  const reject = async () => {
    setBusy(true); setError('');
    try { await api.reject({ hash: approval.hash, reason: reason.trim() || 'Rejected by commander' }); setRejecting(false); }
    catch (err) { setError(plainError(err)); }
    finally { setBusy(false); }
  };

  const why = firstSentence(approval.reason);
  const heading = title || String(approval.playbook);
  return (
    <motion.article className={`inbox-card inbox-approval inbox-approval--${status}`} {...motionProps} layout={false}>
      <header className="inbox-card__head">
        <div className="inbox-card__title">
          <h3 className="inbox-card__h" title={heading}>{heading}</h3>
          <span className="mono inbox-id">{approval.playbook}</span>
        </div>
        <div className="inbox-card__chips">
          <Chip tone={S.tone} icon={<S.Icon {...ICON} />}>{S.word}</Chip>
        </div>
      </header>
      <p className="inbox-why" title={String(approval.reason ?? '')}>{why}</p>
      <dl className="inbox-facts">
        <dt>Asked by</dt><dd title={roleName(approval.owner)}>{roleName(approval.owner)}</dd>
        <dt>Targets</dt><dd className="mono" title={(approval.targets ?? []).join(', ')}>{(approval.targets ?? []).join(', ') || 'none'}</dd>
        <dt>Clone test</dt>
        <dd className={`inbox-clone inbox-clone--${ct.state}`} title={ct.detail}>
          <FlaskConical {...ICON} />
          <strong>{ct.state === 'pass' ? 'Passed' : ct.state === 'fail' ? 'Failed' : 'Not run'}</strong>
        </dd>
      </dl>
      {open && (
        <div className="inbox-timer" role="timer" aria-label="Time left to decide">
          <span className="mono inbox-timer__text"><Clock {...ICON} /> {clockText(left)} left</span>
          <span className="inbox-timer__bar"><span style={{ transform: `scaleX(${frac})` }} /></span>
        </div>
      )}
      {!open && approval.reject_reason != null && <p className="inbox-note">Reason: {String(approval.reject_reason)}</p>}
      {open && !pinHere && !rejecting && (
        <div className="inbox-actions">
          <button type="button" className="inbox-btn inbox-btn--primary" onClick={() => openPin(approval.hash, 'inbox')}>Approve</button>
          <button type="button" className="inbox-btn" onClick={() => { openPin(null); setRejecting(true); }}>Reject</button>
          {pinElsewhere && <span className="inbox-note">PIN pad is open on the Commander node.</span>}
        </div>
      )}
      {open && rejecting && (
        <form className="inbox-reject" onSubmit={(e) => { e.preventDefault(); void reject(); }}>
          <label className="inbox-field">Reason for rejecting
            <input autoFocus value={reason} maxLength={200} onChange={(e) => setReason(e.target.value)} placeholder="Short reason" onKeyDown={(e) => { if (e.key === 'Escape') setRejecting(false); }} />
          </label>
          <div className="inbox-actions">
            <button type="submit" className="inbox-btn inbox-btn--danger" disabled={busy}>{busy ? 'Rejecting' : 'Confirm reject'}</button>
            <button type="button" className="inbox-btn" onClick={() => setRejecting(false)}>Back</button>
          </div>
          {error && <p className="inbox-error" role="alert">{error}</p>}
        </form>
      )}
      {open && pinHere && (
        <PinPad title="Commander PIN" subtitle={`Approve ${approval.playbook} on ${(approval.targets ?? []).join(', ')}`}
          onSubmit={approve} onCancel={() => openPin(null)} />
      )}
    </motion.article>
  );
}
