@echo off
chcp 65001 >nul 2>&1
REM ========================================
REM PC-UI 认证功能自动化测试
REM ========================================

echo ====================================
echo BDC-AI 认证功能测试
echo ====================================
echo.

REM 切换到项目根目录
cd /d "%~dp0..\.."

echo [提示] 此脚本将测试后端认证功能
echo.

echo [步骤 1] 检查后端服务...
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 后端服务未运行
    echo.
    echo 请先启动后端服务：
    echo   python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
    echo.
    echo 或运行启动脚本：
    echo   scripts\start_backend.bat
    echo.
    pause
    exit /b 1
)

echo [成功] 后端服务运行中
echo.

echo [步骤 2] 运行测试脚本...
echo.
python "scripts\测试\test_auth_manual.py"

echo.
echo ====================================
echo 测试完成
echo ====================================
echo.
pause
