const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const source = ts.transpileModule(fs.readFileSync(require.resolve('../src/lib/api.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

for (const nextToken of [null, 'new-session', 'old-session']) {
  test(`delayed unauthorized response with current token ${nextToken}`, async () => {
    const storage = new Map([['careermind_token', 'old-session'], ['careermind_research_job', 'job']]);
    const redirects = [];
    let finish;
    const context = {
      exports: {}, process: { env: {} }, FormData, AbortSignal,
      localStorage: { getItem: k => storage.get(k) ?? null, removeItem: k => storage.delete(k) },
      window: { location: { assign: path => redirects.push(path) } },
      fetch: () => new Promise(resolve => { finish = resolve; }),
    };
    vm.runInNewContext(source, context);
    const request = context.exports.fetchApi('/analysis/reports');
    if (nextToken === null) storage.delete('careermind_token');
    else storage.set('careermind_token', nextToken);
    finish(new Response(JSON.stringify({ detail: 'Session expired' }), {
      status: 401, headers: { 'Content-Type': 'application/json' },
    }));
    await assert.rejects(request, error => error.status === 401);
    assert.deepEqual(redirects, nextToken === 'old-session' ? ['/login'] : []);
    assert.equal(storage.get('careermind_token') ?? null, nextToken === 'old-session' ? null : nextToken);
    assert.equal(storage.has('careermind_research_job'), nextToken !== 'old-session');
  });
}
