@echo off
chcp 65001 >nul 2>&1
REM ========================================
REM PC-UI 认证功能测试脚本
REM ========================================

echo ====================================
echo BDC-AI PC-UI 认证功能测试
echo ====================================
echo.

REM 检查后端是否运行
echo [1/4] 检查后端服务状态...
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 后端服务运行中 (http://localhost:8000)
) else (
    echo ✗ 后端服务未运行，请先启动后端：
    echo   python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
    pause
    exit /b 1
)
echo.

REM 检查 PC-UI 是否运行
echo [2/4] 检查 PC-UI 服务状态...
curl -s http://localhost:8080 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ PC-UI 服务运行中 (http://localhost:8080)
) else (
    echo ✗ PC-UI 服务未运行，正在启动...
    start "BDC-AI PC-UI" python -m desktop.nicegui_app.pc_app
    echo 等待 PC-UI 启动...
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:8080 >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ PC-UI 启动成功
    ) else (
        echo ✗ PC-UI 启动失败
        pause
        exit /b 1
    )
)
echo.

echo [3/4] 测试步骤说明：
echo.
echo 1. 打开浏览器访问: http://localhost:8080
echo 2. 应该自动跳转到登录页面 (http://localhost:8080/login)
echo 3. 使用以下凭证登录：
echo    用户名: admin
echo    密码: admin123
echo 4. 登录成功后应该跳转到主页
echo 5. 验证页面右上角显示用户信息和登出按钮
echo 6. 点击刷新按钮，验证登录状态保持
echo 7. 点击登出按钮，验证跳转回登录页
echo.

echo [4/4] 打开浏览器...
start http://localhost:8080
echo.

echo ====================================
echo 测试准备完成！
echo 请按照上述步骤在浏览器中测试
echo ====================================
echo.

echo 按任意键查看测试后端日志...
pause >nul

echo.
echo ====================================
echo 后端服务日志（最近 20 行）
echo ====================================
echo.

REM 如果后端在单独的窗口，无法直接获取日志
echo 提示：请查看后端运行窗口的日志输出
echo.

pause
