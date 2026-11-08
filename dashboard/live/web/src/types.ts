export type EventKind = 'session'|'tick'|'inject'|'scheduled'|'model'|'alert'|'agent_task'|'agent_step'|'agent_final'|'agent_busy'|'msg'|'verdict'|'clock_obligation'|'approval'|'execute'|'heal'|'patch_stage'|'rollback'|'reattack'|'autonomy'|'kill'|'gap'|'phase'|'impact'|'clock_waiting'|'clock_resumed'|'error';
export type LiveEvent = { seq:number; t:number; ts:string; kind:EventKind|string; audience?:'control'; [key:string]: unknown };
export type SiteState = { state:'ok'|'degraded'|'down'|'healing'; active_path?:string; gateway?:string; snr_db?:number; link_margin_db?:number; packet_loss?:number; battery_pct?:number; mains_power?:boolean; terminals_up?:number; traffic_load?:number; txn_success?:number };
export type Approval = { hash:string; playbook:string; owner:string; targets:string[]; reason:string; expires_at:string; clone_test?:string; status:string; mode?:string; [key:string]: unknown };
export type Agent = { role:string; busy?:boolean; queue?:number; lastAction?:string };
