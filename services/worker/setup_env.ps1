# GLM-4V Worker 环境变量快速设置脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GLM-4V Worker 环境配置向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置后端地址
$backendUrl = Read-Host "请输入后端服务地址（默认: http://127.0.0.1:8000）"
if (-not $backendUrl) {
    $backendUrl = "http://127.0.0.1:8000"
}
$env:BDC_BACKEND_BASE_URL = $backendUrl
Write-Host "✓ BDC_BACKEND_BASE_URL = $backendUrl" -ForegroundColor Green
Write-Host ""

# 设置存储目录
$defaultStorage = "d:\Huawei Files\华为家庭存储\Programs\program-bdc-ai\data\local_storage"
$storageDir = Read-Host "请输入本地存储目录（默认: $defaultStorage）"
if (-not $storageDir) {
    $storageDir = $defaultStorage
}
$env:BDC_LOCAL_STORAGE_DIR = $storageDir
Write-Host "✓ BDC_LOCAL_STORAGE_DIR = $storageDir" -ForegroundColor Green
Write-Host ""

# 检查目录是否存在
if (-not (Test-Path $storageDir)) {
    Write-Host "⚠️  警告: 目录不存在: $storageDir" -ForegroundColor Yellow
    $create = Read-Host "是否创建此目录？(y/n)"
    if ($create -eq "y") {
        New-Item -ItemType Directory -Path $storageDir -Force | Out-Null
        Write-Host "✓ 目录已创建" -ForegroundColor Green
    }
}
Write-Host ""

# 设置 GLM API Key
Write-Host "请输入 GLM API Key（从 https://open.bigmodel.cn/ 获取）" -ForegroundColor Cyan
$glmApiKey = Read-Host "GLM_API_KEY"
if (-not $glmApiKey) {
    Write-Host "❌ 错误: GLM_API_KEY 不能为空" -ForegroundColor Red
    exit 1
}
$env:GLM_API_KEY = $glmApiKey
Write-Host "✓ GLM_API_KEY = $($glmApiKey.Substring(0, 10))..." -ForegroundColor Green
Write-Host ""

# 可选：项目 ID 过滤
$projectId = Read-Host "可选：仅处理指定项目（留空则处理所有项目）"
if ($projectId) {
    $env:BDC_SCENE_PROJECT_ID = $projectId
    Write-Host "✓ BDC_SCENE_PROJECT_ID = $projectId" -ForegroundColor Green
}
Write-Host ""

# 轮询间隔
$pollInterval = Read-Host "轮询间隔（秒，默认: 60）"
if (-not $pollInterval) {
    $pollInterval = "60"
}
$env:BDC_SCENE_WORKER_POLL_INTERVAL = $pollInterval
Write-Host "✓ BDC_SCENE_WORKER_POLL_INTERVAL = $pollInterval" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "环境变量配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "注意：这些环境变量仅在当前 PowerShell 会话中有效" -ForegroundColor Yellow
Write-Host "如需永久生效，请将以下内容添加到系统环境变量中：" -ForegroundColor Yellow
Write-Host ""
Write-Host "`$env:BDC_BACKEND_BASE_URL = `"$backendUrl`"" -ForegroundColor White
Write-Host "`$env:BDC_LOCAL_STORAGE_DIR = `"$storageDir`"" -ForegroundColor White
Write-Host "`$env:GLM_API_KEY = `"$glmApiKey`"" -ForegroundColor White
if ($projectId) {
    Write-Host "`$env:BDC_SCENE_PROJECT_ID = `"$projectId`"" -ForegroundColor White
}
Write-Host "`$env:BDC_SCENE_WORKER_POLL_INTERVAL = `"$pollInterval`"" -ForegroundColor White
Write-Host ""
Write-Host "现在可以运行 .\start_worker.ps1 启动 Worker" -ForegroundColor Cyan
Write-Host ""
