import { fakeEvents } from './events';
import type { LiveEvent } from '../types';
export function playFake(onEvent:(event:LiveEvent)=>void) { let index=0; const id=window.setInterval(()=>{ if(index>=fakeEvents.length){window.clearInterval(id);return;} onEvent(fakeEvents[index++]); }, 480); return () => window.clearInterval(id); }
