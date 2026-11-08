import { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, ChevronDown, FileSearch, XCircle } from 'lucide-react';
import { api } from '../api';
import { useLiveStore } from '../store';
import type { LiveEvent } from '../types';
import { ConfirmButton } from './ConfirmButton';
import { Chip, ICON, useCardMotion } from './parts';
import './inbox.css';

type Decision = 'confirm' | 'reject';

/** Gap candidate. `gap` is a verdict event that carries gap_id (a legacy `gap` event also works). */
export function GapCard({ gap }: { gap: LiveEvent }) {
  const motionProps = useCardMotion();
  const gapId = String(gap.gap_id ?? '');
  const raw = useLiveStore((s) => s.raw);
  const logged = [...raw].reverse().find((e) => e.kind === 'gap_human_decision' && (e.draft_id === gapId || e.gap_id === gapId));
  const [local, setLocal] = useState<Decision | null>(null);
  const decided = (local ?? (logged ? String(logged.decision) : null)) as Decision | null;

  const topic = String(gap.topic ?? gap.title ?? gap.question ?? 'Policy gap');
  const text = String(gap.explanation ?? gap.india ?? '');
  const records = ((gap.records ?? gap.record_ids ?? []) as unknown[]).map(String);
  const recommendation = gap.recommendation ? String(gap.recommendation) : '';

  const submit = (decision: Decision) => async () => {
    const res = await api.gap({ gap_id: gapId, decision, pin: 'click' });
    if (res && (res as Record<string, unknown>).ok === false) throw new Error(String((res as Record<string, unknown>).error ?? 'The console did not accept that.'));
    setLocal(decision);
  };

  const [expanded, setExpanded] = useState(false);
  const chip = decided === 'confirm' ? <Chip tone="ok" icon={<CheckCircle2 {...ICON} />}>Confirmed</Chip>
    : decided === 'reject' ? <Chip tone="critical" icon={<XCircle {...ICON} />}>Rejected</Chip>
    : <Chip tone="healing" icon={<FileSearch {...ICON} />}>Gap</Chip>;
  return (
    <motion.article className="inbox-card inbox-gap" {...motionProps} layout={false}>
      <button type="button" className="inbox-gap__line" aria-expanded={expanded} onClick={() => setExpanded((x) => !x)} title={`${gapId}: ${topic}`}>
        <span className="mono inbox-id inbox-gap__id">{gapId}</span>
        <span className="inbox-gap__topic">{topic}</span>
        {chip}
        <ChevronDown {...ICON} className="inbox-gap__chev" />
      </button>
      {expanded && (
        <>
          {text && <p className="inbox-body">{text}</p>}
          {recommendation && <p className="inbox-body inbox-body--muted">Recommendation: {recommendation}</p>}
          {records.length > 0 && <div className="inbox-records">{records.map((r) => <span key={r} className="mono inbox-record" title={r}>{r}</span>)}</div>}
          {!decided && (
            <div className="inbox-actions">
              <ConfirmButton label="Confirm gap" confirmLabel="Confirm as a real gap" onConfirm={submit('confirm')} />
              <ConfirmButton label="Reject" confirmLabel="Confirm reject" tone="plain" onConfirm={submit('reject')} />
            </div>
          )}
        </>
      )}
    </motion.article>
  );
}
