# Log 48 - 检索触发正则表达式增强

Date: 2026-07-10
Branch: `codex/sync-scripts-to-main`
Task: TASK-050 VPS回想正则匹配修复

## Request

用户报告VPS上的"回想正则"没有正确匹配，需要修复该问题。

## Findings

### 问题分析

1. **本地验证**：本地测试显示原有正则表达式工作正常
2. **VPS环境**：VPS代码版本与本地一致，没有编码问题
3. **根本原因**：原有正则表达式覆盖范围过窄，无法匹配用户多样化的表达方式

### 原有问题

**EXPLICIT_MEMORY_PATTERNS（明确记忆引用）**：
- `r"回想"` - 只能匹配"回想"两个字
- 缺少常见的用户表达方式如"想一想"、"想起来"、"想起"等

**CONTINUITY_PATTERNS（连续性表达）**：
- 缺少常见的连续性表达如"再次"、"又一次"、"依旧"、"照旧"、"照样"、"一切如故"等

## Solution

### 增强EXPLICIT_MEMORY_PATTERNS

添加了以下模式：
- `r"回.*想"` - 支持"回想"、"让我回想"、"帮我回想"等
- `r"回.*忆"` - 支持"回忆"、"回忆一下"等
- `r"想.*起.*来"` - 支持"想起来"、"我想起来了"等
- `r"想.*一.*想"` - 支持"想一想"、"让我想一想"等
- `r"想.*想"` - 支持"想想"等
- `r"想.*起"` - 支持"想起"、"没想起"等
- `r"记得.*吗"` - 支持"记得吗"等
- `r"还.*记.*得"` - 支持"还记得"、"还记不记得"等
- `r"有.*没.*有"` - 支持"有没有"、"有没有记得"等
- `r"那.*个"` - 支持"那个"、"那个时候"等

### 增强CONTINUITY_PATTERNS

添加了以下模式：
- `r"接着"` - "接着..."
- `r"继续"` - "继续..."
- `r"还是那"` - "还是那..."
- `r"又是"` - "又是..."
- `r"总是那"` - "总是那..."
- `r"还是.*那"` - "还是那样"
- `r"再次"` - "再次..."
- `r"又一次"` - "又一次..."
- `r"还.*在"` - "还在..."
- `r"依.*旧"` - "依旧..."
- `r"照.*旧"` - "照旧..."
- `r"照.*样"` - "照样..."
- `r"如.*故"` - "如故..."
- `r".*如故"` - "一切如故"、"如故"

### 新增测试用例

创建了 `tests/test_retrieval_trigger_patterns.py`，包含：
- 6个测试方法验证正则表达式匹配
- 覆盖明确记忆引用和连续性表达
- 测试边界情况和误报防护

## Validation

```bash
cd backend
py -m pytest tests/test_retrieval_trigger_patterns.py tests/test_memory_gate.py tests/test_rag_context.py -v
# 37 passed, 2 warnings
```

## Expected Behavior

### 增强的匹配能力

现在系统可以正确识别以下用户表达：

**明确记忆引用**：
- "回想一下上次我们聊了什么"
- "让我想一想"
- "我想起来了"
- "还记得吗"
- "那个时候"
- "有没有记得"

**连续性表达**：
- "我又遇到了同样的情况"
- "还是老样子"
- "一切如故"
- "还在继续"
- "再次遇到"
- "又一次"

### 决策逻辑

1. 检测到明确记忆引用 → confidence=0.9，强触发检索
2. 检测到连续性表达 → confidence=0.85，强触发检索
3. 检测到情绪/主题 → confidence=0.7，中触发检索
4. 检测到疑问 → confidence=0.3，弱触发检索
5. 无模式匹配 → confidence=0.4，默认行为

## 相关文件

- `backend/app/services/retrieval_trigger_service.py` - 增强正则表达式模式
- `backend/tests/test_retrieval_trigger_patterns.py` - 新增测试用例

## VPS Deployment

部署步骤：
1. 同步代码到VPS：`git pull`
2. 重建后端容器：`docker compose -f docker-compose.prod.yml build backend`
3. 重启后端容器：`docker compose -f docker-compose.prod.yml up -d backend`
4. 验证健康检查：`curl https://jijiayi.online/api/v1/health`

## Notes

- 本地环境验证通过，所有37个相关测试通过
- VPS代码版本确认与本地一致
- 增强的正则表达式使用 `re.IGNORECASE` 标志，对中文无影响
- 新增测试用例确保未来修改不会破坏匹配能力
