/**
 * Chat API types for Inner Garden.
 *
 * Source of truth:
 * - backend/app/schemas/chat.py
 * - FastAPI /openapi.json
 * - docs/contracts/chat-api-v1.md
 */

export type ConversationMode = 'companion' | 'past_self';
export type MessageRole = 'user' | 'assistant';
export type SourceType = 'anchor' | 'retrieved';
export type SafetyLevel = 'none' | 'low' | 'medium' | 'high';
export type SafetyCategory = 'emotional_distress' | 'self_harm_risk' | 'violence_risk' | null;
export type SafetyAction = 'none' | 'show_notice' | 'suggest_support' | 'trigger_emergency_flow';

export interface ApiResponse<T> {
  success: true;
  data: T;
  message: string;
  request_id: string;
}

export interface ApiErrorResponse {
  success: false;
  data: unknown;
  message: string;
  request_id: string;
  error_code: string;
  details?: Record<string, unknown> | null;
  error?: {
    code: string;
    message: string;
    details: Record<string, unknown> | null;
  };
}

export interface ChatRequest {
  conversation_id?: number | null;
  mode?: ConversationMode | null;
  content: string;
  use_memory?: boolean;
  anchor_diary_id?: number | null;
}

export interface ConversationCreate {
  mode: ConversationMode;
  title?: string | null;
  anchor_diary_id?: number | null;
}

export interface ConversationRead {
  id: number;
  mode: ConversationMode;
  title: string | null;
  anchor_diary_id: number | null;
  started_at: string;
  updated_at: string;
  message_count: number;
}

export interface MessageRead {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface MessageSource {
  diary_id: number;
  diary_date: string;
  title: string;
  excerpt: string;
  emotion_label: string;
  relevance_score: number;
  source_type: SourceType;
}

export interface MessageSourceRead {
  id: number;
  diary_id: number | null;
  source_type: SourceType;
  diary_date_snapshot: string | null;
  title_snapshot: string;
  excerpt_snapshot: string;
  emotion_label_snapshot: string | null;
  relevance_score: number;
  rank: number;
}

export interface RetrievalMetadata {
  used: boolean;
  strategy: string;
  total_found: number;
  used_in_context: number;
}

export interface SafetyCheck {
  flagged: boolean;
  level: SafetyLevel;
  category: SafetyCategory;
  action: SafetyAction;
}

export interface ChatResponse {
  conversation: ConversationRead;
  user_message: MessageRead;
  assistant_message: MessageRead;
  retrieval: RetrievalMetadata;
  sources: MessageSource[];
  safety: SafetyCheck;
}

export interface ConversationListResponse {
  conversations: ConversationRead[];
  page: number;
  page_size: number;
  total: number;
}

export interface ConversationDetailResponse {
  conversation: ConversationRead;
}

export interface ChatHistoryItem {
  message: MessageRead;
  sources: MessageSourceRead[];
}

export interface MessageListResponse {
  messages: ChatHistoryItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface DeleteConversationResponse {
  deleted_conversation_id: number;
}

export type Conversation = ConversationRead;
export type Message = MessageRead;
export type CreateMessageRequest = ChatRequest;
export type CreateMessageResponse = ApiResponse<ChatResponse>;
export type CreateConversationRequest = ConversationCreate;
export type CreateConversationResponse = ApiResponse<ConversationDetailResponse>;
export type ListConversationsResponse = ApiResponse<ConversationListResponse>;
export type GetConversationResponse = ApiResponse<ConversationDetailResponse>;
export type ListMessagesResponse = ApiResponse<MessageListResponse>;
