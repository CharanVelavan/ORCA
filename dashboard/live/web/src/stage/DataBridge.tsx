import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { playFake } from '../fake/play';
import { connectStream } from '../stream';
import { useLiveStore } from '../store';
import { usePipeline } from '../pipeline/pipelineStore';
import type { LiveEvent } from '../types';
import { useUi } from './uiStore';
import { present } from './presenter';

/** Smooth over engine shape differences once, before any store sees the event. */
export function normalize(e: LiveEvent): LiveEvent {
  const out: LiveEvent = { ...e };
  if (typeof out.scenario === 'string') out.scenario = out.scenario.toUpperCase();
  if (String(out.kind).startsWith('agent_') && out.role == null && typeof out.actor === 'string') out.role = out.actor;
  if (out.kind === 'approval' && out.hash == null && out.plan_hash) out.hash = out.plan_hash;
  return out;
}

/** Which routes may see ground truth (audience 'control'). The Console never does. */
export const truthRoute = (path: string) => path === '/stage' || path === '/control' || path === '/review';

/** Connects the SSE stream (or the ?fake=1 fixture) to the live store and the Pipeline. Review drives its own replay. */
export function DataBridge() {
  const location = useLocation();
  useEffect(() => {
    if (location.pathname === '/review' || location.pathname === '/') return;
    const truth = truthRoute(location.pathname);
    const live = useLiveStore.getState();
    live.reset();
    usePipeline.getState().reset();
    usePipeline.setState({ truth });
    const apply = (event: LiveEvent) => {
      if (event.kind === 'session') useLiveStore.getState().reset(); // a new run starts: drop the old one
      const s = useLiveStore.getState();
      if (truth) s.addControl(event); else s.add(event);
      usePipeline.getState().ingest(event, truth);
    };
    const q = new URLSearchParams(location.search);
    const fake = q.get('fake') === '1';
    // The Stage is presented step by step (presenter.ts); other routes get events as they come.
    const guided = location.pathname === '/stage' ? present(apply, { live: !fake }) : null;
    const receive = (raw: LiveEvent) => {
      const e = normalize(raw);
      // On the Stage, a finished run's history must not paint the setup screen; Start sends a fresh session.
      if (guided && useUi.getState().mode !== 'running' && e.kind !== 'tick' && e.kind !== 'session') return;
      if (guided) guided.push(e, truth); else apply(e);
    };
    // Back to setup: clear the last run so the scene and flowchart start clean.
    const offUi = useUi.subscribe((u, prev) => { if (u.mode === 'setup' && prev.mode === 'running') { useLiveStore.getState().reset(); usePipeline.getState().reset(); } });
    const stop = fake
      ? (location.pathname === '/stage' && useUi.getState().start(), playFake(receive, q.get('scn') ?? 'S1', Number(q.get('pace') ?? 1200)))
      : connectStream(0, receive);
    return () => { stop(); guided?.stop(); offUi(); };
  }, [location.pathname, location.search]);
  return null;
}
