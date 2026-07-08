/**
 * Chat API Client for Inner Garden
 *
 * This module provides functions to interact with the chat API endpoints.
 * These endpoints will be available once the backend chat API is implemented.
 *
 * Note: These functions are prepared for future backend integration.
 * Currently, they will fail with 404 until the backend API is implemented.
 */

import type {
  CreateConversationRequest,
  CreateConversationResponse,
  CreateMessageRequest,
  CreateMessageResponse,
  ListConversationsResponse,
  ListMessagesResponse,
  GetConversationResponse,
  Conversation,
  Message,
} from '../types/chat';

const API_BASE = '/api/v1';

/**
 * Get stored auth token
 */
function getStoredToken(): string | null {
  return window.localStorage.getItem('innergarden_demo_access_token');
}

/**
 * Make authenticated API request
 */
async function apiRequest(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getStoredToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers as HeadersInit || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
}

/**
 * Parse API response
 */
async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || payload.error?.message || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

/**
 * Create a new conversation
 *
 * POST /api/v1/chat/conversations
 */
export async function createConversation(
  request: CreateConversationRequest
): Promise<CreateConversationResponse> {
  const response = await apiRequest('/chat/conversations', {
    method: 'POST',
    body: JSON.stringify(request),
  });
  return parseResponse<CreateConversationResponse>(response);
}

/**
 * List all conversations for the current user
 *
 * GET /api/v1/chat/conversations
 */
export async function listConversations(): Promise<ListConversationsResponse> {
  const response = await apiRequest('/chat/conversations', {
    method: 'GET',
  });
  return parseResponse<ListConversationsResponse>(response);
}

/**
 * Get a specific conversation by ID
 *
 * GET /api/v1/chat/conversations/{id}
 */
export async function getConversation(conversationId: number): Promise<GetConversationResponse> {
  const response = await apiRequest(`/chat/conversations/${conversationId}`, {
    method: 'GET',
  });
  return parseResponse<GetConversationResponse>(response);
}

/**
 * List messages in a conversation
 *
 * GET /api/v1/chat/conversations/{id}/messages
 */
export async function listMessages(conversationId: number): Promise<ListMessagesResponse> {
  const response = await apiRequest(`/chat/conversations/${conversationId}/messages`, {
    method: 'GET',
  });
  return parseResponse<ListMessagesResponse>(response);
}

/**
 * Send a message in a conversation
 *
 * POST /api/v1/chat/messages
 */
export async function sendMessage(
  request: CreateMessageRequest
): Promise<CreateMessageResponse> {
  const response = await apiRequest('/chat/messages', {
    method: 'POST',
    body: JSON.stringify(request),
  });
  return parseResponse<CreateMessageResponse>(response);
}

/**
 * Delete a conversation
 *
 * DELETE /api/v1/chat/conversations/{id}
 */
export async function deleteConversation(conversationId: number): Promise<void> {
  const response = await apiRequest(`/chat/conversations/${conversationId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || payload.error?.message || `Delete failed: ${response.status}`);
  }
}
