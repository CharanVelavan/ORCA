import { after, test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'vite';
const server = await createServer({configFile:false,server:{middlewareMode:true,hmr:false},optimizeDeps:{noDiscovery:true,include:[]},appType:'custom'});
after(() => server.close());
const { conditionTime, parseActiveConditions } = await server.ssrLoadModule('/src/shell/pages/activeConditions.ts');
test('condition countdown follows simulation time and pending start', () => {
  const pending = {id:'INJ-1',kind:'rain',label:'Rain',target:'CHN-01',start:3,end:8,state:'pending',cancellable:true};
  assert.equal(conditionTime(pending,2), 'Starts next step · 5 min');
  assert.equal(conditionTime({...pending,state:'active'},5), '3 min remaining');
  assert.equal(conditionTime({...pending,state:'active',end:null},5), 'End time unavailable');
});
test('only a valid director snapshot becomes displayed condition state', () => {
  const item = {id:'INJ-1',kind:'rain',label:'Rain',target:'CHN-01',start:3,end:8,state:'active',cancellable:true};
  assert.deepEqual(parseActiveConditions({t:5,running_injections:[item]}), {t:5,items:[item]});
  assert.equal(parseActiveConditions({t:5,running_injections:[{...item,cancellable:'yes'}]}), null);
  assert.equal(parseActiveConditions({t:5,injections:[item]}), null);
});
