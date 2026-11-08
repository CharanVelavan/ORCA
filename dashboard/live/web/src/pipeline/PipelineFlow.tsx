import { ChevronLeft, ChevronRight, CircleDashed, Maximize2, Minimize2, PanelRightClose, PanelRightOpen, Radio } from 'lucide-react';
import { useUi } from '../stage/uiStore';
import { ist } from '../stage/time';
import type { IconName } from './model';
import { ICONS } from './icons';
import { BANDS, NODES } from './pipelineNodes';
import { pathFor } from './scenarioPaths';
import { usePipeline, type Tone } from './pipelineStore';
import { FlowGraph, Ticker } from './FlowGraph';
import './pipeline.css';

const ICON = { size: 15, strokeWidth: 1.5, 'aria-hidden': true } as const;
const Icon = ({ name, size = 15 }: { name: IconName; size?: number }) => {
  const C = ICONS[name] ?? CircleDashed;
  return <C size={size} strokeWidth={1.5} aria-hidden />;
};

export function PipelineFlow({ truth }: { truth: boolean }) {
  const view = useUi((s) => s.pipeline);
  const setPipeline = useUi((s) => s.setPipeline);
  if (view === 'rail') return <PipelineRail onOpen={() => setPipeline('open')} />;
  return (
    <section className={`pf ${view === 'full' ? 'pf--full' : ''}`} aria-label="Pipeline flow">
      <Narration truth={truth} />
      <div className="pf-body"><FlowGraph truth={truth} /><Ticker /></div>
    </section>
  );
}

/* ------------------------------------------------------------------ narration bar (Floorplan Flows pattern) */
function Narration({ truth }: { truth: boolean }) {
  const { scenario, beats, reached, mode, explainIdx, setMode, explainStep } = usePipeline();
  const view = useUi((s) => s.pipeline);
  const setPipeline = useUi((s) => s.setPipeline);
  const path = pathFor(scenario);
  const steps = path?.steps ?? [];
  const beat = beats[beats.length - 1];
  const explaining = mode === 'explain' && steps[explainIdx];
  const title = explaining ? steps[explainIdx].title : beat?.title ?? 'Waiting for the exercise';
  const text = explaining ? steps[explainIdx].text : beat?.text ?? 'Start an exercise. Each step lights up here as it happens.';
  const n = explaining ? explainIdx : Math.max(0, reached);
  const band = NODES.find((x) => x.id === (explaining ? steps[explainIdx].node : beat?.node))?.band ?? 'network';
  const flowStep = BANDS.findIndex((b) => b.id === band) + 1;
  const key = explaining ? `e${explainIdx}` : `b${beat?.id ?? 0}`;
  return (
    <header className="pf-nar">
      <div className="pf-nar__top">
        <span className="pf-nar__mode" data-mode={mode}>{mode === 'live' ? <><Radio {...ICON} size={12} /> LIVE</> : mode === 'replay' ? 'REPLAY' : 'EXPLAIN'}</span>
        <span className="pf-nar__meta mono">{scenario} · step {flowStep} of 7{!explaining && beat ? ` · ${ist(beat.ts)}` : ''}</span>
        <span className="pf-nar__tools">
          <button className="pf-ib" aria-label="Previous step" title="Previous step (Left arrow)" onClick={() => explainStep(-1)}><ChevronLeft {...ICON} /></button>
          <button className="pf-ib" aria-label="Next step" title="Next step (Right arrow)" onClick={() => explainStep(1)}><ChevronRight {...ICON} /></button>
          {mode === 'explain' && <button className="pf-ib pf-ib--txt" onClick={() => setMode('live')} title="Back to live (Esc)">Live</button>}
          <button className="pf-ib" aria-label={view === 'full' ? 'Exit full screen' : 'Full screen'} title={view === 'full' ? 'Exit full screen (Esc)' : 'Full screen (F)'} onClick={() => setPipeline(view === 'full' ? 'open' : 'full')}>{view === 'full' ? <Minimize2 {...ICON} /> : <Maximize2 {...ICON} />}</button>
          <button className="pf-ib" aria-label="Collapse pipeline" title="Collapse (P)" onClick={() => setPipeline('rail')}><PanelRightClose {...ICON} /></button>
        </span>
      </div>
      {!truth && <span className="sr-only">Console view: ground truth hidden</span>}
    </header>
  );
}

/* ------------------------------------------------------------------ collapsed rail */
function PipelineRail({ onOpen }: { onOpen: () => void }) {
  const nodes = usePipeline((s) => s.nodes);
  const worst = (band: string): Tone | undefined => {
    const order: Tone[] = ['critical', 'warn', 'healing', 'accent', 'ok'];
    const tones = NODES.filter((n) => n.band === band).map((n) => nodes[n.id]).filter((x) => x && x.phase === 'active').map((x) => x!.tone);
    return order.find((t) => tones.includes(t));
  };
  return (
    <nav className="pf-rail" aria-label="Pipeline bands">
      <button className="pf-ib" onClick={onOpen} aria-label="Open pipeline" title="Open pipeline (P)"><PanelRightOpen {...ICON} /></button>
      {BANDS.map((b) => { const t = worst(b.id); return (
        <button key={b.id} className={`pf-rail__b ${t ? `t-${t}` : ''}`} onClick={onOpen} title={`${b.n} ${b.title}${t ? `: ${t === 'critical' ? 'alert' : t === 'warn' ? 'attention' : t === 'healing' ? 'healing' : t === 'accent' ? 'working' : 'ok'}` : ''}`}>
          <Icon name={b.icon} size={16} /><span className="mono">{b.n}</span>
        </button>); })}
    </nav>
  );
}
