import { useEffect, useState } from 'react';
import { api } from '../api';
import { SCENARIO_PATHS } from '../pipeline/scenarioPaths';
import { FALLBACK_INJECTORS, FALLBACK_TARGETS } from './injectors';
import type { InjectorCategory, InjectorInfo } from './injectors';

export type ScenarioKind = 'normal' | 'attack' | 'fault' | 'audit' | 'mixed';
export type ScenarioInfo = { id: string; title: string; story: string; kind: ScenarioKind; sites: string[]; m3_expected: string };
export type Catalogue = { scenarios: ScenarioInfo[]; injectors: InjectorInfo[]; targets: string[]; live: boolean };

const ORDER = ['S0', 'S1', 'S2', 'S3', 'N1', 'N2', 'N3', 'N4', 'N5', 'CAP'];
const rank = (id: string) => { const i = ORDER.indexOf(id); return i < 0 ? 99 : i; };
const KINDS: ScenarioKind[] = ['normal', 'attack', 'fault', 'audit', 'mixed'];

const fallbackScenarios = (): ScenarioInfo[] =>
  SCENARIO_PATHS.map((p) => ({ id: p.id, title: p.title, story: p.story, kind: p.kind, sites: p.sites, m3_expected: p.m3Expected }))
    .sort((a, b) => rank(a.id) - rank(b.id));

const asStrings = (value: unknown): string[] => {
  if (Array.isArray(value)) return value.map((v) => (typeof v === 'string' ? v : String((v as { id?: unknown })?.id ?? ''))).filter(Boolean);
  if (value && typeof value === 'object') return Object.keys(value);
  return [];
};

function parse(raw: Record<string, unknown>): Catalogue {
  const fb = fallbackScenarios();
  const fbById = new Map(fb.map((s) => [s.id, s]));
  const apiScenarios = Array.isArray(raw.scenarios) ? (raw.scenarios as Record<string, unknown>[]) : [];
  let scenarios: ScenarioInfo[];
  if (apiScenarios.length <= 1) {
    scenarios = fb;
  } else {
    scenarios = apiScenarios.map((s) => {
      const id = String(s.id ?? '');
      const base = fbById.get(id);
      const kind = KINDS.includes(s.kind as ScenarioKind) ? (s.kind as ScenarioKind) : base?.kind ?? 'normal';
      return {
        id, kind,
        title: String(s.title ?? base?.title ?? id),
        story: String(s.story ?? base?.story ?? ''),
        sites: Array.isArray(s.sites) ? (s.sites as unknown[]).map(String) : base?.sites ?? [],
        m3_expected: String(s.m3_expected ?? base?.m3_expected ?? ''),
      };
    }).sort((a, b) => rank(a.id) - rank(b.id));
  }
  const apiInj = Array.isArray(raw.injectors) ? (raw.injectors as Record<string, unknown>[]) : [];
  const injectors: InjectorInfo[] = apiInj.length
    ? apiInj.map((i) => ({ id: String(i.id), label: String(i.label ?? i.id), default_target: String(i.default_target ?? ''), category: (i.category as InjectorCategory) ?? 'attack' }))
    : FALLBACK_INJECTORS;
  const targets = [...new Set([...asStrings(raw.sites), ...asStrings(raw.gateways), ...asStrings(raw.accounts), 'SAT-MGMT'])];
  return { scenarios, injectors, targets: targets.length > 3 ? targets : FALLBACK_TARGETS, live: true };
}

const fallback = (): Catalogue => ({ scenarios: fallbackScenarios(), injectors: FALLBACK_INJECTORS, targets: FALLBACK_TARGETS, live: false });

let cache: Catalogue | null = null;
let pending: Promise<Catalogue> | null = null;

function load(): Promise<Catalogue> {
  if (cache) return Promise.resolve(cache);
  pending ??= api.catalogue().then(parse).catch(fallback).then((c) => { cache = c; pending = null; return c; });
  return pending;
}

/** Loads api.catalogue() once per page; falls back to local data when the API is down. */
export function useCatalogue(): Catalogue {
  const [data, setData] = useState<Catalogue>(() => cache ?? fallback());
  useEffect(() => {
    let alive = true;
    void load().then((c) => { if (alive) setData(c); });
    return () => { alive = false; };
  }, []);
  return data;
}
