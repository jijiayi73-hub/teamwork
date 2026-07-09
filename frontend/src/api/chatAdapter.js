/**
 * Convert backend Chat API responses into the shape used by chat UI state.
 *
 * Source of truth: docs/contracts/chat-api-v1.md
 */

export function mapChatResponse(apiResponse) {
  const data = apiResponse?.data ?? apiResponse;

  if (!data?.conversation || !data?.user_message || !data?.assistant_message) {
    throw new Error('Invalid ChatResponse payload');
  }

  return {
    conversationId: data.conversation.id,
    conversation: data.conversation,
    userMessage: data.user_message,
    assistantMessage: data.assistant_message,
    sources: data.sources ?? [],
    safety: data.safety ?? null,
    retrieval: data.retrieval ?? null,
  };
}
