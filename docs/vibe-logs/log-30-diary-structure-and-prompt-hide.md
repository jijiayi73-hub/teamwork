# Vibe Log: 日记结构化生成与提示词隐藏

**Date**: 2026-07-09
**Task**: TASK-020
**Type**: Feature Fix
**Status**: ✅ Complete

## 问题背景

用户报告两个体验问题：
1. AI 日记生成未结构化，直接复制粘贴对话记录
2. AI 封面生成提示词对用户可见

## 核修过程

### 问题分析

**问题2根因**:
- 后端 `EMOTION_ANALYSIS_SYSTEM_PROMPT` 只要求返回情绪分析 JSON
- 没有要求 LLM 生成结构化日记内容
- 前端 `transcriptFromMessages()` 只做简单消息拼接

**问题3根因**:
- 前端 DiaryResultPage 显示 "自动封面提示词" textarea
- 用户可以阅读 AI 用于生成封面图的提示词

### 修复方案

**后端修复** (`backend/app/services/analysis_service.py`):
- 扩展 `EMOTION_ANALYSIS_SYSTEM_PROMPT`
- 增加 `diary_content` 字段要求（150-400字结构化日记）
- 增加 `title` 字段要求（日记标题）
- 指定日记格式：日期 + 事件 + 感受 + 总结

**前端修复** (`frontend/src/AppFixed.jsx`):
- 移除 "自动封面提示词" textarea 显示
- 保留 `buildWatercolorPrompt()` 后台生成逻辑
- 只显示封面预览（如有）

## 验证结果

```bash
# 后端验证
cd backend
py -c "from app.services.analysis_service import EMOTION_ANALYSIS_SYSTEM_PROMPT; print('diary_content' in EMOTION_ANALYSIS_SYSTEM_PROMPT)"
# Result: True

# 前端验证
cd frontend
npm run build
# Result: ✓ built in 3.91s
```

## API / 数据库影响

- **API**: 无。`POST /api/v1/entries` 响应格式保持不变
- **数据库**: 无。无需修改表结构

## 风险与限制

- **LLM 输出质量**: 新 prompt 可能需要调优才能稳定生成高质量日记
- **Fallback 逻辑**: 如 LLM 不返回 `diary_content`，会使用模板 `f"今天我记录下了这段感受：{raw_content}"`
- **Token 使用**: 新 prompt 较长 (1065 字符)，可能增加调用成本

## 预期行为

### 日记生成示例

**修改前**:
```
我：你今天发什么了什么好玩的事情？
AI：我今天吃到了好吃的饭。
```

**修改后**:
```
7月9日

今天我和 AI 伙伴聊了一些事情，聊到了今天吃到的好吃的饭。

当时的感受是很开心，觉得那顿饭很美味。

回想起来，今天过得很美好，希望明天也能这样。
```

### 封面提示词处理

**修改前**: textarea 显示完整提示词
**修改后**: 提示词在后台生成，用户只看到封面预览

## 后续建议

1. 真实环境测试 LLM 生成的日记质量
2. 根据 LLM 输出情况调优 prompt
3. 收集用户反馈迭代日记生成逻辑

## 相关文件

- `backend/app/services/analysis_service.py` - LLM prompt 更新
- `frontend/src/AppFixed.jsx` - UI 优化
- `docs/state/task-board.md` - 任务记录
- `docs/state/current-status.md` - 状态更新
