@echo off
chcp 65001 >nul 2>&1
REM ========================================
REM 测试环境检查脚本
REM ========================================

echo ====================================
echo BDC-AI 测试环境检查
echo ====================================
echo.

set BACKEND_OK=0
set PCUI_OK=0

REM 检查后端
echo [1/2] 检查后端服务 (localhost:8000)...
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] 后端服务运行中
    set BACKEND_OK=1
) else (
    echo     [FAIL] 后端服务未运行
    echo.
    echo     启动方法：
    echo       方法 1: scripts\start_backend.bat
    echo       方法 2: python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
)
echo.

REM 检查 PC-UI
echo [2/2] 检查 PC-UI 服务 (localhost:8080)...
curl -s http://localhost:8080 >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] PC-UI 服务运行中
    set PCUI_OK=1
) else (
    echo     [FAIL] PC-UI 服务未运行
    echo.
    echo     启动方法：
    echo       方法 1: scripts\start_pcui.bat
    echo       方法 2: python -m desktop.nicegui_app.pc_app
)
echo.

echo ====================================
echo 环境状态总结
echo ====================================
echo.
echo 后端服务:  %BACKEND_OK%
echo PC-UI 服务: %PCUI_OK%
echo.

if %BACKEND_OK%==1 (
    if %PCUI_OK%==1 (
        echo [成功] 所有服务已就绪
        echo.
        echo 下一步操作：
        echo   1. 运行自动化测试: scripts\测试\run_auth_test.bat
        echo   2. 打开浏览器测试: scripts\测试\test_pc_ui_auth_flow.bat
        echo   3. 直接访问: http://localhost:8080
    ) else (
        echo [提示] 后端已就绪，但 PC-UI 未启动
        echo.
        echo 是否启动 PC-UI? (Y/N^)
        choice /c YN /n /m "请选择: "
        if %errorlevel%==1 (
            echo.
            echo 正在启动 PC-UI...
            start "BDC-AI PC-UI" cmd /k "cd /d %~dp0..\.. && python -m desktop.nicegui_app.pc_app"
            echo 等待 PC-UI 启动...
            timeout /t 5 /nobreak >nul
            echo PC-UI 已启动
        )
    )
) else (
    echo [提示] 后端服务未运行，请先启动后端
    echo.
    echo 按任意键打开后端启动窗口...
    pause >nul
    start "BDC-AI Backend" cmd /k "cd /d %~dp0..\.. && python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo.
    echo 后端窗口已打开，请等待启动完成后再测试
)

echo.
pause
