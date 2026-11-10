import assert from 'node:assert/strict';
import Module from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { buildSync } from 'esbuild';

const source = fileURLToPath(new URL('./data.ts', import.meta.url));
const compiled = buildSync({ entryPoints: [source], bundle: true, platform: 'node', format: 'cjs', write: false, logLevel: 'silent' });
const filename = join(dirname(source), 'policy-test-bundle.cjs');
const bundle = new Module(filename);
bundle.filename = filename;
bundle.paths = Module._nodeModulePaths(dirname(filename));
bundle._compile(compiled.outputFiles[0].text, filename);
const { VERDICTS, actualVerdicts, humanDecision, recordBinding, recordInForce, reportingClocks } = bundle.exports;

test('only actual public rule verdicts from the six-value vocabulary are accepted', () => {
  const events = VERDICTS.map((verdict, index) => ({ kind: 'verdict', seq: index, verdict }));
  events.push({ kind: 'verdict', seq: 10, verdict: 'COMPLIANT', audience: 'control' });
  events.push({ kind: 'verdict', seq: 11, verdict: 'VERIFIED' });
  events.push({ kind: 'gap', seq: 12, verdict: 'POTENTIAL_GAP' });
  assert.deepEqual(actualVerdicts(events).map((event) => event.verdict), VERDICTS);
});

test('binding and commencement labels follow catalogue status, including a future commencement', () => {
  const record = { id: 'TEST', binding_status: 'binding_not_in_force', in_force_status: 'not_yet', in_force_from: '2027-05-13' };
  assert.equal(recordBinding(record).word, 'Binding, not yet in force');
  assert.match(recordInForce(record), /2027/);
  assert.equal(recordBinding({ ...record, in_force_status: 'in_force' }).word, 'Binding');
  assert.equal(recordInForce({ ...record, in_force_status: 'in_force' }), 'In force');
});

test('human decisions distinguish both live and legacy decision values', () => {
  for (const value of ['confirm', 'confirmed']) assert.equal(humanDecision(value), 'confirm');
  for (const value of ['reject', 'rejected']) assert.equal(humanDecision(value), 'reject');
  for (const value of [undefined, 'candidate', 'open']) assert.equal(humanDecision(value), null);
});

test('clock reconciliation preserves the actual trigger and handles notifications before it', () => {
  const event = { seq: 1, kind: 'clock_obligation', regime: 'R', records: ['K'], trigger: 'awareness',
    started_at: '2026-11-10T19:00:00+05:30', due_at: '2026-11-10T20:00:00+05:30', status: 'open' };
  const summary = { seq: 2, kind: 'summary', timings: { clocks: [{ regime: 'R', obligation_seq: 1, record_id: 'K',
    notified_at: '2026-11-10T18:55:00+05:30', notified_before_start: true, time_to_notify_min: 0, window_min: 60, met: true }] } };
  const [clock] = reportingClocks({ obligations: [event], summary, ts: '2026-11-10T19:30:00+05:30' });
  assert.equal(clock.status, 'met');
  assert.equal(clock.trigger, 'awareness');
  assert.equal(clock.notifiedBeforeStart, true);
  assert.equal(clock.notifyMin, 0);
  assert.deepEqual(clock.recordIds, ['K']);
  const [unobserved] = reportingClocks({ obligations: [event], ts: '2026-11-10T20:01:00+05:30' });
  assert.equal(unobserved.status, 'overdue');
  assert.equal(unobserved.notifiedAt, undefined);
  assert.equal(reportingClocks({ obligations: [{ ...event, audience: 'control' }], summary }).length, 0);
  const [controlSummary] = reportingClocks({ obligations: [event], summary: { ...summary, audience: 'control' } });
  assert.equal(controlSummary.status, 'open');
  assert.equal(controlSummary.notifiedAt, undefined);
});
