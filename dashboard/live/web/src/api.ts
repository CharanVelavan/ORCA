export type SessionRequest = { scenario:string; llm:'mock'|'local'; rules:boolean; kb:'india'|'eu'; autoplay:boolean; sync:boolean };
async function call<T>(path:string, body?:unknown): Promise<T> {
  const response = await fetch(`/api/${path}`, body ? { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) } : undefined);
  if (!response.ok) throw new Error(`API ${response.status}: ${path}`);
  return response.json() as Promise<T>;
}
export const api = {
  state: () => call<Record<string, unknown>>('state'), catalogue: () => call<Record<string, unknown>>('catalogue'),
  session: (body:SessionRequest) => call<Record<string, unknown>>('session', body),
  clock: (body:{action:'play'|'pause'|'step';speed?:number}) => call<Record<string, unknown>>('clock', body),
  inject: (body:{kind:string;target:string;duration_min:number;params?:Record<string,unknown>}) => call<Record<string, unknown>>('inject', body),
  autonomy: (body:Record<string,unknown>) => call<Record<string, unknown>>('autonomy', body), approve: (body:{hash:string;pin:string}) => call<Record<string, unknown>>('approve', body),
  reject: (body:{hash:string;reason:string}) => call<Record<string, unknown>>('reject', body), kill: (body:{pin:string;reason:string}) => call<Record<string, unknown>>('kill', body),
  releaseKill: (body:{pin:string}) => call<Record<string, unknown>>('kill/release', body), order: (body:{to:string;text:string}) => call<Record<string, unknown>>('order', body),
  ask: (body:{to:string;question:string}) => call<Record<string, unknown>>('ask', body), rules: (on:boolean) => call<Record<string, unknown>>('rules',{on}), kb: (kb:'india'|'eu') => call<Record<string, unknown>>('kb',{kb}),
  gap: (body:{gap_id:string;decision:'confirm'|'reject';pin:string}) => call<Record<string, unknown>>('gap', body), schedule: () => call<Record<string, unknown>>('schedule'), truth: () => call<Record<string, unknown>>('truth'), replay: (file:string) => call<Record<string, unknown>>(`replay?file=${encodeURIComponent(file)}`),
};
