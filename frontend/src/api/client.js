const API_BASE = '/api/v1';
const TOKEN_KEY = 'innergarden_demo_access_token';
const USER_KEY = 'innergarden_demo_user';

const DEMO_USER = {
  username: 'demo',
  email: 'demo@innergarden.local',
  password: 'innergarden-demo',
  role: 'user',
};

export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const value = window.localStorage.getItem(USER_KEY);
  if (!value) return null;

  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

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
    throw new Error(payload.detail || payload.error?.message || `Request failed: ${response.status}`);
  }

  return payload;
}

async function storeSession(payload) {
  const data = payload.data;
  window.localStorage.setItem(TOKEN_KEY, data.access_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  return data;
}

export async function ensureDemoSession() {
  const token = getStoredToken();
  if (token) {
    try {
      const current = await apiRequest('/auth/me');
      return { access_token: token, user: current.data };
    } catch {
      window.localStorage.removeItem(TOKEN_KEY);
      window.localStorage.removeItem(USER_KEY);
    }
  }

  try {
    const login = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: DEMO_USER.email, password: DEMO_USER.password }),
    });
    return storeSession(login);
  } catch {
    const register = await apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(DEMO_USER),
    });
    return storeSession(register);
  }
}

export async function healthCheck() {
  return apiRequest('/health');
}

export async function createEntry(rawContent) {
  await ensureDemoSession();
  return apiRequest('/entries', {
    method: 'POST',
    body: JSON.stringify({
      raw_content: rawContent,
      input_type: 'text',
      source_language: 'zh-CN',
    }),
  });
}

export async function createDiary(diary) {
  await ensureDemoSession();
  return apiRequest('/diaries', {
    method: 'POST',
    body: JSON.stringify(diary),
  });
}

export async function listDiaries() {
  await ensureDemoSession();
  return apiRequest('/diaries');
}

export async function getDiary(diaryId) {
  await ensureDemoSession();
  return apiRequest(`/diaries/${diaryId}`);
}

export async function getStatsOverview() {
  await ensureDemoSession();
  return apiRequest('/stats/overview');
}

// Chat API functions (for future backend integration)
// These will work once the backend chat API is implemented

/**
 * Create a new conversation
 * POST /api/v1/chat/conversations
 */
export async function createConversation({ mode, title, anchor_diary_id }) {
  await ensureDemoSession();
  return apiRequest('/chat/conversations', {
    method: 'POST',
    body: JSON.stringify({ mode, title, anchor_diary_id }),
  });
}

/**
 * List all conversations for current user
 * GET /api/v1/chat/conversations
 */
export async function listConversations() {
  await ensureDemoSession();
  return apiRequest('/chat/conversations');
}

/**
 * Get a specific conversation by ID
 * GET /api/v1/chat/conversations/{id}
 */
export async function getConversation(conversationId) {
  await ensureDemoSession();
  return apiRequest(`/chat/conversations/${conversationId}`);
}

/**
 * List messages in a conversation
 * GET /api/v1/chat/conversations/{id}/messages
 */
export async function listMessages(conversationId) {
  await ensureDemoSession();
  return apiRequest(`/chat/conversations/${conversationId}/messages`);
}

/**
 * Send a message in a conversation
 * POST /api/v1/chat/messages
 */
export async function sendMessage({ conversation_id, content }) {
  await ensureDemoSession();
  return apiRequest('/chat/messages', {
    method: 'POST',
    body: JSON.stringify({ conversation_id, content }),
  });
}

/**
 * Delete a conversation
 * DELETE /api/v1/chat/conversations/{id}
 */
export async function deleteConversation(conversationId) {
  await ensureDemoSession();
  return apiRequest(`/chat/conversations/${conversationId}`, {
    method: 'DELETE',
  });
}
