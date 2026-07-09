# TASK-031: Chat Dialog Scroll Fix

**Date**: 2026-07-09
**Owner**: Inner Garden Team
**Branch**: `codex/sync-scripts-to-main`
**Status**: ✅ Complete

## Problem

用户报告聊天对话框无法向上滚动查看历史消息。

## Root Cause

`.ai-notification-list` 使用了 `justify-content: flex-end` 让消息从底部开始对齐。这导致：

1. 当消息超过容器高度时，滚动行为不符合用户预期
2. 缺少自动滚动到底部的 JavaScript 逻辑
3. 用户向上滚动时可能遇到"空白区域"而非历史消息

## Solution

### CSS Changes (`frontend/src/styles.css`)

```css
/* Before */
.ai-notification-list {
  justify-content: flex-end;  /* 导致滚动问题 */
}

/* After */
.ai-notification-list {
  /* 移除 justify-content: flex-end，改用 JavaScript 自动滚动 */
}
```

### JavaScript Changes (`frontend/src/AppFixed.jsx`)

1. **添加滚动锚点引用**:
```javascript
const messagesEndRef = useRef(null);
```

2. **添加自动滚动逻辑**:
```javascript
useEffect(() => {
  if (messagesEndRef.current) {
    messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }
}, [messages, isAiTyping]);
```

3. **在 JSX 中添加滚动锚点**:
```jsx
<div className="ai-notification-list">
  {messages.map(...)}
  {isAiTyping && (...)}
  <div ref={messagesEndRef} />  {/* 滚动锚点 */}
</div>
```

## Validation

```bash
cd frontend
npm run build
# Result: ✓ built in 2.04s
```

## Expected Behavior

- ✅ 新消息到达时自动滚动到底部
- ✅ 用户可以自由向上滚动查看历史消息
- ✅ AI 正在输入时自动保持在底部
- ✅ 滚动条可见且易于使用

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/styles.css` | 移除 `justify-content: flex-end` |
| `frontend/src/AppFixed.jsx` | 添加 `messagesEndRef`, `useEffect`, 滚动锚点 |

## Related Issues

- Fixes: 用户报告的"chat对话框没办法向上滚动"
- Related: TASK-019 (AI Chat Thinking Indicator)
