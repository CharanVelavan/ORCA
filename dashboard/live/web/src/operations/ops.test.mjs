import assert from 'node:assert/strict';
import Module from 'node:module';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { buildSync } from 'esbuild';

function load(rel) {
  const source = fileURLToPath(new URL(rel, import.meta.url));
  const compiled = buildSync({ entryPoints: [source], bundle: true, platform: 'node', format: 'cjs', write: false, logLevel: 'silent' });
  const filename = join(dirname(source), 'ops-test-bundle.cjs');
  const bundle = new Module(filename);
  bundle.filename = filename;
  bundle.paths = Module._nodeModulePaths(dirname(filename));
  bundle._compile(compiled.outputFiles[0].text, filename);
  return bundle.exports;
}

const { remediationSteps } = load('./steps.ts');
const { attackFaultEvidence } = load('../investigation/evidence.ts');
const { siteSeries, serviceLines } = load('./TelemetryChart.tsx');
const events = JSON.parse(readFileSync(new URL('../../public/fixtures/S1.json', import.meta.url), 'utf8'));

test('remediation steps stay pending without events', () => {
  const steps = remediationSteps([]);
  assert.equal(steps.length, 5);
  assert.ok(steps.every((step) => step.state === 'pending'));
});

test('remediation steps ignore control-audience events', () => {
  const steps = remediationSteps([{ kind: 'execute', audience: 'control', result: 'ok', seq: 1, t: 1, ts: '' }]);
  assert.equal(steps[1].state, 'pending');
});

test('remediation steps follow the S1 fixture', () => {
  const steps = remediationSteps(events);
  assert.equal(steps[0].state, 'done');
  assert.equal(steps[1].state, 'done');
  const reattack = events.find((event) => event.kind === 'reattack');
  if (reattack) assert.equal(steps[4].state, reattack.blocked === true ? 'done' : 'failed');
});

test('attack-vs-fault evidence uses observed signals only', () => {
  const models = events.filter((event) => event.kind === 'model');
  const ticks = events.filter((event) => event.kind === 'tick');
  const site = models.find((event) => event.model === 'M3' && event.class && event.class !== 'normal')?.site ?? 'CHN-01';
  const view = attackFaultEvidence(models, ticks, site);
  assert.ok(view.sampleCount > 0);
  assert.equal(view.attack.find((item) => item.id === 'm3-attack').met, true);
  const leaked = attackFaultEvidence([{ kind: 'model', model: 'M3', site, class: 'attack-management-plane', audience: 'control', seq: 1, t: 0, ts: '' }], [], site);
  assert.equal(leaked.attack[0].met, null);
});

test('throughput series come from tick.services and tick.sites', () => {
  const ticks = events.filter((event) => event.kind === 'tick');
  const svc = serviceLines({ tickHistory: ticks });
  const sites = siteSeries({ tickHistory: ticks });
  assert.ok(svc.length > 0 && svc.every((line) => line.points.length === ticks.length));
  assert.ok(sites.length > 0);
  const t0 = ticks[0];
  assert.equal(sites[0].points[0].value, t0.sites[sites[0].id].delivered_mbps);
});
