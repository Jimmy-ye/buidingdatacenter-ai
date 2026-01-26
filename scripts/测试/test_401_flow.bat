@echo off
chcp 65001 >nul 2>&1
REM ========================================
REM 401 自动处理测试脚本
REM ========================================

echo ====================================
echo BDC-AI 401 自动处理测试
echo ====================================
echo.

REM 检查环境
echo [检查] 测试环境...
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 后端服务未运行
    echo.
    echo 请先启动后端：
    echo   python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000
    echo.
    pause
    exit /b 1
)

curl -s http://localhost:8080 >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] PC-UI 服务未运行
    echo.
    echo 请先启动 PC-UI：
    echo   python -m desktop.nicegui_app.pc_app
    echo.
    pause
    exit /b 1
)

echo [OK] 所有服务运行正常
echo.

echo ====================================
echo 测试步骤
echo ====================================
echo.
echo 1. 打开浏览器访问: http://localhost:8080
echo.
echo 2. 使用 admin/admin123 登录系统
echo.
echo 3. 访问测试页面: http://localhost:8080/test-401
echo.
echo 4. 在测试页面中依次点击三个测试按钮：
echo.
echo    场景 1: 使用无效 Token
echo    场景 2: 模拟过期 Token
echo    场景 3: 无 Token 访问
echo.
echo 5. 验证每个场景是否：
echo    ✓ 自动跳转到登录页
echo    ✓ 显示"登录已过期"通知
echo    ✓ Token 已被清除
echo.
echo ====================================
echo 正在打开浏览器...
echo ====================================
echo.

start http://localhost:8080
timeout /t 2 /nobreak >nul
start http://localhost:8080/test-401

echo.
echo 浏览器已打开，请按照上述步骤进行测试
echo.
echo 详细测试指南: scripts\测试\test_401_manual.md
echo.
pause
