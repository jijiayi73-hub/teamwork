import React, { Suspense, lazy, useEffect, useMemo, useRef, useState } from 'react';
import {
  createDiary,
  createEntry,
  createMemory,
  deleteMemory,
  generateImage,
  getAdminStats,
  getMemory,
  getStatsOverview,
  healthCheck,
  listMemories,
  pastSelfChat,
} from './api/client';
import { getMessages, listConversations, sendChatMessage } from './api/chat';
import { getCurrentUser, logout, requireAuth } from './api/auth';
import LiquidMemoryBackground from './components/LiquidMemoryBackground';
import LoginPage from './components/LoginPage';

const ParticleWaveHero = lazy(() => import('./components/ParticleWaveHero'));

const DRAFT_KEY = 'mindful_memory_diary_draft';
const EMOTIONS = ['calm', 'joy', 'sadness', 'anxiety', 'tired', 'neutral'];
const MOOD_COLORS = ['#8fb8ff', '#b8e6d0', '#ffd6a5', '#f5b6d3', '#c8b6ff', '#d8dee9'];
const QUESTION_BANK = [
  '如果只选一个画面代表今天，会是什么？',
  '今天有没有一个很小但值得被记住的瞬间？',
  '现在的你最希望被怎样理解？',
  '这件事里，有没有一点已经被你撑过去的部分？',
];

export default function App() {
  const route = useHashRoute();
  const isMemoryRoute = route.name === 'garden' || route.name === 'detail' || route.name === 'admin';
  const [currentUser, setCurrentUser] = useState(getCurrentUser());

  useEffect(() => {
    const handleAuthChange = () => setCurrentUser(getCurrentUser());
    window.addEventListener('auth-change', handleAuthChange);
    return () => window.removeEventListener('auth-change', handleAuthChange);
  }, []);

  if (route.name === 'login') return <LoginPage />;
  if (['chat', 'diary', 'garden', 'detail', 'admin'].includes(route.name) && !requireAuth()) {
    return <LoginPage />;
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#10131e] font-body text-white">
      {isMemoryRoute ? <LiquidMemoryBackground /> : <DreamBackdrop />}
      <TopNav currentUser={currentUser} onAuthChange={() => setCurrentUser(getCurrentUser())} />
      {route.name === 'chat' && <ChatPage />}
      {route.name === 'diary' && <DiaryResultPage />}
      {route.name === 'garden' && <MemoryGardenPage />}
      {route.name === 'detail' && <MemoryDetailPage memoryId={route.id} />}
      {route.name === 'admin' && <AdminDashboardPage />}
      {route.name === 'monthly-report' && <MonthlyReport />}
      {route.name === 'about' && <AboutPage />}
      {route.name === 'home' && <HomePage />}
    </main>
  );
}

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash || '#/');
  useEffect(() => {
    const handleHashChange = () => setHash(window.location.hash || '#/');
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);
  if (hash.startsWith('#/login')) return { name: 'login' };
  if (hash.startsWith('#/ai-companion-chat')) return { name: 'chat' };
  if (hash.startsWith('#/diary-result')) return { name: 'diary' };
  if (hash.startsWith('#/memory-garden/')) return { name: 'detail', id: hash.split('/').pop() };
  if (hash.startsWith('#/memory-garden')) return { name: 'garden' };
  if (hash.startsWith('#/admin')) return { name: 'admin' };
  if (hash.startsWith('#/about')) return { name: 'about' };
  if (hash.startsWith('#/monthly-report')) return { name: 'monthly-report' };
  return { name: 'home' };
}

function TopNav({ currentUser, onAuthChange }) {
  const handleLogout = () => {
    logout();
    onAuthChange();
  };
  return (
    <nav className="relative z-10 flex items-center justify-between px-8 py-6 text-sm text-white/72 lg:px-14">
      <a className="font-display text-lg tracking-wide text-white" href="#/">Mindful Memory Diary</a>
      <div className="flex items-center gap-6 rounded-full border border-white/10 bg-white/[0.06] px-5 py-3 shadow-glow backdrop-blur-xl">
        <a className="transition hover:text-white" href="#/">Home</a>
        <a className="transition hover:text-white" href="#/memory-garden">Memory Garden</a>
        <a className="transition hover:text-white" href="#/monthly-report">Monthly Report</a>
        {currentUser?.role === 'admin' && <a className="transition hover:text-white" href="#/admin">Admin</a>}
        <a className="transition hover:text-white" href="#/about">About</a>
        {currentUser ? (
          <>
            <span className="text-white/40">|</span>
            <span className="transition hover:text-white">{currentUser.email}</span>
            <button className="transition hover:text-white" onClick={handleLogout} type="button">登出</button>
          </>
        ) : (
          <>
            <span className="text-white/40">|</span>
            <a className="transition hover:text-white" href="#/login">登录</a>
          </>
        )}
      </div>
    </nav>
  );
}

function HomePage() {
  return (
    <section className="relative z-10 flex min-h-[calc(100vh-96px)] items-center justify-center px-5 pb-28 pt-6">
      <div className="w-full max-w-4xl rounded-[28px] border border-white/16 bg-white/[0.08] px-6 py-12 text-center shadow-glow backdrop-blur-2xl sm:px-10 lg:px-16">
        <p className="mb-4 text-sm uppercase tracking-[0.38em] text-[#c8e0ff]/80">Inner Garden</p>
        <h1 className="font-display text-5xl leading-tight text-white sm:text-6xl lg:text-7xl">Mindful Memory Diary</h1>
        <p className="mt-5 text-lg text-[#e6eefc]/90 sm:text-xl">把今天的情绪，种成一座记忆花园</p>
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <a className="primary-action w-full sm:w-auto" href="#/ai-companion-chat">开始记录今天</a>
          <a className="secondary-action w-full sm:w-auto" href="#/memory-garden">进入 Memory Garden</a>
        </div>
      </div>
      <p className="absolute bottom-6 left-1/2 w-full max-w-4xl -translate-x-1/2 px-5 text-center text-xs leading-6 text-white/50 sm:text-sm">
        产品边界：Inner Garden 不是心理诊断工具，也不提供治疗、用药或医疗建议；它只做记录、陪伴和回忆整理。
      </p>
    </section>
  );
}

function ChatPage() {
  const [messages, setMessages] = useState([{ content: '慢慢说，我在听。今天发生了什么？', role: 'assistant' }]);
  const [text, setText] = useState('');
  const [note, setNote] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    loadConversations();
  }, []);

  async function loadConversations() {
    try {
      const response = await listConversations({ page_size: 8 });
      setConversations(response.data?.conversations || []);
    } catch (error) {
      setNote(`会话列表读取失败：${error.message}`);
    }
  }

  async function continueConversation(id) {
    setConversationId(id);
    setNote('正在读取历史会话...');
    try {
      const response = await getMessages(id, { page_size: 50 });
      const next = (response.data?.messages || []).map((item) => item.message);
      setMessages(next.length ? next : messages);
      setNote('已继续历史会话。');
    } catch (error) {
      setNote(`历史会话读取失败：${error.message}`);
    }
  }

  async function handleSend() {
    const rawContent = text.trim();
    if (!rawContent || isSending) return;
    const optimisticMessages = [...messages, { content: rawContent, role: 'user' }];
    setMessages(optimisticMessages);
    setText('');
    setIsSending(true);
    setNote('');
    try {
      const response = await sendChatMessage({
        conversation_id: conversationId,
        mode: conversationId ? null : 'companion',
        content: rawContent,
        use_memory: false,
        anchor_diary_id: null,
      });
      const assistant = response.data?.assistant_message || { content: '我收到了你的消息，但这次没有生成回复。可以再试一次。', role: 'assistant' };
      const nextMessages = [...optimisticMessages, assistant];
      const nextConversationId = response.data?.conversation?.id || conversationId;
      setMessages(nextMessages);
      setConversationId(nextConversationId);
      writeDraftFromMessages(nextMessages, nextConversationId);
      setNote('已保存真实对话草稿，可以继续聊，也可以生成日记。');
      loadConversations();
    } catch (error) {
      setMessages(optimisticMessages);
      setNote(`发送失败：${error.message}。用户消息已保留，可以重试或生成草稿。`);
    } finally {
      setIsSending(false);
    }
  }

  function changeQuestion() {
    const question = QUESTION_BANK[Math.floor(Math.random() * QUESTION_BANK.length)];
    const nextMessages = [...messages, { role: 'assistant', content: question }];
    setMessages(nextMessages);
    writeDraftFromMessages(nextMessages, conversationId);
  }

  function handleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setText((current) => `${current}${current ? ' ' : ''}今天有一些说不清的感受，我想先慢慢放在这里。`);
      setMessages((current) => [...current, { content: '没关系，语音现在先用本地文字替代。你可以继续补一点点，我会跟着你的节奏。', role: 'assistant' }]);
      setNote('当前浏览器不支持本地语音识别，已填入一段示例语音文本。');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    setIsListening(true);
    setNote('正在听你说，结束后会自动放进输入框。');
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || '';
      setText((current) => `${current}${current ? ' ' : ''}${transcript}`.trim());
    };
    recognition.onerror = () => {
      setNote('语音识别没有成功，可以先用文字记录。');
    };
    recognition.onend = () => {
      setIsListening(false);
    };
    recognition.start();
  }

  async function handleGenerateDiary() {
    const transcript = transcriptFromMessages(messages);
    if (!transcript.trim()) {
      setNote('先写下一点点，或继续回答一个问题。');
      return;
    }
    setNote('正在把真实对话保存为 entry，并生成日记草稿...');
    try {
      const response = await createEntry(transcript, conversationId);
      const entry = response.data;
      const draft = {
        entry_id: entry.id,
        conversation_id: conversationId,
        title: entry.draft_title || '今天的温柔记录',
        content: entry.draft_content || transcript,
        raw_content: transcript,
        conversation_messages: messages,
        cover_prompt: buildWatercolorPrompt({
          title: entry.draft_title || '今天的记忆',
          content: entry.draft_content || transcript,
          raw_content: transcript,
          conversation_messages: messages,
          analysis: entry.analysis,
        }),
        cover_image_url: '',
        analysis: entry.analysis,
        source: 'chat_api',
      };
      window.localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
      window.location.hash = '#/diary-result';
    } catch (error) {
      setNote(`生成日记草稿失败：${error.message}`);
    }
  }

  return (
    <section className="relative z-10 flex min-h-[calc(100vh-96px)] items-center justify-center px-5 pb-12 pt-4 lg:px-14">
      <Suspense fallback={null}>
        <ParticleWaveHero
          backgroundOpacity={0.62}
          className="chat-particle-wave"
          fit="cover"
          interactive
          particleSize={14}
          waveSpeed={1.35}
          waveStrength={0.28}
        />
      </Suspense>
      <div className="chat-stage">
        <div className="text-center">
          <p className="text-xs uppercase tracking-[0.34em] text-[#c8e0ff]/70">AI Companion Chat</p>
          <h1 className="mt-4 font-display text-4xl leading-tight text-white sm:text-5xl">今天想记录什么？</h1>
          <p className="mt-3 text-sm text-white/58">你说的话会成为封面灵感，不需要上传图片。</p>
        </div>
        <section className="chat-window">
          {conversations.length > 0 && (
            <div className="conversation-strip">
              {conversations.map((conversation) => (
                <button key={conversation.id} onClick={() => continueConversation(conversation.id)} type="button">
                  {conversation.mode === 'past_self' ? 'Past Self' : 'Companion'} · {conversation.title}
                </button>
              ))}
            </div>
          )}
          <div className="ai-notification-list">
            {messages.map((message, index) => (
              <div className={`ai-notification ${message.role === 'user' ? 'ai-notification-user' : ''}`} key={`${message.role}-${index}-${message.content}`}>
                {message.role !== 'user' && <span className="ai-notification-dot" />}
                <p>{message.content}</p>
              </div>
            ))}
          </div>
          {note && <p className="chat-note">{note}</p>}
          <div className="composer-shell">
            <textarea
              className="composer-input"
              onChange={(event) => setText(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              placeholder="慢慢说，我在听。"
              value={text}
            />
            <button
              aria-label={isListening ? '正在语音输入' : '语音输入'}
              className={`composer-icon-button ${isListening ? 'is-listening' : ''}`}
              onClick={handleVoiceInput}
              type="button"
            >
              <span aria-hidden="true">♪</span>
            </button>
            <button aria-label="发送" className="composer-send-button" disabled={isSending || !text.trim()} onClick={handleSend} type="button">
              <span aria-hidden="true">{isSending ? '…' : '→'}</span>
            </button>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button className="generate-link" onClick={handleGenerateDiary} type="button">我说完了，生成日记</button>
            <button className="generate-link" onClick={changeQuestion} type="button">换一个问题</button>
          </div>
        </section>
      </div>
    </section>
  );
}
function DiaryResultPage() {
  const draft = useMemo(() => readJson(DRAFT_KEY), []);
  const [title, setTitle] = useState(draft?.title || '');
  const [content, setContent] = useState(draft?.content || '');
  const [emotion, setEmotion] = useState(draft?.analysis?.primary_emotion || 'calm');
  const [emotionColor, setEmotionColor] = useState('#8fb8ff');
  const [coverImageUrl, setCoverImageUrl] = useState(draft?.cover_image_url || '');
  const [keywords, setKeywords] = useState(extractKeywords(draft));
  const [style, setStyle] = useState('温柔、克制、像写给自己的备忘');
  const [status, setStatus] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [existingMemoryId, setExistingMemoryId] = useState(null);
  const [checkingExisting, setCheckingExisting] = useState(false);

  useEffect(() => {
    async function checkExistingMemory() {
      if (!draft?.entry_id) return;
      setCheckingExisting(true);
      try {
        const response = await listMemories();
        const existingMemory = (response.data || []).find(
          (memory) => memory.diary?.id && memory.diary.entry_id === draft.entry_id
        );
        if (existingMemory) {
          setExistingMemoryId(existingMemory.id);
          setStatus('这份草稿已经保存为记忆卡片，可以直接查看。');
        }
      } catch (error) {
        setStatus(`检查已有记忆卡片失败：${error.message}`);
      } finally {
        setCheckingExisting(false);
      }
    }
    checkExistingMemory();
  }, [draft?.entry_id]);

  function regenerateTone() {
    setContent((current) => `${current.replace(/\n\n调整后的 AI 文风：.*$/s, '')}\n\n调整后的 AI 文风：${style}。`);
    setStatus('已按所选 AI 文风调整正文，可继续编辑后保存。');
  }

  async function handleSave() {
    if (!draft?.entry_id) {
      setStatus('缺少 entry_id，请先从 AI Companion Chat 生成草稿。');
      return;
    }

    if (existingMemoryId) {
      window.location.hash = `#/memory-garden/${existingMemoryId}`;
      return;
    }

    setIsSaving(true);
    setStatus('正在保存 diary，并根据对话生成封面...');
    try {
      const diaryResponse = await createDiary({
        entry_id: draft.entry_id,
        title,
        content,
        diary_date: new Date().toISOString().slice(0, 10),
        is_favorite: false,
      });
      const coverPrompt = buildWatercolorPrompt({ ...draft, title, content, emotion });
      let generatedCoverImageUrl = coverImageUrl;
      if (!generatedCoverImageUrl) {
        try {
          const imageResponse = await generateImage({
            prompt: coverPrompt,
            emotion,
            style: 'natural',
            size: '1024x1024',
            quality: 'standard',
            model: 'dall-e-3',
          });
          generatedCoverImageUrl = imageResponse.data?.image_url || '';
          setCoverImageUrl(generatedCoverImageUrl);
        } catch (imageError) {
          setStatus(`封面生成失败，将先保存记忆卡片并保留提示词：${imageError.message}`);
        }
      }
      const memoryResponse = await createMemory({
        diary_id: diaryResponse.data.id,
        cover_image_url: generatedCoverImageUrl || null,
        cover_prompt: coverPrompt,
        emotion_label: emotion,
        emotion_color: emotionColor,
        keywords,
        conversation_summary: transcriptFromMessages(draft.conversation_messages || []),
      });
      window.localStorage.removeItem(DRAFT_KEY);
      window.location.hash = `#/memory-garden/${memoryResponse.data.id}`;
    } catch (error) {
      if (error.message.includes('already exists') || error.message.includes('409')) {
        setStatus('这份内容已保存，正在查找已有记忆卡片...');
        try {
          const response = await listMemories();
          const existingMemory = (response.data || []).find(
            (memory) => memory.diary?.id && memory.diary.entry_id === draft.entry_id
          );
          if (existingMemory) {
            window.localStorage.removeItem(DRAFT_KEY);
            window.location.hash = `#/memory-garden/${existingMemory.id}`;
            return;
          }
        } catch (searchError) {
          setStatus(`查找已有记忆卡片失败：${searchError.message}`);
        }
      }
      setStatus(`保存失败：${error.message}`);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <PageShell eyebrow="Diary Result" title="把倾诉整理成日记" subtitle="封面会由 AI 根据对话自动生成，也会保存对应提示词。">
      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <section className="panel space-y-4">
          {!draft ? (
            <EmptyState actionHref="#/ai-companion-chat" actionText="回到对话页" text="还没有日记草稿。请先完成一段对话。" />
          ) : (
            <>
              <input className="input-surface text-xl font-semibold" onChange={(event) => setTitle(event.target.value)} value={title} />
              <textarea className="input-surface min-h-72 resize-none leading-8" onChange={(event) => setContent(event.target.value)} value={content} />
              <div className="transcript-box">
                <p>对话记录</p>
                {(draft.conversation_messages || []).map((message, index) => <span key={`${message.role}-${index}`}>{message.role}: {message.content}</span>)}
              </div>
              {existingMemoryId ? (
                <a className="primary-action" href={`#/memory-garden/${existingMemoryId}`}>查看已保存的记忆卡片</a>
              ) : (
                <button className="primary-action" disabled={isSaving || checkingExisting} onClick={handleSave} type="button">
                  {isSaving ? '保存并生成封面中...' : checkingExisting ? '检查中...' : '保存到 Memory Garden'}
                </button>
              )}
            </>
          )}
        </section>
        <aside className="panel space-y-5">
          <ControlLabel label="选择情绪">
            <select className="input-surface" onChange={(event) => setEmotion(event.target.value)} value={emotion}>
              {EMOTIONS.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </ControlLabel>
          <ControlLabel label="选择情绪底色">
            <div className="swatch-row">
              {MOOD_COLORS.map((color) => (
                <button aria-label={color} className={emotionColor === color ? 'swatch is-selected' : 'swatch'} key={color} onClick={() => setEmotionColor(color)} style={{ backgroundColor: color }} type="button" />
              ))}
            </div>
          </ControlLabel>
          <ControlLabel label="自动封面提示词">
            <textarea className="input-surface min-h-28 resize-none text-xs leading-6" readOnly value={buildWatercolorPrompt({ ...draft, title, content, emotion })} />
            {coverImageUrl && <div className="memory-cover" style={{ backgroundImage: `url(${assetUrl(coverImageUrl)})` }} />}
          </ControlLabel>
          <ControlLabel label="重新生成/调整 AI 文风">
            <input className="input-surface" onChange={(event) => setStyle(event.target.value)} value={style} />
            <button className="secondary-action mt-3 w-full" onClick={regenerateTone} type="button">调整文风</button>
          </ControlLabel>
          <ControlLabel label="关键词">
            <input className="input-surface" onChange={(event) => setKeywords(splitKeywords(event.target.value))} value={keywords.join(', ')} />
          </ControlLabel>
          {status && <StatusText>{status}</StatusText>}
        </aside>
      </div>
    </PageShell>
  );
}
function MemoryGardenPage() {
  const [memories, setMemories] = useState([]);
  const [status, setStatus] = useState('');
  const [emotion, setEmotion] = useState('');
  const [keyword, setKeyword] = useState('');

  async function loadGarden(nextFilters = {}) {
    setStatus('');
    try {
      const memoryResponse = await listMemories({ emotion: nextFilters.emotion ?? emotion, keyword: nextFilters.keyword ?? keyword });
      setMemories(memoryResponse.data || []);
    } catch (error) {
      setStatus(`记忆花园暂时没有加载成功：${error.message}`);
    }
  }

  useEffect(() => {
    loadGarden({ emotion: '', keyword: '' });
  }, []);

  async function handleDelete(memoryId) {
    try {
      await deleteMemory(memoryId);
      await loadGarden();
    } catch (error) {
      setStatus(`删除失败：${error.message}`);
    }
  }

  return (
    <section className="memory-garden-page">
      <div className="memory-garden-shell">
        <header className="memory-garden-hero">
          <p className="memory-garden-eyebrow">Memory Garden</p>
          <h1 className="memory-garden-title">你的记忆花园</h1>
          <div className="memory-garden-actions" aria-label="Memory Garden actions">
            <a aria-label="写下今天" className="memory-garden-icon-action" href="#/ai-companion-chat" title="写下今天"><WriteIcon /></a>
            <button aria-label="刷新花园" className="memory-garden-icon-action" onClick={() => loadGarden()} title="刷新花园" type="button"><RefreshIcon /></button>
          </div>
          <p className="memory-garden-total"><span>记忆总数</span><span aria-hidden="true">·</span><strong>{memories.length}</strong></p>
        </header>
        <div className="garden-filter-row">
          <select className="input-surface" onChange={(event) => setEmotion(event.target.value)} value={emotion}>
            <option value="">全部情绪</option>
            {EMOTIONS.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <input className="input-surface" onChange={(event) => setKeyword(event.target.value)} placeholder="按关键词筛选" value={keyword} />
          <button className="secondary-action" onClick={() => loadGarden()} type="button">筛选</button>
        </div>
        <section className="memory-garden-list" aria-label="Memory Garden memory list">
          {memories.length === 0 ? (
            <div className="memory-garden-empty"><p>还没有保存的记忆卡片。</p><a className="memory-garden-empty-action" href="#/ai-companion-chat">开始记录今天</a></div>
          ) : (
            <div className="memory-garden-card-grid">
              {memories.map((memory) => (
                <article className="memory-card" key={memory.id} style={{ borderColor: memory.emotion_color }}>
                  {memory.cover_image_url && <div className="memory-cover" style={{ backgroundImage: `url(${assetUrl(memory.cover_image_url)})` }} />}
                  <p className="text-sm text-white/52">{memory.diary_date}</p>
                  <h3 className="mt-3 font-display text-2xl text-white">{memory.title}</h3>
                  <p className="memory-card-excerpt mt-4 text-sm leading-7 text-white/64">{memory.excerpt}</p>
                  <div className="keyword-row">{memory.keywords.map((item) => <span key={item}>{item}</span>)}</div>
                  <div className="mt-5 flex items-center justify-between gap-3">
                    <a className="secondary-action inline-flex px-4 py-2" href={`#/memory-garden/${memory.id}`}>详情</a>
                    <button className="secondary-action inline-flex px-4 py-2" onClick={() => handleDelete(memory.id)} type="button">删除</button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
        {status && <p className="memory-garden-status">{status}</p>}
      </div>
    </section>
  );
}

function MemoryDetailPage({ memoryId }) {
  const [memory, setMemory] = useState(null);
  const [status, setStatus] = useState('正在读取这张记忆卡片...');
  const [pastSelfMessages, setPastSelfMessages] = useState([]);
  const [pastSelfInput, setPastSelfInput] = useState('');
  const [pastSelfConversationId, setPastSelfConversationId] = useState(null);

  useEffect(() => {
    async function loadMemory() {
      try {
        const response = await getMemory(memoryId);
        setMemory(response.data);
        setStatus('');
      } catch (error) {
        setStatus(`这张记忆卡片暂时没有加载成功：${error.message}`);
      }
    }
    loadMemory();
  }, [memoryId]);

  async function handlePastSelfChat() {
    const message = pastSelfInput.trim() || '那天的我现在最想提醒我什么？';
    setPastSelfInput('');
    setPastSelfMessages((current) => [...current, { role: 'user', content: message }]);
    setStatus('正在整理来自那天的回应...');
    try {
      const response = await pastSelfChat(memoryId, { message, conversation_id: pastSelfConversationId });
      setPastSelfConversationId(response.data.conversation.id);
      setPastSelfMessages((current) => [...current, response.data.assistant_message]);
      setStatus('');
    } catch (error) {
      setStatus(`暂时没有生成回应：${error.message}`);
    }
  }

  return (
    <PageShell eyebrow="Memory Detail" title={memory?.title || '记忆详情'} subtitle="这里展示完整日记、封面、情绪、关键词，以及与过去的自己对话。">
      {!memory ? (
        <EmptyState actionHref="#/memory-garden" actionText="返回 Memory Garden" text={status} />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <article className="panel">
            {memory.cover_image_url && <div className="detail-cover" style={{ backgroundImage: `url(${assetUrl(memory.cover_image_url)})` }} />}
            <p className="text-sm text-white/52">{memory.diary_date}</p>
            <p className="mt-6 whitespace-pre-wrap text-base leading-8 text-white/76">{memory.diary.content}</p>
          </article>
          <aside className="panel space-y-5">
            <p className="text-sm text-white/64">Emotion</p>
            <p className="font-display text-4xl" style={{ color: memory.emotion_color }}>{memory.emotion_label}</p>
            <div className="keyword-row">{memory.keywords.map((item) => <span key={item}>{item}</span>)}</div>
            <div className="past-self-box">
              {pastSelfMessages.map((message, index) => (
                <div className={message.role === 'user' ? 'chat-bubble chat-bubble-user' : 'chat-bubble chat-bubble-ai'} key={`${message.role}-${index}`}>{message.content}</div>
              ))}
            </div>
            <textarea className="input-surface min-h-24" onChange={(event) => setPastSelfInput(event.target.value)} placeholder="问问那天的我..." value={pastSelfInput} />
            <button className="primary-action" onClick={handlePastSelfChat} type="button">和那天的我聊聊</button>
            <a className="secondary-action inline-flex" href="#/memory-garden">返回 Memory Garden</a>
          </aside>
        </div>
      )}
      {status && <StatusText>{status}</StatusText>}
    </PageShell>
  );
}

function AdminDashboardPage() {
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState('');
  useEffect(() => {
    async function loadStats() {
      try {
        const response = await getAdminStats();
        setStats(response.data);
        setStatus('');
      } catch (error) {
        setStatus(`统计数据暂时没有加载成功：${error.message}`);
      }
    }
    loadStats();
  }, []);

  const maxDaily = Math.max(1, ...(stats?.daily_new_memory_cards || []).map((item) => item.count));
  const maxEmotion = Math.max(1, ...(stats?.emotion_distribution || []).map((item) => item.count));
  return (
    <PageShell eyebrow="Admin Dashboard" title="系统统计与服务状态" subtitle="管理员只查看聚合统计，不展示用户私密日记正文。">
      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Users" value={stats?.total_users ?? '-'} />
        <Metric label="Memory Cards" value={stats?.total_memory_cards ?? '-'} />
        <Metric label="Conversations" value={stats?.total_conversations ?? '-'} />
        <Metric label="New 7 Days" value={stats?.new_memory_cards_last_7_days ?? '-'} />
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="panel">
          <h2 className="font-display text-2xl">近 7 天新增</h2>
          <div className="bar-chart">{(stats?.daily_new_memory_cards || []).map((item) => <div key={item.date}><span>{item.date.slice(5)}</span><i style={{ height: `${Math.max(8, (item.count / maxDaily) * 150)}px` }} /><strong>{item.count}</strong></div>)}</div>
        </section>
        <section className="panel">
          <h2 className="font-display text-2xl">情绪分布</h2>
          <div className="distribution-chart">{(stats?.emotion_distribution || []).map((item) => <p key={item.emotion}><span>{item.emotion}</span><i style={{ width: `${Math.max(5, (item.count / maxEmotion) * 100)}%` }} /><strong>{item.count}</strong></p>)}</div>
        </section>
      </div>
      {(status || stats?.privacy_note) && <StatusText>{status || stats?.privacy_note}</StatusText>}
    </PageShell>
  );
}

function AboutPage() {
  const [status, setStatus] = useState('');
  const currentUser = getCurrentUser();
  async function handleHealthCheck() {
    setStatus('正在检查服务状态...');
    try {
      const response = await healthCheck();
      setStatus(`服务状态正常：${response.status || response.data?.status || 'ok'}`);
    } catch (error) {
      setStatus(`服务暂时不可用：${error.message}`);
    }
  }
  return (
    <PageShell eyebrow="About" title="关于 Inner Garden" subtitle="这里保留服务状态检查，同时展示当前登录信息。">
      <section className="panel space-y-5">
        <p className="text-white/70">当前用户：{currentUser?.email || '尚未登录'}</p>
        <button className="primary-action" onClick={handleHealthCheck} type="button">检查服务状态</button>
        <a className="secondary-action" href="#/admin">进入 Admin Dashboard</a>
        {status && <StatusText>{status}</StatusText>}
      </section>
    </PageShell>
  );
}

// ============================================================================
// MONTHLY REPORT CALENDAR COMPONENT (Migrated from E:\teamwork-main)
// ============================================================================

const WEEKDAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function MonthlyReport() {
  const today = new Date();
  const [visibleMonth, setVisibleMonth] = useState({ year: today.getFullYear(), month: today.getMonth() });
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [memories, setMemories] = useState([]);
  const [status, setStatus] = useState('');
  const [toastVisible, setToastVisible] = useState(false);
  const toastTimerRef = useRef(null);

  useEffect(() => {
    loadMemories();
  }, [visibleMonth]);

  async function loadMemories() {
    setStatus('正在读取记忆卡片...');
    try {
      const response = await listMemories();
      const allMemories = response.data || [];
      setMemories(allMemories);
      setStatus(`已读取 ${allMemories.length} 张记忆卡片。`);
    } catch (error) {
      setStatus(`读取记忆卡片失败：${error.message}`);
      setMemories([]);
    }
  }

  function formatDateKey(year, month, day) {
    return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  }

  function getDiaryDateKey(memory) {
    if (!memory) return '';
    const dateStr = memory.diary_date || memory.diary?.diary_date || memory.created_at;
    if (!dateStr) return '';
    const match = String(dateStr).match(/^(\d{4})-(\d{2})-(\d{2})/);
    return match ? `${match[1]}-${match[2]}-${match[3]}` : '';
  }

  function getDiaryEmotion(memory) {
    return memory.emotion_label || memory.diary?.analysis?.primary_emotion || 'calm';
  }

  function getMoodEmoji(memory) {
    const emotion = String(getDiaryEmotion(memory)).trim().toLowerCase();
    if (['joy', 'happy', 'happiness', '开心', '快乐'].includes(emotion)) return '☀';
    if (['calm', 'peaceful', 'peace', '平静', '安定'].includes(emotion)) return '○';
    if (['nostalgia', 'missing', 'miss', '怀念', '想念'].includes(emotion)) return '◇';
    if (['anxiety', 'anxious', 'fear', '焦虑', '紧张'].includes(emotion)) return '△';
    if (['sad', 'sadness', '难过', '伤心', '低落'].includes(emotion)) return '◌';
    return '✦';
  }

  function getDiaryImage(memory) {
    return memory.cover_image_url || memory.diary?.cover_image_url || '';
  }

  function getDiarySummary(memory) {
    return memory.excerpt || memory.conversation_summary || memory.diary?.content || '这一天被温柔地保存下来。';
  }

  function normalizeMemory(memory) {
    const dateKey = getDiaryDateKey(memory);
    if (!dateKey) return null;
    return {
      ...memory,
      dateKey,
      displayDate: memory.diary_date || dateKey,
      displayEmotion: getDiaryEmotion(memory),
      displayImage: getDiaryImage(memory),
      displaySummary: getDiarySummary(memory),
      emoji: getMoodEmoji(memory),
    };
  }

  const diaryIndex = useMemo(() => {
    return memories.reduce((index, memory) => {
      const normalized = normalizeMemory(memory);
      if (!normalized) return index;
      const [diaryYear, diaryMonth] = normalized.dateKey.split('-').map(Number);
      if (diaryYear !== visibleMonth.year || diaryMonth !== visibleMonth.month + 1) return index;
      const existing = index[normalized.dateKey];
      if (!existing || String(normalized.created_at || '') >= String(existing.created_at || '')) {
        index[normalized.dateKey] = normalized;
      }
      return index;
    }, {});
  }, [memories, visibleMonth]);

  const calendarDays = useMemo(() => {
    const firstDay = new Date(visibleMonth.year, visibleMonth.month, 1);
    const daysInMonth = new Date(visibleMonth.year, visibleMonth.month + 1, 0).getDate();
    const prevMonthDays = new Date(visibleMonth.year, visibleMonth.month, 0).getDate();
    const leadingDays = (firstDay.getDay() + 6) % 7;
    const cells = [];

    for (let i = leadingDays - 1; i >= 0; i -= 1) {
      cells.push({ id: `prev-${i}`, day: prevMonthDays - i, isCurrentMonth: false });
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
      const dateKey = formatDateKey(visibleMonth.year, visibleMonth.month, day);
      cells.push({
        id: dateKey,
        day,
        dateKey,
        isCurrentMonth: true,
        entry: diaryIndex[dateKey],
      });
    }

    const trailingDays = Math.ceil(cells.length / 7) * 7 - cells.length;
    for (let day = 1; day <= trailingDays; day += 1) {
      cells.push({ id: `next-${day}`, day, isCurrentMonth: false });
    }

    return cells;
  }, [visibleMonth, diaryIndex]);

  const monthTitle = `${MONTH_NAMES[visibleMonth.month]} ${visibleMonth.year}`;

  function showEmptyToast() {
    setToastVisible(true);
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToastVisible(false), 1800);
  }

  function handleMonthChange(offset) {
    setSelectedEntry(null);
    setVisibleMonth((current) => {
      const nextDate = new Date(current.year, current.month + offset, 1);
      return { year: nextDate.getFullYear(), month: nextDate.getMonth() };
    });
  }

  function handleDayClick(day) {
    if (!day.isCurrentMonth) return;
    if (!day.entry) {
      showEmptyToast();
      return;
    }
    setSelectedEntry(day.entry);
  }

  return (
    <section className="monthly-report-page" aria-label="Monthly mood report">
      <div className="monthly-report-shell">
        <header className="monthly-report-header">
          <h1>Mood Check-In</h1>
        </header>

        <div className="monthly-report-month-row">
          <h2>{monthTitle}</h2>
          <div className="monthly-report-month-actions" aria-label="Monthly report month controls">
            <button type="button" onClick={() => handleMonthChange(-1)} aria-label="Previous month">‹</button>
            <button type="button" onClick={() => handleMonthChange(1)} aria-label="Next month">›</button>
          </div>
        </div>

        <div className="monthly-report-weekdays" aria-hidden="true">
          {WEEKDAYS.map((weekday) => <span key={weekday}>{weekday}</span>)}
        </div>

        <div className="monthly-report-calendar">
          {calendarDays.map((day) => {
            const dayClassName = [
              'monthly-report-day',
              !day.isCurrentMonth ? 'is-placeholder' : '',
              day.isCurrentMonth && !day.entry ? 'has-no-entry' : '',
            ].filter(Boolean).join(' ');

            return (
              <button
                aria-label={day.isCurrentMonth ? `${day.dateKey} mood entry` : 'empty calendar placeholder'}
                className={dayClassName}
                disabled={!day.isCurrentMonth}
                key={day.id}
                onClick={() => handleDayClick(day)}
                type="button"
              >
                <span className="monthly-report-day-number">{day.day}</span>
                {day.entry && <span className="monthly-report-emoji">{day.entry.emoji}</span>}
              </button>
            );
          })}
        </div>

        <footer className="monthly-report-footer">
          <nav className="monthly-report-bottom-nav" aria-label="Monthly report navigation">
            <button className="monthly-report-tab is-active" type="button" aria-label="Home">
              <span className="monthly-report-tab-icon">♪</span>
              <span>Home</span>
            </button>
            <button className="monthly-report-tab" type="button" aria-label="Sleep">
              <span className="monthly-report-tab-icon">☼</span>
              <span>Sleep</span>
            </button>
            <button className="monthly-report-tab" type="button" aria-label="Discover">
              <span className="monthly-report-tab-icon">◆</span>
              <span>Discover</span>
            </button>
            <button className="monthly-report-tab" type="button" aria-label="Profile">
              <span className="monthly-report-tab-icon">◇</span>
              <span>Profile</span>
            </button>
          </nav>
          <p>{status || 'Calm curated by Mobbin'}</p>
        </footer>
      </div>

      {toastVisible && (
        <div className="monthly-report-toast" role="status">这一天还没有记录。</div>
      )}

      {selectedEntry && (
        <div className="monthly-report-modal-backdrop" onClick={() => setSelectedEntry(null)} role="presentation">
          <div
            aria-modal="true"
            className="monthly-report-modal"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            {selectedEntry.displayImage ? (
              <img src={assetUrl(selectedEntry.displayImage)} alt={`${selectedEntry.title || selectedEntry.dateKey} summary`} />
            ) : (
              <div className="monthly-report-modal-image-fallback" aria-hidden="true">
                {selectedEntry.emoji || '✦'}
              </div>
            )}
            <div className="monthly-report-modal-content">
              <span>{selectedEntry.displayDate}</span>
              <h3>{selectedEntry.title || 'Untitled Memory'}</h3>
              <p className="monthly-report-modal-emotion">
                {selectedEntry.emoji} {selectedEntry.displayEmotion}
              </p>
              <p>{selectedEntry.displaySummary || '这一天已经被温柔地保存下来。'}</p>
            </div>
            <button type="button" onClick={() => setSelectedEntry(null)}>关闭</button>
          </div>
        </div>
      )}
    </section>
  );
}

function DreamBackdrop() {
  return (
    <>
      <div className="absolute inset-0 bg-night-garden" />
      <div className="absolute inset-0 bg-watercolor-mist" />
      <div className="particles" aria-hidden="true">{Array.from({ length: 34 }, (_, index) => <span key={index} style={particleStyle(index)} />)}</div>
    </>
  );
}

function PageShell({ eyebrow, title, subtitle, children }) {
  return (
    <section className="relative z-10 px-5 pb-12 pt-4 lg:px-14">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-xs uppercase tracking-[0.34em] text-[#c8e0ff]/70">{eyebrow}</p>
          <h1 className="mt-3 font-display text-4xl leading-tight text-white sm:text-5xl">{title}</h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-white/62 sm:text-base">{subtitle}</p>
        </div>
        {children}
      </div>
    </section>
  );
}

function StatusText({ children }) {
  return <p className="mt-5 rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm leading-6 text-white/64">{children}</p>;
}

function EmptyState({ text, actionHref, actionText }) {
  return <div className="panel flex min-h-64 flex-col items-center justify-center text-center"><p className="max-w-xl text-white/64">{text}</p><a className="primary-action mt-6" href={actionHref}>{actionText}</a></div>;
}

function Metric({ label, value }) {
  return <div className="panel"><p className="text-xs uppercase tracking-[0.24em] text-white/42">{label}</p><p className="mt-3 font-display text-3xl text-white">{value}</p></div>;
}

function ControlLabel({ label, children }) {
  return <label className="block"><span className="mb-2 block text-sm text-white/64">{label}</span>{children}</label>;
}

function WriteIcon() {
  return <svg aria-hidden="true" fill="none" viewBox="0 0 24 24"><path d="M4.75 19.25l4.1-1.05 9.75-9.75a2.12 2.12 0 0 0-3-3L5.85 15.2l-1.1 4.05Z" /><path d="m14.25 6.75 3 3" /><path d="M8.5 19.25h10.75" /></svg>;
}

function RefreshIcon() {
  return <svg aria-hidden="true" fill="none" viewBox="0 0 24 24"><path d="M18.75 8.25A7.25 7.25 0 0 0 6.2 6.1L4.75 7.75" /><path d="M4.75 4.25v3.5h3.5" /><path d="M5.25 15.75a7.25 7.25 0 0 0 12.55 2.15l1.45-1.65" /><path d="M19.25 19.75v-3.5h-3.5" /></svg>;
}

function writeDraftFromMessages(messages, conversationId) {
  const transcript = transcriptFromMessages(messages);
  window.localStorage.setItem(DRAFT_KEY, JSON.stringify({
    conversation_id: conversationId,
    title: 'AI 对话记录',
    content: transcript,
    raw_content: transcript,
    conversation_messages: messages,
    cover_prompt: buildWatercolorPrompt({ title: 'AI 对话记录', raw_content: transcript, conversation_messages: messages }),
    cover_image_url: '',
    analysis: { primary_emotion: 'calm', summary: '来自 AI 对话的记录', suggestion: '可以继续补充，或整理成日记。' },
  }));
}

function transcriptFromMessages(messages) {
  return (messages || []).map((message) => `${message.role === 'user' ? '我' : 'AI'}：${message.content}`).join('\n');
}

function buildCoverPrompt(draft, emotion) {
  const title = draft?.title || 'today memory';
  return `Soft watercolor garden cover, title "${title}", emotion ${emotion}, quiet light, no text.`;
}

function extractKeywords(draft) {
  const emotion = draft?.analysis?.primary_emotion || 'calm';
  return Array.from(new Set([emotion, 'today', 'memory'])).slice(0, 6);
}

function splitKeywords(value) {
  return value.split(/[,，\s]+/).map((item) => item.trim()).filter(Boolean).slice(0, 12);
}

function assetUrl(url) {
  if (!url || /^(blob:|data:|https?:\/\/)/i.test(url)) return url;
  const isViteDev =
    window.location.hostname === 'localhost' &&
    window.location.port === '5173' &&
    url.startsWith('/uploads/');
  return isViteDev ? `http://localhost:8000${url}` : url;
}

function readJson(key) {
  const value = window.localStorage.getItem(key);
  if (!value) return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function particleStyle(index) {
  const left = (index * 29) % 100;
  const top = (index * 47) % 100;
  const size = 2 + (index % 4);
  const delay = (index % 9) * 0.7;
  const duration = 11 + (index % 7);
  return { left: `${left}%`, top: `${top}%`, width: `${size}px`, height: `${size}px`, animationDelay: `${delay}s`, animationDuration: `${duration}s` };
}

// ============================================================================
// IMAGE GENERATION FUNCTIONS (Migrated from E:\teamwork-main)
// ============================================================================

function getCoverPalette(emotion) {
  const palettes = {
    joy: ['#d9c78f', '#e9b7ba', '#7da997', '#f6e6ae'],
    anxiety: ['#8aa5b7', '#b7c7b4', '#6f8791', '#dce7df'],
    sadness: ['#778aa5', '#a9a3be', '#5e718f', '#d8deea'],
    tired: ['#7b89a6', '#a69fbe', '#627b85', '#e1d7e8'],
    relieved: ['#9fbea4', '#eadfb8', '#83a99f', '#f4eed6'],
    calm: ['#8ab7b0', '#a4b79c', '#5e7c8d', '#d8eadf'],
  };
  return palettes[emotion] || palettes.calm;
}

function buildWatercolorPrompt(diary) {
  const title = diary?.title || 'Inner Garden memory card';
  const emotion = diary?.emotion || diary?.analysis?.primary_emotion || 'calm';
  const sourceText = [
    diary?.content,
    diary?.raw_content,
    transcriptFromMessages(diary?.conversation_messages || []),
  ].filter(Boolean).join('\n').replace(/\s+/g, ' ').slice(0, 1200);
  return [
    'Create a poetic, beautiful watercolor cover image for an emotional diary memory card.',
    'Use the conversation and diary content as inspiration, but do not add readable text, UI, logos, real faces, violence, horror, or medical imagery.',
    'Style: soft therapeutic watercolor illustration, dreamy garden atmosphere, gentle light, translucent washes, elegant composition, cinematic but quiet, suitable for a reflective campus diary app.',
    `Diary title: ${title}.`,
    `Dominant emotion: ${emotion}.`,
    sourceText ? `Conversation-derived imagery cues: ${sourceText}` : '',
  ].filter(Boolean).join(' ').slice(0, 3800);
}

function escapeXml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function generateFallbackCover(diary) {
  const emotion = diary?.emotion || diary?.analysis?.primary_emotion || 'calm';
  const palette = getCoverPalette(emotion);
  const flowers = Array.from({ length: 16 }, (_, index) => {
    const x = 100 + ((index * 73) % 720);
    const y = 155 + ((index * 47) % 330);
    const r = 12 + (index % 5) * 6;
    const fill = index % 2 ? '#f4d9df' : '#e8efd7';
    return `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" opacity="0.34"/>`;
  }).join('');
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 640" role="img" aria-label="Memory garden cover">
      <defs>
        <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="${palette[0]}"/>
          <stop offset="48%" stop-color="${palette[1]}"/>
          <stop offset="100%" stop-color="${palette[2]}"/>
        </linearGradient>
        <filter id="soft"><feGaussianBlur stdDeviation="18"/></filter>
      </defs>
      <rect width="900" height="640" fill="url(#bg)"/>
      <circle cx="180" cy="150" r="120" fill="${palette[3]}" opacity="0.45" filter="url(#soft)"/>
      <circle cx="720" cy="130" r="150" fill="#f3dfc2" opacity="0.26" filter="url(#soft)"/>
      <circle cx="470" cy="520" r="260" fill="#dbe8d2" opacity="0.2" filter="url(#soft)"/>
      <path d="M110 520 C240 420 310 455 420 345 C520 245 650 260 790 145" fill="none" stroke="#f7f0df" stroke-width="22" stroke-linecap="round" opacity="0.22"/>
      <path d="M120 548 C250 450 338 492 460 365 C555 265 665 292 805 175" fill="none" stroke="#6f927f" stroke-width="7" stroke-linecap="round" opacity="0.28"/>
      ${flowers}
    </svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

async function generateDiaryCoverImage(diary) {
  await new Promise((resolve) => window.setTimeout(resolve, 260));
  return generateFallbackCover(diary);
}

async function completeDraftCover(draft) {
  if (draft?.cover_image_url || draft?.uploadedImageUrl) {
    return { ...draft, coverType: 'uploaded', coverImageUrl: draft.cover_image_url || draft.uploadedImageUrl, generatedImageUrl: '' };
  }
  const generatedImageUrl = await generateDiaryCoverImage(draft);
  return { ...draft, coverType: 'generated', coverImageUrl: generatedImageUrl, generatedImageUrl };
}

function buildCardQuote(emotion) {
  const quotes = {
    joy: '有一点光，已经在今天开花。',
    anxiety: '不安也可以被温柔地放下。',
    sadness: '低落的时刻，也值得被轻轻保存。',
    tired: '辛苦的一天，先在这里停一停。',
    relieved: '松开的那一刻，也是一种抵达。',
    calm: '今天被安静地保存下来。',
  };
  return quotes[emotion] || quotes.calm;
}
