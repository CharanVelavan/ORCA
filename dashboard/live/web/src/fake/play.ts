import type { LiveEvent } from '../types';

/**
 * ?fake=1[&scn=S1] plays a stream captured from the real engine (public/fixtures/<scn>.json),
 * paced by sim minute so the Pipeline can be checked without a running engine.
 */
export function playFake(onEvent: (event: LiveEvent) => void, scenario = 'S1', msPerMinute = 1200) {
  let stopped = false;
  const timers: number[] = [];
  fetch(`./fixtures/${encodeURIComponent(scenario)}.json`)
    .then((r) => r.json() as Promise<LiveEvent[]>)
    .then((events) => {
      let lastT = 0, at = 0;
      events.forEach((e, i) => {
        const t = Number(e.t ?? 0);
        at += t > lastT ? (t - lastT) * msPerMinute : i ? 40 : 0;
        lastT = Math.max(lastT, t);
        timers.push(window.setTimeout(() => { if (!stopped) onEvent(e); }, at));
      });
    })
    .catch(() => undefined);
  return () => { stopped = true; timers.forEach((t) => window.clearTimeout(t)); };
}
