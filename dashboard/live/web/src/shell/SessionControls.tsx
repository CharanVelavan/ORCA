import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Pause, Play, Plug, X } from 'lucide-react';
import { api } from '../api';
import { useLiveStore } from '../store';
import { useDashboardReplay } from '../review/ReplayProvider';
import './session.css';
import { SessionModeGuide } from './SessionModeGuide';
import { useSessionDraft, type SessionMode } from './sessionDraft';

type Mode = SessionMode;
type ModelConfig = { base_url: string; model: string; key_set: boolean; mode?: string };
export function SessionControls() {
  const {replay:playback}=useDashboardReplay();
  const session = useLiveStore((state) => state.session);
  const source = useLiveStore((state) => state.source);
  const { search } = useLocation();
  const navigate = useNavigate();
  const fake = new URLSearchParams(search).get('fake') === '1';
  const current: Mode = source === 'replay' || fake ? 'replay' : session.llm === 'local' ? 'local' : 'mock';
  const selectedMode = useSessionDraft(state => state.mode);
  const setDraft = useSessionDraft(state => state.setMode);
  const draft = selectedMode ?? current;
  const [open, setOpen] = useState(false);
  const [help, setHelp] = useState(false);
  useEffect(() => setDraft(current), [current]);
  const start = () => {
    if (draft === 'replay') { navigate(`/audit${search}`); return; }
    const params = new URLSearchParams(search);
    params.delete('fake'); params.delete('pace'); params.delete('scn');
    const query = params.toString();
    navigate(`/scenarios${query ? `?${query}` : ''}`);
  };
  const label = !session.llm && current !== 'replay' ? 'Awaiting session' : current === 'replay' ? 'Recorded replay · read-only' : current === 'local' ? `${session.llm_source === 'replay' ? 'Cached model replay' : 'Live endpoint'} · ${String(session.llm_model ?? 'model not reported')}` : 'Mock simulation';
  return <div className="session-controls" data-tour="session-mode">
    <span className="session-source" title={label}>{label}</span>
    {current === 'replay' && !fake && playback.events.length > 0 && <><button type="button" className="sh-btn sh-btn--sm" onClick={playback.toggle} aria-label={playback.playing ? 'Pause recorded replay' : 'Play recorded replay'}>{playback.playing ? <Pause size={14} /> : <Play size={14} />}</button><span className="session-cursor" title="Replay event cursor">{playback.cursor}/{playback.events.length}</span></>}
    <label className="sr-only" htmlFor="session-mode">Mode for a new session</label>
    <select id="session-mode" value={draft} onChange={(event) => setDraft(event.target.value as Mode)}>
      <option value="mock">Mock simulation</option><option value="local">Live endpoint / Qwen</option><option value="replay">Recorded replay</option>
    </select>
    <button className="sh-btn sh-btn--sm" type="button" onClick={start} title="Review a scenario before starting a new run">{draft === 'replay' ? 'Choose recording' : 'Choose scenario'}</button>
    <button className="sh-btn sh-btn--sm" type="button" onClick={() => setHelp(true)}>Mode help</button>
    <button className="sh-btn sh-btn--sm" type="button" onClick={() => setOpen(true)}><Plug size={14} />Model connection</button>
    {help && <SessionModeGuide onClose={() => setHelp(false)} />}
    {open && <ModelConnection onClose={() => setOpen(false)} />}
  </div>;
}

function ModelConnection({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [config, setConfig] = useState<ModelConfig>({ base_url:'http://localhost:8000/v1', model:'', key_set:false });
  const [key, setKey] = useState('');
  const [clearKey, setClearKey] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    ref.current?.showModal();
    let active = true;
    api.modelConfig().then((result) => { if (active) setConfig(result); }).catch((cause) => { if (active) setError(String(cause.message)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  const payload = () => ({ base_url:config.base_url, model:config.model, ...(key ? { api_key:key } : {}), ...(clearKey ? { clear_key:true } : {}) });
  const run = async (action: 'discover' | 'test' | 'save') => {
    setBusy(action); setNotice(''); setError('');
    try {
      if (action === 'discover') {
        const result = await api.discoverModels(payload()); setModels(result.models);
        if (!config.model && result.models.length) setConfig((value) => ({ ...value, model:result.models[0] }));
        setNotice(result.models.length ? `${result.models.length} model(s) discovered. Select one or enter an identifier.` : 'No models reported. Enter the served model identifier manually.');
      } else if (action === 'test') {
        const result = await api.testModel(payload());
        setNotice(result.tool_call_compatible ? 'Endpoint reachable. A parsed tool call passed the compatibility test. No tool was executed.' : 'Endpoint reachable, but a compatible tool call was not returned. Agent execution may not work with this endpoint.');
      } else {
        const result = await api.saveModelConfig(payload()); setConfig(result); setKey(''); setClearKey(false);
        setNotice('Saved in backend memory for the next run. Choose Live endpoint mode, then choose and start a scenario.');
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Connection action failed.'); }
    finally { setBusy(''); }
  };
  return <dialog ref={ref} className="model-dialog" aria-labelledby="model-title" onCancel={(event) => { event.preventDefault(); onClose(); }}>
    <header><div><span className="model-eyebrow">SESSION SETTINGS</span><h2 id="model-title">Model connection</h2></div><button className="sh-btn sh-btn--sm" type="button" aria-label="Close model settings" onClick={onClose}><X size={18} /></button></header>
    <p>Connect a running OpenAI-compatible model server. Qwen is the project model; the identifier below must match your endpoint.</p>
    {loading && <p role="status">Loading connection settings…</p>}
    <fieldset disabled={Boolean(busy) || loading}>
      <label htmlFor="model-url">API base URL</label><input id="model-url" type="url" value={config.base_url} onChange={(event) => setConfig({ ...config, base_url:event.target.value })} spellCheck={false} />
      <small>Use the API base including /v1. Localhost means the machine running the ORCA backend. In Docker on macOS, a model on the host usually uses host.docker.internal.</small>
      <label htmlFor="model-id">Served model identifier</label><input id="model-id" list="discovered-models" value={config.model} onChange={(event) => setConfig({ ...config, model:event.target.value })} placeholder="Discover models or enter an exact identifier" spellCheck={false} />
      <datalist id="discovered-models">{models.map((id) => <option key={id} value={id} />)}</datalist>
      <label htmlFor="model-key">API key (optional)</label><input id="model-key" type="password" value={key} onChange={(event) => setKey(event.target.value)} autoComplete="off" placeholder={config.key_set ? 'Key configured · leave blank to keep' : 'No key configured'} />
      <label className="model-check"><input type="checkbox" checked={clearKey} onChange={(event) => setClearKey(event.target.checked)} />Clear the stored key when saving</label>
      <small>Credentials stay in backend memory. They are not saved in browser storage or included in the audit.</small>
      <div className="model-actions"><button type="button" className="sh-btn" onClick={() => void run('discover')}>Discover models</button><button type="button" className="sh-btn" onClick={() => void run('test')} disabled={!config.model}>Test tool compatibility</button></div>
      <button type="button" className="sh-btn sh-btn--primary" onClick={() => void run('save')} disabled={!config.model}>Use for next run</button>
    </fieldset>
    {busy && <p role="status">{busy === 'test' ? 'Testing endpoint and tool call…' : busy === 'discover' ? 'Discovering models…' : 'Saving settings…'}</p>}
    {notice && <p className="model-notice" role="status">{notice}</p>}
    {error && <p className="session-error" role="alert">{error}</p>}
    <p className="model-help">No endpoint available? Close this panel and choose Mock simulation or Recorded replay. A failed connection never switches modes silently.</p>
  </dialog>;
}
