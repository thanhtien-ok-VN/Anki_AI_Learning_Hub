/* Smoke test for the browser-only Hub bootstrap (no external DOM library). */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const appPath = path.join(__dirname, '..', 'web', 'js', 'app.js');
const appSource = fs.readFileSync(appPath, 'utf8');

const makeElement = () => ({
  addEventListener() {},
  appendChild() {},
  className: '',
  dataset: {},
  hidden: false,
  innerHTML: '',
  onclick: null,
  querySelector: () => makeElement(),
  querySelectorAll: () => [],
  removeEventListener() {},
  style: {},
  textContent: '',
  value: '',
});

async function run() {
  const root = makeElement();
  const listeners = new Map();
  const document = {
    addEventListener(event, callback) { listeners.set(event, callback); },
    documentElement: { lang: '' },
    readyState: 'loading',
    querySelector(selector) {
      return selector === '#app' ? root : makeElement();
    },
    querySelectorAll: () => [],
  };
  const bridge = {
    abortAll() {},
    send() {},
    sendAsync: async () => ({}),
  };
  const window = {
    AbortController,
    Bridge: bridge,
    addEventListener(event, callback) { listeners.set(event, callback); },
    clearInterval,
    clearTimeout,
    console,
    document,
    localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    location: { hash: '' },
    setInterval,
    setTimeout,
  };
  const context = {
    AbortController,
    Bridge: bridge,
    console,
    document,
    localStorage: window.localStorage,
    location: window.location,
    setInterval,
    clearInterval,
    setTimeout,
    clearTimeout,
    window,
  };

  vm.runInNewContext(appSource, context, { filename: appPath });

  assert.equal(typeof window.App, 'object', 'bootstrap must expose window.App');
  assert.equal(typeof window.App.start, 'function', 'bootstrap must expose App.start');
  assert.equal(typeof listeners.get('DOMContentLoaded'), 'function', 'bootstrap must register DOMContentLoaded handler');

  await window.App.start();
  assert.match(root.innerHTML, /AI Learning Hub/, 'starting the app must replace the boot overlay with the home screen');
}

run().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
