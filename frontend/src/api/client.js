import { getStoredToken, isAuthenticated } from './auth.js';

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

/**
 * 健康检查
 */
export async function healthCheck() {
  return apiRequest('/health');
}

/**
 * 创建日记条目
 * 需要用户已登录
 */
export async function createEntry(rawContent) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/entries', {
    method: 'POST',
    body: JSON.stringify({
      raw_content: rawContent,
      input_type: 'text',
      source_language: 'zh-CN',
    }),
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

// Chat API functions
// 这些函数将在后端 Chat API 实现后可用

/**
 * 创建新对话
 * POST /api/v1/chat/conversations
 */
export async function createConversation({ mode, title, anchor_diary_id }) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/chat/conversations', {
    method: 'POST',
    body: JSON.stringify({ mode, title, anchor_diary_id }),
  });
}

/**
 * 获取对话列表
 * GET /api/v1/chat/conversations
 */
export async function listConversations() {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/chat/conversations');
}

/**
 * 获取单个对话
 * GET /api/v1/chat/conversations/{id}
 */
export async function getConversation(conversationId) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/chat/conversations/${conversationId}`);
}

/**
 * 获取对话消息列表
 * GET /api/v1/chat/conversations/{id}/messages
 */
export async function listMessages(conversationId) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/chat/conversations/${conversationId}/messages`);
}

/**
 * 发送消息
 * POST /api/v1/chat/messages
 */
export async function sendMessage({ conversation_id, content }) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest('/chat/messages', {
    method: 'POST',
    body: JSON.stringify({ conversation_id, content }),
  });
}

/**
 * 删除对话
 * DELETE /api/v1/chat/conversations/{id}
 */
export async function deleteConversation(conversationId) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`/chat/conversations/${conversationId}`, {
    method: 'DELETE',
  });
}
