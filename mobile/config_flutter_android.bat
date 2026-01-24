@echo off
REM 配置 Flutter Android SDK 路径

echo ========================================
echo Flutter Android SDK 配置
echo ========================================
echo.

echo 正在设置环境变量...
set ANDROID_SDK_ROOT=C:\Users\86152\AppData\Local\Android\Sdk
set ANDROID_HOME=C:\Users\86152\AppData\Local\Android\Sdk

echo 正在配置 Flutter...
flutter config --android-sdk "C:\Users\86152\AppData\Local\Android\Sdk"

echo.
echo ========================================
echo 验证配置结果
echo ========================================
echo.
flutter doctor --android-licenses

echo.
echo 如果上面显示 Android SDK 许可证接受提示，则配置成功！
pause
