# GLM-4V Scene Issue Worker 启动脚本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GLM-4V Scene Issue Worker 启动向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否设置了必需的环境变量
$backendUrl = $env:BDC_BACKEND_BASE_URL
$storageDir = $env:BDC_LOCAL_STORAGE_DIR
$glmApiKey = $env:GLM_API_KEY

if (-not $backendUrl) {
    Write-Host "❌ 错误: BDC_BACKEND_BASE_URL 环境变量未设置" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先设置环境变量：" -ForegroundColor Yellow
    Write-Host '`$env:BDC_BACKEND_BASE_URL = "http://127.0.0.1:8000"' -ForegroundColor White
    Write-Host '`$env:BDC_LOCAL_STORAGE_DIR = "d:\Huawei Files\华为家庭存储\Programs\program-bdc-ai\data\local_storage"' -ForegroundColor White
    Write-Host '`$env:GLM_API_KEY = "你的_GLM_API_KEY"' -ForegroundColor White
    Write-Host ""
    exit 1
}

if (-not $storageDir) {
    Write-Host "⚠️  警告: BDC_LOCAL_STORAGE_DIR 未设置，使用默认值 ./data/local_storage" -ForegroundColor Yellow
}

if (-not $glmApiKey) {
    Write-Host "❌ 错误: GLM_API_KEY 环境变量未设置" -ForegroundColor Red
    Write-Host ""
    Write-Host "请访问 https://open.bigmodel.cn/ 获取 API Key" -ForegroundColor Yellow
    Write-Host "然后设置: `$env:GLM_API_KEY = \"your-api-key\"`" -ForegroundColor White
    Write-Host ""
    exit 1
}

# 显示配置信息
Write-Host "✓ 环境变量检查通过" -ForegroundColor Green
Write-Host ""
Write-Host "当前配置：" -ForegroundColor Cyan
Write-Host "  后端地址: $backendUrl" -ForegroundColor White
Write-Host "  存储目录: $storageDir" -ForegroundColor White
Write-Host "  API Key: $($glmApiKey.Substring(0, 10))..." -ForegroundColor White
Write-Host ""

# 检查依赖是否安装
Write-Host "检查 Python 依赖..." -ForegroundColor Cyan
try {
    $null = python -c "import requests, openai, PIL" 2>&1
    Write-Host "✓ 依赖已安装" -ForegroundColor Green
} catch {
    Write-Host "⚠️  依赖未完全安装，正在安装..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ 依赖安装完成" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动 Worker..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Worker 将每 $($env:BDC_SCENE_WORKER_POLL_INTERVAL) 秒轮询一次待处理的 scene_issue 图片" -ForegroundColor White
Write-Host "按 Ctrl+C 停止 Worker" -ForegroundColor Yellow
Write-Host ""

# 启动 Worker
python scene_issue_glm_worker.py
