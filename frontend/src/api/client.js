import { getStoredToken, invalidateSession, isAuthenticated } from './auth.js';

const API_BASE = '/api/v1';

// 认证相关函数已迁移到 auth.js 模块
export { getStoredToken, isAuthenticated } from './auth.js';
export { getStoredUser } from './auth.js';

/**
 * 基础 API 请求函数
 * @param {string} path - API 路径
 * @param {object} options - fetch 选项
 * @returns {Promise<object>}
 */
export async function apiRequest(path, options = {}) {
  const token = getStoredToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      invalidateSession();
    }
    // 处理错误消息，避免 [object Object]
    let errorMessage = `Request failed: ${response.status}`;
    if (payload.detail) {
      errorMessage = typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail);
    } else if (payload.error?.message) {
      errorMessage = payload.error.message;
    } else if (payload.error) {
      errorMessage = typeof payload.error === 'string' ? payload.error : JSON.stringify(payload.error);
    }
    throw new Error(errorMessage);
  }

  return payload;
}

function extractErrorMessage(payload, fallback) {
  if (payload?.detail) {
    if (typeof payload.detail === 'string') return payload.detail;
    return JSON.stringify(payload.detail);
  }
  if (payload?.message) return payload.message;
  if (payload?.error?.message) return payload.error.message;
  if (payload?.error) {
    if (typeof payload.error === 'string') return payload.error;
    return JSON.stringify(payload.error);
  }
  if (payload?.details?.fields?.length) {
    return payload.details.fields.map((field) => `${field.field}: ${field.message}`).join('; ');
  }
  return fallback;
}

export async function uploadImage(file) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  const dataUrl = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('图片读取失败'));
    reader.readAsDataURL(file);
  });
  return apiRequest('/uploads/images', {
    method: 'POST',
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type,
      data_url: dataUrl,
    }),
  });
}

export async function generateImage(payload) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/images/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * 健康检查
 */
export async function healthCheck() {
  return apiRequest('/health');
}

/**
 * 创建日记条目
 * 需要用户已登录
 * @param {string} rawContent - 原始内容
 * @param {number} conversationId - 可选的对话 ID，用于获取对话上下文进行情绪分析
 */
export async function createEntry(rawContent, conversationId = null) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  const body = {
    raw_content: rawContent,
    input_type: 'text',
    source_language: 'zh-CN',
  };
  if (conversationId) {
    body.conversation_id = conversationId;
  }
  return apiRequest('/entries', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * 创建日记
 * 需要用户已登录
 */
export async function createDiary(diary) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/diaries', {
    method: 'POST',
    body: JSON.stringify(diary),
  });
}

/**
 * 获取日记列表
 * 需要用户已登录
 */
export async function listDiaries() {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/diaries');
}

/**
 * 获取单个日记
 * 需要用户已登录
 */
export async function getDiary(diaryId) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/diaries/${diaryId}`);
}

/**
 * 获取统计概览
 * 需要用户已登录
 */
export async function getStatsOverview() {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/stats/overview');
}

export async function createMemory(memory) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/memories', {
    method: 'POST',
    body: JSON.stringify(memory),
  });
}

export async function listMemories(filters = {}) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  const params = new URLSearchParams();
  if (filters.emotion) params.set('emotion', filters.emotion);
  if (filters.keyword) params.set('keyword', filters.keyword);
  return apiRequest(`/memories${params.toString() ? `?${params.toString()}` : ''}`);
}

export async function getMemory(memoryId) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/memories/${memoryId}`);
}

export async function deleteMemory(memoryId) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/memories/${memoryId}`, { method: 'DELETE' });
}

export async function pastSelfChat(memoryId, payload) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/memories/${memoryId}/past-self-chat`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ============================================================================
// Admin API Functions
// ============================================================================

export async function listUsers() {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/admin/users');
}

export async function getUser(userId) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/admin/users/${userId}`);
}

export async function updateUser(userId, data) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/admin/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteUser(userId) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/admin/users/${userId}`, { method: 'DELETE' });
}

export async function getLogEntries(filters = {}) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  const params = new URLSearchParams();
  if (filters.level) params.set('level', filters.level);
  if (filters.limit) params.set('limit', filters.limit);
  return apiRequest(`/logs/entries${params.toString() ? `?${params}` : ''}`);
}

export async function getLogStats() {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/logs/stats');
}

export async function clearLogs() {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/logs/clear', { method: 'POST' });
}

export async function getAdminStats() {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/admin/stats/charts');
}

/**
 * 请求密码重置邮件
 * @param {string} email - 用户邮箱
 */
export async function requestPasswordReset(email) {
  return apiRequest('/auth/password-reset/request', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

/**
 * 验证密码重置 token
 * @param {string} token - 重置 token
 */
export async function verifyResetToken(token) {
  return apiRequest('/auth/password-reset/verify', {
    method: 'POST',
    body: JSON.stringify({ token }),
  });
}

/**
 * 确认密码重置并设置新密码
 * @param {string} token - 重置 token
 * @param {string} newPassword - 新密码
 */
export async function confirmPasswordReset(token, newPassword) {
  return apiRequest('/auth/password-reset/confirm', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

// Chat API functions are exported from './chat.js'
// Use: import { sendChatMessage, listConversations, ... } from './chat.js';
