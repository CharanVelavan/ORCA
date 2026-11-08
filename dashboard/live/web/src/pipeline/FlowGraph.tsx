import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from 'react';
import { useReducedMotion } from 'framer-motion';
import { Check, CircleDashed, Clock3 } from 'lucide-react';
import { api } from '../api';
import { PinPad } from '../inbox';
import { useUi } from '../stage/uiStore';
import { ist, leftOf } from '../stage/time';
import type { BandId, NodeDef } from './model';
import { ICONS } from './icons';
import { BANDS, NODES } from './pipelineNodes';
import { pathFor } from './scenarioPaths';
import { usePipeline, type Beat, type NodeInfo, type Packet, type Tone } from './pipelineStore';

// Flowchart v2 (docs/plan/FLOWCHART_V2_PLAN.md): one lane per band, top to bottom, each node drawn in its own
// shape. Edges appear as packets cross them, a dot carries each packet, and the latest sentence sits in a bubble
// next to the node that acted. Positions are measured from the DOM so text keeps its real pixel size.

const BAND_TITLE: Record<BandId, string> = {
  network: 'Chennai network', threat: 'Threat', detect: 'AI models detect', coordinate: 'Agents coordinate',
  commander: 'Commander decides', execute: 'Fix and self-heal', gaps: 'Policy gaps found',
};
const BAND_SUB: Record<BandId, string> = {
  network: 'Emulated satellite backhaul', threat: 'What the attacker does', detect: '4 models watch every link',
  coordinate: '6 agents talk by protocol', commander: 'Code decides, human approves', execute: 'Tested, staged, verified',
  gaps: 'Missing in Indian rules',
};
const BAND_OF: Record<string, BandId> = Object.fromEntries(NODES.map((n) => [n.id, n.band]));
const DEF: Record<string, NodeDef> = Object.fromEntries(NODES.map((n) => [n.id, n]));
const EXEC_ORDER = ['exec:clone', 'exec:r5', 'exec:r25', 'exec:r100', 'exec:reattack', 'exec:cleanpath', 'exec:failover', 'exec:return', 'exec:rollback'];
const AGENT_HUE: Record<string, string> = {
  'agent:mobile_operator': '#5B8DEF', 'agent:satellite_operator': '#3FB5C9', 'agent:power_utility': '#D9B341',
  'agent:cert_in': '#E08A4F', 'agent:regulator': '#A77BD9', 'agent:gap_analyst': '#4FB58A',
};
const holdMs = (speed: number) => (speed >= 10 ? 90 : speed >= 5 ? 160 : speed >= 2 ? 360 : 700);
const lit = (n?: NodeInfo) => !!n && (n.phase === 'active' || (n.phase === 'done' && !!n.at));

/** Which nodes each lane shows. Lanes only show what matters to this run, so nothing is crammed. */
function laneNodes(band: BandId, nodes: Record<string, NodeInfo>, truth: boolean): string[] {
  const ids = NODES.filter((n) => n.band === band).map((n) => n.id);
  switch (band) {
    case 'threat':
      return truth ? ids.filter((id) => !DEF[id].consoleOnly && nodes[id] && nodes[id].phase !== 'idle') : ['threat:anomaly'];
    case 'execute': {
      const on = EXEC_ORDER.filter((id) => nodes[id] && (nodes[id].phase !== 'idle' || lit(nodes[id])) && (id !== 'exec:rollback' || lit(nodes[id])));
      return on.length ? on : ['exec:clone', 'exec:r5', 'exec:r25', 'exec:r100', 'exec:reattack'];
    }
    case 'gaps':
      return ids.filter((id) => nodes[id] && (nodes[id].phase !== 'idle' || lit(nodes[id])));
    default:
      return ids;
  }
}

type Box = { x: number; y: number; w: number; h: number };
type Edge = { key: string; from: string; to: string; tone: Tone; n: number };

/** Curved route between two node boxes: vertical S-curve between lanes, an arc over the top inside a lane. */
function route(a: Box, b: Box): string {
  const ax = a.x + a.w / 2, bx = b.x + b.w / 2;
  if (Math.abs(a.y - b.y) < 8) {
    const y = Math.min(a.y, b.y) + 2, lift = Math.min(46, 18 + Math.abs(ax - bx) / 6);
    return `M${ax},${y} C${ax},${y - lift} ${bx},${y - lift} ${bx},${y}`;
  }
  const down = b.y > a.y;
  const y0 = down ? a.y + a.h : a.y, y1 = down ? b.y : b.y + b.h;
  const k = Math.max(24, Math.abs(y1 - y0) * 0.45) * (down ? 1 : -1);
  return `M${ax},${y0} C${ax},${y0 + k} ${bx},${y1 - k} ${bx},${y1}`;
}

export function FlowGraph({ truth }: { truth: boolean }) {
  const nodes = usePipeline((s) => s.nodes);
  const beats = usePipeline((s) => s.beats);
  const mode = usePipeline((s) => s.mode);
  const explainIdx = usePipeline((s) => s.explainIdx);
  const scenario = usePipeline((s) => s.scenario);
  const current = usePipeline((s) => s.current);
  const pending = usePipeline((s) => s.pending);
  const speed = useUi((s) => s.config.speed);
  const reduced = !!useReducedMotion();

  const lanes = useMemo(() => BANDS.map((b) => ({ band: b, ids: laneNodes(b.id, nodes, truth) })), [nodes, truth]);
  const shown = useMemo(() => new Set(lanes.flatMap((l) => l.ids)), [lanes]);

  // Focus: the node of the latest sentence (or the explained step).
  const step = mode === 'explain' ? pathFor(scenario)?.steps[explainIdx] : undefined;
  const beat: Beat | undefined = beats[beats.length - 1];
  const focusNode = step?.node ?? beat?.node ?? 'sat';
  const focusBand = BAND_OF[focusNode] ?? 'network';
  const reachedBand = BANDS.reduce((acc, b, i) => (lanes[i].ids.some((id) => lit(nodes[id])) && b.id !== 'network' ? i : acc), 0);

  // ---- measuring
  const wrap = useRef<HTMLDivElement>(null);
  const els = useRef(new Map<string, HTMLElement>());
  const [boxes, setBoxes] = useState<Record<string, Box>>({});
  const [size, setSize] = useState({ w: 0, h: 0 });
  const reg = useCallback((id: string) => (el: HTMLElement | null) => { if (el) els.current.set(id, el); else els.current.delete(id); }, []);
  const measure = useCallback(() => {
    const w = wrap.current; if (!w) return;
    const base = w.getBoundingClientRect();
    const out: Record<string, Box> = {};
    els.current.forEach((el, id) => { const r = el.getBoundingClientRect(); out[id] = { x: r.left - base.left, y: r.top - base.top, w: r.width, h: r.height }; });
    setBoxes(out); setSize({ w: w.scrollWidth, h: w.scrollHeight });
  }, []);
  useLayoutEffect(() => { const id = requestAnimationFrame(measure); return () => cancelAnimationFrame(id); }, [measure, nodes, lanes, pending.length]);
  useEffect(() => {
    const w = wrap.current; if (!w) return;
    const ro = new ResizeObserver(() => measure()); ro.observe(w);
    return () => ro.disconnect();
  }, [measure]);

  // ---- director queue: one packet holds the stage at a time (state is already updated)
  const next = usePipeline((s) => s.nextPacket);
  const queued = usePipeline((s) => s.queue.length);
  useEffect(() => { if (!current && queued) next(); }, [current, queued, next]);
  useEffect(() => {
    if (!current) return;
    const t = window.setTimeout(next, reduced ? 0 : holdMs(speed) + 80);
    return () => window.clearTimeout(t);
  }, [current, next, speed, reduced]);

  // ---- edges that have carried a packet this run
  const [edges, setEdges] = useState<Edge[]>([]);
  useEffect(() => { setEdges([]); }, [scenario]);
  useEffect(() => {
    if (!current) return;
    const key = `${current.from}>${current.to}`;
    setEdges((es) => {
      const old = es.find((e) => e.key === key);
      const rest = es.filter((e) => e.key !== key);
      return [...rest, { key, from: current.from, to: current.to, tone: current.tone, n: (old?.n ?? 0) + 1 }].slice(-48);
    });
  }, [current]);

  // ---- keep the focused lane on screen
  const scroller = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scroller.current, b = boxes[focusNode] ?? boxes[`band:${focusBand}`];
    if (!el || !b) return;
    if (b.y < el.scrollTop + 160 || b.y + b.h > el.scrollTop + el.clientHeight - 60) el.scrollTo({ top: Math.max(0, b.y - 170), behavior: reduced ? 'auto' : 'smooth' });
  }, [focusNode, focusBand, boxes, reduced]);

  const activeKey = current ? `${current.from}>${current.to}` : '';
  const rail0 = boxes[`band:${BANDS[0].id}`], railN = boxes[`band:${BANDS[BANDS.length - 1].id}`], railR = boxes[`band:${BANDS[reachedBand].id}`];
  const railX = rail0 ? rail0.x + rail0.w / 2 : 0;
  const railTop = rail0 ? rail0.y + rail0.h / 2 : 0, railEnd = railN ? railN.y + railN.h / 2 : 0, railFill = railR ? railR.y + railR.h / 2 : railTop;

  return (
    <div className="fg-scroll" ref={scroller}>
      <div className="fg" ref={wrap} data-reduced={reduced || undefined}>
        {/* progress rail: fills like a video bar to the furthest lane reached */}
        {rail0 && railN && <>
          <div className="fg-rail" style={{ left: railX - 2, top: railTop, height: railEnd - railTop }} aria-hidden />
          <div className="fg-rail fg-rail--fill" style={{ left: railX - 2, top: railTop, height: railEnd - railTop, transform: `scaleY(${railEnd > railTop ? (railFill - railTop) / (railEnd - railTop) : 0})` }} aria-hidden />
        </>}

        <svg className="fg-edges" width={size.w} height={size.h} aria-hidden>
          {edges.map((e) => {
            const a = boxes[e.from], b = boxes[e.to];
            if (!a || !b || !shown.has(e.from) || !shown.has(e.to)) return null;
            const on = e.key === activeKey;
            return <path key={e.key} d={route(a, b)} className={`fg-e t-${e.tone} ${on ? 'is-on' : ''}`} style={{ strokeWidth: on ? 3 : Math.min(2.4, 1 + e.n * 0.25) }} />;
          })}
        </svg>

        {lanes.map(({ band, ids }, i) => {
          const state = band.id === focusBand ? 'now' : i <= reachedBand ? 'past' : 'future';
          const Icon = ICONS[band.icon];
          return (
            <section key={band.id} className={`fg-lane is-${state}`} data-band={band.id} aria-label={BAND_TITLE[band.id]}>
              <header className="fg-lh">
                <span className="fg-lh__n mono" ref={reg(`band:${band.id}`)}>{i < reachedBand || (i === reachedBand && band.id !== focusBand) ? <Check size={16} strokeWidth={2.2} /> : band.n}</span>
                <span className="fg-lh__t"><b><Icon size={15} strokeWidth={1.75} aria-hidden /> {band.id === 'threat' && !truth ? 'Anomaly' : BAND_TITLE[band.id]}</b><small>{band.id === 'threat' && !truth ? 'Cause not yet known' : BAND_SUB[band.id]}</small></span>
              </header>
              <div className={`fg-row fg-row--${band.id}`}>
                {ids.length === 0 && <Ghost band={band.id} />}
                {ids.map((id) => <GraphNode key={id} id={id} info={nodes[id]} focus={id === focusNode} reg={reg(id)} />)}
                {band.id === 'commander' && pending.length > 0 && <ApprovalAsk />}
              </div>
            </section>
          );
        })}

        {current && !reduced && boxes[current.from] && boxes[current.to] && shown.has(current.from) && shown.has(current.to) && (
          <PacketDot key={current.id} p={current} path={route(boxes[current.from], boxes[current.to])} ms={holdMs(speed)} />
        )}
        <Bubble beat={beat} step={step} box={boxes[focusNode] ?? boxes[`band:${focusBand}`]} width={size.w} />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ nodes, one shape per kind */
const SHAPES: Partial<Record<NodeDef['kind'], ReactNode>> = {
  threat: <polygon points="7,0 93,0 100,50 93,100 7,100 0,50" />,
  rules: <polygon points="50,1 99,50 50,99 1,50" />,
  human: <path d="M50 2 L97 14 L97 52 Q97 84 50 98 Q3 84 3 52 L3 14 Z" />,
  step: <polygon points="0,0 88,0 100,50 88,100 0,100 10,50" />,
  gap: <polygon points="0,0 84,0 100,16 100,100 0,100" />,
};

function GraphNode({ id, info, focus, reg }: { id: string; info?: NodeInfo; focus: boolean; reg: (el: HTMLElement | null) => void }) {
  const def = DEF[id];
  const n = info ?? { phase: 'idle' as const };
  const Icon = ICONS[def.icon] ?? CircleDashed;
  const state = n.phase === 'active' ? 'active' : lit(n) || def.band === 'network' || def.band === 'detect' ? 'done' : 'future';
  const cls = `fg-n fg-n--${def.kind} is-${state} t-${n.tone ?? 'unknown'} ${focus ? 'is-focus' : ''} ${n.pulse ? 'is-pulse' : ''}`;
  const style = (AGENT_HUE[id] ? { '--hue': AGENT_HUE[id] } : undefined) as CSSProperties | undefined;
  const title = `${def.label} · ${def.role}${n.word ? ` · ${n.word}` : ''}${n.detail ? ` · ${n.detail}` : ''}`;
  const shape = SHAPES[def.kind];

  if (def.kind === 'agent') {
    return (
      <div className={cls} style={style} title={title}>
        <span className="fg-av" ref={reg}><span className="fg-av__ring" aria-hidden /><Icon size={22} strokeWidth={1.6} aria-hidden /></span>
        <b className="fg-n__label">{def.label}</b>
        <span className="fg-word mono">{n.word ?? 'IDLE'}</span>
        {n.detail && <span className="fg-n__detail">{n.detail}</span>}
      </div>
    );
  }
  if (def.kind === 'model') return <ModelCard id={id} n={n} cls={cls} title={title} reg={reg} />;
  if (def.kind === 'clocks') {
    return (
      <div className={cls} ref={reg} title={title}>
        <span className="fg-dial" aria-hidden><svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="16" className="fg-dial__bg" /><circle cx="20" cy="20" r="16" className="fg-dial__arc" /></svg><Icon size={16} strokeWidth={1.75} /></span>
        <span className="fg-n__txt"><b className="fg-n__label">{def.label}</b><span className="fg-n__detail">{n.detail ?? 'No deadline yet'}</span></span>
      </div>
    );
  }
  return (
    <div className={cls} ref={reg} title={title}>
      {shape && <svg className="fg-shape" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>{shape}</svg>}
      <Icon className="fg-n__icon" size={def.kind === 'site' ? 15 : 17} strokeWidth={1.6} aria-hidden />
      <span className="fg-n__txt">
        <b className="fg-n__label">{def.label}</b>
        {def.kind !== 'site' && def.kind !== 'step' && def.kind !== 'rules' && !(def.band === 'network' && (n.tone === 'ok' || n.tone === 'unknown')) && <span className="fg-n__detail">{n.detail ?? def.role}</span>}
      </span>
      {n.word && def.kind !== 'site' && def.kind !== 'satellite' && <span className="fg-word mono">{n.word}</span>}
      {def.kind === 'site' && n.word && n.word !== 'OK' && <span className="fg-word mono">{n.word}</span>}
    </div>
  );
}

function ModelCard({ id, n, cls, title, reg }: { id: string; n: NodeInfo; cls: string; title: string; reg: (el: HTMLElement | null) => void }) {
  const def = DEF[id];
  const m1 = usePipeline((s) => s.m1);
  const Icon = ICONS[def.icon];
  const pts = id === 'model:M1' && m1.scores.length > 1
    ? m1.scores.map((v, i) => `${(i / (m1.scores.length - 1)) * 100},${30 - Math.min(1, v) * 28}`).join(' ')
    : '';
  return (
    <div className={cls} ref={reg} title={title}>
      <span className="fg-mc__top"><span className="fg-mc__id mono">{id.slice(6)}</span><Icon size={16} strokeWidth={1.6} aria-hidden /><b className="fg-n__label">{def.label}</b></span>
      <span className="fg-mc__mid">
        <span className="fg-word mono">{n.word ?? 'NORMAL'}</span>
        {pts && <svg className="fg-spark" viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden><line x1="0" x2="100" y1={30 - m1.threshold * 28} y2={30 - m1.threshold * 28} className="fg-spark__th" /><polyline points={pts} /></svg>}
      </span>
      <span className="fg-n__detail">{n.detail ?? def.role}</span>
    </div>
  );
}

function Ghost({ band }: { band: BandId }) {
  return <div className="fg-ghost">{band === 'gaps' ? 'Gaps appear here as the rule engine finds them' : band === 'threat' ? 'No attack or fault yet' : 'Waiting'}</div>;
}

/* ------------------------------------------------------------------ packet, bubble, approval */
function PacketDot({ p, path, ms }: { p: Packet; path: string; ms: number }) {
  const style = { offsetPath: `path('${path}')`, animationDuration: `${ms}ms` } as CSSProperties;
  return (
    <div className={`fg-pk t-${p.tone} ${p.bounce ? 'is-bounce' : ''}`} style={style} aria-hidden>
      <span className="fg-pk__dot" /><span className="fg-pk__label mono">{p.label}</span>
    </div>
  );
}

function Bubble({ beat, step, box, width }: { beat?: Beat; step?: { node: string; title: string; text: string }; box?: Box; width: number }) {
  if (!box || (!beat && !step)) return null;
  const title = step?.title ?? beat!.title, text = step?.text ?? beat!.text, tone = step ? 'accent' : beat!.tone;
  const actor = DEF[step?.node ?? beat!.node];
  const W = Math.min(380, Math.max(260, width * 0.36));
  const cx = box.x + box.w / 2;
  const left = Math.max(8, Math.min(width - W - 8, cx - W / 2));
  const above = box.y > 150;
  const style: CSSProperties = above ? { left, top: box.y - 10, width: W, transform: 'translateY(-100%)' } : { left, top: box.y + box.h + 10, width: W };
  return (
    <div key={`${step ? 's' : 'b'}${beat?.id ?? 0}${step?.title ?? ''}`} className={`fg-bub t-${tone} ${above ? 'is-above' : 'is-below'}`} style={{ ...style, '--tail': `${Math.max(16, Math.min(W - 16, cx - left))}px` } as CSSProperties} role="status">
      <span className="fg-bub__who mono">{actor ? actor.label : ''}{beat && !step ? ` · ${ist(beat.ts)}` : ''}</span>
      <b>{title}</b>
      <span className="fg-bub__txt">{text}</span>
    </div>
  );
}

function ApprovalAsk() {
  const pending = usePipeline((s) => s.pending);
  const ts = usePipeline((s) => s.ts);
  const { pinFor, pinAt, openPin } = useUi();
  const p = pending[pending.length - 1];
  if (!p) return null;
  const open = pinFor === p.hash && pinAt === 'node';
  return (
    <div className="fc-ask fg-ask">
      <div className="fc-ask__title">{p.title}</div>
      <div className="fc-ask__meta mono">{p.playbook} · {p.targets.join(', ')} · asked by {p.owner.replace(/_/g, ' ')}</div>
      <div className="fc-ask__row">
        <span className="fc-ask__wait"><Clock3 size={14} strokeWidth={1.75} />Awaiting your approval</span>
        <span className="mono fc-ask__exp">{leftOf(ts, p.expires_at)} left</span>
      </div>
      {open ? (
        <div className="fc-ask__pin">
          <PinPad compact title={`Approve ${p.playbook}`} subtitle={`#${p.hash.slice(0, 4)}`} onSubmit={async (pin) => { await api.approve({ hash: p.hash, pin }); openPin(null); }} onCancel={() => openPin(null)} />
        </div>
      ) : (
        <button className="fc-btn" onClick={() => openPin(p.hash, 'node')}>Approve with PIN</button>
      )}
      {pending.length > 1 && <div className="fc-ask__more">{pending.length - 1} more in the inbox</div>}
    </div>
  );
}

/* ------------------------------------------------------------------ ticker: the last sentences, so nothing is missed */
export function Ticker() {
  const beats = usePipeline((s) => s.beats);
  const rows: Beat[] = [];
  for (let i = beats.length - 1; i >= 0 && rows.length < 4; i--) { const b = beats[i]; if (!rows.some((r) => r.title === b.title && r.text === b.text)) rows.push(b); }
  return (
    <ol className="fg-tick" aria-label="Latest events" aria-live="polite">
      {rows.length === 0 && <li className="fg-tick__empty">Events appear here as they happen.</li>}
      {rows.map((b, i) => {
        const d = DEF[b.node];
        const Icon = d ? ICONS[d.icon] : CircleDashed;
        return (
          <li key={b.id} className={`t-${b.tone} ${i === 0 ? 'is-new' : ''}`}>
            <span className="mono fg-tick__at">{ist(b.ts)}</span>
            <Icon size={15} strokeWidth={1.75} aria-hidden />
            <span className="fg-tick__who">{d?.label ?? ''}</span>
            <span className="fg-tick__txt" title={`${b.title}. ${b.text}`}><b>{b.title}.</b> {b.text}</span>
          </li>
        );
      })}
    </ol>
  );
}
