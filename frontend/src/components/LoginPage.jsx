import { useState } from 'react';
import { login, register, consumeRedirectPath } from '../api/auth';

/**
 * 最小登录页面组件
 *
 * 这是一个最小可用的登录实现，设计为后期可替换。
 * 当前功能：
 * - 登录/注册切换
 * - 表单验证
 * - 错误提示
 * - 成功后跳转
 *
 * 后期可扩展：
 * - 更丰富的表单验证
 * - 记住我功能
 * - 忘记密码
 * - 社交登录
 * - 更精美的 UI 设计
 */
export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(username, email, password);
      }
      // 登录/注册成功后跳转
      window.location.hash = consumeRedirectPath();
    } catch (err) {
      setError(err.message || (isLogin ? '登录失败' : '注册失败'));
    } finally {
      setIsLoading(false);
    }
  }

  function toggleMode() {
    setIsLogin(!isLogin);
    setError('');
    setUsername('');
    setEmail('');
    setPassword('');
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#10131e] font-body text-white">
      {/* 背景效果 */}
      <div className="absolute inset-0 bg-night-garden" />
      <div className="absolute inset-0 bg-watercolor-mist" />

      {/* 登录卡片 */}
      <section className="relative z-10 flex min-h-screen items-center justify-center px-5">
        <div className="w-full max-w-md rounded-[28px] border border-white/16 bg-white/[0.08] px-8 py-12 shadow-glow backdrop-blur-2xl">
          <div className="mb-8 text-center">
            <p className="mb-4 text-xs uppercase tracking-[0.38em] text-[#c8e0ff]/80">
              {isLogin ? '欢迎回来' : '创建账户'}
            </p>
            <h1 className="font-display text-3xl text-white">
              {isLogin ? '登录 Inner Garden' : '加入 Inner Garden'}
            </h1>
          </div>

          {error && (
            <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            {!isLogin && (
              <div>
                <label htmlFor="username" className="mb-2 block text-sm text-white/64">
                  用户名
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="input-surface w-full"
                  placeholder="请输入用户名"
                />
              </div>
            )}

            <div>
              <label htmlFor="email" className="mb-2 block text-sm text-white/64">
                邮箱
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="input-surface w-full"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-2 block text-sm text-white/64">
                密码
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="input-surface w-full"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="primary-action w-full"
            >
              {isLoading ? '处理中...' : isLogin ? '登录' : '注册'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={toggleMode}
              className="text-sm text-white/60 transition hover:text-white"
            >
              {isLogin ? '还没有账户？去注册' : '已有账户？去登录'}
            </button>
          </div>

          <div className="mt-8 pt-6 border-t border-white/10 text-center">
            <a
              href="#/"
              className="text-sm text-white/40 transition hover:text-white/60"
            >
              返回首页
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
