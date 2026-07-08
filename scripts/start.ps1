# Inner Garden 一键启动脚本 (PowerShell)
# 支持：自动依赖检测、首次安装、并行启动前后端、优雅停止

#Requires -Version 5.1

# 颜色输出函数
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Green { Write-ColorOutput Green $args }
function Write-Blue { Write-ColorOutput Cyan $args }
function Write-Yellow { Write-ColorOutput Yellow $args }
function Write-Red { Write-ColorOutput Red $args }

# 错误处理
$ErrorActionPreference = "Stop"

# ============================================================================
# 1. 初始化
# ============================================================================
Write-Host ""
Write-Blue "🌱 Inner Garden 一键启动 (PowerShell)"
Write-Host ""

# 项目路径
$ScriptRoot = $PSScriptRoot
$ProjectRoot = Split-Path $ScriptRoot -Parent
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$LogDir = Join-Path $ProjectRoot "logs"
$PidFile = Join-Path $LogDir "pids.json"

# 创建日志目录
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# ============================================================================
# 2. 环境检测
# ============================================================================
Write-Yellow "[1/6] 检测环境依赖..."

# 检测 Node.js
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Red "❌ 未找到 Node.js，请先安装: https://nodejs.org/"
    exit 1
}
$NodeVersion = node --version
Write-Host "  ✅ Node.js: $NodeVersion"

# 检测 npm
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Red "❌ 未找到 npm"
    exit 1
}
$NpmVersion = npm --version
Write-Host "  ✅ npm: $NpmVersion"

# 检测 Python
$PythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
    $PythonVersion = py --version
    Write-Host "  ✅ Python: $PythonVersion"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
    $PythonVersion = python --version
    Write-Host "  ✅ Python: $PythonVersion"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
    $PythonVersion = python3 --version
    Write-Host "  ✅ Python: $PythonVersion"
} else {
    Write-Red "❌ 未找到 Python，请先安装: https://www.python.org/"
    exit 1
}

# 检测 pip
& $PythonCmd -m pip --version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Red "❌ 未找到 pip"
    exit 1
}
$PipVersion = & $PythonCmd -m pip --version
Write-Host "  ✅ pip: $PipVersion"

# ============================================================================
# 3. 后端依赖检查
# ============================================================================
Write-Host ""
Write-Yellow "[2/6] 检查后端依赖..."

$VenvDir = Join-Path $BackendDir "venv"
$InstalledFlag = Join-Path $BackendDir ".installed"

if (!(Test-Path $VenvDir)) {
    Write-Host "  🔧 创建虚拟环境..."
    & $PythonCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Red "❌ 虚拟环境创建失败"
        exit 1
    }
    Write-Green "  ✅ 虚拟环境已创建"
} else {
    Write-Host "  ✅ 虚拟环境已存在"
}

# 激活虚拟环境
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    . $ActivateScript
} else {
    Write-Red "❌ 未找到虚拟环境激活脚本"
    exit 1
}

# 检查依赖是否安装
try {
    & $PythonCmd -c "import fastapi" | Out-Null
    Write-Host "  ✅ 后端依赖已存在"
} catch {
    Write-Host "  🔧 安装后端依赖..."
    & $PythonCmd -m pip install -q -r (Join-Path $BackendDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        Write-Red "❌ 依赖安装失败"
        exit 1
    }
    New-Item -ItemType File -Path $InstalledFlag | Out-Null
    Write-Green "  ✅ 后端依赖已安装"
}

# ============================================================================
# 4. 后端配置检查
# ============================================================================
Write-Host ""
Write-Yellow "[3/6] 检查后端配置..."

$EnvFile = Join-Path $BackendDir ".env"
$EnvExample = Join-Path $BackendDir ".env.example"

if (!(Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Write-Host "  🔧 从 .env.example 创建 .env..."
        Copy-Item $EnvExample $EnvFile
        Write-Green "  ✅ .env 已创建"
        Write-Yellow "  ⚠️  请检查并配置 $EnvFile 中的 API 密钥"
    } else {
        Write-Yellow "  ⚠️  未找到 .env.example，跳过配置"
    }
} else {
    Write-Host "  ✅ .env 已存在"
}

# ============================================================================
# 5. 前端依赖检查
# ============================================================================
Write-Host ""
Write-Yellow "[4/6] 检查前端依赖..."

$NodeModulesDir = Join-Path $FrontendDir "node_modules"
$PackageJson = Join-Path $FrontendDir "package.json"

if (!(Test-Path $NodeModulesDir)) {
    Write-Host "  🔧 安装前端依赖..."
    Push-Location $FrontendDir
    npm install --silent --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Red "❌ 前端依赖安装失败"
        exit 1
    }
    Pop-Location
    Write-Green "  ✅ 前端依赖已安装"
} else {
    Write-Host "  ✅ 前端依赖已存在"
}

# ============================================================================
# 6. 检查旧进程
# ============================================================================
Write-Host ""
Write-Yellow "[5/6] 检查旧进程..."

# 检查端口占用
$Port8000InUse = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
$Port5173InUse = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue

if ($Port8000InUse) {
    Write-Yellow "  ⚠️  端口 8000 已被占用 (OwningProcess: $($Port8000InUse.OwningProcess))"
    Write-Host "     提示: 可能已有后端服务在运行"
} else {
    Write-Host "  ✅ 端口 8000 可用"
}

if ($Port5173InUse) {
    Write-Yellow "  ⚠️  端口 5173 已被占用 (OwningProcess: $($Port5173InUse.OwningProcess))"
    Write-Host "     提示: 可能已有前端服务在运行"
} else {
    Write-Host "  ✅ 端口 5173 可用"
}

# ============================================================================
# 7. 启动服务
# ============================================================================
Write-Host ""
Write-Yellow "[6/6] 启动服务..."
Write-Host ""

# 清理旧 PID 文件
if (Test-Path $PidFile) {
    Remove-Item $PidFile
}

# 准备启动信息
$ProcessInfo = @{}

# 启动后端
Write-Blue "🚀 启动后端 (Uvicorn)..."

$BackendLog = Join-Path $LogDir "backend.log"
$BackendPidFile = Join-Path $LogDir "backend.pid"

# 使用 Start-Process 启动后端
$BackendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory $BackendDir -PassThru -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendLog

if ($BackendProcess) {
    $ProcessInfo.BackendPid = $BackendProcess.Id
    $BackendProcess.Id | Out-File -FilePath $BackendPidFile
    Write-Green "  ✅ 后端已启动 (PID: $($BackendProcess.Id))"
} else {
    Write-Red "❌ 后端启动失败"
    exit 1
}

# 等待后端启动
Start-Sleep -Seconds 3

# 检查后端是否仍在运行
$BackendRunning = Get-Process -Id $BackendProcess.Id -ErrorAction SilentlyContinue
if (!$BackendRunning) {
    Write-Red "❌ 后端启动后崩溃，查看日志: $BackendLog"
    Get-Content $BackendLog | Select-Object -Last 20
    exit 1
}

# 启动前端
Write-Blue "🚀 启动前端 (Vite)..."

$FrontendLog = Join-Path $LogDir "frontend.log"
$FrontendPidFile = Join-Path $LogDir "frontend.pid"

$FrontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -PassThru -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendLog

if ($FrontendProcess) {
    $ProcessInfo.FrontendPid = $FrontendProcess.Id
    $FrontendProcess.Id | Out-File -FilePath $FrontendPidFile
    Write-Green "  ✅ 前端已启动 (PID: $($FrontendProcess.Id))"
} else {
    Write-Red "❌ 前端启动失败"
    # 清理后端
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# 保存 PID 信息
$ProcessInfo | ConvertTo-Json | Out-File -FilePath $PidFile

# 等待前端启动
Start-Sleep -Seconds 2

# 检查前端是否仍在运行
$FrontendRunning = Get-Process -Id $FrontendProcess.Id -ErrorAction SilentlyContinue
if (!$FrontendRunning) {
    Write-Red "❌ 前端启动后崩溃，查看日志: $FrontendLog"
    Get-Content $FrontendLog | Select-Object -Last 20
    # 清理后端
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# ============================================================================
# 8. 服务信息
# ============================================================================
Write-Host ""
Write-Green "========================================"
Write-Green "🎉 Inner Garden 已启动!"
Write-Green "========================================"
Write-Host ""
Write-Host "  📡 后端 API:   " -NoNewline; Write-Blue "http://localhost:8000"
Write-Host "  📄 API 文档:   " -NoNewline; Write-Blue "http://localhost:8000/docs"
Write-Host "  🌐 前端界面:   " -NoNewline; Write-Blue "http://localhost:5173"
Write-Host ""
Write-Host "  后端日志: " -NoNewline; Write-Yellow $BackendLog
Write-Host "  前端日志: " -NoNewline; Write-Yellow $FrontendLog
Write-Host ""
Write-Yellow "  按 Ctrl+C 停止所有服务"
Write-Host ""

# ============================================================================
# 9. 优雅停止处理
# ============================================================================
$StopRequested = $false

function Stop-Services {
    if ($StopRequested) { return }
    $StopRequested = $true

    Write-Host ""
    Write-Yellow "🛑 正在停止服务..."

    # 读取 PID 文件
    if (Test-Path $PidFile) {
        $ProcessInfo = Get-Content $PidFile | ConvertFrom-Json

        if ($ProcessInfo.BackendPid) {
            try {
                Stop-Process -Id $ProcessInfo.BackendPid -Force -ErrorAction Stop
                Write-Green "  ✅ 后端已停止"
            } catch {
                Write-Yellow "  ⚠️  后端进程可能已停止"
            }
        }

        if ($ProcessInfo.FrontendPid) {
            try {
                Stop-Process -Id $ProcessInfo.FrontendPid -Force -ErrorAction Stop
                Write-Green "  ✅ 前端已停止"
            } catch {
                Write-Yellow "  ⚠️  前端进程可能已停止"
            }
        }

        Remove-Item $PidFile
    }

    # 清理 PID 文件
    if (Test-Path $BackendPidFile) { Remove-Item $BackendPidFile }
    if (Test-Path $FrontendPidFile) { Remove-Item $FrontendPidFile }

    Write-Green "👋 再见!"
    exit 0
}

# 注册 Ctrl+C 处理
$Handle = [System.Console]::CancelKeyPress.Register({
    Stop-Services
}.GetNewClosure())

# 等待用户中断
try {
    # 定期检查进程状态
    while ($true) {
        Start-Sleep -Seconds 5

        $BackendAlive = Get-Process -Id $BackendProcess.Id -ErrorAction SilentlyContinue
        $FrontendAlive = Get-Process -Id $FrontendProcess.Id -ErrorAction SilentlyContinue

        if (!$BackendAlive -or !$FrontendAlive) {
            Write-Yellow "⚠️  检测到服务已停止"
            Stop-Services
        }
    }
} finally {
    [System.Console]::CancelKeyPress.Unregister($Handle)
    Stop-Services
}
