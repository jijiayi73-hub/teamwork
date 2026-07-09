import React, { Suspense, lazy, useEffect, useMemo, useRef, useState } from 'react';
import {
  clearLogs,
  createDiary,
  createEntry,
  createMemory,
  deleteMemory,
  deleteUser,
  generateImage,
  getAdminStats,
  getLogEntries,
  getLogStats,
  getMemory,
  getStatsOverview,
  getUser,
  healthCheck,
  listMemories,
  listUsers,
  pastSelfChat,
  requestPasswordReset,
  updateUser,
  verifyResetToken,
  confirmPasswordReset,
  uploadImage,
} from './api/client';
import { sendChatMessage } from './api/chat';
import { getCurrentUser, logout, requireAuth } from './api/auth';
import LiquidMemoryBackground from './components/LiquidMemoryBackground';
import LoginPage from './components/LoginPage';

const ParticleWaveHero = lazy(() => import('./components/ParticleWaveHero'));

const DRAFT_KEY = 'mindful_memory_diary_draft';
const EMOTIONS = ['calm', 'joy', 'sadness', 'anxiety', 'tired', 'neutral'];
// 情绪到颜色的固定映射（一个情绪对应一个颜色）
const EMOTION_COLOR_MAP = {
  calm: '#8fb8ff',
  joy: '#b8e6d0',
  sadness: '#ffd6a5',
  anxiety: '#f5b6d3',
  tired: '#c8b6ff',
  neutral: '#d8dee9',
};
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
  if (route.name === 'password-reset') return <PasswordResetPage token={route.token} />;
  if (['chat', 'diary', 'garden', 'detail', 'admin', 'monthly-report'].includes(route.name) && !requireAuth()) {
    return <LoginPage />;
  }

  // 管理员后台路由处理
  if (route.name === 'admin') {
    const adminPage = route.page || 'dashboard';
    if (adminPage === 'dashboard') return <AdminBackendLayout currentPage="dashboard"><AdminDashboardPage /></AdminBackendLayout>;
    if (adminPage === 'users') return <AdminBackendLayout currentPage="users"><UserManagementPage /></AdminBackendLayout>;
    if (adminPage === 'logs') return <AdminBackendLayout currentPage="logs"><LogViewerPage /></AdminBackendLayout>;
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#10131e] font-body text-white">
      {isMemoryRoute ? <LiquidMemoryBackground /> : <DreamBackdrop />}
      <TopNav currentUser={currentUser} onAuthChange={() => setCurrentUser(getCurrentUser())} />
      {route.name === 'chat' && <ChatPage />}
      {route.name === 'diary' && <DiaryResultPage />}
      {route.name === 'garden' && <MemoryGardenPage />}
      {route.name === 'detail' && <MemoryDetailPage memoryId={route.id} />}
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
  if (hash.startsWith('#/password-reset')) return { name: 'password-reset', token: new URLSearchParams(hash.split('?')[1]).get('token') };
  if (hash.startsWith('#/ai-companion-chat')) return { name: 'chat' };
  if (hash.startsWith('#/diary-result')) return { name: 'diary' };
  if (hash.startsWith('#/memory-garden/')) return { name: 'detail', id: hash.split('/').pop() };
  if (hash.startsWith('#/memory-garden')) return { name: 'garden' };
  if (hash.startsWith('#/admin')) {
    const parts = hash.split('/');
    const subRoute = parts[2] || 'dashboard'; // 默认 dashboard
    if (parts.length > 3) {
      return { name: 'admin', page: subRoute, id: parts[3] };
    }
    return { name: 'admin', page: subRoute };
  }
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
    <nav className="relative z-20 flex items-center justify-between px-8 py-6 text-sm text-white/72 lg:px-14">
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
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  async function handleSend() {
    const rawContent = text.trim();
    if (!rawContent || isSending) return;
    const userMessage = { content: rawContent, role: 'user' };
    const optimisticMessages = [...messages, userMessage];
    setMessages(optimisticMessages);
    setText('');
    setIsSending(true);
    setIsAiTyping(true);
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
    } catch (error) {
      setMessages(optimisticMessages);
      setNote(`发送失败：${error.message}。用户消息已保留，可以重试或生成草稿。`);
    } finally {
      setIsSending(false);
      setIsAiTyping(false);
    }
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

  // 自动滚动到底部：当 messages 更新或 AI 正在输入时
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isAiTyping]);

  async function handleImageUpload(file) {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setNote('请选择图片文件');
      return;
    }
    if (file.size > 12 * 1024 * 1024) {
      setNote('图片大小不能超过 12MB');
      return;
    }
    setIsUploading(true);
    setNote('正在上传图片...');
    try {
      const response = await uploadImage(file);
      const imageUrl = response.data?.url || '';
      setUploadedImage(imageUrl);
      setNote('图片上传成功！已设置为背景。再次上传会替换为新的图片。');
    } catch (error) {
      setNote(`图片上传失败：${error.message}`);
    } finally {
      setIsUploading(false);
    }
  }

  function clearUploadedImage() {
    setUploadedImage(null);
    setImagePreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
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
        cover_image_url: uploadedImage || '',
        analysis: entry.analysis,
        source: 'chat_api',
        uploaded_image_url: uploadedImage || '',
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
          backgroundOpacity={uploadedImage ? 0.85 : 0.62}
          className="chat-particle-wave"
          fit="cover"
          imageUrl={uploadedImage || undefined}
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
          <p className="mt-3 text-sm text-white/58">可以上传图片作为背景，也可以直接开始对话。</p>
        </div>
        <section className="chat-window">
          <div className="ai-notification-list">
            {messages.map((message, index) => (
              <div className={`ai-notification ${message.role === 'user' ? 'ai-notification-user' : ''}`} key={`${message.role}-${index}-${message.content}`}>
                {message.role !== 'user' && <span className="ai-notification-dot" />}
                <div>
                  <p>{message.content}</p>
                </div>
              </div>
            ))}
            {isAiTyping && (
              <div className="ai-thinking-indicator">
                <div className="ai-thinking-dot" />
                <div className="ai-thinking-dot" />
                <div className="ai-thinking-dot" />
              </div>
            )}
            {/* 滚动锚点：用于自动滚动到底部 */}
            <div ref={messagesEndRef} />
          </div>
          {note && <p className="chat-note">{note}</p>}
          <input
            ref={fileInputRef}
            accept="image/*"
            className="hidden"
            onChange={(e) => handleImageUpload(e.target.files?.[0])}
            type="file"
          />
          <div className="composer-shell">
            <button
              aria-label="上传图片"
              className="composer-icon-button"
              data-tooltip="上传图片作为背景和本日封面"
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
              type="button"
            >
              <span aria-hidden="true">{isUploading ? '…' : '📷'}</span>
            </button>
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
              data-tooltip={isListening ? '正在录音...' : '语音输入'}
              onClick={handleVoiceInput}
              type="button"
            >
              <span aria-hidden="true">♪</span>
            </button>
            <button
              aria-label="发送"
              className="composer-send-button"
              data-tooltip="发送消息"
              disabled={isSending || !text.trim()}
              onClick={handleSend}
              type="button"
            >
              <span aria-hidden="true">{isSending ? '…' : '→'}</span>
            </button>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button className="generate-link" onClick={handleGenerateDiary} type="button">我说完了，生成日记</button>
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
  // 情绪和颜色由 AI 分析固定，不可编辑
  const emotion = draft?.analysis?.primary_emotion || 'calm';
  const emotionColor = getEmotionColor(emotion);
  const [coverImageUrl, setCoverImageUrl] = useState(draft?.cover_image_url || '');
  const [keywords, setKeywords] = useState(extractKeywords(draft));
  const [status, setStatus] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [existingMemoryId, setExistingMemoryId] = useState(null);
  const [checkingExisting, setCheckingExisting] = useState(false);
  const [isGeneratingCover, setIsGeneratingCover] = useState(false);
  const [coverGenerationStatus, setCoverGenerationStatus] = useState('');
  const coverGenerationAttemptedRef = useRef(false);

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

  // 自动生成封面预览
  useEffect(() => {
    async function generateCoverPreview() {
      if (!draft || coverGenerationAttemptedRef.current) return;
      // 如果用户上传了图片，直接使用，不生成 AI 封面
      if (draft.uploaded_image_url || draft.cover_image_url || coverImageUrl) {
        if (draft.uploaded_image_url && !coverImageUrl) {
          setCoverImageUrl(draft.uploaded_image_url);
        }
        return;
      }
      // 如果正在保存或检查已有卡片，不生成
      if (isSaving || checkingExisting) return;

      coverGenerationAttemptedRef.current = true;
      setIsGeneratingCover(true);
      setCoverGenerationStatus('正在根据对话内容生成 AI 封面...');
      try {
        const coverPrompt = buildWatercolorPrompt({ ...draft, title, content, emotion });
        const imageResponse = await generateImage({
          prompt: coverPrompt,
          emotion,
          provider: 'volces',  // 使用火山引擎豆包文生图（国内 API 更稳定）
          style: 'natural',
          size: '1024x1024',
          quality: 'standard',
          model: 'dall-e-3',
        });
        const generatedUrl = imageResponse.data?.image_url || '';
        setCoverImageUrl(generatedUrl);
        setCoverGenerationStatus(generatedUrl ? '✨ 封面生成成功！' : '⚠️ 封面生成未返回图片');
      } catch (imageError) {
        setCoverGenerationStatus(`封面生成失败：${imageError.message}`);
      } finally {
        setIsGeneratingCover(false);
      }
    }
    // 延迟一点执行，让页面先渲染
    const timer = setTimeout(() => generateCoverPreview(), 500);
    return () => clearTimeout(timer);
  }, [draft, title, content, emotion, coverImageUrl, isSaving, checkingExisting]);

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
    // 如果用户上传了图片，使用上传的图片，否则生成 AI 封面
    const hasUploadedImage = draft.uploaded_image_url || coverImageUrl;
    setStatus(hasUploadedImage ? '正在保存 diary，使用上传的图片作为封面...' : '正在保存 diary，并根据对话生成封面...');
    try {
      const diaryResponse = await createDiary({
        entry_id: draft.entry_id,
        title,
        content,
        diary_date: new Date().toISOString().slice(0, 10),
        is_favorite: false,
      });
      const coverPrompt = buildWatercolorPrompt({ ...draft, title, content, emotion });
      let generatedCoverImageUrl = coverImageUrl || draft.uploaded_image_url || '';
      // 如果已有封面图片（用户上传或已生成），不重新生成
      if (!generatedCoverImageUrl) {
        try {
          const imageResponse = await generateImage({
            prompt: coverPrompt,
            emotion,
            provider: 'volces',  // 使用火山引擎豆包文生图（国内 API 更稳定）
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
    <PageShell eyebrow="Diary Result" title="把倾诉整理成日记" subtitle="如果上传了图片，将直接作为卡片封面；否则 AI 会根据对话自动生成封面。">
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
          {/* 情绪由 AI 分析固定显示 */}
          <ControlLabel label="AI 分析的情绪">
            <div className="emotion-display">
              <span className="emotion-badge" style={{ backgroundColor: emotionColor }}>
                {getEmotionLabel(emotion)}
              </span>
            </div>
          </ControlLabel>
          {/* 封面生成状态和预览 */}
          <div className="space-y-3">
            <p className="text-sm text-white/60">AI 封面生成</p>
            {isGeneratingCover && (
              <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                <div className="ai-thinking-indicator" style={{ padding: '0' }}>
                  <div className="ai-thinking-dot" />
                  <div className="ai-thinking-dot" />
                  <div className="ai-thinking-dot" />
                </div>
                <p className="text-sm text-white/80">{coverGenerationStatus || '生成中...'}</p>
              </div>
            )}
            {coverImageUrl && !isGeneratingCover && (
              <div className="memory-cover-preview">
                <p className="text-sm text-white/52 mb-2">封面预览</p>
                <div className="memory-cover" style={{ backgroundImage: `url(${assetUrl(coverImageUrl)})` }} />
              </div>
            )}
            {!coverImageUrl && !isGeneratingCover && coverGenerationStatus && (
              <p className="text-sm text-white/52">{coverGenerationStatus}</p>
            )}
          </div>
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
                <a
                  key={memory.id}
                  className="memory-card"
                  href={`#/memory-garden/${memory.id}`}
                  style={{ borderColor: memory.emotion_color }}
                >
                  {memory.cover_image_url && (
                    <div className="memory-cover" style={{ backgroundImage: `url(${assetUrl(memory.cover_image_url)})` }} />
                  )}
                  <p className="memory-title">{memory.title}</p>
                  <p className="memory-date">{memory.diary_date}</p>
                </a>
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

// ============================================================================
// ADMIN BACKEND COMPONENTS
// ============================================================================

function AdminBackendLayout({ currentPage, children }) {
  const menuItems = [
    { id: 'dashboard', label: '系统统计', href: '#/admin/dashboard' },
    { id: 'users', label: '用户管理', href: '#/admin/users' },
    { id: 'logs', label: '运行日志', href: '#/admin/logs' },
  ];

  return (
    <div className="flex min-h-[calc(100vh-96px)]">
      <aside className="w-56 flex-shrink-0 border-r border-white/10 bg-white/[0.04] p-6">
        <h2 className="font-display text-xl text-white mb-6">管理后台</h2>
        <nav className="flex flex-col gap-2">
          {menuItems.map(item => (
            <a
              key={item.id}
              href={item.href}
              className={`admin-nav-item ${currentPage === item.id ? 'active' : ''}`}
            >
              {item.label}
            </a>
          ))}
        </nav>
      </aside>
      <main className="flex-1 px-8 py-6 overflow-auto">
        {children}
      </main>
    </div>
  );
}

function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({ status: '', role: '' });

  useEffect(() => {
    loadUsers();
  }, []);

  async function loadUsers() {
    setLoading(true);
    try {
      const response = await listUsers();
      setUsers(response.data || []);
      setError('');
    } catch (err) {
      setError(`加载用户列表失败：${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function handleEdit(user) {
    setEditingUser(user);
    setEditForm({ status: user.status, role: user.role });
  }

  async function handleSave() {
    if (!editingUser) return;
    try {
      await updateUser(editingUser.id, editForm);
      setEditingUser(null);
      loadUsers();
    } catch (err) {
      setError(`保存失败：${err.message}`);
    }
  }

  async function handleDelete(userId) {
    if (!confirm('确定要删除此用户吗？')) return;
    try {
      await deleteUser(userId);
      loadUsers();
    } catch (err) {
      setError(`删除失败：${err.message}`);
    }
  }

  if (loading) return <div className="text-white/72">加载中...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-3xl text-white">用户管理</h1>
        <button className="secondary-action text-sm px-4 py-2" onClick={loadUsers}>
          刷新
        </button>
      </div>

      {error && <StatusText>{error}</StatusText>}

      <div className="panel overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left p-4 text-xs uppercase tracking-wider text-white/52">ID</th>
              <th className="text-left p-4 text-xs uppercase tracking-wider text-white/52">用户名</th>
              <th className="text-left p-4 text-xs uppercase tracking-wider text-white/52">邮箱</th>
              <th className="text-left p-4 text-xs uppercase tracking-wider text-white/52">角色</th>
              <th className="text-left p-4 text-xs uppercase tracking-wider text-white/52">状态</th>
              <th className="text-left p-4 text-xs uppercase tracking-wider text-white/52">注册时间</th>
              <th className="text-left p-4 text-xs uppercase tracking-wider text-white/52">操作</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id} className="border-b border-white/6 hover:bg-white/[0.02]">
                <td className="p-4 text-white/82">{user.id}</td>
                <td className="p-4 text-white/82">{user.username}</td>
                <td className="p-4 text-white/82">{user.email}</td>
                <td className="p-4">
                  <span className={`inline-block px-2 py-1 rounded-full text-xs ${user.role === 'admin' ? 'bg-purple-500/30 text-purple-200' : 'bg-blue-500/30 text-blue-200'}`}>
                    {user.role}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`inline-block px-2 py-1 rounded-full text-xs ${
                    user.status === 'active' ? 'bg-green-500/30 text-green-200' :
                    user.status === 'suspended' ? 'bg-yellow-500/30 text-yellow-200' :
                    'bg-red-500/30 text-red-200'
                  }`}>
                    {user.status}
                  </span>
                </td>
                <td className="p-4 text-white/64 text-sm">
                  {new Date(user.created_at).toLocaleDateString('zh-CN')}
                </td>
                <td className="p-4">
                  <button
                    className="text-white/64 hover:text-white text-sm mr-3"
                    onClick={() => handleEdit(user)}
                  >
                    编辑
                  </button>
                  <button
                    className="text-white/64 hover:text-red-300 text-sm"
                    onClick={() => handleDelete(user.id)}
                  >
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editingUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="panel w-full max-w-md p-6">
            <h2 className="font-display text-xl text-white mb-4">编辑用户</h2>
            <p className="text-white/64 text-sm mb-4">用户: {editingUser.username}</p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/64 mb-2">角色</label>
                <select
                  className="input-surface"
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                >
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-white/64 mb-2">状态</label>
                <select
                  className="input-surface"
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                >
                  <option value="active">active</option>
                  <option value="suspended">suspended</option>
                  <option value="deleted">deleted</option>
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button className="primary-action flex-1" onClick={handleSave}>
                保存
              </button>
              <button className="secondary-action flex-1" onClick={() => setEditingUser(null)}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function LogViewerPage() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [levelFilter, setLevelFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    loadLogs();
    loadStats();
  }, [levelFilter]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadLogs();
        loadStats();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, levelFilter]);

  async function loadLogs() {
    setLoading(true);
    try {
      const response = await getLogEntries(levelFilter ? { level: levelFilter, limit: 100 } : { limit: 100 });
      setLogs(response.data?.logs || []);
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoading(false);
    }
  }

  async function loadStats() {
    try {
      const response = await getLogStats();
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  }

  async function handleClearLogs() {
    if (!confirm('确定要清空所有日志吗？')) return;
    try {
      await clearLogs();
      loadLogs();
      loadStats();
    } catch (err) {
      alert(`清空失败：${err.message}`);
    }
  }

  function getLevelColor(level) {
    const levelLower = (level || '').toLowerCase();
    if (levelLower === 'info') return 'border-blue-400 bg-blue-400/10';
    if (levelLower === 'warning') return 'border-yellow-400 bg-yellow-400/10';
    if (levelLower === 'error' || levelLower === 'critical') return 'border-red-400 bg-red-400/10';
    if (levelLower === 'debug') return 'border-gray-400 bg-gray-400/10';
    return 'border-white/20 bg-white/5';
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-3xl text-white">运行日志</h1>
        <div className="flex gap-3">
          <button
            className={`secondary-action text-sm px-4 py-2 ${autoRefresh ? 'bg-green-500/30' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '停止刷新' : '自动刷新'}
          </button>
          <button className="secondary-action text-sm px-4 py-2" onClick={loadLogs}>
            刷新
          </button>
          <button className="secondary-action text-sm px-4 py-2 text-red-300" onClick={handleClearLogs}>
            清空
          </button>
        </div>
      </div>

      {stats && (
        <div className="flex gap-4 mb-6 text-sm text-white/64">
          <span>Info: {stats.info || 0}</span>
          <span>Warning: {stats.warning || 0}</span>
          <span>Error: {stats.error || 0}</span>
        </div>
      )}

      <div className="flex gap-3 mb-4">
        <select
          className="input-surface w-32"
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
        >
          <option value="">全部级别</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="debug">Debug</option>
        </select>
      </div>

      <div className="panel overflow-auto max-h-[600px]">
        {loading && logs.length === 0 ? (
          <div className="text-center text-white/64 py-8">加载中...</div>
        ) : logs.length === 0 ? (
          <div className="text-center text-white/64 py-8">暂无日志</div>
        ) : (
          <div className="font-mono text-sm">
            {logs.map((log, index) => (
              <div
                key={index}
                className={`log-entry border-l-3 pl-3 py-2 hover:bg-white/[0.02] ${getLevelColor(log.level)}`}
              >
                <span className="text-white/52">{log.timestamp?.replace('T', ' ')?.slice(0, 19)}</span>
                <span className="ml-3 px-2 py-0.5 rounded text-xs uppercase">{log.level}</span>
                {log.url && <span className="ml-3 text-white/64">[{log.url}]</span>}
                {log.message && <span className="ml-3 text-white/82">{log.message}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AdminDashboardPage() {
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);

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

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(async () => {
        try {
          const response = await getAdminStats();
          setStats(response.data);
          setStatus('');
        } catch (error) {
          setStatus(`统计数据暂时没有加载成功：${error.message}`);
        }
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const maxDaily = Math.max(1, ...(stats?.daily_new_memory_cards || []).map((item) => item.count));
  const maxEmotion = Math.max(1, ...(stats?.emotion_distribution || []).map((item) => item.count));
  return (
    <PageShell eyebrow="Admin Dashboard" title="系统统计与服务状态" subtitle="管理员只查看聚合统计，不展示用户私密日记正文。">
      <div className="flex items-center justify-between mb-4">
        <button
          className="secondary-action text-sm px-4 py-2"
          onClick={() => (window.location.hash = '#/')}
          type="button"
        >
          用户视图
        </button>
        <button
          className={`secondary-action text-sm px-4 py-2 ${autoRefresh ? 'bg-green-500/30' : ''}`}
          onClick={() => setAutoRefresh(!autoRefresh)}
          type="button"
        >
          {autoRefresh ? '停止刷新' : '自动刷新'}
        </button>
      </div>
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
  const [activeSection, setActiveSection] = useState('quickStart');
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

  const guideContent = {
    quickStart: {
      title: '快速开始',
      content: [
        {
          type: 'heading',
          level: 3,
          text: '注册与登录'
        },
        {
          type: 'list',
          items: [
            '点击右上角「登录」按钮进入登录页面',
            '选择「注册新账户」，填写用户名、邮箱和密码',
            '注册成功后自动登录，开始使用 Inner Garden'
          ]
        },
        {
          type: 'heading',
          level: 3,
          text: '首次使用建议'
        },
        {
          type: 'ordered',
          items: [
            '先体验「AI 伴侣聊天」，与 AI 分享今日心情',
            '在对话满意后，点击「生成日记」保存今日记录',
            '查看「记忆花园」，欣赏你的情绪卡片',
            '定期查看「月度报告」，回顾情绪变化趋势'
          ]
        }
      ]
    },
    features: {
      title: '核心功能',
      content: [
        {
          type: 'heading',
          level: 3,
          text: '🌱 AI 伴侣聊天'
        },
        {
          type: 'text',
          text: '与智能 AI 伴侣对话，分享你的日常、情绪和想法。AI 会倾听并回应，帮助你梳理思绪。'
        },
        {
          type: 'list',
          items: [
            '💬 自然对话：像与朋友聊天一样轻松',
            '🎤 语音输入：支持语音转文字输入',
            '🖼️ 图片上传：可上传图片作为对话背景',
            '📝 日记生成：对话满意时一键生成结构化日记'
          ]
        },
        {
          type: 'note',
          text: '提示：对话结束后记得点击「生成日记」保存，否则聊天记录不会留存。'
        },
        {
          type: 'heading',
          level: 3,
          text: '🌸 记忆花园'
        },
        {
          type: 'text',
          text: '每一篇日记都会变成一张精美的记忆卡片，展示独特的情绪色彩和封面。'
        },
        {
          type: 'list',
          items: [
            '🎨 情绪色彩：不同情绪对应不同颜色',
            '🖼️ AI 封面：自动生成水彩风格封面',
            '💭 Past Self：与过去的自己对话',
            '🗑️ 软删除：删除的卡片可恢复'
          ]
        },
        {
          type: 'heading',
          level: 3,
          text: '📅 月度报告'
        },
        {
          type: 'text',
          text: '以日历视图回顾整月的情绪记录，点击日期查看详细内容。'
        },
        {
          type: 'list',
          items: [
            '📊 情绪统计：查看本月情绪分布',
            '📆 日历视图：直观展示每日记录',
            '🔍 详情查看：点击日期回顾当日内容'
          ]
        }
      ]
    },
    faq: {
      title: '常见问题',
      content: [
        {
          type: 'heading',
          level: 3,
          text: '账号与安全'
        },
        {
          type: 'question',
          question: '如何找回密码？',
          answer: '在登录页点击「忘记密码」，输入注册邮箱，查收邮件中的重置链接。'
        },
        {
          type: 'question',
          question: '支持用户名登录吗？',
          answer: '是的，你可以使用用户名或邮箱登录。'
        },
        {
          type: 'heading',
          level: 3,
          text: '数据与隐私'
        },
        {
          type: 'question',
          question: '我的数据安全吗？',
          answer: '所有数据都存储在你的私有账户中，其他用户无法访问。我们采用加密存储保护敏感信息。'
        },
        {
          type: 'question',
          question: '可以删除日记吗？',
          answer: '可以。在记忆花园中点击卡片进入详情页，点击「删除记忆卡片」。删除的日记会进入软删除状态，管理员可协助恢复。'
        },
        {
          type: 'heading',
          level: 3,
          text: '功能说明'
        },
        {
          type: 'question',
          question: '对话记录会保存吗？',
          answer: '只有点击「生成日记」后，对话内容才会被分析并保存为日记。未生成的聊天记录不会留存。'
        },
        {
          type: 'question',
          question: 'AI 会判断我的情绪吗？',
          answer: '是的。当你生成日记时，AI 会分析对话内容，识别主要情绪（如平静、快乐、焦虑等），并生成结构化的日记内容。'
        },
        {
          type: 'question',
          question: '封面的图片从哪里来？',
          answer: '默认使用 AI 根据日记内容自动生成水彩风格封面。你也可以上传自己的图片作为封面。'
        }
      ]
    },
    privacy: {
      title: '隐私声明',
      content: [
        {
          type: 'heading',
          level: 3,
          text: 'Inner Garden 隐私承诺'
        },
        {
          type: 'text',
          text: 'Inner Garden 是一个情绪记录与反思工具，不提供任何医疗诊断、治疗或健康建议。'
        },
        {
          type: 'list',
          items: [
            '🔒 你的日记和对话仅你自己可见',
            '🛡️ 我们不向第三方出售你的个人数据',
            '⚕️ 本应用不替代专业心理健康服务',
            '📊 如遇严重情绪困扰，请寻求专业帮助'
          ]
        },
        {
          type: 'note',
          text: '如果你处于危机状态，请联系专业心理健康服务或当地危机干预热线。'
        }
      ]
    }
  };

  function renderContent(block) {
    switch (block.type) {
      case 'heading':
        const HeadingTag = `h${block.level || 2}`;
        return <HeadingTag key={Math.random()} className="md-heading">{block.text}</HeadingTag>;
      case 'text':
        return <p key={Math.random()} className="md-text">{block.text}</p>;
      case 'list':
        return (
          <ul key={Math.random()} className="md-list">
            {block.items.map((item, i) => <li key={i}>{item}</li>)}
          </ul>
        );
      case 'ordered':
        return (
          <ol key={Math.random()} className="md-ordered">
            {block.items.map((item, i) => <li key={i}>{item}</li>)}
          </ol>
        );
      case 'note':
        return <div key={Math.random()} className="md-note">💡 {block.text}</div>;
      case 'question':
        return (
          <div key={Math.random()} className="md-question">
            <h4 className="md-question-title">❓ {block.question}</h4>
            <p className="md-question-answer">{block.answer}</p>
          </div>
        );
      default:
        return null;
    }
  }

  const activeData = guideContent[activeSection] || guideContent.quickStart;

  return (
    <div className="about-page">
      <Suspense fallback={null}>
        <ParticleWaveHero
          backgroundOpacity={0.45}
          className="about-particle-wave"
          fit="cover"
          interactive={false}
          particleSize={10}
          waveSpeed={0.85}
          waveStrength={0.18}
        />
      </Suspense>
      <div className="about-16-9-wrapper">
        <div className="about-16-9-container">
          {/* Header */}
          <div className="about-header">
            <p className="about-eyebrow">Inner Garden</p>
            <h1 className="about-title">Mindful Memory Diary</h1>
            <p className="about-subtitle">关于 Inner Garden · 了解如何使用情绪记录工具</p>
          </div>

          {/* 导航标签 */}
          <div className="about-nav-tabs">
            {Object.keys(guideContent).map(key => (
              <button
                key={key}
                className={`nav-tab ${activeSection === key ? 'nav-tab-active' : ''}`}
                onClick={() => setActiveSection(key)}
                type="button"
              >
                {guideContent[key].title}
              </button>
            ))}
            <button
              className={`nav-tab ${activeSection === 'status' ? 'nav-tab-active' : ''}`}
              onClick={() => setActiveSection('status')}
              type="button"
            >
              服务状态
            </button>
          </div>

          {/* 内容区域 - 16:9 横向滚动区域 */}
          <div className="about-16-9-content">
            {activeSection !== 'status' ? (
              <div className="md-content">
                <h2 className="md-section-title">{activeData.title}</h2>
                <div className="md-body">
                  {activeData.content.map(renderContent)}
                </div>
              </div>
            ) : (
              <div className="about-status-content">
                <h2 className="md-section-title">服务状态</h2>
                <p className="text-white/70">当前用户：{currentUser?.email || '尚未登录'}</p>
                <button className="primary-action" onClick={handleHealthCheck} type="button">检查服务状态</button>
                {currentUser?.role === 'admin' && <a className="secondary-action" href="#/admin">进入 Admin Dashboard</a>}
                {status && <StatusText>{status}</StatusText>}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="about-footer">
            <p>产品边界：Inner Garden 不是心理诊断工具，也不提供治疗、用药或医疗建议；它只做记录、陪伴和回忆整理。</p>
          </div>
        </div>
      </div>
    </div>
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

  function getMonthlyEmotionKey(memory) {
    const emotion = String(getDiaryEmotion(memory)).trim().toLowerCase();
    if (['joy', 'happy', 'happiness', '开心', '快乐'].includes(emotion)) return 'joy';
    if (['calm', 'peaceful', 'peace', '平静', '安定'].includes(emotion)) return 'calm';
    if (['sad', 'sadness', '难过', '伤心', '低落'].includes(emotion)) return 'sadness';
    if (['anxiety', 'anxious', 'fear', '焦虑', '紧张'].includes(emotion)) return 'anxiety';
    if (['tired', 'fatigue', 'exhausted', '疲惫', '疲劳'].includes(emotion)) return 'tired';
    return EMOTION_COLOR_MAP[emotion] ? emotion : 'neutral';
  }

  function getMonthlyEmotionLabel(emotionKey) {
    const labels = {
      anxiety: '焦虑',
      calm: '平静',
      joy: '开心',
      neutral: '中性',
      sadness: '难过',
      tired: '疲惫',
    };
    return labels[emotionKey] || '未知';
  }

  function getDiarySummary(memory) {
    return memory.excerpt || memory.conversation_summary || memory.diary?.content || '这一天被温柔地保存下来。';
  }

  function normalizeMemory(memory) {
    const dateKey = getDiaryDateKey(memory);
    if (!dateKey) return null;
    const emotionKey = getMonthlyEmotionKey(memory);
    return {
      ...memory,
      dateKey,
      displayDate: memory.diary_date || dateKey,
      displayEmotion: getMonthlyEmotionLabel(emotionKey),
      emotionColor: getEmotionColor(emotionKey),
      emotionKey,
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
  const monthlyEntries = useMemo(() => Object.values(diaryIndex), [diaryIndex]);
  const monthlyStats = useMemo(() => {
    const counts = monthlyEntries.reduce((result, entry) => {
      const emotionKey = entry.emotionKey || 'neutral';
      result[emotionKey] = (result[emotionKey] || 0) + 1;
      return result;
    }, {});
    return Object.entries(counts)
      .sort((left, right) => right[1] - left[1])
      .map(([emotionKey, count]) => ({
        color: getEmotionColor(emotionKey),
        count,
        emotionKey,
        label: getMonthlyEmotionLabel(emotionKey),
      }));
  }, [monthlyEntries]);
  const hasMonthlyEntries = monthlyEntries.length > 0;

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
      <section className="monthly-report-summary" aria-label="Monthly emotion summary">
        <p className="monthly-report-summary-label">本月统计</p>
        {hasMonthlyEntries ? (
          <>
            <strong>{monthlyEntries.length} 篇日记</strong>
            <div className="monthly-report-summary-list">
              {monthlyStats.map((item) => (
                <span className="monthly-report-summary-item" key={item.emotionKey}>
                  <i style={{ backgroundColor: item.color }} />
                  {item.label} {item.count}
                </span>
              ))}
            </div>
          </>
        ) : (
          <strong>你还没有开始记录呢</strong>
        )}
      </section>

      <div className="monthly-report-shell">
        <header className="monthly-report-header">
          <p className="monthly-report-eyebrow">Inner Garden</p>
          <h1>Mindful Memory Diary</h1>
          <p className="monthly-report-subtitle">月度情绪报告 · 回顾你的内心旅程</p>
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

        <div className={`monthly-report-calendar ${hasMonthlyEntries ? '' : 'is-empty'}`}>
          {!hasMonthlyEntries && (
            <div className="monthly-report-empty-state" role="status">
              <p>你还没有开始记录呢</p>
            </div>
          )}
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
                {day.entry && (
                  <span
                    aria-label={day.entry.displayEmotion}
                    className="monthly-report-emotion-dot"
                    style={{ backgroundColor: day.entry.emotionColor }}
                  />
                )}
              </button>
            );
          })}
        </div>

        <footer className="monthly-report-footer">
          <p className="monthly-report-note">产品边界：Inner Garden 不是心理诊断工具，也不提供治疗、用药或医疗建议；它只做记录、陪伴和回忆整理。</p>
          {status && <p className="monthly-report-status">{status}</p>}
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
                <span
                  className="monthly-report-inline-dot"
                  style={{ backgroundColor: selectedEntry.emotionColor }}
                />
                {selectedEntry.displayEmotion}
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

// ============================================================================
// EMOTION & COLOR HELPERS
// ============================================================================

/**
 * 根据情绪获取对应的固定颜色
 * @param {string} emotion - 情绪标签
 * @returns {string} 对应的颜色值
 */
function getEmotionColor(emotion) {
  return EMOTION_COLOR_MAP[emotion] || EMOTION_COLOR_MAP.neutral;
}

/**
 * 获取情绪的中文显示名称
 * @param {string} emotion - 情绪标签
 * @returns {string} 中文情绪名称
 */
function getEmotionLabel(emotion) {
  const labels = {
    calm: '平静',
    joy: '开心',
    sadness: '难过',
    anxiety: '焦虑',
    tired: '疲惫',
    neutral: '中性',
  };
  return labels[emotion] || '未知';
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

// ============================================================================
// PASSWORD RESET PAGE
// ============================================================================

function PasswordResetPage({ token }) {
  const [step, setStep] = useState(token ? 'verify' : 'request');
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [verifiedEmail, setVerifiedEmail] = useState('');

  useEffect(() => {
    if (token && step === 'verify') {
      verifyToken();
    }
  }, [token]);

  async function verifyToken() {
    setLoading(true);
    setError('');
    try {
      const result = await verifyResetToken(token);
      if (result.data?.valid) {
        setVerifiedEmail(result.data.email_partial || '');
        setStep('reset');
        setMessage('Token 已验证，请设置新密码');
      } else {
        setError('重置链接无效或已过期，请重新请求');
        setStep('request');
      }
    } catch (err) {
      setError(err.message || '验证失败，请重新请求');
      setStep('request');
    } finally {
      setLoading(false);
    }
  }

  async function handleRequestReset(e) {
    e.preventDefault();
    if (!email) {
      setError('请输入邮箱地址');
      return;
    }
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await requestPasswordReset(email);
      setMessage('如果该邮箱已注册，您将收到密码重置邮件');
      setEmail('');
    } catch (err) {
      setError(err.message || '请求失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }

  async function handlePasswordReset(e) {
    e.preventDefault();
    if (newPassword.length < 6) {
      setError('密码至少需要 6 个字符');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }
    setLoading(true);
    setError('');
    setMessage('');
    try {
      await confirmPasswordReset(token, newPassword);
      setMessage('密码重置成功！您现在可以使用新密码登录');
      setStep('success');
    } catch (err) {
      setError(err.message || '重置失败，请重新申请');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen bg-[#10131e]">
      <DreamBackdrop />
      <div className="relative z-10 flex min-h-screen items-center justify-center px-5">
        <div className="w-full max-w-md rounded-3xl border border-white/10 bg-white/[0.06] p-8 backdrop-blur-2xl">
          <div className="text-center">
            <h1 className="font-display text-3xl text-white">
              {step === 'success' ? '密码重置成功' : '重置密码'}
            </h1>
            <p className="mt-3 text-sm text-white/60">
              {step === 'request' && '输入您的注册邮箱，我们将发送重置链接'}
              {step === 'verify' && '正在验证重置链接...'}
              {step === 'reset' && `为 ${verifiedEmail} 设置新密码`}
              {step === 'success' && '您现在可以使用新密码登录'}
            </p>
          </div>

          {message && !error && (
            <div className="mt-6 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-200">
              {message}
            </div>
          )}

          {error && (
            <div className="mt-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}

          {step === 'request' && (
            <form onSubmit={handleRequestReset} className="mt-6 space-y-4">
              <div>
                <label className="mb-2 block text-sm text-white/60">注册邮箱</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/40 outline-none transition focus:border-white/30"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-[#8fb8ff] px-4 py-3 text-sm font-medium text-black transition hover:bg-[#7aa0e0] disabled:opacity-50"
              >
                {loading ? '发送中...' : '发送重置邮件'}
              </button>
            </form>
          )}

          {step === 'verify' && (
            <div className="mt-6 text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-white/20 border-t-white"></div>
            </div>
          )}

          {step === 'reset' && (
            <form onSubmit={handlePasswordReset} className="mt-6 space-y-4">
              <div>
                <label className="mb-2 block text-sm text-white/60">新密码</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="至少 6 个字符"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/40 outline-none transition focus:border-white/30"
                  disabled={loading}
                />
              </div>
              <div>
                <label className="mb-2 block text-sm text-white/60">确认新密码</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="再次输入新密码"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder-white/40 outline-none transition focus:border-white/30"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-[#8fb8ff] px-4 py-3 text-sm font-medium text-black transition hover:bg-[#7aa0e0] disabled:opacity-50"
              >
                {loading ? '重置中...' : '重置密码'}
              </button>
            </form>
          )}

          {step === 'success' && (
            <div className="mt-6">
              <a
                href="#/login"
                className="block w-full rounded-xl bg-[#8fb8ff] px-4 py-3 text-center text-sm font-medium text-black transition hover:bg-[#7aa0e0]"
              >
                前往登录
              </a>
            </div>
          )}

          <div className="mt-6 text-center">
            <a href="#/login" className="text-sm text-white/40 transition hover:text-white/60">
              返回登录
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}
