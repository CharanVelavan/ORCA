import { create } from 'zustand';

// UI-only state for the Stage, Control and Console layouts. Owner: lead.
// Feature modules (sim, inbox, landing, review) may read it and call its actions; they must not add fields.

export type StageMode = 'setup' | 'running';
export type PipelineView = 'open' | 'rail' | 'full';
export type Theme = 'dark' | 'light';

export type ExerciseConfig = {
  scenario: string;
  llm: 'mock' | 'local';
  rules: boolean;
  kb: 'india' | 'eu';
  speed: 1 | 2 | 5 | 10;
};

/** One fired attack/fault button, for the rail check marks. */
export type FiredInject = { injector: string; target: string; at: string };

type UiStore = {
  mode: StageMode;
  pipeline: PipelineView;
  simDrawer: boolean;
  theme: Theme;
  config: ExerciseConfig;
  fired: FiredInject[];
  /** Hash of the approval the PIN pad is open for (shared by inbox card and commander node). */
  pinFor: string | null;
  /** Where the PIN pad renders: on the inbox card or on the Pipeline commander node. */
  pinAt: 'inbox' | 'node';
  setConfig: (patch: Partial<ExerciseConfig>) => void;
  start: () => void;
  end: () => void;
  setPipeline: (view: PipelineView) => void;
  toggleDrawer: (open?: boolean) => void;
  toggleTheme: () => void;
  markFired: (item: FiredInject) => void;
  openPin: (hash: string | null, at?: 'inbox' | 'node') => void;
};

const readTheme = (): Theme => {
  try { return (localStorage.getItem('orca-theme') as Theme) || 'dark'; } catch { return 'dark'; }
};

export const useUi = create<UiStore>((set) => ({
  mode: 'setup',
  pipeline: 'open',
  simDrawer: false,
  theme: readTheme(),
  config: { scenario: 'S1', llm: 'mock', rules: true, kb: 'india', speed: 1 },
  fired: [],
  pinFor: null,
  pinAt: 'inbox',
  setConfig: (patch) => set((s) => ({ config: { ...s.config, ...patch } })),
  start: () => set({ mode: 'running', pipeline: 'open', simDrawer: false, fired: [] }),
  end: () => set({ mode: 'setup', simDrawer: false, pinFor: null }),
  setPipeline: (pipeline) => set({ pipeline }),
  toggleDrawer: (open) => set((s) => ({ simDrawer: open ?? !s.simDrawer })),
  toggleTheme: () => set((s) => {
    const theme: Theme = s.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('orca-theme', theme); } catch { /* private mode */ }
    return { theme };
  }),
  markFired: (item) => set((s) => ({ fired: [...s.fired, item] })),
  openPin: (pinFor, at = 'inbox') => set({ pinFor, pinAt: at }),
}));
