import { useEffect } from 'react';
import { usePipeline } from '../pipeline/pipelineStore';
import { useUi } from './uiStore';

/** S: simulator drawer, P: collapse pipeline, F: pipeline full screen, arrows: explain steps, Esc: back. */
export function useStageKeys(allowSim: boolean) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)) return;
      if (t && t.getAttribute && t.getAttribute('role') === 'separator' && e.key.startsWith('Arrow')) return; // the split handle owns arrows
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const ui = useUi.getState();
      if (ui.pinFor) return; // the PIN pad owns the keyboard while open
      const k = e.key.toLowerCase();
      if (k === 's' && allowSim && ui.mode === 'running') { ui.toggleDrawer(); e.preventDefault(); }
      else if (k === 'p') { ui.setPipeline(ui.pipeline === 'rail' ? 'open' : 'rail'); e.preventDefault(); }
      else if (k === 'f') { ui.setPipeline(ui.pipeline === 'full' ? 'open' : 'full'); e.preventDefault(); }
      else if (e.key === 'ArrowRight') { usePipeline.getState().explainStep(1); e.preventDefault(); }
      else if (e.key === 'ArrowLeft') { usePipeline.getState().explainStep(-1); e.preventDefault(); }
      else if (e.key === 'Escape') {
        if (ui.simDrawer) ui.toggleDrawer(false);
        else if (ui.pipeline === 'full') ui.setPipeline('open');
        else if (usePipeline.getState().mode === 'explain') usePipeline.getState().setMode('live');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [allowSim]);
}
