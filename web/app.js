/* Relayloom workroom. All authority and revision checks are enforced by the server. */
(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  let csrf = '', snapshot = null, stream = null, selectedRole = 'product', busy = false;
  let intentRevision = null, refreshTimer = null;
  let sessionEpoch = 0;
  const labels = { product: 'Product', engineering: 'Engineering', support: 'Support' };
  const icons = { product: 'P', engineering: 'E', support: 'S' };
  const subtitles = { product: 'Direction & audience', engineering: 'Implementation & constraints', support: 'Connected customer response' };
  const node = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const readable = value => typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  const canEdit = () => snapshot && ['owner', 'editor'].includes(snapshot.member.role);
  const isOwner = () => snapshot && snapshot.member.role === 'owner';
  function notice(message = '') {
    $('#notice').textContent = message;
    $('#notice').hidden = !message;
  }
  function connection(state, label) {
    $('#connection').className = `connection ${state}`;
    $('#connection-label').textContent = label;
  }
  const isCurrent = epoch => epoch === sessionEpoch;
  function requireCurrent(epoch) {
    if (!isCurrent(epoch)) {
      const error = new Error('This workroom session has ended.');
      error.staleSession = true;
      throw error;
    }
  }
  function disconnect() {
    if (stream) stream.close();
    stream = null;
    clearInterval(refreshTimer); refreshTimer = null;
  }
  async function api(path, body, epoch = sessionEpoch, token = csrf) {
    requireCurrent(epoch);
    const headers = { Accept: 'application/json' };
    const options = { headers, credentials: 'same-origin', cache: 'no-store' };
    if (body !== undefined) {
      options.method = 'POST'; headers['Content-Type'] = 'application/json';
      if (token) headers['X-Relayloom-CSRF'] = token;
      options.body = JSON.stringify(body);
    }
    let response;
    try { response = await fetch(`/api/${path}`, options); }
    catch (_) { requireCurrent(epoch); throw new Error('The workroom is unreachable. Check the local server and try again.'); }
    requireCurrent(epoch);
    const data = await response.json().catch(() => ({}));
    requireCurrent(epoch);
    if (!response.ok) {
      if (response.status === 401 && path === 'logout') return {};
      if (response.status === 401 && path !== 'join') signedOut();
      const detail = data.error || data.message;
      throw new Error(typeof detail === 'string' ? detail : `Could not complete this action (${response.status}). Refresh and try again.`);
    }
    return data;
  }
  function signedOut() {
    sessionEpoch += 1;
    disconnect();
    snapshot = null; csrf = ''; busy = false; intentRevision = null; selectedRole = 'product';
    for (const id of ['tasks', 'task-detail', 'artifact-content', 'events', 'usage', 'loom', 'loom-summary', 'autonomy', 'approval-record']) $(`#${id}`).replaceChildren();
    for (const id of ['room-name', 'authority', 'intent-brief', 'intent-audience', 'intent-refund', 'invite-expiry']) $(`#${id}`).textContent = '';
    $('#revision').textContent = 'REV —'; $('#event-count').textContent = '0';
    $('#artifact-status').textContent = 'Awaiting publication';
    $('#mode-title').textContent = 'Local rehearsal';
    $('#mode-description').textContent = 'Invented records · deterministic outputs · no model calls';
    $('#invite-code').value = ''; $('#invite-result').hidden = true;
    $('#copy-invite').textContent = 'Copy invite code';
    for (const id of ['edit-intent', 'invite-button', 'run-button', 'publish-button', 'publish-permission']) {
      $(`#${id}`).disabled = true;
      if (id !== 'publish-permission') $(`#${id}`).hidden = true;
    }
    $('#publish-permission').checked = false; $('#permission-row').hidden = true;
    for (const id of ['result-tab', 'activity-tab']) $(`#${id}`).disabled = true;
    document.querySelectorAll('dialog').forEach(dialog => { if (dialog.open) dialog.close(); });
    document.querySelectorAll('form').forEach(form => {
      form.reset();
      const error = $('.form-error', form); if (error) error.textContent = '';
    });
    $('#intent-form button[type="submit"]').disabled = true;
    $('#invite-form button[type="submit"]').disabled = true;
    $('#create-form button[type="submit"]').disabled = false;
    $('#join-form button[type="submit"]').disabled = false;
    setTab('result'); notice();
    $('#welcome').hidden = false; $('#workroom').hidden = true; $('#logout').hidden = true;
    $('#crumb').textContent = 'Welcome'; $('#member-name').textContent = 'Your workspace';
    $('#member-role').textContent = 'Passwordless access'; $('#member-avatar').textContent = 'R';
    connection('', 'Not connected');
  }
  async function refresh(epoch = sessionEpoch) {
    const state = await api('state', undefined, epoch);
    requireCurrent(epoch);
    render(state, epoch);
  }
  function connect(epoch = sessionEpoch) {
    if (!isCurrent(epoch) || !snapshot || !csrf) return;
    disconnect();
    connection('', 'Connecting…');
    const nextStream = new EventSource('/api/events');
    stream = nextStream;
    const active = () => isCurrent(epoch) && stream === nextStream && !!snapshot;
    nextStream.onopen = () => { if (active()) connection('connected', 'Live workroom'); };
    nextStream.addEventListener('state', event => {
      if (!active()) return;
      try { render(JSON.parse(event.data), epoch); connection('connected', 'Live workroom'); }
      catch (_) { if (active()) notice('A workroom update could not be read. Refresh to get the latest state.'); }
    });
    nextStream.onerror = () => { if (active()) connection('disconnected', 'Reconnecting…'); };
    // Also reconcile after reconnects and in browsers that suspend event streams.
    refreshTimer = setInterval(() => {
      if (active() && document.visibilityState === 'visible') refresh(epoch).catch(() => { if (active()) connection('disconnected', 'Connection interrupted'); });
    }, 15000);
  }
  async function initialize(epoch = sessionEpoch) {
    try {
      const session = await api('session', undefined, epoch);
      requireCurrent(epoch);
      if (!session.signed_in) { signedOut(); return; }
      csrf = session.csrf;
      await refresh(epoch); requireCurrent(epoch); connect(epoch);
    } catch (error) { if (isCurrent(epoch)) { signedOut(); notice(error.message); } }
  }
  function statusBadge(state) { return node('span', `status ${String(state).toLowerCase()}`, String(state).replaceAll('_', ' ')); }
  function render(state, epoch = sessionEpoch) {
    if (!isCurrent(epoch) || !csrf || !state.room || !state.member) return;
    if (snapshot?.room.id === state.room.id && state.room.revision < snapshot.room.revision) return;
    if (snapshot?.room.id === state.room.id && state.room.revision === snapshot.room.revision) {
      const latest = events => Math.max(0, ...(events || []).map(event => Number(event.seq) || 0));
      if (latest(state.events) < latest(snapshot.events)) return;
    }
    snapshot = state;
    $('#welcome').hidden = true; $('#workroom').hidden = false; $('#logout').hidden = false;
    $('#room-name').textContent = state.room.name; $('#crumb').textContent = state.room.name;
    $('#member-name').textContent = state.member.name; $('#member-role').textContent = `${state.member.role} · this workroom`;
    $('#member-avatar').textContent = (state.member.name || 'R').slice(0, 1).toUpperCase();
    $('#authority').textContent = state.member.role.toUpperCase(); $('#revision').textContent = `REV ${state.room.revision}`;
    const rehearsal = state.room.mode !== 'meta';
    $('#mode-title').textContent = rehearsal ? 'Local rehearsal' : 'Meta adapter configured';
    $('#mode-description').textContent = rehearsal ? 'Invented records · deterministic outputs · no model calls' : 'Meta requests on the fixed public fixture · attempts and reported usage below';
    $('#intent-brief').textContent = state.room.intent.brief;
    $('#intent-audience').textContent = state.room.intent.audience || 'Not specified';
    $('#intent-refund').textContent = `${state.room.intent.refund_days ?? '—'} days`;
    $('#edit-intent').hidden = !canEdit(); $('#invite-button').hidden = !isOwner();
    $('#edit-intent').disabled = busy || !canEdit(); $('#invite-button').disabled = busy || !isOwner();
    $('#intent-form button[type="submit"]').disabled = busy || !canEdit();
    $('#invite-form button[type="submit"]').disabled = busy || !isOwner();
    for (const id of ['result-tab', 'activity-tab']) $(`#${id}`).disabled = false;
    $('#run-button').hidden = !canEdit();
    $('#run-button').disabled = busy || state.tasks.some(task => task.state === 'RUNNING');
    $('#run-button').textContent = state.tasks.some(task => task.state === 'RUNNING') ? 'Working…' : 'Run specialists';
    renderTasks(); renderDetail(); renderArtifact(); renderEvents(); renderLoom(); renderAutonomy();
    $('#usage').replaceChildren();
    for (const [key, label] of [['model_calls', rehearsal ? 'model calls' : 'request attempts'], ['outputs_reused', 'outputs reused'], ['artifacts_published', 'artifacts published']]) {
      const item = node('span'); item.append(node('strong', '', String(state.metrics?.[key] ?? 0)), document.createTextNode(label)); $('#usage').append(item);
    }
  }
  function renderTasks() {
    if (!snapshot) return;
    const epoch = sessionEpoch;
    const container = $('#tasks'); container.replaceChildren();
    if (!snapshot.tasks.some(task => task.role === selectedRole)) selectedRole = snapshot.tasks[0]?.role;
    for (const task of snapshot.tasks) {
      const card = node('button', `task${selectedRole === task.role ? ' selected' : ''}`);
      card.type = 'button'; card.setAttribute('aria-pressed', String(selectedRole === task.role));
      const top = node('div', 'task-top'), title = node('div');
      title.append(node('span', 'task-title', task.label || labels[task.role] || task.role), node('span', 'task-subtitle', subtitles[task.role] || 'Specialist'));
      top.append(node('span', 'task-icon', icons[task.role] || '◇'), title, statusBadge(task.state));
      card.append(top, node('p', 'task-reason', task.reason || stateReason(task.state)));
      const bottom = node('div', 'task-bottom');
      const source = task.origin_revision == null ? 'No output yet' : task.state === 'REUSED' ? `Kept from revision ${task.origin_revision}` : `Written on revision ${task.origin_revision}`;
      bottom.append(node('span', '', source), node('span', '', 'Evidence'));
      card.append(bottom);
      card.addEventListener('click', () => { if (!isCurrent(epoch) || !snapshot) return; selectedRole = task.role; renderTasks(); renderDetail(); setTab('result'); });
      container.append(card);
    }
  }
  function stateReason(state) {
    return ({ WAITING: 'Ready when its inputs are available.', RUNNING: 'Working with the current intent.', COMPLETE: 'Output is ready for current checks.', REUSED: 'Valid output retained from an earlier revision.', SUPERSEDED: 'The intent changed. This output is no longer current.', FAILED: 'Execution stopped. See activity for details.' })[state] || 'Waiting for an update.';
  }
  function renderDetail() {
    if (!snapshot) return;
    const container = $('#task-detail'), task = snapshot.tasks.find(item => item.role === selectedRole);
    container.replaceChildren();
    if (!task) { container.append(node('p', 'outcome-message', 'Run the specialists to see their work here.')); return; }
    const heading = node('div', 'detail-heading'); heading.append(node('h3', '', `${task.label || labels[task.role] || task.role} output`), statusBadge(task.state));
    container.append(heading);
    const meta = node('div', 'detail-meta'); meta.append(node('span', '', `Current intent · revision ${snapshot.room.revision}`));
    if (task.origin_revision != null) meta.append(node('span', '', `Output · revision ${task.origin_revision}`));
    container.append(meta);
    if (task.summary) container.append(node('div', 'result-copy', readable(task.summary)));
    else {
      const empty = node('div', 'empty-state'); empty.append(node('span', 'empty-glyph', icons[task.role] || '◇'), node('h3', '', task.state === 'RUNNING' ? 'Work is in progress' : 'The next thread starts here'), node('p', '', task.reason || stateReason(task.state))); container.append(empty);
    }
  }
  function renderArtifact() {
    if (!snapshot) return;
    const artifact = snapshot.artifact, content = $('#artifact-content'); content.replaceChildren();
    const current = artifact && artifact.revision === snapshot.room.revision;
    $('#artifact-status').textContent = current ? `Published · revision ${artifact.revision}` : artifact ? `Earlier · revision ${artifact.revision}` : 'Awaiting publication';
    if (artifact) {
      if (!current) content.append(node('p', 'outcome-message', 'This artifact belongs to an earlier intent. Run current work and publish again.'));
      const policy = artifact.payload?.intent || {};
      const facts = node('dl', 'artifact-facts');
      for (const [label, value] of [['Audience', policy.audience || 'Not recorded'], ['Refund window', Number.isInteger(policy.refund_days) ? `${policy.refund_days} days` : 'Not recorded']]) {
        const fact = node('div'); fact.append(node('dt', '', label), node('dd', '', value)); facts.append(fact);
      }
      content.append(facts);
      const response = node('div', 'artifact-response');
      response.append(node('h4', '', 'Support response'), node('p', '', artifact.payload?.specialists?.support?.summary || 'No support summary was recorded.'));
      content.append(response);
      const checks = node('ul', 'checks');
      const outcomes = [
        ['Current revision', current && artifact.checks?.current_revision === true],
        ['Draft scope', artifact.checks?.draft_only_scope === true && artifact.payload?.scope === 'local-artifact-only'],
        ['Inputs/dependencies', artifact.checks?.inputs_and_dependencies === true],
        ['Owner permission', artifact.checks?.owner_permission === true]
      ];
      for (const [label, passed] of outcomes) {
        const item = node('li', `artifact-check ${passed ? 'passed' : 'attention'}`);
        item.append(node('span', '', label), node('strong', '', passed ? 'Passed' : 'Needs attention')); checks.append(item);
      }
      content.append(checks, node('p', 'subtle', 'Publication checks are recorded evidence. The current revision is compared above.'));
      const technical = node('details', 'technical-evidence');
      technical.append(node('summary', '', 'Technical evidence'), node('pre', 'artifact-json', readable({ revision: artifact.revision, checks: artifact.checks, payload: artifact.payload })));
      content.append(technical);
    } else content.append(node('p', 'outcome-message', 'Complete the specialist work, then publish a checked artifact for this intent.'));
    $('#permission-row').hidden = !isOwner();
    $('#publish-permission').checked = !!snapshot.room.permission?.publish;
    $('#publish-permission').disabled = busy;
    $('#publish-button').hidden = !isOwner();
    const ready = snapshot.tasks.length > 0 && snapshot.tasks.every(task => ['COMPLETE', 'REUSED'].includes(task.state));
    $('#publish-button').disabled = busy || !snapshot.room.permission?.publish || !ready || !!current;
    $('#publish-button').textContent = current ? 'Artifact published' : 'Publish checked artifact';
    if (!isOwner() && !artifact) content.append(node('p', 'subtle', 'The workroom owner can approve and publish the artifact.'));
    renderApproval(current, ready);
  }
  const clock = seconds => {
    const date = new Date(Number(seconds) * 1000);
    return Number.isNaN(date.getTime()) ? 'unknown time' : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };
  function renderApproval(current, ready) {
    const box = $('#approval-record'); box.replaceChildren();
    if (!snapshot) return;
    const revision = snapshot.room.revision;
    const active = (snapshot.approvals || []).find(item => item.active && item.revision === revision && item.operation === 'publish_artifact');
    const limits = snapshot.autonomy?.operations?.publish_artifact?.limits || {};
    const limit = `${limits.artifacts_per_revision ?? 1} artifact, ${String(limits.scope || 'local-artifact-only').replaceAll('-', ' ')}`;
    const step = (label, state, text) => {
      const item = node('li', `approval-step ${state}`);
      item.append(node('span', 'approval-label', label), node('span', 'approval-text', text));
      return item;
    };
    const steps = node('ol', 'approval-steps');
    steps.append(step('Request', ready ? 'done' : 'pending', ready ? `Publish revision ${revision}. Limit: ${limit}.` : `Publishing revision ${revision} can be requested once current work completes.`));
    steps.append(step('Decision', active ? 'done' : 'pending', active ? `Approved by ${active.approver} at ${clock(active.approved_at)} for revision ${active.revision}.` : 'No approval recorded. Publication cannot run.'));
    const outcome = snapshot.outcome;
    let proof;
    if (!current || !outcome || outcome.revision !== revision) proof = step('Outcome', 'pending', 'Checked after publication against the approval record.');
    else if (outcome.status === 'VERIFIED') proof = step('Verified outcome', 'done', outcome.detail || 'Matches its approval record.');
    else if (outcome.status === 'FAILED') proof = step('Outcome check failed', 'failed', outcome.detail || 'The artifact does not match its approval.');
    else proof = step('Outcome UNKNOWN', 'unknown', `${outcome.detail || 'Not yet reconciled.'} It stays unknown until a read-only check passes.`);
    steps.append(proof);
    box.append(node('h4', '', 'Approval and proof'), steps);
  }
  const levelNames = { assist: 'Assist', draft: 'Draft', execute_within_limits: 'Within limits', execute_with_approval: 'With approval' };
  const operationNames = { explain_changes: 'Explain what changed', specialist_draft: 'Write specialist drafts', specialist_run: 'Run ready specialists', meta_request: 'Meta API request', publish_artifact: 'Publish the artifact' };
  function renderAutonomy() {
    const box = $('#autonomy'); box.replaceChildren();
    const operations = snapshot?.autonomy?.operations;
    if (!operations) { box.append(node('li', 'subtle', 'The autonomy policy could not be read from the server.')); return; }
    for (const [name, value] of Object.entries(operations)) {
      if (name === 'meta_request' && snapshot.room.mode !== 'meta') continue;
      const item = node('li', `autonomy-item ${value.level}`);
      let limit = 'Explains only. Takes no action.';
      if (name === 'specialist_run') limit = `${snapshot.autonomy.runs_this_revision ?? 0} of ${value.limits?.max_runs_per_revision} runs used this revision. No automatic retry.`;
      else if (name === 'publish_artifact') limit = 'Owner approval per revision. One local artifact.';
      else if (name === 'specialist_draft') limit = 'Draft only. No external effect.';
      else if (name === 'meta_request') limit = `At most ${value.limits?.max_attempts_ceiling} attempts. No automatic retry.`;
      item.append(node('span', 'autonomy-level', levelNames[value.level] || value.level), node('strong', '', operationNames[name] || name), node('small', '', limit));
      box.append(item);
    }
  }
  const outcomePatterns = [
    [/^(Product|Engineering|Support) started on revision (\d+)\.$/, 'started'],
    [/^(Product|Engineering|Support) completed on revision (\d+)\.$/, 'done'],
    [/^(Product|Engineering|Support) failed validation on revision (\d+)\.$/, 'failed'],
    [/^Late (Product|Engineering|Support) result from revision (\d+) was discarded\.$/, 'discarded']
  ];
  function history() {
    const outcomes = new Map(), changes = new Map();
    for (const event of snapshot.events || []) {
      const message = String(event.message || '');
      for (const [pattern, kind] of outcomePatterns) {
        const match = pattern.exec(message);
        if (!match) continue;
        const key = `${match[1].toLowerCase()}:${match[2]}`;
        if (kind !== 'started' || !outcomes.has(key)) outcomes.set(key, kind);
      }
      const change = /^(.+) advanced intent to revision (\d+);/.exec(message);
      if (event.type === 'intent_changed' && change) changes.set(Number(change[2]), change[1]);
    }
    return { outcomes, changes };
  }
  function loomCell(state, text, current, thread, who) {
    const cell = node('div', `loom-cell${current ? ' current' : ''}`);
    cell.setAttribute('data-state', state);
    cell.setAttribute('data-thread', thread);
    const label = node('small', '', text);
    if (who) label.append(node('span', 'who', ` by ${who}`));
    cell.append(node('i', `knot ${state}`), label);
    return cell;
  }
  function renderLoom() {
    const loom = $('#loom'), summary = $('#loom-summary');
    loom.replaceChildren(); summary.replaceChildren();
    if (!snapshot) return;
    const revision = snapshot.room.revision, first = Math.max(1, revision - 3);
    const columns = [];
    for (let r = first; r <= revision; r++) columns.push(r);
    loom.setAttribute('data-cols', String(columns.length));
    const { outcomes, changes } = history();
    const header = node('div', 'loom-row header');
    header.append(node('div', 'loom-label'));
    for (const r of columns) header.append(node('div', `loom-cell${r === revision ? ' current' : ''}`, r === revision ? `Rev ${r} now` : `Rev ${r}`));
    loom.append(header);
    const people = node('div', 'loom-row intent'), label = node('div', 'loom-label');
    label.append(node('strong', '', 'People'), node('span', '', 'Shared intent'));
    people.append(label);
    for (const r of columns) people.append(loomCell(r === 1 ? 'intent' : 'intent changed', r === 1 ? 'set' : 'changed', r === revision, 'line', r > 1 ? changes.get(r) : null));
    loom.append(people);
    let kept = 0, redo = 0;
    for (const task of snapshot.tasks) {
      const row = node('div', 'loom-row'), title = node('div', 'loom-label');
      title.append(node('strong', '', task.label || labels[task.role] || task.role), node('span', '', subtitles[task.role] || 'Specialist'));
      row.append(title);
      const carriedFrom = task.state === 'REUSED' ? task.origin_revision : null;
      for (const r of columns) {
        const carried = carriedFrom != null && r >= carriedFrom;
        if (r === revision) {
          const map = { REUSED: ['kept', `kept from rev ${task.origin_revision}`], RUNNING: ['running', 'working'], FAILED: ['failed', 'failed'], SUPERSEDED: ['discarded', 'superseded'] };
          let [state, text] = map[task.state] || ['waiting', String(task.state).toLowerCase()];
          if (task.state === 'COMPLETE') [state, text] = revision > 1 ? ['redone', 'redone'] : ['done', 'done'];
          if (task.state === 'WAITING') [state, text] = revision > 1 ? ['todo', 'to redo'] : ['waiting', task.role === 'support' ? 'waits for inputs' : 'ready'];
          row.append(loomCell(state, text, true, carried ? 'carried' : 'line'));
        } else {
          const outcome = outcomes.get(`${task.role}:${r}`);
          const state = outcome === 'started' ? 'discarded' : outcome || (carried ? 'kept' : 'empty');
          const text = { done: 'done', failed: 'failed', discarded: outcome === 'started' ? 'superseded' : 'late, refused', kept: 'kept', empty: 'not run' }[state];
          row.append(loomCell(state, text, false, carried ? 'carried' : outcome ? 'line' : 'none'));
        }
      }
      if (task.state === 'REUSED') kept += 1; else if (revision > 1) redo += 1;
      loom.append(row);
    }
    const refused = (snapshot.events || []).filter(event => event.type === 'stale_discarded').length;
    const chip = (value, text, lead) => {
      const item = node('span', lead ? 'lead' : '');
      item.append(node('strong', '', String(value)), document.createTextNode(text));
      return item;
    };
    if (revision === 1) summary.append(chip(1, 'revision: all work is new', true));
    else summary.append(chip(kept, kept === 1 ? 'output kept' : 'outputs kept', true), chip(redo, redo === 1 ? 'task redone' : 'tasks redone'));
    summary.append(chip(refused, refused === 1 ? 'late result refused' : 'late results refused'), chip(snapshot.metrics?.model_calls ?? 0, snapshot.room.mode === 'meta' ? 'request attempts' : 'model calls'));
  }
  function renderEvents() {
    if (!snapshot) return;
    $('#event-count').textContent = String(snapshot.events.length);
    const list = $('#events'); list.replaceChildren();
    if (!snapshot.events.length) { list.append(node('li', 'event-message', 'No activity recorded yet.')); return; }
    for (const event of [...snapshot.events].reverse()) {
      const item = node('li'); item.append(node('div', 'event-message', event.message));
      const meta = node('div', 'event-meta');
      let time = event.created_at;
      if (time != null) {
        const date = new Date(typeof time === 'number' ? time * 1000 : time);
        if (!Number.isNaN(date.getTime())) time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      }
      meta.append(node('span', '', String(event.type || 'event').replaceAll('_', ' ')), node('time', '', time || ''));
      item.append(meta); list.append(item);
    }
  }
  function setTab(name) {
    for (const tab of ['result', 'activity']) {
      const active = tab === name;
      $(`#${tab}-tab`).classList.toggle('active', active); $(`#${tab}-tab`).setAttribute('aria-selected', String(active));
      $(`#${tab}-panel`).hidden = !active;
    }
  }
  $('#result-tab').addEventListener('click', () => setTab('result'));
  $('#activity-tab').addEventListener('click', () => setTab('activity'));
  $('.tabbar').addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault(); const name = $('#result-panel').hidden ? 'result' : 'activity'; setTab(name); $(`#${name}-tab`).focus();
    }
  });
  document.querySelectorAll('[data-open]').forEach(button => button.addEventListener('click', () => {
    const dialog = document.getElementById(button.dataset.open);
    if (dialog.id === 'intent-dialog' && !canEdit()) return;
    if (dialog.id === 'invite-dialog' && !isOwner()) return;
    $('.form-error', dialog).textContent = '';
    if (dialog.id === 'intent-dialog' && snapshot) {
      const form = $('#intent-form'); intentRevision = snapshot.room.revision;
      for (const key of ['brief', 'audience', 'refund_days']) form.elements[key].value = snapshot.room.intent[key] ?? '';
    }
    if (dialog.id === 'invite-dialog') $('#invite-result').hidden = true;
    dialog.showModal();
  }));
  document.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
  async function mutation(path, body) {
    const epoch = sessionEpoch;
    if (!snapshot || !csrf) throw new Error('Sign in to a workroom before continuing.');
    busy = true; if (snapshot) render(snapshot); notice();
    try { const result = await api(path, body, epoch); await refresh(epoch); requireCurrent(epoch); return result; }
    finally { if (isCurrent(epoch)) { busy = false; if (snapshot) render(snapshot); } }
  }
  for (const type of ['create', 'join', 'intent', 'invite']) {
    $(`#${type}-form`).addEventListener('submit', async event => {
      event.preventDefault(); const form = event.currentTarget, submit = $('button[type="submit"]', form), errorBox = $('.form-error', form);
      let epoch = sessionEpoch;
      errorBox.textContent = ''; submit.disabled = true;
      try {
        if (type === 'intent' && !canEdit()) throw new Error('Sign in with editing permission to change intent.');
        if (type === 'invite' && !isOwner()) throw new Error('Only the signed-in owner can create invites.');
        const body = Object.fromEntries(new FormData(form));
        if (type === 'intent') { body.revision = intentRevision; body.refund_days = Number(body.refund_days); }
        if (type === 'create' || type === 'join') {
          // Invalidate a session check from before this new sign-in attempt.
          epoch = ++sessionEpoch; disconnect();
          await api(type === 'create' ? 'rooms' : 'join', body, epoch);
          await initialize(epoch); requireCurrent(epoch);
          if (!snapshot) throw new Error('Your session could not be opened. Try joining again.');
          form.closest('dialog').close(); form.reset(); notice();
        } else if (type === 'intent') {
          await mutation('intent', body); requireCurrent(epoch); form.closest('dialog').close();
        } else {
          const result = await api('invites', body, epoch); requireCurrent(epoch); $('#invite-code').value = result.invite;
          const expires = new Date(typeof result.expires === 'number' ? result.expires * 1000 : result.expires);
          $('#invite-expiry').textContent = result.expires && !Number.isNaN(expires.getTime()) ? `Expires ${expires.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })} · one use only` : 'One use only. The server enforces invite expiry.';
          $('#invite-result').hidden = false;
        }
      } catch (error) { if (isCurrent(epoch)) { errorBox.textContent = error.message; if (snapshot) refresh(epoch).catch(() => {}); } }
      finally { if (isCurrent(epoch)) submit.disabled = (type === 'intent' && !canEdit()) || (type === 'invite' && !isOwner()); }
    });
  }
  $('#run-button').addEventListener('click', async () => {
    const epoch = sessionEpoch;
    if (!canEdit() || busy) return;
    try { await mutation('run', { revision: snapshot.room.revision }); }
    catch (error) { if (isCurrent(epoch)) notice(error.message); }
  });
  $('#publish-permission').addEventListener('change', async event => {
    const publish = event.target.checked;
    const epoch = sessionEpoch;
    if (!isOwner() || busy) return;
    try { await mutation('permission', { revision: snapshot.room.revision, publish }); }
    catch (error) { if (isCurrent(epoch)) { notice(error.message); if (snapshot) renderArtifact(); } }
  });
  $('#publish-button').addEventListener('click', async () => {
    const epoch = sessionEpoch;
    if (!isOwner() || busy) return;
    try { await mutation('publish', { revision: snapshot.room.revision }); }
    catch (error) { if (isCurrent(epoch)) notice(error.message); }
  });
  $('#logout').addEventListener('click', async () => {
    const token = csrf;
    signedOut();
    const epoch = sessionEpoch;
    try { await api('logout', {}, epoch, token); if (isCurrent(epoch)) notice(); }
    catch (error) { if (isCurrent(epoch)) notice('This page has been cleared, but server sign-out could not be confirmed. Close this browser session on a shared computer.'); }
  });
  $('#copy-invite').addEventListener('click', async () => {
    const epoch = sessionEpoch;
    if (!isOwner()) return;
    const input = $('#invite-code');
    const code = input.value;
    if (!code) return;
    try { await navigator.clipboard.writeText(code); if (!isCurrent(epoch) || !isOwner()) return; $('#copy-invite').textContent = 'Copied ✓'; setTimeout(() => { if (isCurrent(epoch)) $('#copy-invite').textContent = 'Copy invite code'; }, 1800); }
    catch (_) { if (isCurrent(epoch) && isOwner()) { input.focus(); input.select(); $('#invite-expiry').textContent = 'Select and copy this code to share it.'; } }
  });
  initialize();
})();
