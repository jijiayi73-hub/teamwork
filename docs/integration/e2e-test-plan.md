# Inner Garden End-to-End Flow Test Plan

## Purpose
验证完整业务流程能否从头到尾跑通，确保各个模块集成正常。

## Test Philosophy

1. **User Journey Focus**: 每个测试模拟一个完整的用户旅程
2. **No Mocking When Possible**: 尽量使用真实服务和数据库
3. **State Validation**: 验证数据库状态而不仅是 API 响应
4. **Error Recovery**: 测试错误场景和恢复路径
5. **Isolation**: 每个测试独立运行，不依赖其他测试

## Test Flows

### F-001: Authentication Full Flow
**User Journey**: 注册 → 登录 → 访问受保护资源 → 登出 → 验证token失效

**Steps**:
1. POST /api/v1/auth/register - 新用户注册
2. 验证返回 access_token 和 user 信息
3. POST /api/v1/auth/login - 使用相同凭证登录
4. 验证可以获得新 token
5. GET /api/v1/auth/me - 验证 token 有效
6. GET /api/v1/diaries - 验证可以访问受保护资源
7. POST /api/v1/auth/logout (或前端清除 token)
8. 验证旧 token 无法访问受保护资源 (401)

**Acceptance**:
- 所有步骤返回正确的状态码
- Token 失效后无法访问受保护资源
- 数据库中用户记录正确创建

---

### F-002: Diary Creation Full Flow
**User Journey**: 创建日记条目 → 情绪分析 → 保存日记 → 查看列表 → 统计更新

**Steps**:
1. 注册/登录用户
2. POST /api/v1/entries - 创建原始日记条目
3. 验证 entry.status == "analyzed"
4. 验证 entry.analysis 包含情绪标签
5. POST /api/v1/diaries - 将条目保存为日记
6. GET /api/v1/diaries - 验证日记出现在列表中
7. GET /api/v1/stats/overview - 验证统计计数增加
8. GET /api/v1/diaries/{id} - 获取单个日记详情
9. PATCH /api/v1/diaries/{id} - 更新日记
10. DELETE /api/v1/diaries/{id} - 软删除日记
11. 验证删除后不再出现在列表中

**Acceptance**:
- 完整流程无错误
- 数据库状态正确更新
- 软删除后记录仍然存在但 deleted_at 不为空

---

### F-003: Chat Full Flow
**User Journey**: 创建新对话 → 发送消息 → 接收AI回复 → 继续对话 → 查看历史

**Steps**:
1. 注册/登录用户
2. POST /api/v1/chat/messages - 创建新对话 (conversation_id=null, mode="companion")
3. 验证返回 conversation.id, user_message, assistant_message
4. 验证数据库中创建了 conversation 和两条 message
5. POST /api/v1/chat/messages - 继续同一对话 (使用 conversation_id)
6. 验证 message_count 增加
7. GET /api/v1/chat/conversations - 获取对话列表
8. 验证新对话出现在列表中
9. GET /api/v1/chat/conversations/{id}/messages - 获取消息历史
10. 验证返回所有消息按时间排序
11. DELETE /api/v1/chat/conversations/{id} - 删除对话
12. 验证删除后不再出现在列表中

**Acceptance**:
- 对话和消息正确持久化
- 消息按时间顺序返回
- 软删除正常工作

---

### F-004: Memory Garden & Past Self Chat Flow
**User Journey**: 创建日记 → 创建记忆卡片 → 查看记忆花园 → Past Self 聊天

**Steps**:
1. 注册/登录用户
2. 创建 Entry 和 Diary (复用 F-002 步骤)
3. POST /api/v1/uploads/images - 上传封面图片
4. 验证返回 /uploads/... URL
5. POST /api/v1/memories - 创建记忆卡片
6. 验证记忆卡片创建成功
7. GET /api/v1/memories - 获取记忆卡片列表
8. 验证新卡片出现在列表中
9. GET /api/v1/memories/{id} - 获取卡片详情
10. 验证包含 diary 快照信息
11. POST /api/v1/memories/{id}/past-self-chat - 发起 Past Self 聊天
12. 验证创建 past_self 模式的对话
13. GET /api/v1/chat/conversations - 验证对话出现在列表中
14. DELETE /api/v1/memories/{id} - 软删除记忆卡片
15. 验证删除后不再出现在列表中

**Acceptance**:
- 图片上传返回可访问的 URL
- 记忆卡片包含正确的 diary 快照
- Past Self 聊天正确关联到 anchor_diary

---

### F-005: Error Recovery Flows
**User Journey**: 各种错误场景的恢复验证

**Scenarios**:

**5.1 无效 Token Recovery**:
1. 使用无效/过期的 token 访问受保护资源
2. 验证返回 401
3. 前端清除本地会话
4. 重新登录获取新 token
5. 验证可以正常访问

**5.2 AI Provider Error Recovery**:
1. 发送聊天消息时模拟 AI Provider 错误 (502)
2. 验证用户消息已保存，但无 assistant 消息
3. 重新发送消息
4. 验证可以正常获得回复

**5.3 验证错误 Recovery**:
1. 发送缺少必填字段的请求
2. 验证返回 422 和具体错误信息
3. 修正请求后重试
4. 验证成功处理

**5.4 资源不存在 Recovery**:
1. 访问不存在的 conversation/diary/memory
2. 验证返回 404
3. 验证错误信息不泄露其他用户的存在性

**Acceptance**:
- 所有错误场景返回正确的状态码
- 错误信息清晰且不泄露敏感信息
- 客户端可以正确恢复

---

### F-006: Multi-User Isolation Flow
**User Journey**: 验证用户之间的数据隔离

**Steps**:
1. 创建 User A 和 User B
2. User A 创建对话、日记、记忆卡片
3. User B 尝试访问 User A 的资源
4. 验证所有尝试返回 404
5. User B 创建自己的资源
6. 验证两个用户的资源互不影响
7. User A 列出资源时只看到自己的

**Acceptance**:
- 用户无法访问其他用户的资源
- 404 错误不泄露资源是否存在
- 列表端点只返回当前用户的资源

---

## Test Implementation Structure

```
backend/tests/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py              # Shared E2E fixtures
│   ├── test_auth_flow.py       # F-001
│   ├── test_diary_flow.py      # F-002
│   ├── test_chat_flow.py       # F-003
│   ├── test_memory_flow.py     # F-004
│   ├── test_error_recovery.py  # F-005
│   └── test_user_isolation.py  # F-006
```

## Common Fixtures

- `authenticated_client`: 带认证的测试客户端
- `db_session`: 数据库会话
- `fake_ai_provider`: Fake AI Provider for chat tests
- `sample_user`: 预创建的测试用户

## Running Tests

```bash
# 运行所有 E2E 测试
pytest tests/e2e/ -v

# 运行特定流程
pytest tests/e2e/test_chat_flow.py -v

# 并行运行 (如果有 pytest-xdist)
pytest tests/e2e/ -n 4 -v
```

## Success Criteria

1. 所有流程测试通过
2. 测试覆盖率 > 80% (关键路径)
3. 每个测试独立运行，无顺序依赖
4. 测试运行时间 < 30 秒

## Version: 1.0
## Created: 2026-07-09
## Owner: Inner Garden Team
