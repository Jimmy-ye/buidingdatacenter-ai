# Flutter 开发环境安装指南（Windows）

## 📥 系统要求

- **操作系统**：Windows 10 或更高版本（64位）
- **磁盘空间**：至少 5 GB 可用空间
- **内存**：至少 8 GB RAM（推荐 16 GB）
- **网络**：需要互联网连接下载依赖

---

## 🔧 安装步骤

### 步骤 1：下载 Flutter SDK

**方式 A：从官网下载**（推荐）

1. 访问 Flutter 官网下载页面：
   ```
   https://docs.flutter.dev/get-started/install/windows
   ```

2. 下载最新的 **Stable 版本**
   - 推荐版本：**3.27.1** 或更高
   - 文件名：`flutter_3.27.1-stable.zip`（约 1 GB）

3. 下载完成后，解压到安装目录：
   ```powershell
   # 推荐安装路径（避免带空格和中文的路径）
   C:\dev\flutter
   ```

**方式 B：使用 Git 克隆**（高级用户）

```powershell
cd C:\dev
git clone https://github.com/flutter/flutter.git -b stable
```

---

### 步骤 2：配置环境变量

1. **打开环境变量设置**：
   - 按 `Win + X`，选择"系统"
   - 点击"高级系统设置"
   - 点击"环境变量"

2. **添加到用户变量**：
   - 在"用户变量"区域找到 `Path` 变量
   - 点击"编辑"
   - 点击"新建"
   - 添加：`C:\dev\flutter\bin`
   - 点击"确定"保存

3. **验证环境变量**：
   ```powershell
   # 关闭并重新打开命令行窗口
   flutter --version
   ```

   **期望输出**：
   ```
   Flutter 3.27.1 • channel stable
   Engine • revision
   Dart • version
   Tools • DartDev
   ```

---

### 步骤 3：运行 Flutter Doctor

```powershell
flutter doctor
```

**第一次运行会看到一些警告**，这是正常的。我们会逐步解决。

---

## 📱 安装 Android 开发环境

### 步骤 4：安装 Android Studio

1. **下载 Android Studio**：
   ```
   https://developer.android.com/studio
   ```

2. **安装 Android Studio**：
   - 运行安装程序
   - **安装选项**勾选：
     - ✅ Android SDK
     - ✅ Android SDK Platform-Tools
     - ✅ Android Virtual Device (AVD)
   - 安装路径（默认）：
     ```
     C:\Program Files\Android\Android Studio
     ```

3. **首次启动 Android Studio**：
   - 选择 "Standard" 安装类型
   - 等待下载 SDK 和组件（可能需要 30 分钟）

---

### 步骤 5：接受 Android 许可证

```powershell
flutter doctor --android-licenses
```

**提示**：输入 `y` 接受每个许可证，共约 8-10 个

---

### 步骤 6：创建 Android 虚拟设备（AVD）

1. **打开 Android Studio**
2. **打开 AVD Manager**：
   - 菜单：`Tools` → `Device Manager`
   - 或点击工具栏的设备图标

3. **创建虚拟设备**：
   - 点击 `Create Device`
   - 选择设备：**Pixel 6**
   - 点击 `Next`

4. **选择系统镜像**：
   - 推荐镜像：**Android 13.0 (API 33)**
   - 如果未下载，点击 `Download`
   - 等待下载完成（约 1-2 GB）
   - 点击 `Next`

5. **配置 AVD**：
   - AVD Name：`Pixel_6_API_33`
   - 点击 `Finish`

6. **启动 AVD**：
   - 在列表中找到 `Pixel_6_API_33`
   - 点击播放按钮 ▶ 启动
   - 等待虚拟机启动（首次较慢）

---

### 步骤 7：再次运行 Flutter Doctor

```powershell
flutter doctor
```

**期望输出**（所有项打 ✓）：
```
[✓] Flutter (Channel stable, 3.27.1)
[✓] Windows Version (Installed version of Windows is version 10 or higher)
[✓] Android toolchain - develop for Android devices (Android SDK version 34.0.0)
[✓] Android Studio (version 2023.x)
[!] Android Studio (binaries not in PATH)
    ✗ Add Android Studio to PATH
[✓] VS Code (version 1.x)
[✓] Connected device (1 available)

! 发现一些问题，但可以继续开发
```

---

## 🛠️ 安装 VS Code 和 Flutter 插件（可选但推荐）

### 步骤 8：安装 VS Code

1. **下载 VS Code**：
   ```
   https://code.visualstudio.com/
   ```

2. **安装 VS Code**：
   - 运行安装程序
   - 安装选项：
     - ✅ 添加到 PATH
     - ✅ 通过"打开方式"操作打开文件
     - ✅ 在"开始"菜单中添加快捷方式

---

### 步骤 9：安装 Flutter 插件

1. **打开 VS Code**
2. **打开扩展视图**：
   - 按 `Ctrl + Shift + X`
   - 或点击左侧边栏的扩展图标

3. **安装插件**：
   - 搜索 **Flutter**
   - 作者：Dart Code
   - 点击 `Install`

4. **安装 Dart 插件**：
   - 搜索 **Dart**
   - 作者：Dart Code
   - 点击 `Install`

5. **重启 VS Code**

---

## ✅ 最终验证

### 验证 1：命令行

```powershell
flutter doctor -v
```

**期望输出**（关键项）：
```
[✓] Flutter (Channel stable, 3.27.1)
    • Flutter version 3.27.1
    • Upstream repository https://github.com/flutter/flutter.git
    • Framework revision abc123def (2025-01-01)

[✓] Android toolchain - develop for Android devices (Android SDK version 34.0.0)
    • Platform android-34, build-tools 34.0.0
    • Java binary at: C:\Program Files\Android\Android Studio\jbr\bin\java
    • Android Studio at C:\Program Files\Android\Android Studio

[✓] VS Code (version 1.85.1)
    • VS Code at C:\Users\YourName\AppData\Local\Programs\Microsoft VS Code

[✓] Connected device (1 available)
    • Pixel 6 API 33 (mobile) • emulator-5554 • android-x64 • Android 13.0 (API 33)
```

---

### 验证 2：创建测试项目

```powershell
# 1. 创建测试项目
flutter create test_app

# 2. 进入项目目录
cd test_app

# 3. 运行项目（确保 AVD 已启动）
flutter run
```

**期望结果**：
- 应用成功编译
- 在 Android 模拟器中运行
- 显示计数器应用

---

## 🐛 常见问题排查

### 问题 1：Flutter 命令未找到

**症状**：
```
'flutter' 不是内部或外部命令
```

**解决方案**：
1. 确认 Flutter SDK 已解压到 `C:\dev\flutter`
2. 检查环境变量：
   ```powershell
   echo %PATH%
   ```
3. 确认 `C:\dev\flutter\bin` 在 PATH 中
4. **重启命令行窗口**

---

### 问题 2：Android SDK 未找到

**症状**：
```
[!] Android toolchain - develop for Android devices (Android SDK not found)
```

**解决方案**：
1. 确认 Android Studio 已安装
2. 设置环境变量：
   ```powershell
   # 添加到用户环境变量
   ANDROID_HOME = C:\Users\YourName\AppData\Local\Android\Sdk
   ```
3. 重新运行 `flutter doctor`

---

### 问题 3：无法连接到设备

**症状**：
```
[!] No connected devices
```

**解决方案**：
1. 确认 AVD 已启动
2. 检查 ADB 连接：
   ```powershell
   adb devices
   ```
3. 重启 ADB 服务器：
   ```powershell
   adb kill-server
   adb start-server
   ```

---

### 问题 4：Gradle 下载缓慢

**症状**：
```
Running Gradle task 'assembleDebug'...
```
长时间卡住

**解决方案**：
**配置国内镜像源**（可选）：

编辑文件：
```
C:\dev\flutter\packages\flutter_tools\gradle\flutter.gradle
```

添加：
```groovy
buildscript {
    repositories {
        maven { url 'https://maven.aliyun.com/repository/google' }
        maven { url 'https://maven.aliyun.com/repository/jcenter' }
        maven { url 'https://maven.aliyun.com/repository/public' }
    }
}

allprojects {
    repositories {
        maven { url 'https://maven.aliyun.com/repository/google' }
        maven { url 'https://maven.aliyun.com/repository/jcenter' }
        maven { url 'https://maven.aliyun.com/repository/public' }
    }
}
```

---

## 📚 参考资料

- [Flutter 官方文档](https://docs.flutter.dev/)
- [Android Studio 下载](https://developer.android.com/studio)
- [VS Code 下载](https://code.visualstudio.com/)
- [Dart 语言指南](https://dart.dev/guides)

---

## ✅ 安装完成清单

- [ ] Flutter SDK 已安装并添加到 PATH
- [ ] Android Studio 已安装
- [ ] Android SDK 已下载
- [ ] Android 许可证已接受
- [ ] Android 虚拟设备（AVD）已创建
- [ ] VS Code 已安装（可选）
- [ ] Flutter 和 Dart 插件已安装（可选）
- [ ] `flutter doctor` 所有项打 ✓
- [ ] 测试项目运行成功

---

## 🚀 下一步

安装完成后，请继续阅读：
- **移动端开发计划**：`mobile/PROJECT_PLAN.md`
- **后端 API 文档**：`docs/02-技术文档/工程结构API设计.md`

---

**文档维护**：BDC-AI 开发团队
**最后更新**：2026-01-23
**文档版本**：1.0.0
