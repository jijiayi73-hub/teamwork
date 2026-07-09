# Frontend Auth.js readJsonResponse Fix

**Date**: 2026-07-09
**Issue**: I-012
**Status**: ✅ Fixed
**Related**: TASK-029

## Problem

Production environment reported: `readJsonResponse is not defined`

## Root Cause Analysis

In `frontend/src/api/auth.js`, two issues were found:

1. **Missing function definition**: The original file (HEAD commit) called `readJsonResponse(response, fallback)` in the `login()` and `register()` functions, but the function was not defined anywhere in the file.

2. **Missing variable in login()**: The `login()` function referenced a `fallback` variable that was never defined in its scope. The `register()` function correctly defined this variable.

Original code (line 117 in HEAD):
```javascript
export async function login(usernameOrEmail, password) {
  // ...
  const payload = await readJsonResponse(response, fallback); // 'fallback' is undefined!
  // ...
}
```

## Solution

1. Added the `readJsonResponse` helper function (local to the module):
```javascript
async function readJsonResponse(response, fallback) {
  try {
    return await response.json();
  } catch {
    throw new Error(fallback || '请求失败，请稍后重试');
  }
}
```

2. Added the missing `fallback` variable in `login()`:
```javascript
export async function login(usernameOrEmail, password) {
  const fallback = '登录失败，请确认后端服务已启动并稍后重试';
  const response = await fetch('/api/v1/auth/login', {
    // ...
  });
  const payload = await readJsonResponse(response, fallback);
  // ...
}
```

## Changes

| File | Change |
|------|--------|
| `frontend/src/api/auth.js` | Added `readJsonResponse` function definition |
| `frontend/src/api/auth.js` | Added `fallback` variable in `login()` function |

## Validation

```bash
cd frontend
npm run build
# Result: ✓ built in 2.00s
```

Build successful with no errors.

## Impact

- **API**: None
- **Database**: None
- **Frontend**: Authentication (login/register) now works correctly

## Prevention

- Ensure all helper functions are defined before use
- Use ESLint or similar tools to catch undefined variable references at build time
- Review code for undefined variables before committing

## Production Deployment

To deploy this fix to production:
1. Commit the changes to the branch
2. Merge to main
3. Run the deployment workflow to rebuild and redeploy frontend container
