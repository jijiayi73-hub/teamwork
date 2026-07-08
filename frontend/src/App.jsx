import React, { useEffect, useMemo, useState } from 'react';
import {
  createDiary,
  createEntry,
  getDiary,
  getStatsOverview,
  getStoredUser,
  healthCheck,
  listDiaries,
} from './api/client';
import { sendChatMessage } from './api/chat';
import { getCurrentUser, logout, requireAuth, isAuthenticated } from './api/auth';
import LiquidMemoryBackground from './components/LiquidMemoryBackground';
import LoginPage from './components/LoginPage';

const DRAFT_KEY = 'mindful_memory_diary_draft';
const LOCAL_MEMORIES_KEY = 'mindful_memory_diary_memories';

export default function App() {
  const route = useHashRoute();
  const isMemoryRoute = route.name === 'garden' || route.name === 'detail';
  const [currentUser, setCurrentUser] = useState(getCurrentUser());

  // 监听认证状态变化
  useEffect(() => {
    const handleAuthChange = () => {
      setCurrentUser(getCurrentUser());
    };
    window.addEventListener('auth-change', handleAuthChange);
    return () => window.removeEventListener('auth-change', handleAuthChange);
  }, []);

  // 登录页面不需要背景和导航
  if (route.name === 'login') {
    return <LoginPage />;
  }

  // 受保护的路由需要认证
  const protectedRoutes = ['chat', 'diary', 'garden', 'detail'];
  if (protectedRoutes.includes(route.name)) {
    requireAuth();
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#10131e] font-body text-white">
      {isMemoryRoute ? <LiquidMemoryBackground /> : <DreamBackdrop />}
      <TopNav currentUser={currentUser} onAuthChange={() => setCurrentUser(getCurrentUser())} />
      {route.name === 'chat' && <ChatPage />}
      {route.name === 'diary' && <DiaryResultPage />}
      {route.name === 'garden' && <MemoryGardenPage />}
      {route.name === 'detail' && <MemoryDetailPage diaryId={route.id} />}
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
  if (hash.startsWith('#/about')) return { name: 'about' };
  return { name: 'home' };
}

function DreamBackdrop() {
  return (
    <>
      <div className="absolute inset-0 bg-night-garden" />
      <div className="absolute inset-0 bg-watercolor-mist" />
      <div className="particles" aria-hidden="true">
        {Array.from({ length: 34 }, (_, index) => (
          <span key={index} style={particleStyle(index)} />
        ))}
      </div>
    </>
  );
}

function TopNav({ currentUser, onAuthChange }) {
  const handleLogout = () => {
    logout();
    onAuthChange();
  };

  return (
    <nav className="relative z-10 flex items-center justify-between px-8 py-6 text-sm text-white/72 lg:px-14">
      <a className="font-display text-lg tracking-wide text-white" href="#/">
        Mindful Memory Diary
      </a>
      <div className="flex items-center gap-6 rounded-full border border-white/10 bg-white/[0.06] px-5 py-3 shadow-glow backdrop-blur-xl">
        <a className="transition hover:text-white" href="#/">
          Home
        </a>
        <a className="transition hover:text-white" href="#/memory-garden">
          Memory Garden
        </a>
        <a className="transition hover:text-white" href="#/about">
          About
        </a>
        {currentUser ? (
          <>
            <span className="text-white/40">|</span>
            <span className="transition hover:text-white">{currentUser.email}</span>
            <button
              className="transition hover:text-white"
              onClick={handleLogout}
              type="button"
            >
              登出
            </button>
          </>
        ) : (
          <>
            <span className="text-white/40">|</span>
            <a className="transition hover:text-white" href="#/login">
              登录
            </a>
          </>
        )}
      </div>
    </nav>
  );
}

function HomePage() {
  const memoryCount = getLocalMemoryCount();
  const gardenStatus =
    memoryCount > 0
      ? `Your garden has ${memoryCount} ${memoryCount === 1 ? 'memory' : 'memories'} blooming.`
      : '你的花园还很安静，从一次倾诉开始。';

  return (
    <>
      <section className="relative z-10 flex min-h-[calc(100vh-96px)] items-center justify-center px-5 pb-20 pt-6">
        <div className="w-full max-w-4xl rounded-[28px] border border-white/16 bg-white/[0.08] px-6 py-12 text-center shadow-glow backdrop-blur-2xl sm:px-10 lg:px-16">
          <p className="mb-4 text-sm uppercase tracking-[0.38em] text-[#c8e0ff]/80">Inner Garden</p>
          <h1 className="font-display text-5xl leading-tight text-white sm:text-6xl lg:text-7xl">
            Mindful Memory Diary
          </h1>
          <p className="mt-5 text-lg text-[#e6eefc]/90 sm:text-xl">把今天的情绪，种成一座记忆花园</p>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-8 text-white/68 sm:text-lg">
            Talk gently with AI, let your feelings settle into words, and keep each day as a quiet
            bloom in your memory garden.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a className="primary-action w-full sm:w-auto" href="#/ai-companion-chat">
              开始记录今天
            </a>
            <a className="secondary-action w-full sm:w-auto" href="#/memory-garden">
              进入 Memory Garden
            </a>
          </div>
        </div>
      </section>

      <p className="absolute bottom-6 left-1/2 z-10 w-full -translate-x-1/2 px-5 text-center text-sm text-white/56">
        {gardenStatus}
      </p>
    </>
  );
}

function ChatPage() {
  const [messages, setMessages] = useState([
    { content: '慢慢说，我在听。今天发生了什么？', role: 'assistant' },
  ]);
  const [text, setText] = useState('');
  const [note, setNote] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [imagePreview, setImagePreview] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversationMode] = useState('companion');

  async function handleSend() {
    const rawContent = text.trim();
    if (!rawContent || isSending) return;

    setIsSending(true);
    setNote('');
    setText('');

    // 添加用户消息到界面
    setMessages((current) => [
      ...current,
      { content: rawContent, role: 'user' },
    ]);

    try {
      const response = await sendChatMessage({
        conversation_id: conversationId,
        mode: conversationId ? null : conversationMode,
        content: rawContent,
        use_memory: false,
        anchor_diary_id: null,
      });

      // 保存 conversation_id 以继续对话
      if (response.data?.conversation?.id) {
        setConversationId(response.data.conversation.id);
      }

      // 添加 AI 回复到界面
      setMessages((current) => [
        ...current,
        {
          content: response.data?.assistant_message?.content || '我收到了你的消息，但似乎没能生成回复。请再试一次。',
          role: 'assistant',
        },
      ]);

      setNote('已为你轻轻整理好这一段。');

      // 保存 draft 用于日记生成（兼容现有流程）
      const draftData = {
        entry_id: response.data?.user_message?.id || `chat-${Date.now()}`,
        title: response.data?.conversation?.title || 'AI 对话记录',
        content: rawContent,
        raw_content: rawContent,
        image_preview: imagePreview,
        analysis: {
          primary_emotion: 'calm',
          summary: '来自 AI 对话的记录',
          suggestion: '你可以继续和 AI 聊天，或者将这段对话整理成日记。',
          emotion_score: 60,
          risk_level: 'low',
        },
        source: 'chat_api',
      };
      window.localStorage.setItem(DRAFT_KEY, JSON.stringify(draftData));
    } catch (error) {
      const errorDetail = error.message || (typeof error === 'string' ? error : JSON.stringify(error));
      setNote(`发送失败：${errorDetail}`);
      console.error('Chat API 调用失败:', error);

      // 移除用户消息（因为发送失败）
      setMessages((current) => current.filter((m) => m.content !== rawContent));
    } finally {
      setIsSending(false);
    }
  }

  function handleImageUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const imageData = reader.result;
      setImagePreview(imageData);
      setNote('图片已作为本地预览保存。');
    };
    reader.readAsDataURL(file);
  }

  function handleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setText((current) => `${current}${current ? ' ' : ''}今天有一些说不清的感受，我想先慢慢放在这里。`);
      setMessages((current) => [...current, { content: '没关系，语音现在先用本地文字替代。你可以继续补一点点，我会跟着你的节奏。' }]);
      setNote('当前浏览器不支持本地语音识别，已填入一段 mock 语音文本。');
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

  function handleGenerateDiary() {
    const rawContent = text.trim();
    if (rawContent && !window.localStorage.getItem(DRAFT_KEY)) {
      window.localStorage.setItem(DRAFT_KEY, JSON.stringify(buildLocalDraft(rawContent, imagePreview)));
    }

    if (!window.localStorage.getItem(DRAFT_KEY)) {
      setNote('先写下一点点，或者用语音留下一句话。');
      return;
    }
    window.location.hash = '#/diary-result';
  }

  return (
    <section className="relative z-10 flex min-h-[calc(100vh-96px)] items-center justify-center px-5 pb-12 pt-4 lg:px-14">
      {imagePreview && (
        <div
          aria-hidden="true"
          className="chat-photo-backdrop"
          style={{ backgroundImage: `url(${imagePreview})` }}
        />
      )}

      <div className="chat-stage">
        <div className="text-center">
          <p className="text-xs uppercase tracking-[0.34em] text-[#c8e0ff]/70">AI Companion Chat</p>
          <h1 className="mt-4 font-display text-4xl leading-tight text-white sm:text-5xl">今天想记录什么？</h1>
          <p className="mt-3 text-sm text-white/58">亦言亦思皆为序章</p>
        </div>

        <section className="chat-window">
          <div className="ai-notification-list">
            {messages.map((message, index) => (
              <div className="ai-notification" key={`${message.content}-${index}`}>
                {message.role !== 'user' && <span className="ai-notification-dot" />}
                <p>{message.content}</p>
              </div>
            ))}
          </div>

          {note && <p className="chat-note">{note}</p>}

          <div className="composer-shell">
            <label className="composer-icon-button" title="上传图片">
              <input accept="image/*" className="hidden" onChange={handleImageUpload} type="file" />
              <span aria-hidden="true">＋</span>
            </label>
            <textarea
              className="composer-input"
              onChange={(event) => setText(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              placeholder="慢慢说，我在听。今天发生了什么？"
              value={text}
            />
            <button
              aria-label={isListening ? '正在语音输入' : '语音输入'}
              className={`composer-icon-button ${isListening ? 'is-listening' : ''}`}
              onClick={handleVoiceInput}
              type="button"
            >
              <span aria-hidden="true">⌁</span>
            </button>
            <button
              aria-label="发送"
              className="composer-send-button"
              disabled={isSending || !text.trim()}
              onClick={handleSend}
              type="button"
            >
              <span aria-hidden="true">{isSending ? '…' : '↑'}</span>
            </button>
          </div>

          <button className="generate-link" onClick={handleGenerateDiary} type="button">
            我说完了，生成日记
          </button>
        </section>
      </div>
    </section>
  );
}

function DiaryResultPage() {
  const draft = useMemo(() => readJson(DRAFT_KEY), []);
  const [title, setTitle] = useState(draft?.title || '');
  const [content, setContent] = useState(draft?.content || '');
  const [status, setStatus] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    if (!draft?.entry_id) {
      setStatus('缺少 entry_id。请先从 AI Companion Chat 发送文字生成草稿。');
      return;
    }
    setIsSaving(true);
    setStatus('正在通过 POST /api/v1/diaries 保存日记...');

    try {
      let entryId = Number(draft.entry_id);
      if (!Number.isInteger(entryId) || entryId <= 0) {
        const entryResponse = await createEntry(draft.raw_content || content);
        entryId = entryResponse.data.id;
        window.localStorage.setItem(
          DRAFT_KEY,
          JSON.stringify({
            ...draft,
            entry_id: entryId,
            title,
            content,
            analysis: entryResponse.data.analysis || draft.analysis,
          }),
        );
      }

      const response = await createDiary({
        entry_id: entryId,
        title,
        content,
        diary_date: new Date().toISOString().slice(0, 10),
        is_favorite: false,
      });
      rememberLocalDiary(response.data);
      setStatus('保存成功，已写入真实后端 /api/v1/diaries。');
      window.location.hash = '#/memory-garden';
    } catch (error) {
      const errorDetail = error.message || (typeof error === 'string' ? error : JSON.stringify(error));
      console.error('保存日记失败:', error);
      const fallbackDiary = rememberLocalDiary(buildSavedLocalDiary(draft, title, content));
      setStatus(`已保存到本地 Memory Garden，后端暂时不可用：${errorDetail}`);
      window.location.hash = `#/memory-garden/${fallbackDiary.id}`;
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <PageShell
      eyebrow="Diary Result"
      title="把倾诉整理成日记"
      subtitle="这个页面使用 /api/v1/entries 返回的草稿；保存按钮已接 /api/v1/diaries。"
    >
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <section className="panel space-y-4">
          {!draft ? (
            <EmptyState
              actionHref="#/ai-companion-chat"
              actionText="回到对话页"
              text="还没有日记草稿。请先发送一段文字，让后端生成 entry 和 draft diary。"
            />
          ) : (
            <>
              <input className="input-surface text-xl font-semibold" onChange={(event) => setTitle(event.target.value)} value={title} />
              <textarea className="input-surface min-h-72 resize-none leading-8" onChange={(event) => setContent(event.target.value)} value={content} />
              <button className="primary-action" disabled={isSaving} onClick={handleSave} type="button">
                {isSaving ? '保存中...' : '保存到 Memory Garden'}
              </button>
            </>
          )}
        </section>
        <aside className="panel space-y-4">
          <p className="text-sm text-white/64">今日情绪</p>
          <p className="font-display text-4xl text-white">{draft?.analysis?.primary_emotion || 'calm'}</p>
          <p className="text-sm leading-7 text-white/64">{draft?.analysis?.summary || '等待后端分析结果。'}</p>
          <StatusText>{status || '保存会创建真实 diary；记忆卡片 API 尚未实现。'}</StatusText>
        </aside>
      </div>
    </PageShell>
  );
}

function buildCompanionReply(rawContent, analysis) {
  if (analysis?.summary && analysis?.suggestion) {
    return `${analysis.summary} ${analysis.suggestion}`;
  }

  if (rawContent.length < 18) {
    return '我听见了。哪怕只是很短的一句，也已经是一颗小小的种子。';
  }

  return '我把你说的这些先放在心里了。它们不需要立刻变得整齐，慢慢来就好。';
}

function buildLocalDraft(rawContent, imagePreview) {
  return {
    entry_id: `local-${Date.now()}`,
    title: '亦言亦思皆为序章',
    content: `今天，我把一些还没有完全整理好的感受留在这里。\n\n${rawContent}\n\n也许它们还不是答案，但它们已经让我更靠近此刻的自己一点。`,
    analysis: {
      primary_emotion: 'calm',
      summary: '这是一段本地 mock 的温柔整理，用来保证前端演示流程可以继续。',
      suggestion: '先不用急着判断这些感受，只要把它们稳稳放下。',
      emotion_score: 58,
      risk_level: 'low',
    },
    raw_content: rawContent,
    image_preview: imagePreview,
    source: 'local_mock',
  };
}

function MemoryGardenPage() {
  const [diaries, setDiaries] = useState([]);
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState('正在读取 /api/v1/diaries...');

  async function loadGarden() {
    setStatus('正在读取 /api/v1/diaries 和 /api/v1/stats/overview...');
    try {
      const [diaryResponse, statsResponse] = await Promise.all([listDiaries(), getStatsOverview()]);
      const mergedDiaries = mergeLocalDiaries(diaryResponse.data || []);
      setDiaries(mergedDiaries);
      setStats({ ...(statsResponse.data || {}), total_diaries: mergedDiaries.length });
      setStatus('Memory Garden 已接入真实 diary 列表接口。');
    } catch (error) {
      const localDiaries = readLocalDiaries();
      setDiaries(localDiaries);
      setStats({ total_diaries: localDiaries.length });
      setStatus(`Memory Garden 已显示本地保存的日记，后端读取失败：${error.message}`);
    }
  }

  useEffect(() => {
    loadGarden();
  }, []);

  return (
    <section className="memory-garden-page">
      <div className="memory-garden-shell">
        <header className="memory-garden-hero">
          <p className="memory-garden-eyebrow">Memory Garden</p>
          <h1 className="memory-garden-title">你的记忆花园</h1>

          <div className="memory-garden-actions" aria-label="Memory Garden actions">
            <a
              aria-label="写下今天"
              className="memory-garden-icon-action"
              href="#/ai-companion-chat"
              title="写下今天"
            >
              <WriteIcon />
            </a>
            <button
              aria-label="刷新花园"
              className="memory-garden-icon-action"
              onClick={loadGarden}
              title="刷新花园"
              type="button"
            >
              <RefreshIcon />
            </button>
          </div>

          <p className="memory-garden-total">
            <span>Total Diaries</span>
            <span aria-hidden="true">·</span>
            <strong>{stats?.total_diaries ?? diaries.length}</strong>
          </p>
        </header>

        <section className="memory-garden-list" aria-label="Memory Garden diary list">
          {diaries.length === 0 ? (
            <div className="memory-garden-empty">
              <p>后端里还没有保存的日记。</p>
              <a className="memory-garden-empty-action" href="#/ai-companion-chat">
                开始记录今天
              </a>
            </div>
          ) : (
            <div className="memory-garden-card-grid">
              {diaries.map((diary) => (
                <a className="memory-card" href={`#/memory-garden/${diary.id}`} key={diary.id}>
                  <p className="text-sm text-white/52">{diary.diary_date}</p>
                  <h3 className="mt-3 font-display text-2xl text-white">{diary.title}</h3>
                  <p className="memory-card-excerpt mt-4 text-sm leading-7 text-white/64">
                    {diary.content}
                  </p>
                  <span className="mt-5 inline-flex rounded-full bg-white/10 px-3 py-1 text-xs text-white/72">
                    {diary.analysis?.primary_emotion || 'memory'}
                  </span>
                </a>
              ))}
            </div>
          )}
        </section>

        <p className="memory-garden-status">{status}</p>
      </div>
    </section>
  );
}

function WriteIcon() {
  return (
    <svg aria-hidden="true" fill="none" viewBox="0 0 24 24">
      <path d="M4.75 19.25l4.1-1.05 9.75-9.75a2.12 2.12 0 0 0-3-3L5.85 15.2l-1.1 4.05Z" />
      <path d="m14.25 6.75 3 3" />
      <path d="M8.5 19.25h10.75" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg aria-hidden="true" fill="none" viewBox="0 0 24 24">
      <path d="M18.75 8.25A7.25 7.25 0 0 0 6.2 6.1L4.75 7.75" />
      <path d="M4.75 4.25v3.5h3.5" />
      <path d="M5.25 15.75a7.25 7.25 0 0 0 12.55 2.15l1.45-1.65" />
      <path d="M19.25 19.75v-3.5h-3.5" />
    </svg>
  );
}

function MemoryDetailPage({ diaryId }) {
  const [diary, setDiary] = useState(null);
  const [status, setStatus] = useState('正在读取 /api/v1/diaries/{id}...');
  const [pastSelfReply, setPastSelfReply] = useState('');

  useEffect(() => {
    async function loadDiary() {
      try {
        const response = await getDiary(diaryId);
        setDiary(response.data);
        setStatus('详情已接入真实后端 /api/v1/diaries/{id}。');
      } catch (error) {
        const localDiary = findLocalDiary(diaryId);
        if (localDiary) {
          setDiary(localDiary);
          setStatus(`详情已显示本地保存的日记，后端读取失败：${error.message}`);
        } else {
          setStatus(`读取失败：${error.message}`);
        }
      }
    }
    loadDiary();
  }, [diaryId]);

  function handlePastSelfChat() {
    setPastSelfReply('那天的我想说：谢谢你回来看我。那一刻不一定完美，但它已经被好好保存下来了。');
    setStatus('Past Self Chat 当前使用本地 mock；后端缺少 /api/v1/memories/{id}/past-self-chat。');
  }

  return (
    <PageShell
      eyebrow="Memory Detail"
      title={diary?.title || '记忆详情'}
      subtitle="详情读取真实 diary；过去的我对话接口尚未实现，暂用本地 mock。"
    >
      {!diary ? (
        <EmptyState actionHref="#/memory-garden" actionText="返回 Memory Garden" text={status} />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <article className="panel">
            <p className="text-sm text-white/52">{diary.diary_date}</p>
            <p className="mt-6 whitespace-pre-wrap text-base leading-8 text-white/76">{diary.content}</p>
          </article>
          <aside className="panel space-y-5">
            <p className="text-sm text-white/64">Emotion</p>
            <p className="font-display text-4xl">{diary.analysis?.primary_emotion}</p>
            <p className="text-sm leading-7 text-white/64">{diary.analysis?.suggestion}</p>
            <button className="primary-action" onClick={handlePastSelfChat} type="button">
              和那天的我聊聊
            </button>
            {pastSelfReply && <div className="chat-bubble chat-bubble-ai">{pastSelfReply}</div>}
            <a className="secondary-action inline-flex" href="#/memory-garden">
              返回 Memory Garden
            </a>
          </aside>
        </div>
      )}
      <StatusText>{status}</StatusText>
    </PageShell>
  );
}

function AboutPage() {
  const [status, setStatus] = useState('');
  const currentUser = getCurrentUser();

  async function handleHealthCheck() {
    setStatus('正在调用 GET /api/v1/health...');
    try {
      const response = await healthCheck();
      setStatus(`后端健康检查成功：${response.status || response.data?.status || 'ok'}`);
    } catch (error) {
      setStatus(`后端健康检查失败：${error.message}`);
    }
  }

  return (
    <PageShell
      eyebrow="About"
      title="接口对接状态"
      subtitle="这里用于演示当前按钮能接入哪些真实后端 API，以及哪些能力仍是待实现接口。"
    >
      <section className="panel space-y-5">
        <p className="text-white/70">当前用户：{currentUser?.email || '尚未登录'}</p>
        <button className="primary-action" onClick={handleHealthCheck} type="button">
          检查后端健康状态
        </button>
        <StatusText>{status || '可用 API：/auth、/entries、/diaries、/stats、/admin。'}</StatusText>
      </section>
    </PageShell>
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
  return (
    <p className="mt-5 rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm leading-6 text-white/64">
      {children}
    </p>
  );
}

function EmptyState({ text, actionHref, actionText }) {
  return (
    <div className="panel flex min-h-64 flex-col items-center justify-center text-center">
      <p className="max-w-xl text-white/64">{text}</p>
      <a className="primary-action mt-6" href={actionHref}>
        {actionText}
      </a>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="panel">
      <p className="text-xs uppercase tracking-[0.24em] text-white/42">{label}</p>
      <p className="mt-3 font-display text-3xl text-white">{value}</p>
    </div>
  );
}

function getLocalMemoryCount() {
  const memories = readJson(LOCAL_MEMORIES_KEY);
  return Array.isArray(memories) ? memories.length : 0;
}

function rememberLocalDiary(diary) {
  const memories = readJson(LOCAL_MEMORIES_KEY);
  const currentMemories = normalizeLocalDiaries(Array.isArray(memories) ? memories : []);
  const diaryKey = getDiaryDedupeKey(diary);
  const nextMemories = normalizeLocalDiaries([
    diary,
    ...currentMemories.filter((memory) => getDiaryDedupeKey(memory) !== diaryKey),
  ]);
  window.localStorage.setItem(LOCAL_MEMORIES_KEY, JSON.stringify(nextMemories));
  return diary;
}

function buildSavedLocalDiary(draft, title, content) {
  const now = new Date().toISOString();
  const stableId = getLocalDiaryId(draft, title, content);
  return {
    id: stableId,
    entry_id: draft?.entry_id || `local-entry-${Date.now()}`,
    analysis_id: draft?.analysis?.id || `local-analysis-${Date.now()}`,
    title,
    content,
    diary_date: now.slice(0, 10),
    is_favorite: false,
    visibility: 'private',
    created_at: now,
    updated_at: now,
    analysis: draft?.analysis || {
      primary_emotion: 'memory',
      suggestion: '',
      summary: '',
    },
  };
}

function readLocalDiaries() {
  const memories = readJson(LOCAL_MEMORIES_KEY);
  const normalizedMemories = normalizeLocalDiaries(Array.isArray(memories) ? memories : []);
  if (Array.isArray(memories) && normalizedMemories.length !== memories.length) {
    window.localStorage.setItem(LOCAL_MEMORIES_KEY, JSON.stringify(normalizedMemories));
  }
  return normalizedMemories;
}

function mergeLocalDiaries(diaries) {
  const remoteIds = new Set(diaries.map((diary) => String(diary.id)));
  const localOnly = readLocalDiaries().filter((diary) => !remoteIds.has(String(diary.id)));
  return [...localOnly, ...diaries];
}

function findLocalDiary(diaryId) {
  return readLocalDiaries().find((diary) => String(diary.id) === String(diaryId)) || null;
}

function getLocalDiaryId(draft, title, content) {
  if (draft?.saved_diary_id) return draft.saved_diary_id;
  if (draft?.entry_id) return `local-${draft.entry_id}`;
  return `local-${stableMemoryKey(title, new Date().toISOString().slice(0, 10), content)}`;
}

function getDiaryDedupeKey(diary) {
  if (diary?.entry_id) return `entry:${diary.entry_id}`;
  return `content:${stableMemoryKey(diary?.title, diary?.diary_date, diary?.content)}`;
}

function stableMemoryKey(title, diaryDate, content) {
  return [title || '', diaryDate || '', content || ''].join('|').trim();
}

function normalizeLocalDiaries(diaries) {
  const seen = new Set();
  return diaries.filter((diary) => {
    const key = getDiaryDedupeKey(diary);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
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

  return {
    left: `${left}%`,
    top: `${top}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
  };
}

