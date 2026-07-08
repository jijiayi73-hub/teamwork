# Log 16 - Windows start.bat 启动脚本修复

## Log ID and Date

- Log ID: 16
- Date: 2026-07-08
- Branch: `backend/chat-database-schema`

## Goal

修复用户在 PowerShell 中运行 `scripts/start.bat` 时出现的命令识别和 batch 解析错误。

## Existing Context

用户先在 `E:\Project\teamwork\scripts` 中运行：

```powershell
start.bat
```

PowerShell 报错：当前目录命令需要显式写成 `.\start.bat`。

用户随后运行：

```powershell
.\start.bat
```

`cmd.exe` 将 batch 文件切成大量碎片命令，例如 `"PROJECT_ROOT=..\"`、`level`、`m`、`rements.txt"` 等，并且中文输出显示为 mojibake。

## Progress Truth Audit Summary

| Claim | Evidence read | Verdict |
| --- | --- | --- |
| PowerShell 需要 `.\start.bat` | 用户终端输出 | verified |
| `start.bat` 被 cmd 错读 | 用户终端输出；本地 `cmd /d /c "scripts\start.bat --check"` 复现 | verified |
| 文件为 LF-only batch | byte check: `CRCount=0`, `LFCount=289` | verified |
| 修复后 cmd 可解析 | `cmd /d /c "scripts\start.bat --check"` | verified |

## Changes Made

| 文件 | 操作 | 原因 |
| --- | --- | --- |
| `scripts/start.bat` | 重写为 ASCII + CRLF | 避免 Windows batch 编码和 LF-only 解析问题 |
| `scripts/start.bat` | 新增 `--check` 参数 | 安全验证路径、Python、npm.cmd，不启动服务 |

## Validation

```powershell
cmd /d /c "scripts\start.bat --check"
```

结果：

```text
Inner Garden starting...
Project root: E:\Project\teamwork

Check OK.
Python command: py
npm command: npm.cmd
Backend: E:\Project\teamwork\backend
Frontend: E:\Project\teamwork\frontend
```

字节检查结果：

- `CRCount=151`
- `LFCount=151`
- `NulCount=0`
- 文件开头为 ASCII `@echo off\r\n`

## Final Result

`scripts/start.bat` 现在可以被 `cmd.exe` 正常解析。PowerShell 中应使用：

```powershell
cd E:\Project\teamwork\scripts
.\start.bat
```

或先自检：

```powershell
.\start.bat --check
```

## Conclusion

PASS: Windows batch 启动脚本的解析问题已修复并通过 `--check` 验证。
