import { Activity, Check, ChevronsRight, Loader } from 'lucide-react';
import { useUi } from '../stage/uiStore';
import { CATEGORY_LABEL, INJECTOR_ICONS, groupInjectors } from './injectors';
import { useCatalogue } from './useCatalogue';
import { useFire } from './useFire';
import './sim.css';

/** State B. 64px wide, full height. The parent must not clip overflow (tooltips open to the right). */
export function AttackRail() {
  const { injectors } = useCatalogue();
  const fired = useUi((s) => s.fired);
  const toggleDrawer = useUi((s) => s.toggleDrawer);
  const { fire, pending, errors } = useFire();
  const lastFired = new Map(fired.map((f) => [f.injector, f]));

  return (
    <nav className="sim-rail" aria-label="Attack and fault events">
      {groupInjectors(injectors).map((g) => (
        <div key={g.category} className="sim-rail-group" role="group" aria-label={CATEGORY_LABEL[g.category]}>
          <span className="sim-rail-label">{CATEGORY_LABEL[g.category]}</span>
          {g.items.map((i) => {
            const Icon = INJECTOR_ICONS[i.id] ?? Activity;
            const hit = lastFired.get(i.id);
            const err = errors[i.id];
            return (
              <div key={i.id} className="sim-rail-item">
                <button type="button" className={`sim-rail-btn${hit ? ' is-fired' : ''}${err ? ' is-failed' : ''}`}
                  aria-label={`${i.label}, target ${i.default_target}`} disabled={pending === i.id}
                  onClick={() => void fire(i.id, i.default_target)}>
                  {pending === i.id ? <Loader size={18} strokeWidth={1.5} className="sim-spin" aria-hidden /> : <Icon size={18} strokeWidth={1.5} aria-hidden />}
                  {hit && !err && <span className="sim-rail-check" aria-hidden><Check size={10} strokeWidth={2} /></span>}
                </button>
                {hit && <span className="sim-rail-time mono">{hit.at}</span>}
                {err && <span className="sim-rail-fail">Failed</span>}
                <span className="sim-tip" role="tooltip">
                  <span className="sim-tip-label">{i.label}</span>
                  <span className="sim-tip-target mono">{i.default_target}</span>
                  {err && <span className="sim-tip-err">{err}</span>}
                </span>
              </div>
            );
          })}
        </div>
      ))}
      <div className="sim-rail-spacer" />
      <div className="sim-rail-item">
        <button type="button" className="sim-rail-btn" title="Open simulator (S)" aria-label="Open simulator (S)" onClick={() => toggleDrawer(true)}>
          <ChevronsRight size={18} strokeWidth={1.5} aria-hidden />
        </button>
      </div>
    </nav>
  );
}
