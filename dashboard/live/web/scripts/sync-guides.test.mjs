import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
const script = await readFile(resolve(dirname(fileURLToPath(import.meta.url)), 'sync-guides.mjs'));
async function setup() {
  const root = await mkdtemp(join(tmpdir(), 'orca-guide-sync-'));
  const scripts = join(root, 'dashboard/live/web/scripts');
  await mkdir(scripts, {recursive:true}); await mkdir(join(root, 'docs'), {recursive:true});
  const file = join(scripts, 'sync-guides.mjs'); await writeFile(file, script);
  return {root,file,output:join(root,'dashboard/live/web/public/docs')};
}
test('copies each actual source guide byte-for-byte', async () => {
  const env=await setup(); try {
    const files=[['guide.md','guide.md'],['docs/JUDGE_REPRODUCIBILITY.md','JUDGE_REPRODUCIBILITY.md'],['docs/JUDGE_WINDOWS.md','JUDGE_WINDOWS.md']];
    for(const [source] of files) await writeFile(join(env.root,source),`Actual source: ${source}\n`);
    const run=spawnSync(process.execPath,[env.file],{encoding:'utf8'}); assert.equal(run.status,0,run.stderr);
    for(const [source,dest] of files) assert.deepEqual(await readFile(join(env.output,dest)),await readFile(join(env.root,source)));
  } finally {await rm(env.root,{recursive:true,force:true});}
});
test('missing source fails clearly without partially refreshing downloads',async () => {
  const env=await setup(); try {
    await writeFile(join(env.root,'guide.md'),'present');
    const run=spawnSync(process.execPath,[env.file],{encoding:'utf8'}); assert.notEqual(run.status,0);assert.match(run.stderr,/Restore guide\.md/);
    await assert.rejects(readFile(join(env.output,'guide.md')),{code:'ENOENT'});
  } finally {await rm(env.root,{recursive:true,force:true});}
});
