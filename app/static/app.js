const urlParams = new URLSearchParams(window.location.search);
const storedInvitation = JSON.parse(localStorage.getItem('celebrait.invitation') || 'null');
const state = { invitation: storedInvitation, response: null, invitationId: urlParams.get('invitation') || storedInvitation?.id || '', responseToken: urlParams.get('response') || '' };
const feedback = (element, message, kind = '') => { element.textContent = message; element.className = `feedback ${kind}`; };
const asISO = (value) => new Date(value).toISOString();
const localDate = (value) => new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
const localInput = (value) => new Date(value).toISOString().slice(0, 16);
const saveInvitation = (invitation) => { state.invitation = invitation; state.invitationId = invitation.id; localStorage.setItem('celebrait.invitation', JSON.stringify(invitation)); };
const api = async (url, options) => { const response = await fetch(url, options); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Something went wrong.'); return data; };

function showView(name) {
  document.querySelectorAll('[data-view-panel]').forEach((panel) => panel.classList.toggle('active', panel.dataset.viewPanel === name));
  document.querySelectorAll('[data-view]').forEach((button) => button.classList.toggle('active', button.dataset.view === name));
  if (name === 'dashboard') renderDashboard();
  if (name === 'manage') renderManage();
  if (name === 'view') renderPreview();
  if (name === 'rsvps') loadResponses();
  if (name === 'guest') loadGuestInvitation();
  const query = new URLSearchParams();
  if (state.invitationId) query.set('invitation', state.invitationId);
  if (state.responseToken) query.set('response', state.responseToken);
  history.replaceState(null, '', `${query.toString() ? `?${query}` : ''}#${name}`);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.addEventListener('click', (event) => { const button = event.target.closest('[data-view]'); if (button) { event.preventDefault(); showView(button.dataset.view); } });

function renderDashboard() {
  const list = document.querySelector('#invitation-list');
  const count = document.querySelector('#invitation-count');
  if (!state.invitation) { count.textContent = '0 events'; return; }
  count.textContent = '1 event';
  list.innerHTML = `<article class="invitation-row"><div class="event-date"><strong>${new Date(state.invitation.starts_at).getDate()}</strong><span>${new Date(state.invitation.starts_at).toLocaleString([], { month: 'short' })}</span></div><div class="event-details"><h3>${state.invitation.title}</h3><p>${localDate(state.invitation.starts_at)} · RSVP closes ${localDate(state.invitation.rsvp_deadline)}</p><small>ID ${state.invitation.id}</small></div><div class="row-actions"><button class="icon-button" data-view="view" title="View invitation">◌</button><button class="icon-button" data-view="manage" title="Edit invitation">✎</button></div></article>`;
}

function renderManage() {
  if (!state.invitation) return showView('create');
  document.querySelector('#manage-title').textContent = state.invitation.title;
  const form = document.querySelector('#edit-form');
  ['title', 'description'].forEach((name) => { form.elements[name].value = state.invitation[name] || ''; });
  ['starts_at', 'rsvp_deadline', 'expires_at'].forEach((name) => { form.elements[name].value = localInput(state.invitation[name]); });
  document.querySelector('#preview-card').innerHTML = `<p class="eyebrow">Live invitation</p><h2>${state.invitation.title}</h2><p>${state.invitation.description || 'A special gathering, thoughtfully planned.'}</p><div class="preview-rule"></div><strong>${localDate(state.invitation.starts_at)}</strong><span>RSVP by ${localDate(state.invitation.rsvp_deadline)}</span><button class="text-button" data-view="view">Open guest view →</button>`;
}

function renderPreview() {
  const invitation = state.invitation;
  if (!invitation) return showView('create');
  document.querySelector('#view-title').textContent = invitation.title;
  document.querySelector('#invitation-preview').innerHTML = `<div class="large-invite"><p class="eyebrow">You are invited</p><h2>${invitation.title}</h2><p class="invite-description">${invitation.description || 'Come celebrate with us.'}</p><div class="preview-rule"></div><p><strong>${localDate(invitation.starts_at)}</strong><br>RSVP by ${localDate(invitation.rsvp_deadline)}</p><button class="button button-primary" data-view="guest">Reply to invitation →</button></div>`;
}

document.querySelector('#create-form').addEventListener('submit', async (event) => {
  event.preventDefault(); const form = new FormData(event.currentTarget); const output = document.querySelector('#create-feedback'); const submit = event.currentTarget.querySelector('button[type="submit"]'); submit.disabled = true; feedback(output, 'Creating your invitation...');
  try { const invitation = await api('/v1/invitations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ owner_email: form.get('owner_email'), title: form.get('title'), description: form.get('description'), starts_at: asISO(form.get('starts_at')), rsvp_deadline: asISO(form.get('rsvp_deadline')), expires_at: asISO(form.get('expires_at')) }) }); saveInvitation(invitation); showView('manage'); } catch (error) { feedback(output, error.message, 'error'); } finally { submit.disabled = false; }
});

document.querySelector('#edit-form').addEventListener('submit', async (event) => {
  event.preventDefault(); const form = new FormData(event.currentTarget); const output = document.querySelector('#edit-feedback');
  try { const invitation = await api(`/v1/invitations/${state.invitation.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: form.get('title'), description: form.get('description'), starts_at: asISO(form.get('starts_at')), rsvp_deadline: asISO(form.get('rsvp_deadline')), expires_at: asISO(form.get('expires_at')), notify_guests: form.get('notify_guests') === 'on' }) }); saveInvitation(invitation.invitation); feedback(output, invitation.guest_notification_queued ? 'Saved and guests will be notified.' : 'Saved quietly. Guests were not notified.', 'success'); renderManage(); } catch (error) { feedback(output, error.message, 'error'); }
});

document.querySelector('#show-rsvps').addEventListener('click', () => showView('rsvps'));
async function loadResponses() { if (!state.invitation) return showView('create'); const list = document.querySelector('#response-list'); list.innerHTML = '<div class="loading">Loading replies...</div>'; try { const responses = await api(`/v1/invitations/${state.invitation.id}/responses`); const attending = responses.filter((item) => item.status === 'attending').length; document.querySelector('#response-summary').innerHTML = `<div><strong>${attending}</strong><span>Attending</span></div><div><strong>${responses.length}</strong><span>Total replies</span></div>`; list.innerHTML = responses.length ? responses.map((item) => `<article class="response-row"><div class="avatar">${item.guest_name[0].toUpperCase()}</div><div><h3>${item.guest_name}</h3><p>${item.guest_email}${item.note ? ` · ${item.note}` : ''}</p></div><span class="status status-${item.status}">${item.status.replace('_', ' ')}</span></article>`).join('') : '<div class="empty-state"><span>◌</span><h3>No replies yet.</h3><p>They will appear here as guests respond.</p></div>'; } catch (error) { list.innerHTML = `<div class="feedback error">${error.message}</div>`; } }

function guestLink(invitationId, responseToken = '') {
  const query = new URLSearchParams({ invitation: invitationId });
  if (responseToken) query.set('response', responseToken);
  return `${window.location.origin}${window.location.pathname}?${query}#guest`;
}

async function loadGuestInvitation() {
  if (!state.invitationId) {
    document.querySelector('#guest-heading').textContent = 'Your invitation.';
    document.querySelector('#guest-subheading').textContent = 'This link is missing its invitation details.';
    return;
  }
  try {
    const invitation = await api(`/v1/invitations/${encodeURIComponent(state.invitationId)}`);
    document.querySelector('#guest-invitation').classList.remove('hidden');
    document.querySelector('#guest-invitation').innerHTML = `<strong>${invitation.title}</strong><span>${localDate(invitation.starts_at)} · RSVP by ${localDate(invitation.rsvp_deadline)}</span>`;
    document.querySelector('#guest-heading').textContent = invitation.title;
    state.invitation = invitation;
    if (state.responseToken) {
      const response = await api(`/v1/invitations/${encodeURIComponent(state.invitationId)}/responses/${encodeURIComponent(state.responseToken)}`);
      state.response = response;
      const form = document.querySelector('#respond-form');
      form.elements.guest_name.value = response.guest_name;
      form.elements.guest_email.value = response.guest_email;
      form.elements.status.value = response.status;
      form.elements.note.value = response.note || '';
      document.querySelector('#respond-submit').innerHTML = 'Update my RSVP <span aria-hidden="true">→</span>';
      document.querySelector('#guest-subheading').textContent = 'Update your answer below. Your private edit link keeps the details out of the form.';
    }
  } catch (error) {
    document.querySelector('#guest-invitation').classList.remove('hidden');
    document.querySelector('#guest-invitation').innerHTML = '<strong>This invitation is no longer available.</strong><span>Ask the host to send you a new invitation link.</span>';
    document.querySelector('#respond-form').querySelectorAll('input, textarea, button').forEach((field) => { field.disabled = true; });
    feedback(document.querySelector('#respond-feedback'), 'This invitation link is no longer available. Ask the host to create or send a new link.', 'error');
  }
}

document.querySelector('#respond-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const output = document.querySelector('#respond-feedback');
  const submit = event.currentTarget.querySelector('button[type="submit"]');
  submit.disabled = true;
  feedback(output, state.responseToken ? 'Updating your RSVP...' : 'Sending your RSVP...');
  try {
    const path = `/v1/invitations/${encodeURIComponent(state.invitationId)}/responses`;
    const response = await api(state.responseToken ? `${path}/${encodeURIComponent(state.responseToken)}` : path, {
      method: state.responseToken ? 'PATCH' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ guest_name: form.get('guest_name'), guest_email: form.get('guest_email'), status: form.get('status'), note: form.get('note') || null }),
    });
    state.response = response;
    const wasEditing = Boolean(state.responseToken);
    state.responseToken = response.manage_token;
    feedback(output, wasEditing ? 'Your RSVP has been updated.' : 'Your RSVP has been received.', 'success');
    const editLink = document.querySelector('#guest-edit-link');
    editLink.classList.remove('hidden');
    editLink.innerHTML = `Need to change your answer later? <a href="${guestLink(state.invitationId, state.responseToken)}">Open your private edit link →</a>`;
    history.replaceState(null, '', guestLink(state.invitationId, state.responseToken).replace(window.location.origin + window.location.pathname, ''));
  } catch (error) { feedback(output, error.message, 'error'); } finally { submit.disabled = false; }
});

const initialView = window.location.hash.slice(1) || (state.invitationId ? 'guest' : 'dashboard');
showView(['dashboard', 'create', 'manage', 'rsvps', 'guest', 'view'].includes(initialView) ? initialView : 'dashboard');
