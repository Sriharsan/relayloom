'use strict';
// Offline session-boundary tests. This DOM double tests application state, not layout.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '..', 'web', 'app.js'), 'utf8');

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}
const reply = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });
function state(overrides = {}) {
  return {
    room: { id: 'synthetic-room', name: 'PRIVATE ROOM MARKER', revision: 1,
      intent: { brief: 'PRIVATE GOAL MARKER', audience: 'Synthetic customers', refund_days: 30 },
      permission: { publish: true }, mode: 'rehearsal' },
    member: { name: 'PRIVATE MEMBER MARKER', role: 'owner' },
    tasks: [{ role: 'product', label: 'Product', state: 'COMPLETE', origin_revision: 1, summary: 'PRIVATE OUTPUT MARKER' }],
    events: [{ seq: 1, type: 'synthetic', message: 'PRIVATE EVENT MARKER', created_at: 1700000000 }],
    artifact: null, metrics: { model_calls: 0, outputs_reused: 0, artifacts_published: 0 }, ...overrides
  };
}

test('an older same-revision snapshot cannot undo a newer permission event', async () => {
  const app=harness(); await app.settled();
  const newer=state(); newer.events=[{seq:8,type:'permission',message:'Current permission',created_at:1700000000}];
  newer.room.permission.publish=false;
  app.streams[0].emit(newer);
  assert.equal(app.get('publish-permission').checked,false);
  const older=state(); older.events=[{seq:7,type:'permission',message:'Old permission',created_at:1700000000}];
  older.room.permission.publish=true;
  app.streams[0].emit(older);
  assert.equal(app.get('publish-permission').checked,false);
  assert.ok(app.get('events').textContent.includes('Current permission'));
});

function harness(initialSession = reply({ signed_in: true, csrf: 'synthetic-csrf' })) {
  const all = [], ids = new Map(), routes = new Map(), requests = [], intervals = new Map(), streams = [];
  let timer = 0;
  class Element {
    constructor(tag = 'div', id = '') {
      this.tagName = tag; this.id = id; this.children = []; this._text = ''; this.value = '';
      this.hidden = false; this.disabled = false; this.open = false; this.checked = false;
      this.listeners = {}; this.attributes = {}; this.dataset = {}; this.elements = {};
      this.classList = { toggle() {} }; all.push(this);
    }
    set textContent(value) { this._text = String(value); this.children = []; }
    get textContent() { return this._text + this.children.map(child => child.textContent || '').join(''); }
    append(...children) { this.children.push(...children); }
    replaceChildren(...children) { this._text = ''; this.children = [...children]; }
    addEventListener(name, callback) { this.listeners[name] = callback; }
    setAttribute(name, value) { this.attributes[name] = value; }
    querySelector(selector) {
      if (selector === '.form-error') return this.error;
      if (selector === 'button[type="submit"]') return this.submit;
      throw new Error(`Unexpected element selector: ${selector}`);
    }
    closest(selector) { assert.equal(selector, 'dialog'); return this.dialog; }
    reset() { for (const field of Object.values(this.elements)) field.value = ''; }
    showModal() { this.open = true; }
    close() { this.open = false; }
    focus() {}
    select() {}
    async emit(name, extra = {}) {
      return this.listeners[name]?.({ currentTarget: this, target: this, preventDefault() {}, ...extra });
    }
  }
  function get(id) { if (!ids.has(id)) ids.set(id, new Element('div', id)); return ids.get(id); }
  const forms = [], dialogs = [];
  const names = { create: ['display_name', 'name', 'brief'], join: ['display_name', 'invite'], intent: ['brief', 'audience', 'refund_days'], invite: ['role'] };
  for (const [type, fields] of Object.entries(names)) {
    const form = get(`${type}-form`), dialog = get(`${type}-dialog`);
    form.tagName = 'form'; dialog.tagName = 'dialog'; form.dialog = dialog;
    form.error = new Element(); form.submit = new Element('button');
    fields.forEach(name => { form.elements[name] = new Element('input'); });
    forms.push(form); dialogs.push(dialog);
  }
  const openers = ['create', 'join', 'intent', 'invite'].map(type => {
    const button = type === 'intent' ? get('edit-intent') : type === 'invite' ? get('invite-button') : get(`open-${type}`);
    button.dataset.open = `${type}-dialog`; return button;
  });
  const tabbar = new Element();
  const document = {
    visibilityState: 'visible', getElementById: get,
    querySelector(selector) {
      if (selector === '.tabbar') return tabbar;
      const match = /^#([\w-]+)(?: (.+))?$/.exec(selector);
      if (match) return match[2] ? get(match[1]).querySelector(match[2]) : get(match[1]);
      throw new Error(`Unexpected document selector: ${selector}`);
    },
    querySelectorAll(selector) {
      return ({ '[data-open]': openers, '[data-close]': [], dialog: dialogs, form: forms })[selector] || [];
    },
    createElement: tag => new Element(tag), createTextNode: text => ({ textContent: String(text) })
  };
  class EventSource {
    constructor() { this.listeners = {}; this.closed = false; streams.push(this); }
    addEventListener(name, callback) { this.listeners[name] = callback; }
    close() { this.closed = true; }
    emit(data) { this.listeners.state?.({ data: JSON.stringify(data) }); }
  }
  routes.set('session', () => initialSession);
  routes.set('state', () => reply(state()));
  routes.set('logout', () => reply({ ok: true }));
  const context = {
    document, EventSource, FormData: class { constructor(form) { return Object.entries(form.elements).map(([key, element]) => [key, element.value]); } },
    navigator: { clipboard: { writeText: async () => {} } },
    setInterval(callback) { intervals.set(++timer, callback); return timer; },
    clearInterval(id) { intervals.delete(id); }, setTimeout() {},
    fetch: async (url, options) => {
      const action = url.slice('/api/'.length); requests.push({ action, options });
      const handler = routes.get(action); if (!handler) throw new Error(`Unexpected request ${action}`);
      return handler(options);
    }
  };
  vm.runInNewContext(source, context);
  return { get, all, routes, requests, streams, intervals, forms, openers,
    async settled() { for (let index = 0; index < 6; index++) await new Promise(setImmediate); },
    text() { return [...ids.values(), ...forms.flatMap(form => Object.values(form.elements))].map(element => `${element.textContent} ${element.value}`).join('\n'); }
  };
}

test('sign out clears private DOM and ignores a pending refresh and old stream events', async () => {
  const app = harness(); await app.settled();
  assert.equal(app.get('workroom').hidden, false);
  const oldStream = app.streams[0], pending = deferred();
  app.routes.set('state', () => pending.promise);
  [...app.intervals.values()][0](); await app.settled();
  app.get('invite-dialog').open = true;
  app.get('invite-code').value = 'PRIVATE INVITE MARKER';
  app.get('intent-form').elements.brief.value = 'PRIVATE DIALOG MARKER';
  const leaving = app.get('logout').emit('click');
  assert.equal(app.requests.find(item => item.action === 'logout').options.headers['X-Relayloom-CSRF'], 'synthetic-csrf');
  assert.equal(app.get('workroom').hidden, true);
  assert.equal(app.get('welcome').hidden, false);
  assert.equal(app.get('run-button').disabled, true);
  assert.equal(app.get('publish-button').disabled, true);
  assert.equal(app.get('invite-dialog').open, false);
  assert.equal(app.get('invite-code').value, '');
  assert.ok(!app.text().includes('PRIVATE '));
  assert.equal(oldStream.closed, true);
  assert.equal(app.intervals.size, 0);
  pending.resolve(reply(state())); await leaving; await app.settled();
  oldStream.emit(state()); oldStream.onopen(); oldStream.onerror();
  assert.equal(app.get('workroom').hidden, true);
  assert.equal(app.get('connection-label').textContent, 'Not connected');
  assert.ok(!app.text().includes('PRIVATE '));
});

test('late session initialization cannot reopen a locally signed-out workroom', async () => {
  const pending = deferred(), app = harness(pending.promise);
  await app.get('logout').emit('click');
  pending.resolve(reply({ signed_in: true, csrf: 'old-session' })); await app.settled();
  assert.equal(app.get('welcome').hidden, false);
  assert.equal(app.get('workroom').hidden, true);
  assert.equal(app.streams.length, 0);
  assert.equal(app.requests.filter(item => item.action === 'state').length, 0);
});

test('a late invite response cannot restore code or dialog content after sign out', async () => {
  const app = harness(); await app.settled();
  const pending = deferred(); app.routes.set('invites', () => pending.promise);
  app.get('invite-dialog').open = true; app.get('invite-form').elements.role.value = 'editor';
  const inviting = app.get('invite-form').emit('submit');
  await app.get('logout').emit('click');
  pending.resolve(reply({ invite: 'PRIVATE LATE INVITE', expires: 1700000000 }));
  await inviting;
  assert.equal(app.get('invite-dialog').open, false);
  assert.equal(app.get('invite-result').hidden, true);
  assert.equal(app.get('invite-code').value, '');
  assert.ok(!app.text().includes('PRIVATE '));
});

test('a late mutation does not refresh or restore action controls after sign out', async () => {
  const app = harness(); await app.settled();
  const pending = deferred(); app.routes.set('run', () => pending.promise);
  const running = app.get('run-button').emit('click');
  await app.get('logout').emit('click'); pending.resolve(reply({ ok: true })); await running;
  assert.equal(app.requests.filter(item => item.action === 'state').length, 1);
  assert.equal(app.get('run-button').disabled, true);
  assert.equal(app.get('workroom').hidden, true);
  assert.equal(app.get('notice').hidden, true);
});

test('an older initial session response cannot cancel a newly created session', async () => {
  const old = deferred(), app = harness(old.promise);
  app.routes.set('rooms', () => reply({ ok: true }));
  app.routes.set('session', () => reply({ signed_in: true, csrf: 'new-session' }));
  const form = app.get('create-form'); form.elements.display_name.value = 'New owner';
  form.elements.name.value = 'New workroom'; form.elements.brief.value = 'A synthetic goal';
  await form.emit('submit');
  old.resolve(reply({ signed_in: false })); await app.settled();
  assert.equal(app.get('workroom').hidden, false);
  assert.equal(app.get('welcome').hidden, true);
  assert.equal(app.streams.length, 1);
});

test('invite expiry is a readable date and private content still clears on failed logout', async () => {
  const app = harness(); await app.settled();
  app.routes.set('invites', () => reply({ invite: 'SYNTHETIC-CODE', expires: 1700000000 }));
  app.get('invite-form').elements.role.value = 'viewer'; await app.get('invite-form').emit('submit');
  assert.match(app.get('invite-expiry').textContent, /^Expires .+ · one use only$/);
  assert.ok(!app.get('invite-expiry').textContent.includes('1700000000'));
  app.routes.set('logout', () => { throw new Error('offline'); }); await app.get('logout').emit('click');
  assert.equal(app.get('workroom').hidden, true);
  assert.ok(!app.text().includes('PRIVATE '));
  assert.match(app.get('notice').textContent, /server sign-out could not be confirmed/);
});

test('published policy is readable and exact technical evidence starts collapsed', async () => {
  const payload = { intent: { brief: 'Synthetic launch policy', audience: 'Customers', refund_days: 14 },
    specialists: { support: { summary: 'Explain the inclusive 14-day refund window.', dependencies: { product: 'synthetic-digest' } } },
    scope: 'local-artifact-only', mode: 'rehearsal' };
  const artifact = { revision: 1, checks: { current_revision: true, draft_only_scope: true, inputs_and_dependencies: true, owner_permission: true }, payload };
  const app = harness(); app.routes.set('state', () => reply(state({ artifact }))); await app.settled();
  const content = app.get('artifact-content');
  assert.match(content.textContent, /AudienceCustomersRefund window14 days/);
  assert.match(content.textContent, /Support responseExplain the inclusive 14-day refund window/);
  const checks = content.children.find(child => child.className === 'checks');
  assert.equal(checks.children.length, 4);
  assert.ok(checks.children.every(child => child.children[1].textContent === 'Passed'));
  const details = content.children.find(child => child.tagName === 'details');
  assert.ok(details); assert.equal(details.open, false);
  assert.equal(details.children[0].textContent, 'Technical evidence');
  assert.deepEqual(JSON.parse(details.children[1].textContent), artifact);
  assert.ok(!content.children.some(child => child.tagName === 'pre'));
});

test('earlier artifact and non-boolean checks never become a current passing proof', async () => {
  const artifact = { revision: 1, checks: { current_revision: true, draft_only_scope: 'true', inputs_and_dependencies: false, owner_permission: true },
    payload: { intent: { audience: 'Customers', refund_days: 14 }, scope: 'external-change' } };
  const app = harness();
  const current = state({ artifact }); current.room.revision = 2;
  app.routes.set('state', () => reply(current)); await app.settled();
  const checks = app.get('artifact-content').children.find(child => child.className === 'checks');
  assert.deepEqual(checks.children.map(child => child.children[1].textContent), ['Needs attention', 'Needs attention', 'Needs attention', 'Passed']);
  assert.match(app.get('artifact-status').textContent, /Earlier/);
});
