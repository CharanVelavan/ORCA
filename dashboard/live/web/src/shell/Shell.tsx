/**
 * Shell — the app frame: top nav + routed page + one bottom stepper (every page except Home).
 * Owns the global chrome so page owners only render their PageFrame body.
 */
import { Outlet, useLocation } from 'react-router-dom';
import { TopNav } from './TopNav';
import { Stepper } from './Stepper';
import { ContextStrip } from './ContextStrip';
import { SessionControls } from './SessionControls';
import { useLiveStore } from '../store';

export function Shell() {
  const { pathname } = useLocation();
  const isHome = pathname === '/';
  const error = useLiveStore((state) => state.errors.at(-1));
  return (
    <div className={`sh-root${isHome ? ' sh-root--learn' : ' sh-root--workspace'}`}>
      <a className="sh-skip" href="#main-content">Skip to content</a>
      <TopNav />
      {!isHome && <div className="workspace-session"><ContextStrip /><SessionControls /></div>}
      {error && <div className="sh-global-error" role="alert">{String(error.message ?? 'Engine error')}</div>}
      <main className="sh-main" id="main-content" tabIndex={-1}>
        <Outlet />
      </main>
      {!isHome && (
        <footer className="sh-footer">
          <Stepper />
        </footer>
      )}
    </div>
  );
}
