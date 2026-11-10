import { after, test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'vite';
const server=await createServer({configFile:false,server:{middlewareMode:true,hmr:false},optimizeDeps:{noDiscovery:true,include:[]},appType:'custom'});
after(()=>server.close());
const {reportingClocks}=await server.ssrLoadModule('/src/policy/data.ts');
const {taskEvidence}=await server.ssrLoadModule('/src/workflow.ts');
const {TOUR_STEPS}=await server.ssrLoadModule('/src/onboarding/steps.ts');
test('clock never borrows a notification from another obligation in the same regime',()=>{
 const rows=reportingClocks({ts:'2026-11-10T12:00:00+05:30',obligations:[{seq:3,regime:'R',obligation_id:'old',started_at:'2026-11-10T00:00:00+05:30',due_at:'2026-11-10T06:00:00+05:30'}],summary:{timings:{clocks:[{regime:'R',obligation_id:'new',met:true,notified_at:'2026-11-10T11:00:00+05:30'}]}}});
 assert.equal(rows[0].notifiedAt,undefined);assert.equal(rows[0].status,'overdue');
});
test('legacy recording clock joins only the exact trigger and deadline tuple',()=>{
 const obligation={seq:3,regime:'R',started_at:'2026-11-10T10:00:00+05:30',due_at:'2026-11-10T16:00:00+05:30'};
 const matching={...obligation,met:true,notified_at:'2026-11-10T11:00:00+05:30'};
 const data={ts:'2026-11-10T12:00:00+05:30',obligations:[obligation],summary:{timings:{clocks:[matching]}}};
 assert.equal(reportingClocks(data)[0].status,'met');
 data.summary.timings.clocks=[{...matching,started_at:'2026-11-09T10:00:00+05:30'}];assert.equal(reportingClocks(data)[0].notifiedAt,undefined);
});
test('a newer approval cannot borrow an older successful execution',()=>{
 const data={approvals:[{hash:'new',status:'requested',playbook:'PB-11'}],events:[{seq:1,kind:'execute',result:'ok'},{seq:2,kind:'approval',hash:'new',status:'requested'}]};
 assert.equal(taskEvidence('contain',data).status,'pending');
});
test('clean-path evidence alone does not prove failover',()=>{
 const data={events:[{seq:1,kind:'heal',check:{clean:true}}]};
 assert.equal(taskEvidence('clean',data).status,'done');assert.equal(taskEvidence('heal',data).status,'pending');
});
test('tour explains the complete journey and never contains executable actions',()=>{
 assert.deepEqual([...new Set(TOUR_STEPS.map(s=>s.route))],['/','/scenarios','/workspace','/policy','/recovery','/audit']);
 assert.ok(TOUR_STEPS.every(s=>typeof s.body==='string' && !('action' in s)));
});

test('re-attack success alone cannot prove restored service',()=>{
 assert.equal(taskEvidence('validate',{events:[{seq:1,kind:'reattack',blocked:true}]}).status,'pending');
});
test('fresh plans cannot borrow old rollout stages',()=>{
 const data={approvals:[{hash:'new',playbook:'PB-11',status:'requested'}],events:[{seq:1,kind:'patch_stage',pct:100,health:'ok'},{seq:2,kind:'approval',hash:'new'}]};
 assert.equal(taskEvidence('rollout100',data).status,'pending');
});

test('forecast and allocation require their own public model evidence',()=>{
 const data={models:[{kind:'model',model:'M1'},{kind:'model',model:'M2',audience:'control'}]};
 assert.equal(taskEvidence('forecast',data).status,'pending');
 assert.equal(taskEvidence('allocate',data).status,'pending');
 data.models.push({kind:'model',model:'M2'});
 assert.equal(taskEvidence('forecast',data).status,'done');
 assert.equal(taskEvidence('allocate',data).status,'pending');
 data.models.push({kind:'model',model:'M4'});
 assert.equal(taskEvidence('allocate',data).status,'done');
});

test('a repeated plan hash starts a fresh execution-evidence window',()=>{
 const data={approvals:[{hash:'same',playbook:'PB-01',status:'requested'}],events:[
  {seq:1,kind:'approval',hash:'same',playbook:'PB-01',status:'requested'},
  {seq:2,kind:'execute',plan_hash:'same',playbook:'PB-01',result:'ok'},
  {seq:3,kind:'approval',hash:'same',playbook:'PB-01',status:'requested'}]};
 assert.equal(taskEvidence('contain',data).status,'pending');
});

test('reported stages before an approval update stay inside their requested plan window',()=>{
 const data={approvals:[{hash:'same',playbook:'PB-01',status:'approved'}],events:[
  {seq:1,kind:'approval',hash:'same',playbook:'PB-01',status:'requested'},
  {seq:2,kind:'patch_stage',plan_hash:'same',playbook:'PB-01',pct:100,health:'ok'},
  {seq:3,kind:'approval',hash:'same',playbook:'PB-01',status:'approved'}]};
 assert.equal(taskEvidence('rollout',data).status,'done');
});
