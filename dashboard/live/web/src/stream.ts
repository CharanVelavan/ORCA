import type { LiveEvent } from './types';

export function connectStream(since:number, onEvent:(event:LiveEvent)=>void, onError?:(error:Event)=>void) {
  let closed = false; let source:EventSource|undefined;
  const open = () => { if (closed) return; source = new EventSource(`/api/stream?since=${since}`); source.onmessage = ({data}) => { try { const event = JSON.parse(data) as LiveEvent; since = event.seq; onEvent(event); } catch { /* malformed events never stop the console */ } }; source.onerror = (error) => { source?.close(); onError?.(error); if (!closed) window.setTimeout(open, 1000); }; };
  open(); return () => { closed = true; source?.close(); };
}
