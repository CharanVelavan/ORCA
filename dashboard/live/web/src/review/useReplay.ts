import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../api';
import { usePipeline } from '../pipeline/pipelineStore';
import { useLiveStore } from '../store';
import type { LiveEvent } from '../types';
import { normalizeEvents, scenarioFromFile } from './normalize';

export type Speed = 1 | 4 | 10;

/** Real-time gap before event i+1 plays: 1.2 s per sim minute at x1, 250 ms inside a minute, scaled by speed. */
export const gapMs = (a: LiveEvent, b: LiveEvent, speed: Speed): number => {
  const dm = Math.max(0, Number(b.t) - Number(a.t));
  const base = dm > 0 ? Math.min(3000, dm * 1200) : 250;
  return Math.max(30, base / speed);
};

export function useReplay(file: string | null) {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cursor, setCursor] = useState(0); // number of events applied
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<Speed>(1);
  const applied = useRef(0);
  const eventsRef = useRef<LiveEvent[]>([]);

  const scenario = useMemo(() => {
    const s = events.find((e) => e.kind === 'session');
    return s ? String(s.scenario) : scenarioFromFile(file ?? '');
  }, [events, file]);
  const scenarioRef = useRef(scenario);
  scenarioRef.current = scenario;

  useEffect(() => {
    usePipeline.getState().setMode('replay');
    return () => { usePipeline.getState().setMode('live'); };
  }, []);

  const rebuild = useCallback((target: number, sc: string) => {
    const list = eventsRef.current;
    usePipeline.getState().reset(sc);
    useLiveStore.getState().reset();
    for (let i = 0; i < target; i++) { useLiveStore.getState().addControl(list[i]); usePipeline.getState().ingest(list[i], true); }
    usePipeline.setState({ queue: [], current: null }); // silent: no packets for a seek
    applied.current = target;
  }, []);

  const seek = useCallback((raw: number) => {
    const list = eventsRef.current;
    const target = Math.max(0, Math.min(list.length, Math.round(raw)));
    if (target === applied.current) { setCursor(target); return; }
    if (target < applied.current || target - applied.current > 1) rebuild(target, scenarioRef.current);
    else { const e = list[applied.current]; useLiveStore.getState().addControl(e); usePipeline.getState().ingest(e, true); applied.current = target; }
    setCursor(target);
  }, [rebuild]);

  useEffect(() => {
    if (!file) { eventsRef.current = []; setEvents([]); return; }
    let live = true;
    setLoading(true); setError(null); setPlaying(false);
    api.replay(file).then((res) => {
      if (!live) return;
      const raw = (Array.isArray(res.events) ? res.events : []) as LiveEvent[];
      const list = normalizeEvents(raw, file);
      eventsRef.current = list; setEvents(list);
      const sc = (list.find((e) => e.kind === 'session')?.scenario as string | undefined) ?? scenarioFromFile(file);
      scenarioRef.current = sc;
      rebuild(0, sc); setCursor(0);
    }).catch((err: unknown) => { if (live) { eventsRef.current = []; setEvents([]); setError(err instanceof Error ? err.message : 'Cannot load recording'); } })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [file, rebuild]);

  useEffect(() => {
    if (!playing) return;
    const list = eventsRef.current;
    if (cursor >= list.length) { setPlaying(false); return; }
    const delay = cursor === 0 ? 200 : gapMs(list[cursor - 1], list[cursor], speed);
    const id = window.setTimeout(() => seek(cursor + 1), delay);
    return () => window.clearTimeout(id);
  }, [playing, cursor, speed, seek]);

  const play = useCallback(() => {
    if (!eventsRef.current.length) return;
    if (applied.current >= eventsRef.current.length) seek(0);
    setPlaying(true);
  }, [seek]);
  const pause = useCallback(() => setPlaying(false), []);
  const toggle = useCallback(() => (playing ? pause() : play()), [playing, play, pause]);
  const step = useCallback((delta: number) => { setPlaying(false); seek(applied.current + delta); }, [seek]);
  const jump = useCallback((i: number) => { setPlaying(false); seek(i); }, [seek]);

  return { events, loading, error, cursor, playing, speed, scenario, setSpeed, play, pause, toggle, step, seek: jump };
}
