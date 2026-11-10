import assert from 'node:assert/strict';
import { test } from 'node:test';
import { buildSync } from 'esbuild';
import Module from 'node:module';
import { fileURLToPath } from 'node:url';
const filename=fileURLToPath(new URL('./judgeEvidence.ts',import.meta.url));
const built=buildSync({entryPoints:[filename],bundle:true,platform:'node',format:'cjs',write:false,logLevel:'silent'});
const module=new Module(filename);module._compile(built.outputFiles[0].text,filename);
const {judgeCheckpoints,reviewProofPresent}=module.exports;
const ev=(kind,extra={})=>({kind,seq:1,t:0,ts:'2026-11-10T19:00:00+05:30',...extra});
test('plans, phases and hidden truth cannot complete judge checkpoints',()=>{
 const rows=judgeCheckpoints({session:{scenario:'S1'},events:[ev('phase',{latest:'fix'}),ev('heal',{check:{}}),ev('execute',{result:{}}),ev('model',{model:'M3',audience:'control'}),ev('verdict',{verdict:'POTENTIAL_GAP',record_ids:['A'],gap_id:'G',truth:true})]});
 assert.equal(rows.filter(row=>row.evidence).length,0);
});
test('checkpoint availability preserves pending decisions and failed recovery evidence',()=>{
 const rows=judgeCheckpoints({session:{scenario:'S1'},events:[ev('approval',{hash:'real-plan',status:'requested'}),ev('execute',{seq:2,result:'refused'}),ev('verdict',{seq:3,verdict:'POTENTIAL_GAP',record_ids:['IN-A'],gap_id:'G'})]});
 assert.match(rows.find(row=>row.id==='decision').detail,/requested/);
 assert.equal(rows.find(row=>row.id==='recovery').evidence.result,'refused');
 assert.ok(rows.find(row=>row.id==='gap').evidence);
});
test('review acknowledgement loses support after rewind or missing session metadata',()=>{
 const event=ev('model',{model:'M1'}),key=`model:1:${event.ts}`;
 assert.equal(reviewProofPresent(key,{session:{scenario:'S1'},events:[event]},'models'),true);
 assert.equal(reviewProofPresent(key,{session:{scenario:'S1'},events:[event,ev('model',{seq:2,model:'M2'})]},'models'),true);
 assert.equal(reviewProofPresent(key,{session:{scenario:'S1'},events:[event]},'network'),false);
 assert.equal(reviewProofPresent(key,{session:{scenario:'S1'},events:[]}),false);
 assert.equal(reviewProofPresent(key,{events:[event]}),false);
});
