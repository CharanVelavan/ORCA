import { useEffect, useState } from 'react';
import { Pause, Play, SkipForward } from 'lucide-react';
import { usePresenter } from '../stage/presenter';
import { BANDS } from './pipelineNodes';
import { pathFor } from './scenarioPaths';
import { usePipeline } from './pipelineStore';
import { ICONS } from './icons';

/** "What happens next" card over the flowchart. The run is paused while it shows. */
export function GuideCard() {
  const card = usePresenter((s) => s.card);
  const skip = usePresenter((s) => s.skip);
  const scenario = usePipeline((s) => s.scenario);
  const [, tick] = useState(0);
  useEffect(() => { if (!card) return; const t = window.setInterval(() => tick((n) => n + 1), 100); return () => window.clearInterval(t); }, [card]);
  if (!card) return null;
  const left = Math.max(0, card.started + card.ms - Date.now());
  const pct = 1 - left / card.ms;
  if (card.kind === 'intro') {
    const path = pathFor(scenario);
    return (
      <div className="gd-wrap" role="dialog" aria-label="What will happen">
        <div className="gd gd--intro">
          <span className="gd-kicker mono">{scenario} · what will happen</span>
          <h2>{path?.title ?? card.title}</h2>
          {path?.story && <p className="gd-story">{path.story}</p>}
          <ol className="gd-steps">
            {BANDS.slice(1).map((b) => { const I = ICONS[b.icon]; return <li key={b.id}><span className="gd-n mono">{b.n}</span><I size={17} strokeWidth={1.75} aria-hidden /><b>{b.title}</b><span>{b.subtitle}</span></li>; })}
          </ol>
          <Footer pct={pct} onSkip={skip} label="Begin now" />
        </div>
      </div>
    );
  }
  const band = BANDS.find((b) => b.id === card.band);
  const Icon = band ? ICONS[band.icon] : null;
  return (
    <div className="gd-wrap" role="dialog" aria-label={`Next: ${card.title}`}>
      <div className={`gd gd--step b-${card.band}`} key={card.started}>
        <span className="gd-kicker mono">Next · step {band?.n ?? ''} of 7</span>
        <h2>{Icon && <Icon size={26} strokeWidth={1.75} aria-hidden />}{card.title}</h2>
        <p>{card.text}</p>
        <Footer pct={pct} onSkip={skip} label="Continue" />
      </div>
    </div>
  );
}

function Footer({ pct, onSkip, label }: { pct: number; onSkip: () => void; label: string }) {
  return (
    <div className="gd-foot">
      <span className="gd-bar" aria-hidden><i style={{ transform: `scaleX(${pct})` }} /></span>
      <span className="gd-note">Simulation paused</span>
      <button className="gd-btn" onClick={onSkip}><SkipForward size={15} strokeWidth={1.75} aria-hidden />{label}</button>
    </div>
  );
}

/** Small control in the narration bar: hold the run, and see how many events are still to show. */
export function GuideControls() {
  const held = usePresenter((s) => s.held);
  const queued = usePresenter((s) => s.queued);
  const toggle = usePresenter((s) => s.toggleHold);
  return (
    <button className="pf-ib pf-ib--txt" onClick={toggle} title={held ? 'Resume the run' : 'Hold the run here'} aria-pressed={held}>
      {held ? <Play size={14} strokeWidth={1.75} aria-hidden /> : <Pause size={14} strokeWidth={1.75} aria-hidden />}{held ? 'Resume' : 'Hold'}{queued > 0 ? <span className="mono gd-q">{queued}</span> : null}
    </button>
  );
}
