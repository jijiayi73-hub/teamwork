# Vibe Log: Memory Garden 409 Save Error Fix

**Date**: 2026-07-08
**Task**: TASK-005 - Debug and fix Memory Garden save failure (409 error)
**Owner**: Codex
**Branch**: `codex/sync-scripts-to-main`

## Problem Description

用户报告 Memory Garden 界面保存失败，错误信息：`保存失败：Request failed: 409`

### Root Cause Analysis

1. **后端限制**:
   - `POST /api/v1/diaries` 对 `entry_id` 有唯一性约束 (diaries.py:39-40)
   - `POST /api/v1/memories` 对 `diary_id` 有唯一性约束 (memories.py:164-165)
   - 每个 entry 只能创建一个 diary，每个 diary 只能创建一个 memory card

2. **场景复现**:
   - 用户完成 AI 对话 → 生成 entry (假设 id=1)
   - 用户点击"保存到 Memory Garden" → 成功创建 diary 和 memory card
   - 用户再次进入 diary-result 页面，再次点击"保存"
   - `createDiary(entry_id=1)` 返回 409 Conflict

3. **用户体验问题**:
   - 前端显示技术性错误消息："Request failed: 409"
   - 用户被困在 diary-result 页面，无法访问已保存的内容

## Solution

### 前端修复 (frontend/src/AppFixed.jsx)

1. **新增状态**:
   ```jsx
   const [existingMemoryId, setExistingMemoryId] = useState(null);
   const [checkingExisting, setCheckingExisting] = useState(false);
   ```

2. **页面加载时检查现有 memory card**:
   ```jsx
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
           setStatus('该草稿已保存为记忆卡片，点击下方按钮查看。');
         }
       } catch (error) {
         // Silently fail - we'll handle it during save
       } finally {
         setCheckingExisting(false);
       }
     }
     checkExistingMemory();
   }, [draft?.entry_id]);
   ```

3. **保存时处理现有 memory card**:
   ```jsx
   async function handleSave() {
     // If we already know a memory card exists, redirect to it
     if (existingMemoryId) {
       window.location.hash = `#/memory-garden/${existingMemoryId}`;
       return;
     }
     // ... rest of save logic

     // Handle 409 errors gracefully
     catch (error) {
       if (error.message.includes('already exists') || error.message.includes('409')) {
         setStatus('该内容已保存，正在查找现有记忆卡片...');
         // Try to find the existing memory card
         const response = await listMemories();
         const existingMemory = (response.data || []).find(
           (memory) => memory.diary?.id && memory.diary.entry_id === draft.entry_id
         );
         if (existingMemory) {
           window.localStorage.removeItem(DRAFT_KEY);
           window.location.hash = `#/memory-garden/${existingMemory.id}`;
           return;
         }
       }
     }
   }
   ```

4. **UI 更新**:
   ```jsx
   {existingMemoryId ? (
     <a className="primary-action" href={`#/memory-garden/${existingMemoryId}`}>
       查看已保存的记忆卡片
     </a>
   ) : (
     <button className="primary-action" disabled={isSaving || checkingExisting} onClick={handleSave}>
       {isSaving ? '保存中...' : checkingExisting ? '检查中...' : '保存到 Memory Garden'}
     </button>
   )}
   ```

## Verification

### Static Validation
- ✅ 前端构建成功 (`npm run build` in 2.97s)
- ✅ 无 TypeScript 或语法错误

### Pending User Verification
- [ ] 用户测试重复保存场景
- [ ] 验证"查看已保存的记忆卡片"按钮显示
- [ ] 验证跳转到现有 memory detail 页面

## API/Database Impact

**无变化** - 此修复完全在前端实现，不涉及后端 API 或数据库架构变更。

## Known Risks

1. **`memory.diary.entry_id` 依赖**: 修复假设 `memory.diary` 包含 `entry_id` 字段。如果后端 API 响应结构变化，需要同步更新。
2. **网络延迟**: `listMemories()` 调用可能因网络延迟导致短暂的"检查中..."状态。
3. **大量 memory 卡片**: 如果用户有大量 memory 卡片，线性查找效率可能下降（一般用户场景下影响可忽略）。

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/AppFixed.jsx` | Added existing memory card detection and 409 error handling |

## Related Issues

- Fixes: Memory Garden save failure (409 error)
- Related: TASK-003 (Memory Card implementation)

## Status

✅ **Completed** - Frontend fix implemented and built successfully. Pending user verification.
