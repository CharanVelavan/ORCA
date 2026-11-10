import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { createServer } from 'vite';
const server = await createServer({configFile:false,server:{middlewareMode:true,hmr:false},optimizeDeps:{noDiscovery:true,include:[]},appType:'custom'});
after(() => server.close());
const { scenarioDimensions, DIMENSIONS } = await server.ssrLoadModule('/src/simulator/scenarioDimensions.ts');
test('all ten scenario plans use only the nine selected dimensions with explicit reasons', () => {
  for (const [id,count] of Object.entries({S0:5,S1:9,S2:9,S3:9,N1:9,N2:8,N3:8,N4:9,N5:9,CAP:9})) {
    const plan = scenarioDimensions(id);
    assert.equal(plan.count,count,id); assert.equal(plan.total,9);
    assert.equal(new Set(plan.dimensions).size,count); assert.ok(plan.reason.length>30);
    assert.ok(plan.dimensions.every(dimension=>Object.hasOwn(DIMENSIONS,dimension)));
  }
});
test('baseline and payment/audit exclusions remain explicit; unknown scenarios get no invented count', () => {
  for (const id of ['D6','D8','D9','D11']) assert.ok(!scenarioDimensions('s0').dimensions.includes(id));
  for (const id of ['N2','N3']) assert.ok(!scenarioDimensions(id).dimensions.includes('D11'));
  assert.equal(scenarioDimensions('unknown'),null);
});
