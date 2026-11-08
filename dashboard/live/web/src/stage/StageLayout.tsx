import { Component, lazy, Suspense, useCallback, useRef, useState, type KeyboardEvent as ReactKeyEvent, type PointerEvent as ReactPointerEvent, type ReactNode } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { PipelineFlow } from '../pipeline/PipelineFlow';
import { CommanderInbox } from '../inbox';
import { useUi } from './uiStore';
import { TopBar } from './TopBar';
import { useStageKeys } from './useKeys';
import './stage.css';

const NetworkScene = lazy(() => import('../scenes/NetworkScene').then((m) => ({ default: m.NetworkScene })));
const enter = [0.165, 0.84, 0.44, 1] as const;
const morph = [0.645, 0.045, 0.355, 1] as const;

/** WebGL can be missing (old projector PC, locked-down browser). The 3D view must never take the console down. */
class SceneBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (this.state.failed) return <div className="st-scene-wait"><span className="mono">3D view unavailable on this device (no WebGL). The Pipeline and inbox keep working.</span></div>;
    return this.props.children;
  }
}

export function Scene3D({ truth }: { truth: boolean }) {
  return <SceneBoundary><Suspense fallback={<div className="st-scene-wait mono">Loading emulated network</div>}><NetworkScene truth={truth} /></Suspense></SceneBoundary>;
}

const SPLIT_KEY = 'orca-split';
const SPLIT_DEFAULT = 0.6;
const SPLIT_MIN = 0.4;
const SPLIT_MAX = 0.75;
const RAIL_PX = 64;
const clampSplit = (v: number) => Math.min(SPLIT_MAX, Math.max(SPLIT_MIN, v));
const readSplit = () => {
  try {
    const v = parseFloat(localStorage.getItem(SPLIT_KEY) ?? '');
    return Number.isFinite(v) ? clampSplit(v) : SPLIT_DEFAULT;
  } catch { return SPLIT_DEFAULT; }
};
const writeSplit = (v: number) => { try { localStorage.setItem(SPLIT_KEY, String(v)); } catch { /* storage may be blocked */ } };

/**
 * Shared frame for Stage and Console.
 * setup:   [ left 34% | 3D ]
 * running: [ rail 64px | Pipeline flowchart (--split of the rest, default 60%) | 8px drag handle | 3D over inbox (60/40) ]
 * The handle is draggable (40-75%), keyboard-operable and persisted in localStorage `orca-split`.
 * Dragging only writes the CSS variable --split on .st-main; React state is committed on pointer-up.
 * Pipeline 'rail' mode: 56px column, handle hidden. 'full' mode is handled inside PipelineFlow.
 */
export function StageLayout({ view, truth, setupPanel, rail: railPanel, drawer, running }: {
  view: 'stage' | 'console'; truth: boolean; running: boolean;
  setupPanel?: ReactNode; rail: ReactNode; drawer?: ReactNode;
}) {
  const pipeline = useUi((s) => s.pipeline);
  const reduced = useReducedMotion();
  useStageKeys(view === 'stage');
  const t = (d: number, ease: readonly number[] = enter) => (reduced ? { duration: 0 } : { duration: d, ease: ease as unknown as number[] });
  const [split, setSplit] = useState(readSplit);
  const mainRef = useRef<HTMLElement>(null);
  const live = useRef(split);
  const setVar = (v: number) => { live.current = v; mainRef.current?.style.setProperty('--split', String(v)); };
  const commit = useCallback((v: number) => { const c = clampSplit(v); live.current = c; setSplit(c); writeSplit(c); }, []);
  const drag = useRef<{ id: number } | null>(null);
  const onDown = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    drag.current = { id: e.pointerId };
    mainRef.current?.setAttribute('data-dragging', '');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  };
  const onMove = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (!drag.current || !mainRef.current) return;
    const r = mainRef.current.getBoundingClientRect();
    const usable = r.width - RAIL_PX;
    if (usable > 0) setVar(clampSplit((e.clientX - r.left - RAIL_PX) / usable));
  };
  const endDrag = (e: ReactPointerEvent<HTMLDivElement>) => {
    if (!drag.current) return;
    drag.current = null;
    try { e.currentTarget.releasePointerCapture(e.pointerId); } catch { /* already released */ }
    mainRef.current?.removeAttribute('data-dragging');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    commit(live.current);
  };
  const onKeyDown = (e: ReactKeyEvent<HTMLDivElement>) => {
    const step = e.key === 'ArrowLeft' ? -0.08 : e.key === 'ArrowRight' ? 0.08 : 0;
    if (step) { commit(live.current + step); setVar(clampSplit(live.current)); }
    else if (e.key === 'Home') { commit(SPLIT_DEFAULT); setVar(SPLIT_DEFAULT); }
    else return;
    e.preventDefault();
    e.stopPropagation();
  };
  const onReset = () => { commit(SPLIT_DEFAULT); setVar(SPLIT_DEFAULT); };
  const rail = pipeline === 'rail';
  const cols = running
    ? rail
      ? `${RAIL_PX}px 56px 0 minmax(0,1fr)`
      : `${RAIL_PX}px minmax(0, calc(var(--split) * (100% - ${RAIL_PX}px))) 8px minmax(0,1fr)`
    : 'clamp(420px, 34%, 620px) minmax(0,1fr)';
  return (
    <div className="st-app">
      <TopBar view={view} />
      <main ref={mainRef} className="st-main" style={{ gridTemplateColumns: cols, ['--split' as string]: split }} data-running={running || undefined} data-pipe={running ? pipeline : undefined}>
        <AnimatePresence initial={false} mode="popLayout">
          {running ? (
            <motion.aside key="rail" className="st-rail" initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }} transition={t(0.24)}>{railPanel}</motion.aside>
          ) : (
            <motion.aside key="setup" className="st-setup" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -32 }} transition={t(0.32, morph)}>{setupPanel}</motion.aside>
          )}
        </AnimatePresence>
        {running && (
          <>
            <aside className="st-pipe st-enter-left">
              <PipelineFlow truth={truth} />
            </aside>
            <div
              className="st-split"
              role="separator"
              aria-orientation="vertical"
              aria-label="Resize Pipeline and 3D view"
              aria-valuemin={40}
              aria-valuemax={75}
              aria-valuenow={Math.round(split * 100)}
              tabIndex={rail ? -1 : 0}
              aria-hidden={rail || undefined}
              onPointerDown={onDown}
              onPointerMove={onMove}
              onPointerUp={endDrag}
              onPointerCancel={endDrag}
              onLostPointerCapture={endDrag}
              onDoubleClick={onReset}
              onKeyDown={onKeyDown}
            ><span className="st-split-grip" aria-hidden="true" /></div>
          </>
        )}
        <section className="st-center">
          <div className="st-scene">
            <Scene3D truth={truth} />
            {drawer}
          </div>
          {running && (
            <div className="st-inbox st-enter-up">
              <CommanderInbox />
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
