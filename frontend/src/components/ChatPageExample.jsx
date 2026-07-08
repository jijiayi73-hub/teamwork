/**
 * ChatPage Example Component
 *
 * This is a reference implementation showing how to use the new chat API
 * once the backend chat endpoints are implemented.
 *
 * Current status: BACKEND API NOT YET IMPLEMENTED
 * This component will not work until the backend chat API is available.
 *
 * To use: Replace the current ChatPage in App.jsx with this component
 * once the backend API is ready.
 */

import React, { useEffect, useState } from 'react';
import {
  createConversation,
  listConversations,
  sendMessage,
  listMessages,
  deleteConversation,
} from '../api/client';

/**
 * ChatPage with conversation history and message sources support
 */
export function ChatPageExample() {
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [status, setStatus] = useState('Chat API 尚未实现 - 这是参考实现');

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  async function loadConversations() {
    try {
      const response = await listConversations();
      setConversations(response.data || []);
      setStatus(`加载了 ${response.data?.length || 0} 个对话`);
    } catch (error) {
      setStatus(`加载对话列表失败: ${error.message}`);
    }
  }

  async function handleNewConversation(mode = 'companion', anchorDiaryId = null) {
    try {
      const response = await createConversation({
        mode,
        title: mode === 'companion' ? 'AI Companion 对话' : '与过去的自己对话',
        anchor_diary_id: anchorDiaryId,
      });
      const newConversation = response.data;
      setConversations((prev) => [newConversation, ...prev]);
      setCurrentConversation(newConversation);
      setMessages([]);
      setStatus('创建新对话成功');
    } catch (error) {
      setStatus(`创建对话失败: ${error.message}`);
    }
  }

  async function selectConversation(conversation) {
    setCurrentConversation(conversation);
    try {
      const response = await listMessages(conversation.id);
      setMessages(response.data || []);
      setStatus(`加载了 ${response.data?.length || 0} 条消息`);
    } catch (error) {
      setStatus(`加载消息失败: ${error.message}`);
    }
  }

  async function handleSend() {
    const content = text.trim();
    if (!content || !currentConversation || isSending) return;

    setIsSending(true);
    setText('');
    setStatus('发送中...');

    try {
      const response = await sendMessage({
        conversation_id: currentConversation.id,
        content,
      });

      const newMessage = response.data.message;
      setMessages((prev) => [...prev, newMessage]);
      setStatus('消息发送成功');

      // If there are sources, show them
      if (newMessage.sources && newMessage.sources.length > 0) {
        setStatus(`消息已发送，引用了 ${newMessage.sources.length} 条日记`);
      }
    } catch (error) {
      setStatus(`发送失败: ${error.message}`);
    } finally {
      setIsSending(false);
    }
  }

  async function handleDeleteConversation(conversationId) {
    try {
      await deleteConversation(conversationId);
      setConversations((prev) => prev.filter((c) => c.id !== conversationId));
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(null);
        setMessages([]);
      }
      setStatus('对话已删除');
    } catch (error) {
      setStatus(`删除失败: ${error.message}`);
    }
  }

  return (
    <section className="relative z-10 flex min-h-[calc(100vh-96px)] items-center justify-center px-5 pb-12 pt-4 lg:px-14">
      <div className="w-full max-w-6xl">
        <div className="mb-6 text-center">
          <p className="text-xs uppercase tracking-[0.34em] text-[#c8e0ff]/70">AI Chat with Conversations</p>
          <h1 className="mt-4 font-display text-4xl leading-tight text-white sm:text-5xl">聊天对话</h1>
          <p className="mt-3 text-sm text-white/58">支持对话历史和消息来源引用</p>
        </div>

        {/* Conversation List */}
        <div className="mb-4 panel">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">对话列表</h2>
            <button
              className="primary-action px-4 py-2 text-sm"
              onClick={() => handleNewConversation('companion')}
            >
              新建对话
            </button>
          </div>
          {conversations.length === 0 ? (
            <p className="text-white/56">还没有对话，点击"新建对话"开始。</p>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`cursor-pointer rounded-lg border p-3 transition ${
                    currentConversation?.id === conv.id
                      ? 'border-white/40 bg-white/10'
                      : 'border-white/10 bg-white/5 hover:border-white/20'
                  }`}
                  onClick={() => selectConversation(conv)}
                >
                  <p className="text-sm text-white/70">{conv.mode}</p>
                  <p className="mt-1 font-semibold text-white">{conv.title}</p>
                  <p className="mt-2 text-xs text-white/42">{new Date(conv.updated_at).toLocaleString()}</p>
                  <button
                    className="mt-2 text-xs text-red-400 hover:text-red-300"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteConversation(conv.id);
                    }}
                  >
                    删除
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Chat Window */}
        {currentConversation ? (
          <div className="panel">
            <h3 className="mb-4 text-lg font-semibold text-white">
              {currentConversation.title}
            </h3>

            {/* Messages */}
            <div className="mb-4 max-h-96 overflow-y-auto rounded-lg bg-white/5 p-4">
              {messages.length === 0 ? (
                <p className="text-center text-white/42">开始第一条消息吧</p>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`mb-4 rounded-lg p-3 ${
                      msg.role === 'user'
                        ? 'bg-blue-500/20 ml-8'
                        : 'bg-white/10 mr-8'
                    }`}
                  >
                    <p className="text-xs uppercase text-white/56">{msg.role}</p>
                    <p className="mt-1 text-white">{msg.content}</p>

                    {/* Message Sources */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 rounded bg-white/5 p-2">
                        <p className="text-xs text-white/56">引用来源:</p>
                        {msg.sources.map((source) => (
                          <div key={source.id} className="mt-2 text-sm">
                            <p className="text-white/70">{source.title_snapshot}</p>
                            <p className="text-xs text-white/42">{source.excerpt_snapshot}</p>
                            <p className="mt-1 text-xs text-white/56">
                              相关度: {(source.relevance_score * 100).toFixed(0)}%
                            </p>
                          </div>
                        ))}
                      </div>
                    )}

                    {msg.status === 'failed' && (
                      <p className="mt-2 text-xs text-red-400">发送失败</p>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Input */}
            <div className="flex gap-2">
              <textarea
                className="input-surface flex-1 min-h-24 resize-none"
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="输入消息..."
                disabled={isSending}
              />
              <button
                className="primary-action self-end px-6 py-3"
                onClick={handleSend}
                disabled={isSending || !text.trim()}
              >
                {isSending ? '...' : '发送'}
              </button>
            </div>
          </div>
        ) : (
          <div className="panel text-center">
            <p className="text-white/56">选择一个对话或创建新对话开始聊天</p>
          </div>
        )}

        {/* Status */}
        {status && <p className="mt-4 text-center text-sm text-white/56">{status}</p>}
      </div>
    </section>
  );
}
