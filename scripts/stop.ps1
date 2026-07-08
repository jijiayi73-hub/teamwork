# Inner Garden 停止脚本 (PowerShell)
# 优雅停止所有前后端服务

#Requires -Version 5.1

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Green { Write-ColorOutput Green $args }
function Write-Yellow { Write-ColorOutput Yellow $args }
function Write-Red { Write-ColorOutput Red $args }

$ErrorActionPreference = "Stop"

# 项目路径
$ScriptRoot = $PSScriptRoot
$ProjectRoot = Split-Path $ScriptRoot -Parent
$LogDir = Join-Path $ProjectRoot "logs"
$PidFile = Join-Path $LogDir "pids.json"
$BackendPidFile = Join-Path $LogDir "backend.pid"
$FrontendPidFile = Join-Path $LogDir "frontend.pid"

Write-Host ""
Write-Yellow "🛑 Inner Garden 停止服务"
Write-Host ""

$StoppedCount = 0

# 尝试从 PID 文件读取
if (Test-Path $PidFile) {
    $ProcessInfo = Get-Content $PidFile | ConvertFrom-Json

    if ($ProcessInfo.BackendPid) {
        try {
            $Process = Get-Process -Id $ProcessInfo.BackendPid -ErrorAction Stop
            Stop-Process -Id $ProcessInfo.BackendPid -Force -ErrorAction Stop
            Write-Green "✅ 后端已停止 (PID: $($ProcessInfo.BackendPid))"
            $StoppedCount++
        } catch {
            Write-Yellow "⚠️  后端进程 $($ProcessInfo.BackendPid) 未找到或已停止"
        }
    }

    if ($ProcessInfo.FrontendPid) {
        try {
            $Process = Get-Process -Id $ProcessInfo.FrontendPid -ErrorAction Stop
            Stop-Process -Id $ProcessInfo.FrontendPid -Force -ErrorAction Stop
            Write-Green "✅ 前端已停止 (PID: $($ProcessInfo.FrontendPid))"
            $StoppedCount++
        } catch {
            Write-Yellow "⚠️  前端进程 $($ProcessInfo.FrontendPid) 未找到或已停止"
        }
    }

    Remove-Item $PidFile -ErrorAction SilentlyContinue
}

# 备用：从单独的 PID 文件读取
if (Test-Path $BackendPidFile) {
    try {
        $Pid = Get-Content $BackendPidFile -Raw
        $Pid = $Pid.Trim()
        if ($Pid) {
            Stop-Process -Id $Pid -Force -ErrorAction Stop
            Write-Green "✅ 后端已停止 (PID: $Pid)"
            $StoppedCount++
        }
    } catch {
        Write-Yellow "⚠️  后端进程未找到"
    }
    Remove-Item $BackendPidFile -ErrorAction SilentlyContinue
}

if (Test-Path $FrontendPidFile) {
    try {
        $Pid = Get-Content $FrontendPidFile -Raw
        $Pid = $Pid.Trim()
        if ($Pid) {
            Stop-Process -Id $Pid -Force -ErrorAction Stop
            Write-Green "✅ 前端已停止 (PID: $Pid)"
            $StoppedCount++
        }
    } catch {
        Write-Yellow "⚠️  前端进程未找到"
    }
    Remove-Item $FrontendPidFile -ErrorAction SilentlyContinue
}

# 最后手段：按名称查找并停止
if ($StoppedCount -eq 0) {
    Write-Yellow "未找到 PID 文件，尝试按名称查找..."

    # 查找 uvicorn 进程
    $UvicornProcesses = Get-Process | Where-Object {
        $_.ProcessName -like "*python*" -or
        $_.ProcessName -like "*uvicorn*"
    }

    foreach ($Process in $UvicornProcesses) {
        try {
            $CommandLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($Process.Id)").CommandLine
            if ($CommandLine -like "*uvicorn*app.main*") {
                Stop-Process -Id $Process.Id -Force -ErrorAction Stop
                Write-Green "✅ 后端已停止 (PID: $($Process.Id))"
                $StoppedCount++
            }
        } catch {
            # 忽略无法访问的进程
        }
    }

    # 查找 vite/node 进程
    $NodeProcesses = Get-Process | Where-Object {
        $_.ProcessName -like "*node*"
    }

    foreach ($Process in $NodeProcesses) {
        try {
            $CommandLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($Process.Id)").CommandLine
            if ($CommandLine -like "*vite*") {
                Stop-Process -Id $Process.Id -Force -ErrorAction Stop
                Write-Green "✅ 前端已停止 (PID: $($Process.Id))"
                $StoppedCount++
            }
        } catch {
            # 忽略无法访问的进程
        }
    }
}

Write-Host ""
if ($StoppedCount -gt 0) {
    Write-Green "👋 已停止 $StoppedCount 个服务"
} else {
    Write-Yellow "未找到运行中的服务"
}
Write-Host ""
