import assert from 'node:assert/strict';
import Module from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { buildSync } from 'esbuild';

const source = fileURLToPath(new URL('./normalize.ts', import.meta.url));
const compiled = buildSync({ entryPoints: [source], bundle: true, platform: 'node', format: 'cjs', write: false, logLevel: 'silent' });
const filename = join(dirname(source), 'normalize-test-bundle.cjs');
const bundle = new Module(filename);
bundle.filename = filename;
bundle.paths = Module._nodeModulePaths(dirname(filename));
bundle._compile(compiled.outputFiles[0].text, filename);
const { scenarioFromFile } = bundle.exports;

test('recording names preserve the S, N, and CAP scenario families', () => {
  assert.equal(scenarioFromFile('live-20261109-190000-s1-rules-mock.jsonl'), 'S1');
  assert.equal(scenarioFromFile('live-20261109-190000-n5-rules-mock.jsonl'), 'N5');
  assert.equal(scenarioFromFile('live-20261109-190000-cap-rules-mock.jsonl'), 'CAP');
  assert.equal(scenarioFromFile('unknown-recording.jsonl'), 'S1');
});
