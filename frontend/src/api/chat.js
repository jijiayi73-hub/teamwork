/**
 * Chat API client for RAG-based conversation feature.
 *
 * All functions follow the API contract defined in:
 * docs/contracts/chat-api-v1.md
 *
 * @module chat
 */

import { apiRequest } from './client.js';

// ============================================================================
// API Functions
// ============================================================================

/**
 * Send message and get AI response.
 *
 * @param {Object} request - Chat request
 * @param {number|null} request.conversation_id - Conversation ID (null for new conversation)
 * @param {'companion'|'past_self'|null} request.mode - Conversation mode (required for new conversation)
 * @param {string} request.content - User message content (1-5000 chars)
 * @param {boolean} [request.use_memory=false] - Whether to retrieve historical context
 * @param {number|null} [request.anchor_diary_id] - Anchor diary ID (required for past_self)
 * @returns {Promise<ChatApiResponse>} Response with conversation, messages, sources, and safety info
 *
 * @example
 * // New companion conversation
 * const response = await sendChatMessage({
 *   conversation_id: null,
 *   mode: 'companion',
 *   content: '今天感觉很累',
 *   use_memory: false
 * });
 *
 * @example
 * // Continue conversation
 * const response = await sendChatMessage({
 *   conversation_id: 5,
 *   content: '后来怎么样了？',
 *   use_memory: true
 * });
 */
export async function sendChatMessage(request) {
  return apiRequest('/chat/messages', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * List user's conversations.
 *
 * @param {Object} [params] - Query parameters
 * @param {number} [params.page=1] - Page number (1-indexed)
 * @param {number} [params.page_size=20] - Items per page (1-100)
 * @param {'companion'|'past_self'} [params.mode] - Optional mode filter
 * @returns {Promise<ConversationListApiResponse>} Response with conversations and pagination
 */
export async function listConversations(params = {}) {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.set('page', params.page);
  if (params.page_size) queryParams.set('page_size', params.page_size);
  if (params.mode) queryParams.set('mode', params.mode);

  const queryString = queryParams.toString();
  const path = `/chat/conversations${queryString ? `?${queryString}` : ''}`;

  return apiRequest(path);
}

/**
 * Create new conversation.
 *
 * @param {Object} request - Conversation create request
 * @param {'companion'|'past_self'} request.mode - Conversation mode
 * @param {string|null} [request.title] - Optional conversation title
 * @param {number|null} [request.anchor_diary_id] - Anchor diary ID (required for past_self)
 * @returns {Promise<ConversationDetailApiResponse>} Response with created conversation
 */
export async function createConversation(request) {
  return apiRequest('/chat/conversations', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get conversation metadata by ID.
 *
 * @param {number} conversationId - Conversation ID
 * @returns {Promise<ConversationDetailApiResponse>} Response with conversation metadata
 */
export async function getConversation(conversationId) {
  return apiRequest(`/chat/conversations/${conversationId}`);
}

/**
 * Get messages for a conversation (paginated).
 *
 * @param {number} conversationId - Conversation ID
 * @param {Object} [params] - Query parameters
 * @param {number} [params.page=1] - Page number (1-indexed)
 * @param {number} [params.page_size=50] - Items per page (1-100)
 * @returns {Promise<MessageListApiResponse>} Response with messages and sources
 */
export async function getMessages(conversationId, params = {}) {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.set('page', params.page);
  if (params.page_size) queryParams.set('page_size', params.page_size);

  const queryString = queryParams.toString();
  const path = `/chat/conversations/${conversationId}/messages${queryString ? `?${queryString}` : ''}`;

  return apiRequest(path);
}

/**
 * Delete conversation (soft delete).
 *
 * @param {number} conversationId - Conversation ID
 * @returns {Promise<DeleteApiResponse>} Response with deleted conversation ID
 */
export async function deleteConversation(conversationId) {
  return apiRequest(`/chat/conversations/${conversationId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Type Definitions (JSDoc for IDE support)
// ============================================================================

/**
 * @typedef {Object} MessageSource
 * @property {number} diary_id - Diary ID
 * @property {string} diary_date - Diary date (ISO 8601)
 * @property {string} title - Diary title
 * @property {string} excerpt - Content excerpt (first 100 chars)
 * @property {string} emotion_label - Primary emotion
 * @property {number} relevance_score - Relevance score (0.0 to 1.0)
 * @property {'anchor'|'retrieved'} source_type - Source type
 */

/**
 * @typedef {Object} RetrievalMetadata
 * @property {boolean} used - Whether retrieval was attempted
 * @property {string} strategy - Strategy name used
 * @property {number} total_found - Total matching diaries found
 * @property {number} used_in_context - How many were sent to AI
 */

/**
 * @typedef {Object} SafetyCheck
 * @property {boolean} flagged - Whether content was flagged
 * @property {'none'|'low'|'medium'|'high'} level - Safety level
 * @property {'emotional_distress'|'self_harm_risk'|'violence_risk'|null} category - Risk category
 * @property {'none'|'show_notice'|'suggest_support'|'trigger_emergency_flow'} action - Action to take
 */

/**
 * @typedef {Object} ChatMessage
 * @property {number} id - Message ID
 * @property {number} conversation_id - Conversation ID
 * @property {'user'|'assistant'} role - Message role
 * @property {string} content - Message content
 * @property {string} created_at - Creation time (ISO 8601)
 */

/**
 * @typedef {Object} ChatConversation
 * @property {number} id - Conversation ID
 * @property {'companion'|'past_self'} mode - Conversation mode
 * @property {string|null} title - Conversation title
 * @property {number|null} anchor_diary_id - Anchor diary ID
 * @property {string} started_at - Start time (ISO 8601)
 * @property {string} updated_at - Last update time (ISO 8601)
 * @property {number} message_count - Total messages in conversation
 */

/**
 * @typedef {Object} ChatResponse
 * @property {ChatConversation} conversation - Conversation metadata
 * @property {ChatMessage} user_message - User's message
 * @property {ChatMessage} assistant_message - AI's response
 * @property {RetrievalMetadata} retrieval - Retrieval metadata
 * @property {MessageSource[]} sources - Source diaries
 * @property {SafetyCheck} safety - Safety check result
 */

/**
 * @typedef {Object} ChatApiResponse
 * @property {boolean} success - Success status
 * @property {ChatResponse} data - Response data
 * @property {string} message - Response message
 * @property {string} request_id - Request ID
 */

/**
 * @typedef {Object} ConversationListResponse
 * @property {ChatConversation[]} conversations - List of conversations
 * @property {number} page - Current page number
 * @property {number} page_size - Items per page
 * @property {number} total - Total conversations
 */

/**
 * @typedef {Object} ConversationListApiResponse
 * @property {boolean} success - Success status
 * @property {ConversationListResponse} data - Response data
 * @property {string} message - Response message
 * @property {string} request_id - Request ID
 */

/**
 * @typedef {Object} ConversationDetailResponse
 * @property {ChatConversation} conversation - Conversation metadata
 */

/**
 * @typedef {Object} ConversationDetailApiResponse
 * @property {boolean} success - Success status
 * @property {ConversationDetailResponse} data - Response data
 * @property {string} message - Response message
 * @property {string} request_id - Request ID
 */

/**
 * @typedef {Object} DeleteConversationResponse
 * @property {number} deleted_conversation_id - Deleted conversation ID
 */

/**
 * @typedef {Object} DeleteApiResponse
 * @property {boolean} success - Success status
 * @property {DeleteConversationResponse} data - Response data
 * @property {string} message - Response message
 * @property {string} request_id - Request ID
 */

/**
 * @typedef {Object} MessageListResponse
 * @property {Array} messages - List of message items with sources
 * @property {number} page - Current page number
 * @property {number} page_size - Items per page
 * @property {number} total - Total messages
 */

/**
 * @typedef {Object} MessageListApiResponse
 * @property {boolean} success - Success status
 * @property {MessageListResponse} data - Response data
 * @property {string} message - Response message
 * @property {string} request_id - Request ID
 */
