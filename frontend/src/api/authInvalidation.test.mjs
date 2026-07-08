import assert from 'node:assert/strict';

class LocalStorageMock {
  constructor() {
    this.store = new Map();
  }

  getItem(key) {
    return this.store.has(key) ? this.store.get(key) : null;
  }

  setItem(key, value) {
    this.store.set(key, String(value));
  }

  removeItem(key) {
    this.store.delete(key);
  }
}

const events = [];

global.Event = class Event {
  constructor(type) {
    this.type = type;
  }
};

global.window = {
  localStorage: new LocalStorageMock(),
  location: { hash: '#/memory-garden' },
  dispatchEvent(event) {
    events.push(event.type);
  },
};

global.fetch = async (_url, options) => {
  assert.equal(options.headers.Authorization, 'Bearer stale-token');
  return {
    ok: false,
    status: 401,
    async json() {
      return { detail: 'Inactive or missing user' };
    },
  };
};

window.localStorage.setItem('innergarden_access_token', 'stale-token');
window.localStorage.setItem('innergarden_user', JSON.stringify({ email: 'old@example.com' }));

const { apiRequest } = await import('./client.js');

await assert.rejects(
  apiRequest('/memories'),
  /Inactive or missing user/,
);

assert.equal(window.localStorage.getItem('innergarden_access_token'), null);
assert.equal(window.localStorage.getItem('innergarden_user'), null);
assert.equal(window.localStorage.getItem('innergarden_redirect_after_login'), '#/memory-garden');
assert.equal(window.location.hash, '#/login');
assert.deepEqual(events, ['auth-change']);

console.log('auth invalidation ok');
