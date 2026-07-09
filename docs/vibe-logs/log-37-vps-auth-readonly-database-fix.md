# VPS 认证只读数据库修复

**Date**: 2026-07-09
**Issue**: VPS 上无法注册和登录，显示"邮箱/账户可能已经被注册"
**Status**: ✅ Fixed

## Problem

生产环境 (https://jijiayi.online) 注册和登录功能完全失败：
- 无论使用任何邮箱/账户都显示"邮箱/账户可能已经被注册"
- 后端日志显示：`sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) attempt to write a readonly database`

## Root Cause

**用户 ID 不匹配**：
- `docker-compose.prod.yml` 配置 `user: "1000:1001"`
- 但数据目录 `/opt/inner-garden/backend/data/` 归 uid 999 所有
- Dockerfile 中创建的 `appuser` uid 为 999，与 docker-compose 中的 1000 不一致

**文件权限映射**：
```
主机视图：1000:1001 → ubuntu:ubuntu
容器视图：1000:1001 → appuser:appuser (内部显示)
```

## Solution

1. **修改数据目录权限**：
```bash
ssh vps "sudo chown -R 1000:1001 /opt/inner-garden/backend/data/"
```

2. **重启后端容器**：
```bash
ssh vps "docker compose -f /opt/inner-garden/docker-compose.prod.yml restart backend"
```

## Verification

```bash
# 注册测试
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser1783611347","email":"test1783611347@example.com","password":"testpass123"}'
# 结果：{"success":true,...}

# 登录测试
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"testuser1783611347","password":"testpass123"}'
# 结果：{"success":true,...}
```

## Changes

| Item | Before | After |
|------|--------|-------|
| `/opt/inner-garden/backend/data/` ownership | 999:999 (lxd:docker) | 1000:1001 (ubuntu:ubuntu) |
| Registration | ❌ Readonly database | ✅ Working |
| Login | ❌ Readonly database | ✅ Working |

## Prevention

建议同步 Dockerfile 和 docker-compose 中的用户配置：

**方案 1**：修改 docker-compose.prod.yml，移除 `user: "1000:1001"` 指令

**方案 2**：修改 Dockerfile，创建 uid 1000 的用户：
```dockerfile
RUN groupadd -g 1000 appuser && useradd -u 1000 -g 1000 appuser
```

## Related Files

- `docker-compose.prod.yml` - Line 8: `user: "1000:1001"`
- `backend/Dockerfile` - Line 29: Creates user with uid 999
- `/opt/inner-garden/backend/data/` - Data directory that needs correct ownership

## Impact

- **API**: None
- **Database**: None (permission fix only)
- **Frontend**: None (backend issue)
- **Users**: Can now register and login
