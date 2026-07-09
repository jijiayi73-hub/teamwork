# VPS 502 错误修复记录

**Date**: 2026-07-10
**Issue**: VPS 线上记忆花园加载失败：Request failed: 502
**Root Cause**: `aiohttp` 依赖缺失

## 问题诊断

### 症状
- 前端显示：`Request failed: 502`
- 记忆花园功能无法使用

### 根本原因
后端容器启动失败，日志显示：
```
ModuleNotFoundError: No module named 'aiohttp'
```

**问题链路**：
1. TASK-037 AI朗读功能在本地开发时添加了 `aiohttp` 到 `requirements.txt`
2. 部署到 VPS 时，旧的 `requirements.txt` 被使用（没有 aiohttp）
3. 后端导入 `volcengine_tts/http_client.py` 时失败
4. 后端服务无法启动 → Nginx 返回 502 Bad Gateway

## 修复步骤

### 1. 同步 requirements.txt
```bash
scp backend/requirements.txt vps:/tmp/
ssh vps "sudo cp /tmp/requirements.txt /opt/inner-garden/backend/requirements.txt"
```

### 2. 重建后端容器
```bash
ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml build --no-cache backend"
```

### 3. 重启服务
```bash
ssh vps "cd /opt/inner-garden && docker compose -f docker-compose.prod.yml up -d"
```

## 验证结果

| 检查项 | 结果 |
|--------|------|
| 后端容器健康状态 | ✅ healthy |
| 本地健康检查 | ✅ 正常 |
| 公网 API | ✅ 正常 |
| Memory Garden API | ✅ 正常 |

## 预防措施

1. **部署前检查依赖同步**：确保 `requirements.txt` 同步到 VPS
2. **添加依赖检查**：在部署脚本中验证依赖完整性
3. **CI/CD 改进**：自动化依赖同步和镜像重建流程

## 相关文件

- `backend/requirements.txt` - 添加了 `aiohttp`
- `backend/app/services/volcengine_tts/http_client.py` - 使用 aiohttp 的模块
- `scripts/vps-fix-backend.sh` - 快速修复脚本
