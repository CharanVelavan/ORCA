import { create } from 'zustand';
import type { Agent, Approval, LiveEvent, SiteState } from './types';

type Store = { seq:number; t:number; ts:string; session:Record<string,unknown>; sites:Record<string,SiteState>; gateways:Record<string,string>; paths:Record<string,unknown>[]; alerts:LiveEvent[]; models:LiveEvent[]; messages:LiveEvent[]; verdicts:LiveEvent[]; obligations:LiveEvent[]; approvals:Approval[]; gaps:LiveEvent[]; phases:string[]; impact:LiveEvent|null; autonomy:LiveEvent|null; kill:LiveEvent|null; agents:Record<string,Agent>; errors:LiveEvent[]; raw:LiveEvent[]; truth:LiveEvent[]; schedules:LiveEvent[]; waiting:boolean; agentSteps:LiveEvent[]; add:(event:LiveEvent)=>void; addControl:(event:LiveEvent)=>void; reset:()=>void };
const initial = { seq:0, t:0, ts:'', session:{}, sites:{}, gateways:{}, paths:[], alerts:[], models:[], messages:[], verdicts:[], obligations:[], approvals:[], gaps:[], phases:[], impact:null, autonomy:null, kill:null, agents:{}, errors:[], raw:[], truth:[], schedules:[], waiting:false, agentSteps:[] as LiveEvent[] };
const cap = <T,>(items:T[]) => items.slice(-60);
const reduce = (state:Store, event:LiveEvent, includeControl:boolean):Partial<Store> => {
  if (event.audience === 'control') return state;
  const next = { ...state, seq:Math.max(state.seq,event.seq), t:typeof event.t==='number'?Math.max(state.t,event.t):state.t, ts:typeof event.ts==='string'&&event.ts>state.ts?event.ts:state.ts };
  switch(event.kind) {
    case 'session': return { ...next, session:event };
    case 'tick': return { ...next, sites:(event.sites as Record<string,SiteState>) ?? state.sites, gateways:(event.gateways as Record<string,string>) ?? state.gateways, paths:(event.paths as Record<string,unknown>[]) ?? state.paths };
    case 'alert': return { ...next, alerts:cap([...state.alerts,event]) };
    case 'model': return { ...next, models:cap([...state.models,event]) };
    case 'msg': return { ...next, messages:cap([...state.messages,event]) };
    case 'verdict': return { ...next, verdicts:cap([...state.verdicts,event]) };
    case 'clock_obligation': return { ...next, obligations:cap([...state.obligations.filter(x=>x.regime !== event.regime),event]) };
    case 'approval': { const a=event as unknown as Approval; const old=state.approvals.find(x=>x.hash===a.hash); return { ...next, approvals:cap([...state.approvals.filter(x=>x.hash!==a.hash),old?{...old,...a}:a]) }; }
    case 'gap': return { ...next, gaps:cap([...state.gaps.filter(x=>x.gap_id!==event.gap_id),event]) };
    case 'phase': return { ...next, phases:Array.isArray(event.phase) ? event.phase as string[] : [String(event.phase)] };
    case 'impact': return { ...next, impact:event };
    case 'autonomy': return { ...next, autonomy:event };
    case 'kill': return { ...next, kill:event };
    case 'agent_busy': return { ...next, agents:{...state.agents,[String(event.role)]:{...state.agents[String(event.role)],role:String(event.role),busy:Boolean(event.busy),queue:Number(event.queue ?? 0)}} };
    case 'agent_task': case 'agent_step': case 'agent_final': return { ...next, agentSteps:event.kind==='agent_task'?state.agentSteps:[...state.agentSteps,event].slice(-400), agents:{...state.agents,[String(event.role)]:{...state.agents[String(event.role)],role:String(event.role),lastAction:String(event.text ?? event.final ?? event.result ?? event.task ?? event.tool ?? 'Working')}} };
    case 'clock_waiting': return { ...next, waiting:true };
    case 'clock_resumed': return { ...next, waiting:false };
    case 'error': return { ...next, errors:cap([...state.errors,event]) };
    case 'inject': return { ...next, truth:cap([...state.truth,event]), raw:cap([...state.raw,event]) };
    case 'scheduled': return { ...next, schedules:cap([...state.schedules.filter(x=>x.id!==event.id),event]), raw:cap([...state.raw,event]) };
    case 'execute': case 'heal': case 'patch_stage': case 'rollback': case 'reattack': return { ...next, raw:cap([...state.raw,event]) };
    default: return { ...next, raw:cap([...state.raw,event]) };
  }
};
export const useLiveStore = create<Store>((set) => ({ ...initial, reset:() => set(initial), add:(event) => set((state) => reduce(state,event,false)), addControl:(event) => set((state) => event.audience==='control' ? ({...state,seq:Math.max(state.seq,event.seq),truth:event.kind==='scheduled'?state.truth:cap([...state.truth,event]),schedules:event.kind==='scheduled'?cap([...state.schedules.filter(x=>x.id!==event.id),event]):state.schedules,raw:cap([...state.raw,event])}) : reduce(state,event,true)) }));
