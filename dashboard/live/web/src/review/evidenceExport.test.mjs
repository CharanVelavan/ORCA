import assert from 'node:assert/strict';
import Module from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { buildSync } from 'esbuild';
const source = fileURLToPath(new URL('./evidenceExport.ts', import.meta.url));
const compiled = buildSync({entryPoints:[source],bundle:true,platform:'node',format:'cjs',write:false,logLevel:'silent'});
const filename=join(dirname(source),'evidence-export-test.cjs'); const bundle=new Module(filename);
bundle.filename=filename;bundle.paths=Module._nodeModulePaths(dirname(filename));bundle._compile(compiled.outputFiles[0].text,filename);
const {buildEvidencePackage}=bundle.exports;
const event=(seq,kind,extra={})=>({seq,t:seq,ts:`2026-11-10T19:0${seq}:00+05:30`,kind,...extra});
const row=(seq,kind,payload={})=>({seq,kind,actor:'system',payload,raw:{seq,kind,actor:'system',payload}});
const base={file:'live-s1.jsonl',source:'stream',generatedAt:new Date('2026-11-10T13:30:00Z')};
test('exports public evidence with recording scope and explicit integrity limits',()=>{
 const p=buildEvidencePackage({...base,events:[event(1,'session',{scenario:'s1'}),event(2,'model',{model:'M3',incident_id:'INC-12'}),event(3,'clock_obligation',{regime:'IN-R'}),event(4,'approval',{hash:'abc'}),event(5,'execute',{result:'ok'}),event(6,'summary',{final:true})],entries:[row(1,'run_meta',{scenario:'s1'}),row(2,'verdict',{verdict:'COMPLIANT'})],chain:{ok:true,bad_seq:null,note:'verified'},omittedControl:2});
 assert.equal(p.scope.scenario,'s1');assert.equal(p.scope.incident_id,null);assert.deepEqual(p.scope.recorded_incident_ids,['INC-12']);assert.match(p.scope.description,/multiple conditions/);
 assert.equal(p.evidence.models[0].model,'M3');assert.equal(p.evidence.duties[0].regime,'IN-R');assert.equal(p.evidence.approvals[0].hash,'abc');assert.equal(p.evidence.execution[0].result,'ok');assert.equal(p.evidence.outcomes[0].final,true);
 assert.equal(p.provenance.original_chain_status.ok,true);assert.match(p.provenance.integrity_limit,/cannot verify/);assert.equal(p.provenance.audit_control_entries_withheld,2);assert.match(p.provenance.redaction_limit,/not comprehensive/);
 assert.ok(!p.missing_evidence.some(x=>x.includes('verdicts')));assert.ok(p.missing_evidence.some(x=>x.includes('facts')));
});
test('withholds known control and truth rows and does not invent incident or scenario',()=>{
 const p=buildEvidencePackage({...base,source:'audit',events:[event(1,'inject',{injector:'hidden'}),event(2,'alert',{audience:'control'}),event(3,'alert',{truth:true})],entries:[row(1,'inject',{kind:'secret'}),row(2,'verdict',{audience:'control'})]});
 assert.equal(p.scope.scenario,null);assert.equal(p.scope.incident_id,null);assert.equal(p.public_audit_entries.length,0);assert.equal(p.evidence.facts.length,0);assert.match(p.provenance.replay_events,/reconstructed/);assert.equal(p.missing_evidence.length,7);
});
