import assert from 'node:assert/strict';
import Module from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { buildSync } from 'esbuild';

const source = fileURLToPath(new URL('./audit.ts', import.meta.url));
const compiled = buildSync({ entryPoints: [source], bundle: true, platform: 'node', format: 'cjs', write: false, logLevel: 'silent' });
const filename = join(dirname(source), 'audit-test-bundle.cjs');
const bundle = new Module(filename);
bundle.filename = filename;
bundle.paths = Module._nodeModulePaths(dirname(filename));
bundle._compile(compiled.outputFiles[0].text, filename);
const { toEntries, isControlEntry, actorType, split, summarize, hashState, toJsonl, phaseCursor, cursorForTs } = bundle.exports;

const rows = [
  { seq: 1, ts: '2026-11-10T19:00:00+05:30', actor: 'system', kind: 'run_meta', hash: 'a', payload: { scenario: 's1', kb: 'india', rules: true, llm: 'mock' } },
  { seq: 2, ts: '2026-11-10T19:00:00+05:30', actor: 'scenario', kind: 'inject', hash: 'b', payload: { kind: 'mgmt_intrusion' } },
  { seq: 3, ts: '2026-11-10T19:02:00+05:30', actor: 'rules', kind: 'verdict', hash: 'c', payload: { verdict: 'COMPLIANT', rule_id: 'IN-R-X', record_ids: ['IN-A'] } },
  { seq: 4, ts: '2026-11-10T19:03:00+05:30', actor: 'satellite_operator', kind: 'agent_step', hash: 'd', payload: { tool: 'read_alerts', rationale: 'look' } },
  { seq: 5, ts: '2026-11-10T19:04:00+05:30', actor: 'human:commander', kind: 'autonomy_set', hash: 'e', payload: { mode: 'AUTO', granted_by: 'commander', expires: 'x' } },
  { seq: 6, ts: '2026-11-10T19:05:00+05:30', actor: 'autonomy:AUTO (granted by commander)', kind: 'approved', hash: 'f', payload: { playbook: 'PB-01', audience: 'control' } },
  { seq: 7, ts: '2026-11-10T19:05:00+05:30', actor: 'autonomy:AUTO (granted by commander)', kind: 'approved', hash: 'g', payload: { playbook: 'PB-01' } },
  { seq: 8, ts: '2026-11-10T19:06:00+05:30', actor: 'scenario', kind: 'alert', hash: 'h', truth: true, payload: { text: 'control-only marker' } },
  { seq: 9, ts: '2026-11-10T19:07:00+05:30', actor: 'scenario', kind: 'alert', hash: 'i', payload: { truth: true, text: 'nested control-only marker' } },
  { seq: 10, ts: '2026-11-10T19:08:00+05:30', actor: 'scenario', kind: 'alert', hash: 'j', payload: { audience: 'control', text: 'nested control audience' } },
];

test('control and truth entries never reach the audit view', () => {
  const entries = toEntries(rows);
  assert.deepEqual(entries.map((e) => e.seq), [1, 3, 4, 5, 7]);
  assert.ok(!toJsonl(entries).includes('inject'));
  assert.ok(!toJsonl(entries).includes('"audience":"control"'));
  assert.ok(!toJsonl(entries).includes('"truth":true'));
  assert.equal(isControlEntry({ kind: 'alert', audience: 'control' }), true);
  assert.equal(isControlEntry({ kind: 'alert', payload: { audience: 'control' } }), true);
  assert.equal(isControlEntry({ kind: 'alert', truth: true }), true);
  assert.equal(isControlEntry({ kind: 'alert', payload: { truth: true } }), true);
});

test('actor types and AI vs human split', () => {
  assert.equal(actorType('human:commander'), 'human');
  assert.equal(actorType('autonomy:AUTO (granted by commander)'), 'autonomy');
  assert.equal(actorType('rules'), 'rule');
  assert.equal(actorType('M3'), 'model');
  assert.equal(actorType('satellite_operator'), 'agent');
  assert.equal(actorType('system'), 'system');
  assert.deepEqual(split(toEntries(rows)), { ai: 1, human: 1, deterministic: 3 });
});

test('summaries come from payload fields only', () => {
  const [meta, verdict] = toEntries(rows);
  assert.equal(summarize(meta), 'Run started: scenario S1, KB india, rule engine on, LLM mock');
  assert.equal(summarize(verdict), 'COMPLIANT · IN-R-X · IN-A');
});

test('hash state follows the verified chain', () => {
  const [entry, later] = toEntries(rows).slice(1, 3);
  assert.equal(hashState(entry, { ok: true, bad_seq: null, note: '' }), 'ok');
  assert.equal(hashState(entry, { ok: false, bad_seq: 4, note: '' }), 'ok');
  assert.equal(hashState(later, { ok: false, bad_seq: 4, note: '' }), 'broken');
  assert.equal(hashState(entry, { ok: null, bad_seq: null, note: '' }), 'unknown');
});

test('phase and timestamp cursors', () => {
  const events = [
    { seq: 1, t: 0, ts: '2026-11-10T19:00:00+05:30', kind: 'session' },
    { seq: 2, t: 1, ts: '2026-11-10T19:01:00+05:30', kind: 'phase', latest: 'predict', active: ['predict'] },
    { seq: 3, t: 4, ts: '2026-11-10T19:04:00+05:30', kind: 'phase', latest: 'contain', active: ['contain'] },
  ];
  assert.equal(phaseCursor(events, 'contain'), 3);
  assert.equal(phaseCursor(events, 'fix'), undefined);
  assert.equal(cursorForTs(events, '2026-11-10T19:02:00+05:30'), 2);
});
