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

global.Event = class Event {
  constructor(type) {
    this.type = type;
  }
};

global.window = {
  localStorage: new LocalStorageMock(),
  location: { hash: '#/login' },
  dispatchEvent() {},
};

const { login, register } = await import('./auth.js');

global.fetch = async () => ({
  ok: false,
  status: 500,
  async text() {
    return '';
  },
});

await assert.rejects(
  login('user@example.com', 'password123'),
  /登录失败，请确认后端服务已启动并稍后重试/,
);

await assert.rejects(
  register('user', 'user@example.com', 'password123'),
  /注册失败，请确认后端服务已启动并稍后重试/,
);

global.fetch = async () => ({
  ok: true,
  status: 200,
  async text() {
    return '<html>not json</html>';
  },
});

await assert.rejects(
  login('user@example.com', 'password123'),
  /服务器返回了无法解析的数据，请稍后重试/,
);

console.log('auth empty response handling ok');
