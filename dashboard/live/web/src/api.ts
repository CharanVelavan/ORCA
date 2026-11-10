import type { ReplayResponse } from './types';

export type SessionRequest = { scenario:string; llm:'mock'|'local'; rules:boolean; kb:'india'|'eu'; autoplay:boolean; sync:boolean };
async function call<T>(path:string, body?:unknown, method='POST'): Promise<T> {
  const response = await fetch(`/api/${path}`, body === undefined && method === 'GET' ? undefined : { method, headers:{'Content-Type':'application/json'}, body:body === undefined ? undefined : JSON.stringify(body) });
  if (!response.ok) { let msg = `API ${response.status}: ${path}`; try { const j = await response.json() as {error?:string}; if (j?.error) msg = j.error; } catch { /* non-JSON error body */ } throw new Error(msg); }
  const result:unknown = await response.json();
  if (result && typeof result === 'object' && 'ok' in result && result.ok === false) {
    const detail = 'error' in result && typeof result.error === 'string' ? result.error
      : 'result' in result && result.result && typeof result.result === 'object' && 'error' in result.result && typeof result.result.error === 'string'
        ? result.result.error : `The ${path} request was refused`;
    throw new Error(detail);
  }
  return result as T;
}
export type ModelDraft = { base_url:string; model:string; api_key?:string; clear_key?:boolean };
export type ModelConfig = { base_url:string; model:string; key_set:boolean; mode?:string };
export const api = {
  modelConfig: () => call<ModelConfig>('model-config', undefined, 'GET'),
  saveModelConfig: (body:ModelDraft) => call<ModelConfig>('model-config', body),
  discoverModels: (body:ModelDraft) => call<{models:string[]}>('model-config/discover', body),
  testModel: (body:ModelDraft) => call<{reachable:boolean;tool_call_compatible:boolean}>('model-config/test', body),
  state: () => call<Record<string, unknown>>('state', undefined, 'GET'),
  catalogue: async () => {
    if (new URLSearchParams(window.location.search).get('fake') !== '1') return call<Record<string, unknown>>('catalogue', undefined, 'GET');
    const response = await fetch('/fixtures/catalogue.json');
    if (!response.ok) throw new Error(`Fixture catalogue unavailable (HTTP ${response.status})`);
    return response.json() as Promise<Record<string, unknown>>;
  },
  session: (body:SessionRequest) => call<Record<string, unknown>>('session', body),
  clock: (body:{action:'play'|'pause'|'step';speed?:number}) => call<Record<string, unknown>>('clock', body),
  inject: (body:{kind:string;target:string;duration_min:number;params?:Record<string,unknown>}) => call<Record<string, unknown>>('inject', body),
  autonomy: (body:Record<string,unknown>) => call<Record<string, unknown>>('autonomy', body), approve: (body:{hash:string}) => call<Record<string, unknown>>('approve', body),
  reject: (body:{hash:string;reason:string}) => call<Record<string, unknown>>('reject', body), kill: (body:{reason:string}) => call<Record<string, unknown>>('kill', body),
  releaseKill: (body:{}) => call<Record<string, unknown>>('kill/release', body), order: (body:{to:string;text:string}) => call<Record<string, unknown>>('order', body),
  ask: (body:{to:string;question:string}) => call<Record<string, unknown>>('ask', body), rules: (on:boolean) => call<Record<string, unknown>>('rules',{on}), kb: (kb:'india'|'eu') => call<Record<string, unknown>>('kb',{kb}),
  gap: (body:{gap_id:string;decision:'confirm'|'reject'}) => call<Record<string, unknown>>('gap', body),
  schedule: (body:{kind:string;target:string;at_t:number;duration_min:number;params?:Record<string,unknown>}) => call<Record<string, unknown>>('schedule', body),
  deleteSchedule: (id:string) => call<Record<string, unknown>>(`schedule/${encodeURIComponent(id)}`, undefined, 'DELETE'),
  truth: () => call<Record<string, unknown>>('truth', undefined, 'GET'),
  stopInject: (body: { kind?: string; id?: string }) => call<Record<string, unknown>>('inject/stop', body),
  runs: () => call<{ runs?: { file: string; scenario: string | null; stream: boolean; size: number; mtime: number }[] }>('runs', undefined, 'GET'),
  replay: (file:string) => call<ReplayResponse>(`replay?file=${encodeURIComponent(file)}`, undefined, 'GET'),
};
