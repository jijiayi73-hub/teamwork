# TASK-018: Username/Email Login Support

**Date**: 2026-07-09
**Owner**: Codex
**Branch**: `codex/sync-scripts-to-main`
**Status**: Complete

## 目标

登录界面第一个表格支持用户名或邮箱登录都可以。

## 修改内容

### Backend Schema

**File**: `backend/app/schemas/auth.py`

- `UserLogin.email` → `UserLogin.username_or_email`
- 字段类型从 `DevelopmentEmailStr` 改为 `str = Field(min_length=2, max_length=128)`

```python
class UserLogin(BaseModel):
    username_or_email: str = Field(min_length=2, max_length=128)
    password: str
```

### Backend Router

**File**: `backend/app/routers/auth.py`

- 查询逻辑支持 `or_(User.username == ..., User.email == ...)`
- 错误提示从 "Invalid email or password" 改为 "Invalid username, email or password"

```python
@router.post("/login", response_model=ApiResponse[TokenRead])
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(User.username == payload.username_or_email, User.email == payload.username_or_email)
    ).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username, email or password")
```

### Frontend Auth API

**File**: `frontend/src/api/auth.js`

- `login()` 函数参数从 `email` 改为 `usernameOrEmail`
- 请求体字段从 `{ email, password }` 改为 `{ username_or_email, password }`
- 错误处理统一返回简体中文，隐藏技术细节：
  - 登录失败: "用户名、邮箱或密码错误"
  - 注册失败: "注册失败，用户名或邮箱可能已被使用"

### Frontend Login Page

**File**: `frontend/src/components/LoginPage.jsx`

- 标签从 "邮箱" 改为 "用户名/邮箱"
- placeholder 从 "your@email.com" 改为 "用户名或邮箱"
- 输入类型从 `type="email"` 改为 `type="text"`

## 验证

```bash
cd backend
py -c "from app.schemas.auth import UserLogin; print('Fields:', [f for f in UserLogin.model_fields])"
# Result: Fields: ['username_or_email', 'password']

cd frontend
npm run build
# Result: ✓ built in 2.85s
```

## Bug Fix: 初始实现遗漏

**问题**: 初始实现只更新了 Schema 和 Router，遗漏了 `frontend/src/api/auth.js` 中的请求体字段名。

**修复**: 将 `body: JSON.stringify({ email, password })` 改为 `body: JSON.stringify({ username_or_email: usernameOrEmail, password })`

## API 契约变更

**POST /api/v1/auth/login**

|  | 之前 | 现在 |
|---|---|---|
| Request Body | `{ email, password }` | `{ username_or_email, password }` |
| Response | unchanged | unchanged |

## 风险与限制

- 破坏性 API 变更：任何直接调用登录 API 的客户端需要同步更新字段名
- 前端已同步更新，内部集成无风险
