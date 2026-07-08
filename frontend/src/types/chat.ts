/**
 * Chat Types for Inner Garden
 *
 * Based on backend database schema for conversations, messages, and message_sources.
 * These types will be used when the backend chat API is implemented.
 */

/**
 * Conversation mode: companion for AI companion chat, past_self for chatting with past self
 */
export type ConversationMode = 'companion' | 'past_self';

/**
 * Message role: user or assistant
 */
export type MessageRole = 'user' | 'assistant';

/**
 * Message status: pending, completed, or failed
 */
export type MessageStatus = 'pending' | 'completed' | 'failed';

/**
 * Source type: anchor for the diary being discussed, retrieved for related diaries
 */
export type SourceType = 'anchor' | 'retrieved';

/**
 * Conversation entity
 */
export interface Conversation {
  id: number;
  user_id: number;
  mode: ConversationMode;
  title: string;
  anchor_diary_id: number | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

/**
 * Message entity
 */
export interface Message {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  retrieval_used: boolean;
  model_name: string | null;
  latency_ms: number | null;
  token_usage_input: number | null;
  token_usage_output: number | null;
  error_code: string | null;
  created_at: string;
  sources?: MessageSource[];
}

/**
 * Message Source entity - snapshot of diary at message creation time
 */
export interface MessageSource {
  id: number;
  message_id: number;
  diary_id: number | null;
  source_type: SourceType;
  diary_date_snapshot: string | null;
  title_snapshot: string;
  excerpt_snapshot: string;
  emotion_label_snapshot: string | null;
  relevance_score: number;
  rank: number;
  created_at: string;
}

/**
 * Request payload for creating a conversation
 */
export interface CreateConversationRequest {
  mode: ConversationMode;
  title: string;
  anchor_diary_id?: number;
}

/**
 * Request payload for creating a message
 */
export interface CreateMessageRequest {
  conversation_id: number;
  content: string;
}

/**
 * Response from POST /api/v1/chat/messages
 */
export interface CreateMessageResponse {
  message: Message;
  conversation: Conversation;
}

/**
 * Response from GET /api/v1/chat/conversations
 */
export interface ListConversationsResponse {
  data: Conversation[];
}

/**
 * Response from GET /api/v1/chat/conversations/{id}
 */
export interface GetConversationResponse {
  data: Conversation;
}

/**
 * Response from GET /api/v1/chat/conversations/{id}/messages
 */
export interface ListMessagesResponse {
  data: Message[];
}

/**
 * Response from POST /api/v1/chat/conversations
 */
export interface CreateConversationResponse {
  data: Conversation;
}
