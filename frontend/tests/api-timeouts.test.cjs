const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');

const source = ts.transpileModule(fs.readFileSync(require.resolve('../src/lib/api.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

function createApiContext(overrides = {}) {
  const storage = new Map();
  const context = {
    exports: {},
    process: { env: {} },
    FormData,
    AbortSignal,
    AbortController,
    localStorage: {
      getItem: (k) => storage.get(k) ?? null,
      setItem: (k, v) => storage.set(k, v),
      removeItem: (k) => storage.delete(k),
    },
    window: { location: { assign: () => {} } },
    fetch: () => new Promise(() => {}),
    ...overrides,
  };
  vm.runInNewContext(source, context);
  return context.exports;
}

test('endpoint timeouts match specification', () => {
  const { getDefaultTimeoutForEndpoint } = createApiContext();
  assert.equal(getDefaultTimeoutForEndpoint('/user/settings'), 15000);
  assert.equal(getDefaultTimeoutForEndpoint('/settings'), 15000);
  assert.equal(getDefaultTimeoutForEndpoint('/analysis/research/42'), 20000);
  assert.equal(getDefaultTimeoutForEndpoint('/analysis/research/status'), 20000);
  assert.equal(getDefaultTimeoutForEndpoint('/resume/upload'), 45000);
  assert.equal(getDefaultTimeoutForEndpoint('/resume/pipeline'), 200000);
  assert.equal(getDefaultTimeoutForEndpoint('/interview/start'), 200000);
  assert.equal(getDefaultTimeoutForEndpoint('/interview/evaluate'), 200000);
  assert.equal(getDefaultTimeoutForEndpoint('/chat/message'), 200000);
  assert.equal(getDefaultTimeoutForEndpoint('/analysis/analyze'), 200000);
  assert.equal(getDefaultTimeoutForEndpoint('/auth/login'), 30000);
  assert.equal(getDefaultTimeoutForEndpoint('/auth/change-password'), 30000);
  assert.equal(getDefaultTimeoutForEndpoint('/other/endpoint'), 30000);
});

test('request timeout produces 408 ApiError', async () => {
  const exports = createApiContext({
    fetch: () => {
      const err = new Error('The operation was aborted');
      err.name = 'TimeoutError';
      return Promise.reject(err);
    },
  });

  await assert.rejects(
    exports.fetchApi('/user/settings'),
    (err) => {
      assert.equal(err.status, 408);
      assert.match(err.message, /timed out/i);
      return true;
    }
  );
});

test('caller abort produces 499 cancellation error', async () => {
  const controller = new AbortController();
  const exports = createApiContext({
    fetch: () => {
      const err = new Error('The operation was aborted');
      err.name = 'AbortError';
      return Promise.reject(err);
    },
  });

  controller.abort();
  await assert.rejects(
    exports.fetchApi('/user/settings', { signal: controller.signal }),
    (err) => {
      assert.equal(err.status, 499);
      assert.match(err.message, /cancelled/i);
      return true;
    }
  );
});
