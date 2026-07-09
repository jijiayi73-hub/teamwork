# Log-43: Monthly Report 日历卡片溢出修复

## 任务信息

**任务类型**: Bug Fix
**日期**: 2026-07-10
**相关组件**: Monthly Report Page
**问题来源**: VPS 用户反馈

## 问题描述

用户报告 Monthly Diary (月记) 页面中，每天的显示组件依旧超出框架边界。

## 根本原因

分析 CSS 样式发现三个溢出来源：

1. **情绪点阴影溢出**: `.monthly-report-emotion-dot` 的 `box-shadow: 0 6px 16px rgba(0, 0, 0, 0.28)` 向外延伸 16px，超出卡片边界
2. **Hover 阴影**: `:hover` 状态的 `box-shadow: 0 8px 18px` 向外延伸 18px
3. **Focus 轮廓**: `:focus-visible` 的 `outline` 配合 `outline-offset: 2px` 向外延伸 5px

## 修复方案

### 修改文件
- `frontend/src/styles.css`

### 具体变更

1. **基础状态添加溢出裁剪**
   ```css
   .monthly-report-day {
     /* ...existing styles... */
     overflow: hidden; /* 新增 */
   }
   ```

2. **Hover 状态允许阴影显示**
   ```css
   .monthly-report-day:hover {
     overflow: visible; /* 新增，允许 hover 阴影显示 */
     /* ...existing styles... */
   }
   ```

3. **Focus 状态允许轮廓显示**
   ```css
   .monthly-report-day:focus-visible {
     overflow: visible; /* 新增，允许 focus 轮廓显示 */
     /* ...existing styles... */
   }
   ```

4. **优化情绪点阴影**
   ```css
   .monthly-report-emotion-dot {
     box-shadow:
       0 0 0 3px rgba(255, 255, 255, 0.08),
       0 2px 8px rgba(0, 0, 0, 0.35); /* 从 0 6px 16px 减小到 0 2px 8px */
   }
   ```

## 验证结果

```bash
cd frontend
npm run build
# ✓ built in 2.72s
```

## 预期效果

- 默认状态下，情绪点阴影被裁剪在卡片内
- Hover 和 Focus 状态下，阴影和轮廓可以正常显示（视觉溢出是有意的设计效果）
- 卡片本身不会因为内部阴影而撑大容器

## 风险与限制

无。修改仅影响 Monthly Report 页面的日历卡片样式，为纯 CSS 变更。

## 部署建议

修复已完成，需要重新构建前端并部署到 VPS：

```bash
# 在 VPS 上
cd /opt/inner-garden
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```
