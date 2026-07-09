# Image Loading CORS Fix

**Date**: 2026-07-10
**Task**: Chat-AI 图片上传后背景图不更新、封面图显示时有时无问题排查

## Problem Description

用户在 VPS 环境中遇到两个问题：
1. Chat-AI 界面图片上传后不会更新背景图
2. Memory Garden 封面图显示会时有时无

## Root Cause Analysis

经过详细排查，定位到根本原因：

### 技术细节

1. **`ParticleWaveHero` 组件设置 CORS 要求**
   - 文件：`frontend/src/components/ParticleWaveHero.jsx:382`
   - 代码：`image.crossOrigin = 'anonymous'`
   - 效果：要求服务器返回 CORS headers（`Access-Control-Allow-Origin`）

2. **FastAPI 静态文件服务不经过 CORS 中间件**
   - 文件：`backend/app/main.py:35`
   - 代码：`app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")`
   - 问题：`StaticFiles` 挂载点绕过了 `CORSMiddleware`，直接返回文件而不添加 CORS headers

3. **nginx 代理未配置 CORS headers**
   - 文件：`nginx/nginx.conf:99-107`
   - 代码：`location /uploads/ { proxy_pass http://backend/uploads/; ... }`
   - 问题：nginx 也没有添加 CORS headers

### 失败链路

```
Browser 请求图片 → 设置 crossOrigin='anonymous' 
    → nginx 代理到后端 StaticFiles 
    → StaticFiles 返回文件（无 CORS headers）
    → Browser 拒绝加载图片（CORS 错误）
    → ParticleWaveHero 图片加载失败
    → 背景图不更新，封面图不显示
```

## Solution

**移除 `ParticleWaveHero` 中的 `image.crossOrigin = 'anonymous'` 设置**

### 理由

1. **同源访问**：图片通过 nginx 代理或后端静态文件服务从同一域名加载
2. **不需要跨域**：不需要 `crossOrigin` 属性
3. **简化配置**：避免在生产环境配置 CORS headers 的复杂性

### 代码修改

```diff
function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
-   image.crossOrigin = 'anonymous';
+   // Removed crossOrigin = 'anonymous' because:
+   // 1. Images are served from the same origin (via nginx proxy or backend static files)
+   // 2. StaticFiles mount points in FastAPI don't go through CORS middleware
+   // 3. Setting crossOrigin caused image loading failures in production (VPS)
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = src;
  });
}
```

## Files Modified

- `frontend/src/components/ParticleWaveHero.jsx` - 移除 `crossOrigin` 设置

## Verification

### 本地验证

```bash
cd frontend
npm run build
# Result: ✓ built in 4.07s
```

### VPS 部署步骤

1. 同步代码到 VPS
2. 重建前端容器：
   ```bash
   ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml build frontend"
   ```
3. 重启前端容器：
   ```bash
   ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml up -d frontend"
   ```
4. 验证图片上传和显示功能

## Expected Behavior

修复后：
- Chat-AI 界面上传图片后，背景图立即更新
- Memory Garden 封面图稳定显示，不会时有时无
- 图片可以正常加载并显示

## Technical Notes

### 为什么 StaticFiles 不经过 CORS 中间件

FastAPI 的中间件机制：
- 中间件在 `Starlette` 层处理请求
- `app.mount()` 直接挂载 `ASGI` 应用（`StaticFiles`）
- 请求到达 `StaticFiles` 后直接返回文件，不经过 FastAPI 路由处理
- 因此 `CORSMiddleware` 无法拦截这些请求

### 替代方案（未采用）

1. **方案 B：nginx 添加 CORS headers**
   - 优点：后端无需改动
   - 缺点：增加 nginx 配置复杂性

2. **方案 C：使用 FastAPI 路由提供静态文件**
   - 优点：可以经过 CORS 中间件
   - 缺点：需要重写静态文件服务逻辑

采用方案 A（移除 `crossOrigin`）是最简单且最有效的解决方案。

## Related Issues

- TASK-034: 聊天背景动画效果修复
- TASK-024: 图片上传后直接用作背景和封面
