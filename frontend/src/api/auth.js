/**
 * 认证业务层模块
 *
 * 提供用户注册、登录、登出等认证相关业务函数。
 * 本模块设计为后期可替换的最小实现。
 */

const TOKEN_KEY = 'innergarden_access_token';
const USER_KEY = 'innergarden_user';
const REDIRECT_KEY = 'innergarden_redirect_after_login';

function formatAuthError(payload, fallback) {
  if (payload?.detail) {
    return typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail);
  }
  if (payload?.message) return payload.message;
  if (payload?.error?.message) return payload.error.message;
  if (payload?.details?.fields?.length) {
    return payload.details.fields.map((field) => `${field.field}: ${field.message}`).join('; ');
  }
  return fallback;
}

/**
 * 从 localStorage 获取存储的 token
 */
export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

/**
 * 从 localStorage 获取存储的用户信息
 */
export function getStoredUser() {
  const value = window.localStorage.getItem(USER_KEY);
  if (!value) return null;

  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

/**
 * 保存认证会话到 localStorage
 */
function saveSession(data) {
  if (!data?.access_token || !data?.user) {
    throw new Error('服务器返回的登录数据不完整，请稍后重试');
  }
  const { access_token, user } = data;
  window.localStorage.setItem(TOKEN_KEY, access_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  // 触发认证状态变化事件，让 App 组件更新
  window.dispatchEvent(new Event('auth-change'));
  return { access_token, user };
}

/**
 * 清除本地认证会话
 */
export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  // 触发认证状态变化事件，让 App 组件更新
  window.dispatchEvent(new Event('auth-change'));
}

export function invalidateSession({ redirect = true } = {}) {
  const currentHash = window.location.hash || '#/';
  clearSession();
  if (redirect && !currentHash.startsWith('#/login')) {
    saveRedirectPath(currentHash);
    window.location.hash = '#/login';
  }
}

/**
 * 检查当前是否已认证
 */
export function isAuthenticated() {
  return !!getStoredToken();
}

/**
 * 获取当前登录用户
 */
export function getCurrentUser() {
  return getStoredUser();
}

/**
 * 用户登录
 * @param {string} usernameOrEmail - 用户名或邮箱
 * @param {string} password - 用户密码
 * @returns {Promise<{access_token: string, user: object}>}
 */
export async function login(usernameOrEmail, password) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username_or_email: usernameOrEmail, password }),
  });

  const payload = await readJsonResponse(response, fallback);

  if (!response.ok) {
    // 隐藏技术细节，统一返回简体中文错误信息
    throw new Error('用户名、邮箱或密码错误');
  }

  return saveSession(payload.data);
}

/**
 * 用户注册
 * @param {string} username - 用户名
 * @param {string} email - 用户邮箱
 * @param {string} password - 用户密码
 * @returns {Promise<{access_token: string, user: object}>}
 */
export async function register(username, email, password) {
  const fallback = '注册失败，请确认后端服务已启动并稍后重试';
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  });

  const payload = await readJsonResponse(response, fallback);

  if (!response.ok) {
    // 隐藏技术细节，统一返回简体中文错误信息
    throw new Error('注册失败，用户名或邮箱可能已被使用');
  }

  return saveSession(payload.data);
}

/**
 * 用户登出
 */
export function logout() {
  clearSession();
  // 登出后跳转到首页
  window.location.hash = '#/';
}

/**
 * 保存登录后的重定向路径
 */
export function saveRedirectPath(path) {
  window.localStorage.setItem(REDIRECT_KEY, path);
}

/**
 * 获取并清除保存的重定向路径
 */
export function consumeRedirectPath() {
  const path = window.localStorage.getItem(REDIRECT_KEY);
  window.localStorage.removeItem(REDIRECT_KEY);
  return path || '#/'; // 默认返回首页
}

/**
 * 检查认证状态，未认证则跳转到登录页
 * @returns {boolean} - 是否已认证
 */
export function requireAuth() {
  if (!isAuthenticated()) {
    // 保存当前路径以便登录后返回
    saveRedirectPath(window.location.hash || '#/');
    // 跳转到登录页
    window.location.hash = '#/login';
    return false;
  }
  return true;
}
