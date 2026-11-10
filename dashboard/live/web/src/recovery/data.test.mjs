import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import Module from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { buildSync } from 'esbuild';

const source = fileURLToPath(new URL('./data.ts', import.meta.url));
const compiled = buildSync({ entryPoints: [source], bundle: true, platform: 'node', format: 'cjs', write: false, logLevel: 'silent' });
const filename = join(dirname(source), 'recovery-test-bundle.cjs');
const bundle = new Module(filename);
bundle.filename = filename;
bundle.paths = Module._nodeModulePaths(dirname(filename));
bundle._compile(compiled.outputFiles[0].text, filename);
const { availabilityAfter, availabilitySeries, deliverySeries, latestRollout, measurementSummary,
  observedOutageMinutes, publicRecoveryInput, recoveryMarkers, rollbackPlaybook, siteMeasurements } = bundle.exports;

test('measured zero is retained, missing metrics are unavailable, and control events are filtered', () => {
  const ticks = [
    { seq: 1, kind: 'tick', t: 0, ts: '2026-11-10T19:00:00+05:30', services: { general: { demand_mbps: 10, delivered_mbps: 0 } } },
    { seq: 2, kind: 'tick', t: 1, ts: '2026-11-10T19:01:00+05:30', services: { general: { demand_mbps: 10 } } },
    { seq: 3, kind: 'tick', t: 2, audience: 'control', services: { general: { demand_mbps: 10, delivered_mbps: 10 } } },
  ];
  const controlImpact = { seq: 4, kind: 'impact', t: 0, audience: 'control', instantaneous: { network_availability_pct: 100 } };
  const measuredImpact = { seq: 5, kind: 'impact', t: 0, instantaneous: { network_availability_pct: 0 } };
  const input = { tickHistory: ticks, events: [controlImpact, measuredImpact] };
  assert.deepEqual(availabilitySeries(input).map((point) => point.value), [0]);
  assert.deepEqual(availabilitySeries({ tickHistory: ticks, events: [controlImpact] }), []);
  assert.deepEqual(deliverySeries(input)[0].points.map((point) => point.value), [0]);
  assert.equal(measurementSummary(input)[0].delivered, undefined);
  assert.equal(publicRecoveryInput(input).tickHistory.length, 2);
  assert.equal(recoveryMarkers({ events: [{ seq: 5, kind: 'alert', t: 0, label: 'attack-secret', audience: 'control' }] }).length, 0);
  assert.equal(recoveryMarkers({ events: [
    { seq: 6, kind: 'alert', t: 1, source: 'M1', label: 'attack-label' },
    { seq: 7, kind: 'alert', t: 2, source: 'M3', label: 'fault-weather' },
  ] })[0].label, 'M3 detection: fault-weather');
  assert.deepEqual(siteMeasurements({ tickHistory: [
    { seq: 8, kind: 'tick', audience: 'control', sites: { 'SAT-MGMT': { delivered_mbps: 99 } } },
    { seq: 9, kind: 'tick', sites: { 'CHN-01': { state: 'degraded', delivered_mbps: 0, demand_mbps: 10 } } },
  ] }), [{ id: 'CHN-01', state: 'degraded', delivered: 0, demand: 10, capacity: undefined, activePath: undefined, gateway: undefined }]);
});

test('rollout retries never inherit health checks from an earlier attempt', () => {
  const stage = (seq, pct, health) => ({ seq, kind: 'patch_stage', t: seq, playbook: 'PB', pct, health });
  const rollback = { seq: 3, kind: 'rollback', t: 3, playbook: 'PB' };
  const first = [stage(1, 5, 'ok'), stage(2, 25, 'fail'), rollback, stage(4, 5, 'ok')];
  assert.deepEqual(latestRollout({ events: first }).stages.map((step) => step.event?.health), ['ok', undefined, undefined]);
  assert.deepEqual(latestRollout({ events: [...first, stage(5, 25, 'ok'), stage(6, 100, 'ok')] }).stages.map((step) => step.event?.health), ['ok', 'ok', 'ok']);
  const noRollback = [stage(1, 5, 'ok'), stage(2, 25, 'ok'), stage(3, 100, 'ok'), stage(4, 5, 'ok')];
  assert.deepEqual(latestRollout({ events: noRollback }).stages.map((step) => step.event?.health), ['ok', undefined, undefined]);
  const late = [stage(61, 5, 'ok'), stage(62, 25, 'fail'), stage(63, 5, 'ok'), stage(64, 25, 'ok'), stage(65, 100, 'ok'), { seq: 82, kind: 'rollback', t: 2, playbook: 'PB' }];
  const flushed = latestRollout({ events: late });
  assert.deepEqual(flushed.stages.map((step) => step.event?.health), ['ok', 'ok', 'ok']);
  assert.equal(flushed.rolledBack, false);
  assert.equal(flushed.earlierFailed, 1);
  assert.equal(latestRollout({ events: late.slice(0, 2).concat(late[5]) }).rolledBack, true);
});

test('rollback events correlate to their execution hash when no playbook is repeated', () => {
  const events = [
    { seq: 1, kind: 'execute', hash: 'approval-hash', playbook: 'PB-11', result: 'ok' },
    { seq: 2, kind: 'patch_stage', playbook: 'PB-11', pct: 5, health: 'ok' },
    { seq: 3, kind: 'patch_stage', playbook: 'PB-11', pct: 25, health: 'ok' },
    { seq: 4, kind: 'rollback', hash: 'approval-hash', why: 'health check failed' },
  ];
  assert.equal(rollbackPlaybook(events[3], events), 'PB-11');
  assert.equal(latestRollout({ events }).rolledBack, true);
});

test('S1 data exposes the real service dip, public markers and observed restoration', () => {
  const events = JSON.parse(readFileSync(new URL('../../public/fixtures/S1.json', import.meta.url), 'utf8'));
  const pub = events.filter((event) => event.audience !== 'control');
  const input = { events: pub, tickHistory: pub.filter((event) => event.kind === 'tick'),
    summary: pub.filter((event) => event.kind === 'summary').at(-1) };
  const samples = availabilitySeries(input);
  const degraded = input.summary.timings.degraded;
  assert.equal(samples.find((sample) => sample.t === degraded.t).value, degraded.pct);
  assert.equal(observedOutageMinutes(input), (Date.parse(input.summary.timings.restored_at) - Date.parse(degraded.ts)) / 60000);
  assert.equal(availabilityAfter(input, samples), samples.find((point) => Date.parse(point.ts) >= Date.parse(input.summary.timings.restored_at)).value);
  const kinds = new Set(recoveryMarkers(input).map((marker) => marker.kind));
  for (const kind of ['alert', 'degradation', 'execute', 'fix', 'rollback']) assert.ok(kinds.has(kind), kind);
  const byId = new Map(measurementSummary(input).map((row) => [row.id, row]));
  for (const service of ['112', 'hospital', 'general']) assert.equal(byId.get(service).delivered, input.tickHistory.at(-1).services[service].delivered_mbps);
  assert.equal(availabilityAfter({ summary: { ...input.summary, audience: 'control' } }, samples), undefined);
  assert.equal(observedOutageMinutes({ summary: { ...input.summary, audience: 'control' } }), undefined);
});
