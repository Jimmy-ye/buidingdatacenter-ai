@echo off
REM Flutter 国内镜像源配置脚本
REM 使用方法：双击运行或在命令行执行

echo ========================================
echo Flutter 国内镜像源配置
echo ========================================
echo.

REM 设置环境变量
set PUB_HOSTED_URL=https://pub.flutter-io.cn
set FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn

echo 当前环境变量：
echo PUB_HOSTED_URL = %PUB_HOSTED_URL%
echo FLUTTER_STORAGE_BASE_URL = %FLUTTER_STORAGE_BASE_URL%
echo.

echo ========================================
echo 镜像源已临时设置（仅当前窗口有效）
echo ========================================
echo.

echo 现在可以运行 Flutter 命令了：
echo   flutter --version
echo   flutter doctor
echo.

REM 保持窗口打开
cmd /k
