import { Link } from 'react-router-dom';
import { Moon, Square, Sun } from 'lucide-react';
import { api } from '../api';
import { useLiveStore } from '../store';
import { AutonomyBadge, KillSwitchButton } from '../inbox';
import { endExercise } from '../sim';
import { useUi, type ExerciseConfig } from './uiStore';
import { ist } from './time';

const ICON = { size: 15, strokeWidth: 1.5, 'aria-hidden': true } as const;
const SPEEDS: ExerciseConfig['speed'][] = [1, 2, 5, 10];

export function TopBar({ view }: { view: 'stage' | 'console' | 'control' }) {
  const mode = useUi((s) => s.mode);
  const theme = useUi((s) => s.theme);
  const toggleTheme = useUi((s) => s.toggleTheme);
  const speed = useUi((s) => s.config.speed);
  const setConfig = useUi((s) => s.setConfig);
  const session = useLiveStore((s) => s.session);
  const ts = useLiveStore((s) => s.ts);
  const running = view === 'console' || mode === 'running';
  const setSpeed = (v: ExerciseConfig['speed']) => { setConfig({ speed: v }); api.clock({ action: 'play', speed: v }).catch(() => undefined); };
  const llm = String(session.llm_model ?? session.llm ?? '');
  return (
    <header className="st-top">
      <Link to="/" className="st-brand">ORCA<span>-NTN</span></Link>
      <span className="st-sep" />
      {running && session.scenario ? (
        <span className="st-title"><b className="mono">{String(session.scenario)}</b>{String(session.title ?? '')}</span>
      ) : (
        <span className="st-title st-title--muted">{view === 'console' ? 'Operator console' : view === 'control' ? 'Simulator' : 'Exercise stage'} · Chennai</span>
      )}
      <span className="st-tag mono">EMULATED</span>
      <span className="st-grow" />
      {llm && <span className="st-meta mono" title="Agent language model, as reported by the engine">LLM {llm}</span>}
      <span className="st-clock mono" title="Simulation time, IST">{ist(ts)} IST</span>
      {running && view !== 'console' && (
        <div className="st-seg" role="group" aria-label="Simulation speed">
          {SPEEDS.map((v) => <button key={v} className={v === speed ? 'is-on' : ''} onClick={() => setSpeed(v)}>x{v}</button>)}
        </div>
      )}
      {running && <AutonomyBadge />}
      {running && <KillSwitchButton />}
      <button className="st-ib" onClick={toggleTheme} aria-label={theme === 'dark' ? 'Light theme' : 'Dark theme'} title="Theme">{theme === 'dark' ? <Sun {...ICON} /> : <Moon {...ICON} />}</button>
      {running && view !== 'console' && <button className="st-end" onClick={() => endExercise().catch(() => useUi.getState().end())}><Square {...ICON} size={12} />End exercise</button>}
    </header>
  );
}
