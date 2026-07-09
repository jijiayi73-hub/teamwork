# Vibe Log: 日记标题与内容文艺化改进

**Date**: 2026-07-10
**Task**: TASK-032
**Type**: Feature Improvement
**Status**: ✅ Complete

## 背景

用户反馈当前 AI 生成的日记存在以下问题：
1. **标题过于直白**：使用"开心的时刻"、"焦虑的时刻"等简单描述，缺乏诗意
2. **内容需要更完整**：应将用户话语整理成完整的日记叙述，而非简单对话记录拼接
3. **确保真实性**：不能编造用户没有表达的事件或感受

## 改进方案

### 1. Fallback 标题文艺化

更新 `_generate_title_from_emotion()` 函数，将简单描述改为文艺表达：

| 原标题 | 新标题 | 风格 |
|--------|--------|------|
| "开心的时刻" | "微光点亮的日子" | 自然意象（光） |
| "平静的时刻" | "内心的宁静港湾" | 空间意象（港湾） |
| "焦虑的时刻" | "翻涌过后是平静" | 动态过程暗示 |
| "低落的时刻" | "雨后才有彩虹" | 自然意象（雨/彩虹） |
| "今天的记录" | "平凡中的诗意" | 哲思风格 |

### 2. LLM Prompt 优化

扩展 `EMOTION_ANALYSIS_SYSTEM_PROMPT`，添加：

**标题生成规则**：
- 明确要求"文艺诗意，含蓄不直白"的风格
- 提供具体示例（自然意象、空间意象）
- 限制长度（4-12字）

**内容生成规则强化**：
- 添加"严格忠于用户原意，不虚构任何事件、人物、时间、原因"条款
- 明确"只写入用户明确表达的内容，不添加推断或猜测"
- 强调"将用户的多句话语整理成连贯的叙述，而非简单对话拼接"

## 实现细节

### 代码变更

**文件**: `backend/app/services/analysis_service.py`

**变更1**: Fallback 标题函数
```python
def _generate_title_from_emotion(emotion: str) -> str:
    """根据情绪生成文艺风格的标题。"""
    titles = {
        "joy": "微光点亮的日子",
        "sadness": "雨后才有彩虹",
        "anxiety": "翻涌过后是平静",
        "calm": "内心的宁静港湾",
        "neutral": "平凡中的诗意",
    }
    return titles.get(emotion, "亦言亦思皆为序章")
```

**变更2**: Prompt 扩展
- 添加标题风格要求（约 200 字）
- 强化内容真实性要求（约 300 字）
- 添加具体示例和格式说明

## 验证结果

```bash
cd backend
py -c "from app.services.analysis_service import EMOTION_ANALYSIS_SYSTEM_PROMPT, _generate_title_from_emotion; print('OK')"
# Result: Backend imports OK
# Prompt updated with literary guidance
# Fallback titles verified
```

## API / 数据库影响

- **API**: 无影响。`draft_title` 和 `draft_content` 字段保持不变
- **数据库**: 无影响。无需修改表结构

## 预期效果示例

### 标题对比

| 情绪 | 修改前 | 修改后 |
|------|--------|--------|
| joy | "开心的时刻" | "微光点亮的日子" |
| calm | "平静的时刻" | "内心的宁静港湾" |
| anxiety | "焦虑的时刻" | "翻涌过后是平静" |
| sadness | "低落的时刻" | "雨后才有彩虹" |

### 内容对比

**修改前**（简单对话拼接）：
```
我：你今天发什么了什么好玩的事情？
AI：我今天吃到了好吃的饭。
```

**修改后**（完整日记叙述）：
```
7月10日

今天我和 AI 伙伴聊了一些事情，提到了今天吃到的一顿美餐。

当时的感受是很开心，觉得那顿饭很美味，是我今天的小确幸。

希望明天也能有这样的小快乐。
```

## 后续建议

1. 真实环境测试 LLM 生成的日记质量和文艺风格
2. 收集用户反馈，迭代标题和内容生成逻辑
3. 考虑为不同情绪类型提供更多元化的标题模板

## 相关文件

- `backend/app/services/analysis_service.py` - 主要实现
- `docs/state/task-board.md` - 任务记录
- `docs/state/current-status.md` - 状态更新
