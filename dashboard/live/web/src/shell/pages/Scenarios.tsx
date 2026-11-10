import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, BookOpen, Check, ChevronRight, Clock3, FlaskConical, Layers, LockKeyhole, Play, Search, ShieldCheck } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useCatalogue, type ScenarioKind } from '../../sim/useCatalogue';
import { isReadOnlyNow } from '../../sim/readOnly';
import { ScenarioGuide } from '../../simulator/ScenarioGuide';
import { useDirectorControls } from '../../simulator/useDirectorControls';
import { useLiveStore } from '../../store';
import { useSessionDraft } from '../sessionDraft';
import { PageFrame } from '../PageFrame';
import { simClockIST } from '../ContextStrip';
import './scenarios.css';

const KINDS: { id: ScenarioKind | 'all'; label: string }[] = [
  { id: 'all', label: 'All' }, { id: 'attack', label: 'Attack' }, { id: 'fault', label: 'Fault' },
  { id: 'mixed', label: 'Mixed' }, { id: 'normal', label: 'Normal' }, { id: 'audit', label: 'Audit' },
];

export default function Scenarios() {
  const { search } = useLocation();
  const navigate = useNavigate();
  const catalogue = useCatalogue();
  const source = useLiveStore(state => state.source);
  const session = useLiveStore(state => state.session);
  const ts = useLiveStore(state => state.ts);
  const draftMode = useSessionDraft(state => state.mode);
  const fake = new URLSearchParams(search).get('fake') === '1';
  const recordedReplay = source === 'replay';
  const controls = useDirectorControls(fake || recordedReplay);
  const nextMode = draftMode ?? (controls.llm || (session.llm === 'local' ? 'local' : 'mock'));
  const [selectedId, setSelectedId] = useState('');
  const [kind, setKind] = useState<ScenarioKind | 'all'>('all');
  const [query, setQuery] = useState('');
  const [launching, setLaunching] = useState(false);
  const launchLock = useRef(false);
  const mounted = useRef(true);
  const briefing = useRef<HTMLDivElement>(null);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => { if (nextMode !== 'replay' && controls.llm !== nextMode) controls.chooseLlm(nextMode); }, [nextMode, controls.llm, controls.chooseLlm]);
  const scenarios = useMemo(() => fake ? catalogue.scenarios.filter(scenario => catalogue.fixtureScenarios?.includes(scenario.id)) : catalogue.scenarios, [fake, catalogue.scenarios, catalogue.fixtureScenarios]);
  useEffect(() => {
    if (catalogue.loading || selectedId && scenarios.some(scenario => scenario.id === selectedId)) return;
    const requested = new URLSearchParams(search).get('scenario')?.toUpperCase();
    setSelectedId(requested && scenarios.some(scenario => scenario.id === requested) ? requested : scenarios.some(scenario => scenario.id === session.scenario) ? String(session.scenario) : scenarios[0]?.id ?? '');
  }, [catalogue.loading, scenarios, selectedId, search, session.scenario]);
  const selected = scenarios.find(scenario => scenario.id === selectedId);
  const needle = query.trim().toLowerCase();
  const filtered = scenarios.filter(scenario => (kind === 'all' || scenario.kind === kind) && (!needle || `${scenario.id} ${scenario.title} ${scenario.story}`.toLowerCase().includes(needle)));
  const ready = controls.rules !== null && controls.sync !== null && controls.llm === nextMode;
  const canStart = Boolean(selected && !catalogue.loading && !launching && !recordedReplay && (fake || nextMode !== 'replay' && controls.canCommand && ready));
  const currentId = typeof session.scenario === 'string' ? session.scenario.toUpperCase() : '';
  const currentSource = recordedReplay ? 'Recorded replay · read only' : fake ? 'Bundled fixture · read only' : session.llm === 'local' ? session.llm_source === 'replay' ? 'Cached model replay' : 'Live endpoint' : session.llm === 'mock' ? 'Mock simulation' : 'Awaiting session metadata';
  const nextSource = fake ? 'Bundled fixture' : nextMode === 'replay' ? 'Recorded replay' : nextMode === 'local' ? 'Live endpoint / Qwen' : 'Mock simulation';
  const choose = (id: string) => {
    if (launchLock.current) return;
    setSelectedId(id);
    if (briefing.current) briefing.current.scrollTop = 0;
  };
  const start = async () => {
    if (!selected || !canStart || launchLock.current || useLiveStore.getState().source === 'replay') return;
    const scenario = selected.id;
    if (fake) {
      const params = new URLSearchParams(search); params.set('scn', scenario); params.delete('scenario');
      navigate(`/workspace?${params.toString()}`); return;
    }
    if (isReadOnlyNow() || nextMode === 'replay' || controls.llm !== nextMode) return;
    launchLock.current = true; setLaunching(true);
    try {
      const started = await controls.start(scenario);
      if (started && mounted.current && !isReadOnlyNow()) {
        const params = new URLSearchParams(search); params.delete('scenario'); params.delete('scn');
        navigate(`/workspace${params.size ? `?${params.toString()}` : ''}`);
      }
    } finally { launchLock.current = false; if (mounted.current) setLaunching(false); }
  };

  return <PageFrame title="Choose an exercise" subtitle="Preview the briefing, then start a fresh run." actions={<><span className="scenario-prep-source"><ShieldCheck size={13} />{currentSource}</span><Link className="sh-btn sh-btn--sm" to={`/workspace${search}`}>Resume Console <ArrowRight size={14} /></Link></>}>
    <div className="scenario-prep">
      <div className="scenario-prep__journey" aria-label="Exercise preparation"><span><b>01</b>Choose scenario</span><ChevronRight size={14} /><span><b>02</b>Read briefing</span><ChevronRight size={14} /><span><b>03</b>{fake ? 'Load fixture' : 'Start & open Console'}</span><small>Selection previews only. Your current run stays unchanged.</small></div>
      <div className="scenario-prep__workspace">
        <aside className="scenario-prep__catalogue" data-tour="simulator-scenarios" aria-label="Scenario selection"><header><h2><Layers size={16} />Scenarios</h2><span>{scenarios.length} available</span></header><div className="scenario-prep__filters"><label><Search size={15} /><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search scenarios" aria-label="Search scenarios" disabled={launching} /></label><div role="group" aria-label="Scenario type">{KINDS.map(item => <button type="button" key={item.id} aria-pressed={kind === item.id} disabled={launching} onClick={() => setKind(item.id)}>{item.label}</button>)}</div></div><div className="scenario-prep__list">{catalogue.loading && <p className="scenario-prep__empty" role="status">Loading the scenario catalogue…</p>}{!catalogue.loading && filtered.length === 0 && <p className="scenario-prep__empty">No scenarios match. Change the search or type filter.</p>}{filtered.map(scenario => <button type="button" key={scenario.id} aria-pressed={selectedId === scenario.id} disabled={launching} onClick={() => choose(scenario.id)} className={selectedId === scenario.id ? 'is-selected' : ''}><span className="scenario-prep__scenario-meta"><b>{scenario.id}</b><span>{scenario.kind}</span>{selectedId === scenario.id && <Check size={14} />}</span><strong>{scenario.title}</strong><span className="scenario-prep__story">{scenario.story}</span>{currentId === scenario.id && <small>Current session scenario</small>}</button>)}</div><footer>{fake ? 'Source: bundled fixture catalogue' : catalogue.live ? 'Source: backend scenario catalogue' : catalogue.loading ? 'Loading source metadata…' : 'Source: local fallback catalogue'}{catalogue.error && <p role="status">{catalogue.error}</p>}</footer></aside>
        <section className="scenario-prep__detail" aria-label="Selected scenario briefing"><header><h2><BookOpen size={16} />Scenario briefing</h2><span>Plans and director schedule · all links emulated</span></header><div className="scenario-prep__briefing" ref={briefing}><ScenarioGuide scenario={selected} previewOnly /></div><div className="scenario-prep__launch" data-tour="scenario-start"><div className="scenario-prep__next"><span>Next run</span><strong>{nextSource}</strong><small>{fake ? 'Client-only fixture · no engine command' : 'India policy context · configured mode'}</small></div>{recordedReplay ? <div className="scenario-prep__readonly"><LockKeyhole size={17} /><p>Recorded replay is read-only. Resume Console to inspect it, or leave replay in Audit before starting a fresh exercise.</p><Link className="sh-btn sh-btn--sm" to={`/audit${search}`}>Open Audit &amp; Replay</Link></div> : nextMode === 'replay' && !fake ? <Link className="sh-btn sh-btn--primary" to={`/audit${search}`}>Open recordings <ArrowRight size={15} /></Link> : <button type="button" className="sh-btn sh-btn--primary" disabled={!canStart} onClick={() => void start()}>{fake ? <FlaskConical size={15} /> : <Play size={15} />}{launching || controls.busy === 'Start exercise' ? 'Starting exercise…' : fake ? 'Load fixture' : 'Start exercise'}</button>}<p className="scenario-prep__launch-note">{recordedReplay ? 'No new session is started from recorded playback.' : fake ? 'Loads the selected recorded fixture. This does not create a backend run.' : nextMode === 'replay' ? 'Open an existing recording. Playback stays read-only; no fresh backend run is created.' : 'Start resets the exercise to this scenario, starts its clock and opens Console after backend confirmation.'}</p>{(controls.error || controls.connectionError || controls.notice) && <p className={`scenario-prep__command${controls.error || controls.connectionError ? ' is-error' : ''}`} role={controls.error || controls.connectionError ? 'alert' : 'status'}>{controls.error ?? controls.connectionError ?? controls.notice}</p>}{!fake && !recordedReplay && nextMode !== 'replay' && !ready && <p className="scenario-prep__command" role="status">Waiting for confirmed session settings. Use Model connection above for a live endpoint.</p>}</div></section>
      </div>
      <footer className="scenario-prep__current"><Clock3 size={14} /><strong>Current session</strong><span>{currentId || 'Not reported'}</span><span>{ts ? `${simClockIST(ts)} IST` : 'Clock unavailable'}</span><span>{currentSource}</span><small>The briefing is a plan. Observed results appear in Console.</small></footer>
    </div>
  </PageFrame>;
}
