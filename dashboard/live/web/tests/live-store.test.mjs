import { after, beforeEach, test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'vite';

const server = await createServer({
  configFile: false,
  server: { middlewareMode: true, hmr:false },
  optimizeDeps: { noDiscovery: true, include: [] },
  appType: 'custom',
});
const { useLiveStore } = await server.ssrLoadModule('/src/store.ts');
const derive = await server.ssrLoadModule('/src/derive.ts');
const { activeBranch, flowNodeStatus } = await server.ssrLoadModule('/src/shell/FlowPanel.tsx');
const { autonomyView } = await server.ssrLoadModule('/src/shell/ContextStrip.tsx');
const { createStreamGate } = await server.ssrLoadModule('/src/stage/DataBridge.tsx');
const { FLOW_RESPONSE, FLOW_RECOVERY } = await server.ssrLoadModule('/src/shell/flowConfig.ts');
after(() => server.close());
beforeEach(() => useLiveStore.getState().reset());

function emit(seq, event) {
  useLiveStore.getState().add({ seq, t:seq, ts:'', ...event });
}

test('legacy plan_hash approvals update the exact request without duplicate cards', () => {
  emit(1,{kind:'approval',hash:'same-plan',playbook:'PB-01',owner:'satellite_operator',targets:['noc-vendor-7'],status:'requested'});
  emit(2,{kind:'approval',plan_hash:'same-plan',playbook:'PB-01',status:'approved'});
  const approvals=useLiveStore.getState().approvals;
  assert.equal(approvals.length,1);
  assert.equal(approvals[0].hash,'same-plan');
  assert.equal(approvals[0].status,'approved');
  assert.deepEqual(approvals[0].targets,['noc-vendor-7']);
});

test('a pending response cannot inherit an earlier response approval', () => {
  emit(1,{kind:'approval',hash:'old',playbook:'PB-01',status:'requested'});
  emit(2,{kind:'approval',hash:'old',playbook:'PB-01',status:'approved'});
  emit(3,{kind:'approval',hash:'new',playbook:'PB-11',status:'requested'});
  const input=derive.selectInput(useLiveStore.getState());
  assert.equal(flowNodeStatus(FLOW_RECOVERY.nodes[0],input),'pending');
});

test('a current response cannot take a historical re-attack branch', () => {
  emit(1,{kind:'approval',hash:'old',playbook:'PB-01',status:'requested'});
  emit(2,{kind:'reattack',plan_hash:'old',playbook:'PB-01',blocked:true});
  emit(3,{kind:'approval',hash:'new',playbook:'PB-11',status:'requested'});
  const node=FLOW_RECOVERY.nodes.find(n=>n.id==='reattack');
  assert.equal(activeBranch(node,derive.selectInput(useLiveStore.getState())),undefined);
});

test('a stream stops accepting during replay and never resumes after closing', () => {
  let replay = false;
  const gate = createStreamGate(() => replay);
  assert.equal(gate.accepting(), true);
  replay = true;
  assert.equal(gate.accepting(), false);
  gate.close();
  replay = false;
  assert.equal(gate.accepting(), false);
  assert.equal(createStreamGate(() => replay).accepting(), true);
});

test('model results remain available when high-frequency M1 updates arrive', () => {
  emit(1, { kind:'model', model:'M4', solution:'optimal' });
  emit(2, { kind:'model', model:'M3', class:'fault-weather' });
  for (let seq = 3; seq < 103; seq++) emit(seq, { kind:'model', model:'M1', score:0.1 });
  const views = derive.models(derive.selectInput(useLiveStore.getState()));
  assert.equal(views.find((view) => view.id === 'M4').solution, 'optimal');
  assert.equal(views.find((view) => view.id === 'M3').klass, 'fault-weather');
});

test('M2 forecast history survives frequent M1 updates', () => {
  emit(1, { kind:'model', model:'M2', horizon_min:12 });
  for (let seq = 2; seq < 82; seq++) emit(seq, { kind:'model', model:'M1', score:0.1 });
  emit(82, { kind:'model', model:'M2', horizon_min:8 });
  for (let seq = 83; seq < 163; seq++) emit(seq, { kind:'model', model:'M1', score:0.2 });
  const forecast = derive.models(derive.selectInput(useLiveStore.getState())).find((view) => view.id === 'M2');
  assert.deepEqual(forecast.spark, [12, 8]);
});

test('model history remains bounded independently for each model', () => {
  for (let seq = 1; seq <= 90; seq++) emit(seq, { kind:'model', model:'M2', horizon_min:seq });
  const forecast = derive.models(derive.selectInput(useLiveStore.getState())).find((view) => view.id === 'M2');
  assert.equal(forecast.spark.length, 60);
  assert.equal(forecast.spark[0], 31);
  assert.equal(forecast.spark.at(-1), 90);
});

test('a normal report from another site does not hide an active M3 classification', () => {
  emit(1, { kind:'model', model:'M3', site:'CHN-01', class:'attack-management-plane', state:'flagged', confidence:0.91 });
  emit(2, { kind:'model', model:'M3', site:'CHN-02', class:'normal', state:'ok' });
  let classifier = derive.models(derive.selectInput(useLiveStore.getState())).find((view) => view.id === 'M3');
  assert.equal(classifier.klass, 'attack-management-plane');
  assert.equal(classifier.event.site, 'CHN-01');
  emit(3, { kind:'model', model:'M3', site:'CHN-01', class:'normal', state:'ok' });
  classifier = derive.models(derive.selectInput(useLiveStore.getState())).find((view) => view.id === 'M3');
  assert.equal(classifier.klass, 'normal');
});

test('latest model output per site survives frequent reports from other sites', () => {
  emit(1, { kind:'model', model:'M3', site:'CHN-01', class:'attack-management-plane', state:'flagged' });
  for (let seq = 2; seq < 92; seq++) emit(seq, { kind:'model', model:'M3', site:'CHN-02', class:'normal', state:'ok' });
  const classifier = derive.models(derive.selectInput(useLiveStore.getState())).find((view) => view.id === 'M3');
  assert.equal(classifier.klass, 'attack-management-plane');
});

test('M2 forecast history uses the selected site and metric only', () => {
  emit(1, { kind:'model', model:'M2', site:'CHN-01', metric:'link_margin', horizon_min:12, state:'flagged' });
  emit(2, { kind:'model', model:'M2', site:'CHN-02', metric:'link_margin', horizon_min:50, state:'ok' });
  emit(3, { kind:'model', model:'M2', site:'CHN-01', metric:'link_margin', horizon_min:8, state:'flagged' });
  emit(4, { kind:'model', model:'M2', site:'CHN-02', metric:'link_margin', horizon_min:45, state:'ok' });
  const forecast = derive.models(derive.selectInput(useLiveStore.getState())).find((view) => view.id === 'M2');
  assert.equal(forecast.minutesToFailure, 8);
  assert.deepEqual(forecast.spark, [12, 8]);
});

test('a flagged classifier output completes the task while the condition stays flagged', () => {
  const node = FLOW_RESPONSE.nodes.find((item) => item.id === 'classify');
  const data = {
    models:[{ kind:'model', model:'M3', site:'CHN-01', class:'attack-jamming', state:'flagged' }],
    phaseHistory:[{ active:['report'], latest:'report' }],
  };
  assert.equal(flowNodeStatus(node, data), 'done');
});

test('flow does not mark a clean-path check complete without a heal check', () => {
  const node = FLOW_RECOVERY.nodes.find((item) => item.id === 'clean');
  const data = { phaseHistory:[{ active:['heal'], latest:'heal' }], events:[] };
  assert.equal(flowNodeStatus(node, data), 'pending');
  data.events.push({ kind:'heal', check:{ clean:false } });
  assert.equal(flowNodeStatus(node, data), 'failed');
  data.events.push({ kind:'heal', check:{ clean:true } });
  assert.equal(flowNodeStatus(node, data), 'done');
});

test('flow uses model, approval and execution evidence rather than generic phase', () => {
  const node = (id) => FLOW_RESPONSE.nodes.find((item) => item.id === id);
  const data = { phaseHistory:[{ active:['predict','contain'], latest:'contain' }], events:[], models:[], approvals:[] };
  assert.equal(flowNodeStatus(node('detect'), data), 'pending');
  assert.equal(flowNodeStatus(node('decision'), data), 'pending');
  data.models.push({ kind:'model', model:'M1', site:'CHN-01', state:'flagged' });
  data.approvals.push({ status:'requested' });
  assert.equal(flowNodeStatus(node('detect'), data), 'done');
  assert.equal(flowNodeStatus(node('decision'), data), 'current');
  data.approvals.push({ status:'approved' });
  assert.equal(flowNodeStatus(node('decision'), data), 'done');
  const contain = node('decision').branches.find((branch) => branch.id === 'approve').nodes[0];
  assert.equal(flowNodeStatus(contain, data), 'pending');
  data.events.push({ kind:'execute', result:'ok' });
  assert.equal(flowNodeStatus(contain, data), 'done');
  data.events.push({ kind:'execute', changed:true, result:{ ok:false } });
  assert.equal(flowNodeStatus(contain, data), 'failed');
});

test('rollout, reattack and restoration need their own evidence', () => {
  const node = (id) => FLOW_RECOVERY.nodes.find((item) => item.id === id);
  const data = { phaseHistory:[{ active:['fix'], latest:'fix' }], events:[] };
  assert.equal(flowNodeStatus(node('rollout'), data), 'pending');
  assert.equal(flowNodeStatus(node('reattack'), data), 'pending');
  assert.equal(flowNodeStatus(node('validate'), data), 'pending');
  data.events.push({ kind:'patch_stage', pct:25, health:'ok' });
  assert.equal(flowNodeStatus(node('rollout'), data), 'current');
  data.events.push({ kind:'patch_stage', pct:100, health:'ok' });
  assert.equal(flowNodeStatus(node('rollout'), data), 'done');
  data.events.push({ kind:'reattack', blocked:false });
  assert.equal(flowNodeStatus(node('reattack'), data), 'failed');
  data.events.push({ kind:'reattack', blocked:true });
  assert.equal(flowNodeStatus(node('reattack'), data), 'done');
  data.summary = { timings:{ time_to_restore_min:3 } };
  assert.equal(flowNodeStatus(node('validate'), data), 'done');
});

test('phase recency alone is not evidence of active or completed work', () => {
  const steps = derive.phaseSteps({
    phaseHistory:[
      { active:['predict'], latest:'predict', ts:'2026-11-10T19:00:00+05:30' },
      { active:['contain','report'], latest:'report', ts:'2026-11-10T19:01:00+05:30' },
    ],
  });
  assert.equal(steps.find((step) => step.id === 'predict').status, 'seen');
  assert.equal(steps.find((step) => step.id === 'contain').status, 'seen');
  assert.equal(steps.find((step) => step.id === 'report').status, 'seen');
  assert.equal(steps.find((step) => step.id === 'contain').isLatest, false);
  assert.equal(steps.find((step) => step.id === 'report').isLatest, false);
});

test('control-audience events stay separate from the public event history', () => {
  useLiveStore.getState().addControl({
    kind:'inject', audience:'control', seq:1, t:1, ts:'', target:'private-target',
  });
  const state = useLiveStore.getState();
  assert.equal(state.truth.length, 1);
  assert.equal(state.events.length, 0);
  assert.equal(state.raw.length, 0);
});

test('KB changes clear current jurisdiction views but retain audit history', () => {
  emit(1, { kind:'session', kb:'india' });
  emit(2, { kind:'gap', gap_id:'IN-GAP' });
  emit(3, { kind:'verdict', verdict:'POTENTIAL_GAP' });
  emit(4, { kind:'clock_obligation', regime:'IN-R' });
  emit(5, { kind:'summary', final:false });
  emit(6, { kind:'kb_changed', kb:'eu' });
  const state = useLiveStore.getState();
  assert.equal(state.session.kb, 'eu');
  assert.deepEqual(state.gaps, []);
  assert.deepEqual(state.verdicts, []);
  assert.deepEqual(state.obligations, []);
  assert.equal(state.summary, null);
  assert.equal(state.events.length, 6);
  emit(7, { kind:'clock_obligation', regime:'EU-R' });
  assert.equal(useLiveStore.getState().obligations[0].regime, 'EU-R');
});

test('catalogue counts follow the active KB rather than a stale jurisdiction cache', async () => {
  const previousWindow = globalThis.window;
  const previousFetch = globalThis.fetch;
  globalThis.window = { location:{ search:'' } };
  let requests = 0;
  globalThis.fetch = async () => ({
    ok:true,
    json:async () => ({ records:Array.from({ length:++requests }), gaps:[], roles:[], scenarios:[] }),
  });
  try {
    emit(1, { kind:'session', kb:'india' });
    assert.equal((await derive.fetchCatalogueCounts()).records, 1);
    emit(2, { kind:'kb_changed', kb:'eu' });
    assert.equal((await derive.fetchCatalogueCounts()).records, 2);
    emit(3, { kind:'kb_changed', kb:'india' });
    assert.equal((await derive.fetchCatalogueCounts()).records, 3);
    globalThis.window.location.search = '?fake=1';
    assert.equal((await derive.fetchCatalogueCounts()).records, 4);
  } finally {
    globalThis.window = previousWindow;
    globalThis.fetch = previousFetch;
  }
});

test('autonomy pill reflects downgrades, expired grants, and kill-switch revocation', () => {
  const at = '2026-11-10T19:05:00+05:30';
  assert.equal(autonomyView({ seq:1, mode:'AUTO', expires:'2026-11-10T19:04:00+05:30' }, null, at).label, 'Grant expired');
  assert.equal(autonomyView({ seq:2, from:'AUTO', to:'ASSISTED' }, null, at).mode, 'ASSISTED');
  assert.equal(autonomyView({ seq:1, mode:'AUTO' }, { seq:2, engaged:true }, at).label, 'MANUAL · kill active');
  assert.equal(autonomyView({ seq:1, mode:'AUTO' }, { seq:3, engaged:false }, at).mode, 'MANUAL');
  assert.equal(autonomyView({ seq:4, mode:'ASSISTED' }, { seq:3, engaged:false }, at).mode, 'ASSISTED');
});

test('a scoped manual change does not claim that all autonomy is manual', () => {
  const scoped = autonomyView({ seq:1, mode:'MANUAL', sites:['CHN-01'], playbooks:['PB-10'] }, null);
  assert.equal(scoped.mode, null);
  assert.equal(scoped.label, 'Scoped MANUAL requested');
  const nested = autonomyView({ seq:2, mode:'MANUAL', scope:{ sites:['CHN-01'], playbooks:['PB-10'] } }, null);
  assert.equal(nested.mode, null);
  const global = autonomyView({ seq:3, mode:'MANUAL', sites:'*', playbooks:'*' }, null);
  assert.equal(global.mode, 'MANUAL');
});

test('an older catalogue request cannot overwrite counts after a KB change', async () => {
  const previousWindow = globalThis.window;
  const previousFetch = globalThis.fetch;
  globalThis.window = { location:{ search:'' } };
  let resolveFirst;
  let requests = 0;
  globalThis.fetch = () => {
    requests += 1;
    if (requests === 1) return new Promise((resolve) => { resolveFirst = resolve; });
    return Promise.resolve({ ok:true, json:async () => ({ records:[{}, {}] }) });
  };
  try {
    emit(1, { kind:'session', kb:'india' });
    const first = derive.fetchCatalogueCounts();
    emit(2, { kind:'kb_changed', kb:'eu' });
    assert.equal((await derive.fetchCatalogueCounts()).records, 2);
    resolveFirst({ ok:true, json:async () => ({ records:[{}] }) });
    await first;
    assert.equal((await derive.fetchCatalogueCounts()).records, 2);
    assert.equal(requests, 2);
  } finally {
    globalThis.window = previousWindow;
    globalThis.fetch = previousFetch;
  }
});

test('rules toggles cannot leave stale policy results visible', () => {
  emit(1, { kind:'session', rules:true });
  emit(2, { kind:'gap', gap_id:'IN-GAP' });
  emit(3, { kind:'verdict', verdict:'POTENTIAL_GAP' });
  emit(4, { kind:'clock_obligation', regime:'IN-R' });
  emit(5, { kind:'rules_changed', rules:false });
  const state = useLiveStore.getState();
  assert.equal(state.session.rules, false);
  assert.deepEqual(state.gaps, []);
  assert.deepEqual(state.verdicts, []);
  assert.deepEqual(state.obligations, []);
  assert.equal(state.events.length, 5);
});

test('selectors distinguish unavailable telemetry from zero and exclude forbidden gateways', () => {
  assert.equal(derive.deliveredMbps({}), undefined);
  assert.equal(derive.deliveredMbps({
    tickHistory:[{ services:{ general:{ demand_mbps:9, delivered_mbps:0 } } }],
  }), 0);
  assert.equal(derive.gatewayHealth({}), undefined);
  assert.deepEqual(derive.gatewayHealth({
    gateways:{ 'GW-IN-1':'up', 'GW-IN-2':'down', 'GW-XX':'up' },
  }), { up:1, total:2 });
});

test('citations use record ids from verdicts and gap evidence', () => {
  const ids = derive.citationIds({
    verdicts:[{ record_ids:['IN-RECORD'] }],
    gaps:[{ evidence:['IN-EVIDENCE', null], global_examples:[{ record:'EU-RECORD' }] }],
  });
  assert.deepEqual(ids, ['IN-RECORD', 'IN-EVIDENCE', 'EU-RECORD']);
});

test('real agent work and a pending human decision can be active together', () => {
  const steps = derive.phaseSteps({ agents:{ mobile_operator:{ busy:true } }, approvals:[{status:'requested'}] });
  assert.equal(steps.find(s => s.id === 'coordinate').status, 'current');
  assert.equal(steps.find(s => s.id === 'contain').status, 'current');
});
test('restored service timing does not prove re-attack validation', () => {
  assert.equal(flowNodeStatus({id:'validate'}, {summary:{timings:{time_to_restore_min:3}}}), 'pending');
});
