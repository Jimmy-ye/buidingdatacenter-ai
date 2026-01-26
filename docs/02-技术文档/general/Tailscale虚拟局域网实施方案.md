# Tailscale 虚拟局域网实施方案

**项目**: BDC-AI 建筑节能诊断与能源管理平台
**版本**: 1.0
**日期**: 2026-01-24
**维护人**: 技术团队

---

## 目录

- [1. 方案概述](#1-方案概述)
- [2. 前置准备](#2-前置准备)
- [3. 服务端配置](#3-服务端配置247-电脑)
- [4. 移动端配置](#4-移动端配置flutter)
- [5. PC 端配置](#5-pc-端配置windows)
- [6. 多设备管理](#6-多设备管理)
- [7. 部署检查清单](#7-部署检查清单)
- [8. 故障排查](#8-故障排查)
- [9. 安全最佳实践](#9-安全最佳实践)
- [10. 性能优化](#10-性能优化)
- [11. 成本评估](#11-成本评估)
- [12. 维护指南](#12-维护指南)
- [13. 附录](#13-附录)

---

## 1. 方案概述

### 1.1 什么是 Tailscale

Tailscale 是一种基于 WireGuard 的零配置虚拟局域网（VPN）解决方案，能够让分布在不同网络的设备安全地互联，就像在同一个局域网内一样。

**核心特性**：
- **零配置**: 无需复杂的路由器设置、端口映射
- **P2P 优先**: 设备间直接连接，低延迟
- **自动 NAT 穿透**: 在任何网络环境下都能工作
- **端到端加密**: 基于 WireGuard，军用级加密
- **跨平台**: 支持 Windows、macOS、Linux、Android、iOS
- **中继支持**: 当 P2P 不可用时，自动使用 DERP 中继

### 1.2 为什么选择 Tailscale

**对比其他方案**：

| 特性 | Tailscale | ZeroTier | frp | 内网穿透路由器 |
|------|-----------|----------|-----|--------------|
| 部署难度 | ⭐ 极简 | ⭐⭐ 中等 | ⭐⭐⭐ 复杂 | ⭐⭐⭐⭐ 极复杂 |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 安全性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 成本 | 免费（100设备） | 免费（25设备） | 需要公网服务器 | 需要支持的路由器 |
| 移动端支持 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| 自动重连 | ✅ | ✅ | ❌ | ❌ |

**BDC-AI 项目的选择理由**：

1. **现场工程师友好**：只需安装 App 并登录，无需技术背景
2. **网络环境无关**：无论家庭、公司、移动网络都能工作
3. **零维护成本**：无需配置路由器、无需公网 IP
4. **企业级安全**：支持 ACL、设备审批、审计日志
5. **免费额度充足**：100 设备完全满足 5-10 人团队需求

### 1.3 网络架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Tailscale Tailnet (虚拟局域网)             │
│                  100.x.x.x/24 (私有 CIDR)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  24/7 Server │  │ Manager Phone│  │Engineer Tablet│        │
│  │              │  │              │  │              │        │
│  │ IP: 100.x.x.1│  │ IP: 100.x.x.2│  │ IP: 100.x.x.3│        │
│  │              │  │              │  │              │        │
│  │ FastAPI      │  │ Flutter App  │  │ Flutter App  │        │
│  │ PostgreSQL   │  │ (移动端)     │  │ (移动端)     │        │
│  │ Port: 8000   │  │              │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                  │                  │              │
│         │                  │                  │              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Home Router │  │ Office WiFi  │  │ 4G/5G Mobile │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
    ┌─────────────────────────────────────────────────┐
    │              Public Internet                    │
    └─────────────────────────────────────────────────┘

通信流程：
1. 所有设备安装 Tailscale 客户端
2. 登录同一 Tailscale 账号，自动加入 Tailnet
3. 分配 Tailscale IP（如 100.x.x.x）
4. 设备间通过 Tailscale IP 直接通信（P2P）
5. 如果 P2P 不可用，自动通过 DERP 中继

访问后端服务：
- Flutter App → http://100.x.x.1:8000 → FastAPI → PostgreSQL
```

### 1.4 适用场景分析

✅ **非常适合 BDC-AI 项目**：
- 5-10 人小团队
- 设备分布在不同网络
- 需要安全访问后端服务
- 移动端现场上传照片
- PC 端查看数据和生成报告
- 团队成员技术背景不同

✅ **扩展场景**：
- 远程访问 24/7 电脑的桌面（RDP via Tailscale）
- 多个项目团队的设备隔离（通过 ACL）
- 临时合作伙伴访问（过期设备密钥）
- 备用服务器部署

---

## 2. 前置准备

### 2.1 硬件要求

| 设备类型 | 最低配置 | 推荐配置 |
|---------|---------|---------|
| **24/7 服务器** | Windows 10/11, 4GB RAM | Windows 11, 8GB+ RAM, SSD |
| **Android 手机** | Android 8.0+ | Android 12+ |
| **iOS 手机** | iOS 13+ | iOS 16+ |
| **PC 端** | Windows 10/11 | Windows 11 |

### 2.2 软件要求

| 软件 | 版本 | 用途 |
|------|------|------|
| **Tailscale 客户端** | 最新版 | 虚拟局域网 |
| **Flutter SDK** | 3.38.7 | 移动端开发 |
| **Python** | 3.11+ | 后端服务 |
| **PostgreSQL** | 15+ | 数据库 |

### 2.3 账号注册

**注册步骤**：

1. 访问 https://tailscale.com/signup
2. 选择登录方式（推荐 Google、GitHub）
3. 完成 Email 验证
4. 登录 Tailscale 管理控制台

**推荐配置**：
- 启用两步验证（2FA）
- 配置邮箱通知
- 设置设备审批策略（可选）

### 2.4 时间估算

| 任务 | 时间 | 依赖 |
|------|------|------|
| 账号注册 | 5 分钟 | - |
| 服务端配置 | 20 分钟 | - |
| 移动端配置（每台设备） | 10 分钟 | 服务端已完成 |
| PC 端配置（每台设备） | 10 分钟 | 服务端已完成 |
| 移动端代码集成 | 2 小时 | - |
| 测试验证 | 30 分钟 | 所有设备已配置 |
| **总计** | **4 小时** | **建议分 2 天完成** |

---

## 3. 服务端配置（24/7 电脑）

### 3.1 下载和安装 Tailscale

**Windows 环境**：

1. 访问 https://tailscale.com/download/windows
2. 下载 `Tailscale Setup.exe`
3. 双击运行安装程序
4. 等待安装完成（约 1 分钟）

### 3.2 登录和配置

1. 安装完成后，Tailscale 会自动打开浏览器
2. 点击 "Log in" 按钮
3. 选择登录方式（Google、GitHub 等）
4. 授权 Tailscale 访问
5. 等待连接成功

**验证安装**：

```powershell
# 打开 PowerShell（管理员）
tailscale status
```

预期输出：
```
100.x.x.1    your-username@github    windows    -
# 输出你的 Tailscale IP 地址
```

### 3.3 获取 Tailscale IP

**方法 1：通过系统托盘**
1. 点击任务栏的 Tailscale 图标（🦊）
2. 查看 "Tailscale IP" 字段

**方法 2：通过命令行**
```powershell
tailscale ip -4
```

**记录 IP 地址**：
- 假设获取的 IP 为 `100.x.x.1`
- 将此 IP 配置到移动端和 PC 端的后端 API 地址

### 3.4 防火墙配置

**Windows 防火墙**：

Tailscale 会自动配置防火墙规则，但需要手动开放后端服务端口：

```powershell
# 以管理员身份运行 PowerShell
# 允许 Tailscale 网络访问 8000 端口
New-NetFirewallRule -DisplayName "BDC-AI Backend (Tailscale)" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**或者通过图形界面**：
1. 打开 "Windows Defender 防火墙" → "高级设置"
2. 选择 "入站规则" → "新建规则"
3. 规则类型：端口
4. 协议：TCP，端口：8000
5. 操作：允许连接
6. 配置文件：域、专用、公用（全部勾选）
7. 名称：BDC-AI Backend (Tailscale)

### 3.5 后端服务监听地址修改

**修改 FastAPI 监听地址**：

当前配置可能是 `localhost:8000`，需要改为 `0.0.0.0:8000` 以允许外部访问。

**方法 1：修改启动命令**

```bash
# 从项目根目录启动
python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**方法 2：创建启动脚本（推荐）**

创建 `scripts/start_backend.bat`：

```batch
@echo off
echo Starting BDC-AI Backend Service...
cd /d "D:\Huawei Files\华为家庭存储\Programs\program-bdc-ai"
python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
```

**方法 3：配置为 Windows 服务（高级）**

使用 NSSM 将后端服务注册为 Windows 服务：

```powershell
# 下载 NSSM: https://nssm.cc/download
# 安装为服务
nssm install BDC-AI-Backend "C:\Python311\python.exe" "-m" "uvicorn" "services.backend.app.main:app" "--host" "0.0.0.0" "--port" "8000"
nssm start BDC-AI-Backend
```

### 3.6 测试验证

**本地测试**：
```bash
curl http://localhost:8000/api/v1/health
```

**Tailscale IP 测试**：
```bash
curl http://100.x.x.1:8000/api/v1/health
```

预期响应：
```json
{
  "status": "healthy",
  "service": "bdc-ai-backend",
  "version": "0.1.0"
}
```

**记录配置信息**：
```
Tailscale IP: 100.x.x.1
后端服务地址: http://100.x.x.1:8000
API 文档: http://100.x.x.1:8000/docs
```

---

## 4. 移动端配置（Flutter）

### 4.1 Android 配置

#### 4.1.1 安装 Tailscale App

1. 打开 Google Play Store
2. 搜索 "Tailscale"
3. 安装官方应用（开发者：Tailscale Inc.）
4. 打开应用并登录（与服务端相同账号）

#### 4.1.2 验证连接

1. 打开 Tailscale App
2. 查看 "Connection status" 应为 "Connected"
3. 查看 "Your Tailscale IP"（如 `100.x.x.2`）

#### 4.1.3 添加依赖

在 `mobile/pubspec.yaml` 中添加：

```yaml
dependencies:
  flutter:
    sdk: flutter

  # 网络状态检测
  connectivity_plus: ^6.0.3

  # HTTP 请求
  dio: ^5.4.0

  # 本地存储（保存 Tailscale IP）
  shared_preferences: ^2.2.2

  # UI 组件
  flutter_bloc: ^8.1.3
```

运行安装：
```bash
flutter pub get
```

### 4.2 iOS 配置

#### 4.2.1 安装 Tailscale App

1. 打开 App Store
2. 搜索 "Tailscale"
3. 安装应用
4. 登录与服务端相同账号

#### 4.2.2 验证连接

与 Android 相同，查看连接状态和 Tailscale IP。

### 4.3 Flutter 代码实现

#### 4.3.1 网络状态检测服务

创建 `mobile/lib/services/network_service.dart`：

```dart
import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 网络状态
enum NetworkStatus {
  connected,      // 已连接到后端
  disconnected,   // 未连接
  checking,       // 正在检测
}

/// 网络服务
class NetworkService {
  static final NetworkService _instance = NetworkService._internal();
  factory NetworkService() => _instance;
  NetworkService._internal();

  final Connectivity _connectivity = Connectivity();
  final Dio _dio = Dio();

  // 配置
  static const String _tailscaleIpKey = 'tailscale_backend_ip';
  static const String _defaultTailscaleIp = '100.x.x.1'; // 替换为实际 IP
  static const int _backendPort = 8000;
  static const Duration _checkInterval = Duration(seconds: 30);

  // 状态流
  final _statusController = StreamController<NetworkStatus>.broadcast();
  Stream<NetworkStatus> get statusStream => _statusController.stream;

  NetworkStatus _currentStatus = NetworkStatus.checking;
  NetworkStatus get currentStatus => _currentStatus;

  String? _backendUrl;
  String? get backendUrl => _backendUrl;

  Timer? _checkTimer;
  bool _isInitialized = false;

  /// 初始化网络服务
  Future<void> initialize() async {
    if (_isInitialized) return;
    _isInitialized = true;

    // 加载保存的 Tailscale IP
    final prefs = await SharedPreferences.getInstance();
    final savedIp = prefs.getString(_tailscaleIpKey);
    _backendUrl = 'http://${savedIp ?? _defaultTailscaleIp}:$_backendPort';

    // 监听网络变化
    _connectivity.onConnectivityChanged.listen((_) {
      _checkConnection();
    });

    // 启动定时检查
    _startPeriodicCheck();

    // 立即检查一次
    await _checkConnection();
  }

  /// 启动定时检查
  void _startPeriodicCheck() {
    _checkTimer?.cancel();
    _checkTimer = Timer.periodic(_checkInterval, (_) {
      _checkConnection();
    });
  }

  /// 检查后端连接
  Future<bool> _checkConnection() async {
    _updateStatus(NetworkStatus.checking);

    try {
      final response = await _dio.get(
        '$_backendUrl/api/v1/health',
        options: Options(
          receiveTimeout: const Duration(seconds: 5),
          sendTimeout: const Duration(seconds: 5),
        ),
      );

      final isConnected = response.statusCode == 200;
      _updateStatus(isConnected ? NetworkStatus.connected : NetworkStatus.disconnected);
      return isConnected;
    } catch (e) {
      _updateStatus(NetworkStatus.disconnected);
      return false;
    }
  }

  /// 更新状态
  void _updateStatus(NetworkStatus status) {
    if (_currentStatus != status) {
      _currentStatus = status;
      _statusController.add(status);
    }
  }

  /// 更新 Tailscale IP
  Future<void> updateTailscaleIp(String ip) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tailscaleIpKey, ip);
    _backendUrl = 'http://$ip:$_backendPort';
    await _checkConnection();
  }

  /// 获取当前连接类型
  Future<List<ConnectivityResult>> getConnectivityType() async {
    return await _connectivity.checkConnectivity();
  }

  /// 手动触发连接检查
  Future<bool> checkConnectionNow() async {
    return await _checkConnection();
  }

  /// 释放资源
  void dispose() {
    _checkTimer?.cancel();
    _statusController.close();
  }
}
```

#### 4.3.2 用户引导对话框

创建 `mobile/lib/widgets/tailscale_guide_dialog.dart`：

```dart
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class TailscaleGuideDialog extends StatelessWidget {
  const TailscaleGuideDialog({super.key});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.wifi_off, color: Colors.orange),
          SizedBox(width: 8),
          Text('无法连接到服务器'),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '检测到您尚未连接到 Tailscale 虚拟局域网。请按以下步骤操作：',
              style: TextStyle(fontSize: 14),
            ),
            const SizedBox(height: 16),
            _buildStep('1', '下载 Tailscale App', '从应用商店搜索 "Tailscale" 并安装'),
            const SizedBox(height: 12),
            _buildStep('2', '登录账号', '使用团队账号登录（与服务器相同）'),
            const SizedBox(height: 12),
            _buildStep('3', '等待连接', '确认连接状态为 "Connected"'),
            const SizedBox(height: 12),
            _buildStep('4', '返回本应用', '连接成功后，点击下方按钮重新检测'),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.info_outline, color: Colors.blue.shade700, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        '为什么需要 Tailscale？',
                        style: TextStyle(
                          color: Colors.blue.shade700,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Tailscale 是一个安全的虚拟局域网工具，\n'
                    '让您在不同网络环境下也能安全访问\n'
                    '项目服务器，无需配置路由器。',
                    style: TextStyle(fontSize: 12),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => _openTailscaleDownload(),
          child: const Text('下载 Tailscale'),
        ),
        ElevatedButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: const Text('我已连接，重新检测'),
        ),
      ],
    );
  }

  Widget _buildStep(String number, String title, String description) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 24,
          height: 24,
          decoration: const BoxDecoration(
            color: Colors.blue,
            shape: BoxShape.circle,
          ),
          child: Center(
            child: Text(
              number,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              Text(
                description,
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _openTailscaleDownload() async {
    final url = 'https://tailscale.com/download';
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}

/// 显示引导对话框
Future<bool> showTailscaleGuide(BuildContext context) async {
  return await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (context) => const TailscaleGuideDialog(),
  ) ?? false;
}
```

#### 4.3.3 网络状态指示器

创建 `mobile/lib/widgets/network_status_indicator.dart`：

```dart
import 'package:flutter/material.dart';
import '../services/network_service.dart';

class NetworkStatusIndicator extends StatefulWidget {
  const NetworkStatusIndicator({super.key});

  @override
  State<NetworkStatusIndicator> createState() => _NetworkStatusIndicatorState();
}

class _NetworkStatusIndicatorState extends State<NetworkStatusIndicator> {
  final NetworkService _networkService = NetworkService();
  NetworkStatus _status = NetworkStatus.checking;

  @override
  void initState() {
    super.initState();
    _status = _networkService.currentStatus;
    _networkService.statusStream.listen((status) {
      if (mounted) {
        setState(() {
          _status = status;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: _getStatusColor().withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _getStatusColor(), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            _getStatusIcon(),
            size: 16,
            color: _getStatusColor(),
          ),
          const SizedBox(width: 8),
          Text(
            _getStatusText(),
            style: TextStyle(
              color: _getStatusColor(),
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor() {
    switch (_status) {
      case NetworkStatus.connected:
        return Colors.green;
      case NetworkStatus.disconnected:
        return Colors.red;
      case NetworkStatus.checking:
        return Colors.orange;
    }
  }

  IconData _getStatusIcon() {
    switch (_status) {
      case NetworkStatus.connected:
        return Icons.cloud_done;
      case NetworkStatus.disconnected:
        return Icons.cloud_off;
      case NetworkStatus.checking:
        return Icons.sync;
    }
  }

  String _getStatusText() {
    switch (_status) {
      case NetworkStatus.connected:
        return '已连接';
      case NetworkStatus.disconnected:
        return '未连接';
      case NetworkStatus.checking:
        return '检测中';
    }
  }
}
```

#### 4.3.4 App 启动检查

修改 `mobile/lib/main.dart`：

```dart
import 'package:flutter/material.dart';
import 'services/network_service.dart';
import 'widgets/tailscale_guide_dialog.dart';
import 'widgets/network_status_indicator.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 初始化网络服务
  final networkService = NetworkService();
  await networkService.initialize();

  runApp(MyApp(networkService: networkService));
}

class MyApp extends StatelessWidget {
  final NetworkService networkService;

  const MyApp({super.key, required this.networkService});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BDC-AI 移动端',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: SplashScreen(networkService: networkService),
    );
  }
}

/// 启动屏幕
class SplashScreen extends StatefulWidget {
  final NetworkService networkService;

  const SplashScreen({super.key, required this.networkService});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkNetworkAndNavigate();
  }

  Future<void> _checkNetworkAndNavigate() async {
    // 等待 2 秒以显示启动画面
    await Future.delayed(const Duration(seconds: 2));

    if (!mounted) return;

    final isConnected = widget.networkService.currentStatus == NetworkStatus.connected;

    if (isConnected) {
      // 已连接，进入主界面
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (context) => MainScreen(networkService: widget.networkService),
        ),
      );
    } else {
      // 未连接，显示引导对话框
      final shouldRetry = await showTailscaleGuide(context);

      if (shouldRetry && mounted) {
        // 重新检测
        await widget.networkService.checkConnectionNow();
        final retryConnected = widget.networkService.currentStatus == NetworkStatus.connected;

        if (retryConnected && mounted) {
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(
              builder: (context) => MainScreen(networkService: widget.networkService),
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.energy_savings_leaf, size: 80, color: Colors.green),
            const SizedBox(height: 24),
            const Text(
              'BDC-AI',
              style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text('建筑节能诊断与能源管理平台'),
            const SizedBox(height: 48),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}

/// 主屏幕
class MainScreen extends StatelessWidget {
  final NetworkService networkService;

  const MainScreen({super.key, required this.networkService});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BDC-AI'),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Center(
              child: NetworkStatusIndicator(),
            ),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle, size: 64, color: Colors.green),
            const SizedBox(height: 24),
            const Text(
              '连接成功！',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Text(
              '后端地址: ${networkService.backendUrl}',
              style: TextStyle(color: Colors.grey.shade600),
            ),
          ],
        ),
      ),
    );
  }
}
```

### 4.4 后端 API 地址配置

创建 `mobile/lib/config/api_config.dart`：

```dart
import 'package:shared_preferences/shared_preferences.dart';
import '../services/network_service.dart';

class ApiConfig {
  // 默认配置（会被 Tailscale IP 覆盖）
  static const String defaultTailscaleIp = '100.x.x.1'; // 替换为实际 IP
  static const int backendPort = 8000;

  // API 端点
  static String get baseUrl {
    final networkService = NetworkService();
    return networkService.backendUrl ?? 'http://$defaultTailscaleIp:$backendPort';
  }

  static const String health = '/api/v1/health';
  static const String projects = '/api/v1/projects';
  static const String assets = '/api/v1/assets';

  /// 更新 Tailscale IP
  static Future<void> updateTailscaleIp(String ip) async {
    final networkService = NetworkService();
    await networkService.updateTailscaleIp(ip);
  }

  /// 获取完整 URL
  static String getUrl(String endpoint) {
    return '$baseUrl$endpoint';
  }
}
```

### 4.5 测试验证

**步骤**：

1. 确保 Tailscale App 已登录并连接
2. 运行 Flutter 应用：
   ```bash
   cd mobile
   flutter run
   ```
3. 观察启动流程：
   - 显示启动画面
   - 自动检测网络连接
   - 如果未连接，显示引导对话框
   - 连接成功后进入主界面
4. 查看网络状态指示器（右上角）

**预期结果**：
- ✅ 网络状态指示器显示"已连接"（绿色）
- ✅ 可以访问后端 API
- ✅ 后端地址显示为 `http://100.x.x.1:8000`

---

## 5. PC 端配置（Windows）

### 5.1 安装 Tailscale

与服务端相同：

1. 访问 https://tailscale.com/download/windows
2. 下载并安装 `Tailscale Setup.exe`
3. 使用与服务端相同账号登录

### 5.2 验证连接

```powershell
# 查看 Tailscale IP
tailscale ip -4

# 查看连接状态
tailscale status
```

### 5.3 测试后端访问

**通过浏览器测试**：
1. 打开浏览器
2. 访问 `http://100.x.x.1:8000/docs`
3. 应能看到 Swagger API 文档

**通过命令行测试**：
```bash
curl http://100.x.x.1:8000/api/v1/health
```

**通过 NiceGUI 应用测试**（如果已开发）：
```python
# 配置后端地址
BACKEND_URL = "http://100.x.x.1:8000"
```

### 5.4 配置 PC 端应用

**方法 1：环境变量**
```bash
# Windows PowerShell
$env:BDC_BACKEND_URL="http://100.x.x.1:8000"

# 永久设置
[System.Environment]::SetEnvironmentVariable('BDC_BACKEND_URL', 'http://100.x.x.1:8000', 'User')
```

**方法 2：配置文件**

创建 `config/pc_config.json`：
```json
{
  "backend_url": "http://100.x.x.1:8000",
  "tailscale_ip": "100.x.x.1",
  "backend_port": 8000
}
```

---

## 6. 多设备管理

### 6.1 设备命名规范

**推荐命名格式**：`BDC-{角色}-{设备类型}`

**示例**：
- `BDC-Server-Win` - 服务器（Windows）
- `BDC-Manager-Phone-Pixel` - 项目经理手机（Pixel）
- `BDC-Engineer-Tablet-iPad` - 工程师平板（iPad）
- `BDC-Engineer-Laptop-Dell` - 工程师笔记本（Dell）

**修改设备名称**：

1. 登录 Tailscale 管理控制台
2. 进入 "Machines" 页面
3. 点击设备右侧的 "..." 菜单
4. 选择 "Rename"
5. 输入新名称并保存

### 6.2 设备权限控制

**设备审批策略**：

1. 登录 Tailscale 管理控制台
2. 进入 "Settings" → "ACLs"
3. 启用 "Require approvals for new devices"

**效果**：
- 新设备登录后需要管理员审批
- 审批前设备无法访问 Tailnet
- 提高安全性，防止未授权设备接入

### 6.3 设备移除流程

**步骤**：

1. **方法 1：通过管理控制台**
   - 登录 Tailscale 管理控制台
   - 进入 "Machines" 页面
   - 选择要移除的设备
   - 点击 "..." → "Delete"

2. **方法 2：通过客户端**
   - 打开 Tailscale 客户端
   - 进入 "Settings" → "Sign out"
   - 设备会自动从 Tailnet 移除

**注意事项**：
- 设备移除后，分配的 IP 地址会被回收
- 移除前确保设备上没有重要数据未同步
- 建议定期审计设备列表，移除不活跃设备

### 6.4 密钥轮换

**定期更换密钥**（推荐每 90 天）：

1. 登录 Tailscale 管理控制台
2. 进入 "Settings" → "Keys"
3. 撤销旧密钥
4. 生成新密钥
5. 重新登录所有设备

### 6.5 ACL（访问控制列表）配置

**基础 ACL 示例**：

```json
{
  // ACL 配置
  "acls": [
    // 允许所有设备互访（简单配置）
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["*:*"]
    }
  ],

  // 标签（可选）
  "tagOwners": {
    "tag:server": ["group:admins"],
    "tag:client": ["group:users"]
  },

  // 组
  "groups": {
    "group:admins": ["user1@example.com", "user2@example.com"],
    "group:users": ["user3@example.com", "user4@example.com"]
  },

  // 主机别名
  "hosts": {
    "bdc-server": "100.x.x.1"
  }
}
```

**项目级权限隔离**（可选）：

```json
{
  "acls": [
    // 服务器对所有设备开放 8000 端口
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["tag:server:8000"]
    },

    // 管理员可以访问所有设备
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["*:*"]
    },

    // 普通用户只能访问服务器
    {
      "action": "accept",
      "src": ["group:users"],
      "dst": ["tag:server:*"]
    }
  ]
}
```

### 6.6 审计日志

**启用审计日志**：

1. 登录 Tailscale 管理控制台
2. 进入 "Settings" → "Logging"
3. 启用 "Audit logging"

**日志内容包括**：
- 设备登录/登出
- 文件访问记录
- ACL 变更历史
- 设备审批记录

**日志导出**：
- 支持导出到 Syslog
- 支持导出到 S3 存储桶
- 可集成到 SIEM 系统

---

## 7. 部署检查清单

### 7.1 服务端检查清单

**安装和配置**：
- [ ] 下载 Tailscale 客户端（Windows）
- [ ] 安装 Tailscale（运行安装程序）
- [ ] 登录 Tailscale（使用 Google/GitHub 账号）
- [ ] 验证连接状态（`tailscale status`）
- [ ] 获取 Tailscale IP（`tailscale ip -4`）
- [ ] 记录 Tailscale IP（例如 `100.x.x.1`）

**防火墙配置**：
- [ ] 开放 8000 端口给 Tailscale 网络
- [ ] 验证防火墙规则（`Get-NetFirewallRule`）

**后端服务配置**：
- [ ] 修改 Uvicorn 监听地址为 `0.0.0.0`
- [ ] 更新启动脚本（使用 `--host 0.0.0.0`）
- [ ] 启动后端服务
- [ ] 测试本地访问（`curl localhost:8000/api/v1/health`）
- [ ] 测试 Tailscale 访问（`curl 100.x.x.1:8000/api/v1/health`）
- [ ] 测试 API 文档（浏览器访问 `http://100.x.x.1:8000/docs`）

**验证**：
- [ ] 后端服务正常运行
- [ ] 可以通过 Tailscale IP 访问
- [ ] API 文档可以打开
- [ ] 数据库连接正常

### 7.2 移动端检查清单

**Tailscale App 配置**：
- [ ] 从应用商店下载 Tailscale App
- [ ] 安装并打开应用
- [ ] 登录与服务端相同账号
- [ ] 验证连接状态为 "Connected"
- [ ] 查看 Tailscale IP（例如 `100.x.x.2`）

**Flutter 应用配置**：
- [ ] 添加 `connectivity_plus` 依赖
- [ ] 添加 `dio` 依赖
- [ ] 添加 `shared_preferences` 依赖
- [ ] 运行 `flutter pub get`
- [ ] 复制 `network_service.dart` 到项目
- [ ] 复制 `tailscale_guide_dialog.dart` 到项目
- [ ] 复制 `network_status_indicator.dart` 到项目
- [ ] 修改 `main.dart` 集成启动检查
- [ ] 更新 `api_config.dart` 中的 Tailscale IP

**代码验证**：
- [ ] 网络服务初始化（`NetworkService.initialize()`）
- [ ] 状态流正常工作（`statusStream`）
- [ ] 网络状态指示器显示正确
- [ ] 引导对话框正常显示
- [ ] 重连机制正常工作

**测试**：
- [ ] 运行 Flutter 应用（`flutter run`）
- [ ] 启动画面正常显示
- [ ] 自动检测网络连接
- [ ] 未连接时显示引导对话框
- [ ] 连接成功后进入主界面
- [ ] 网络状态指示器显示"已连接"（绿色）
- [ ] 可以访问后端 API
- [ ] 测试 API 请求成功

### 7.3 PC 端检查清单

**Tailscale 配置**：
- [ ] 下载并安装 Tailscale（Windows）
- [ ] 登录与服务端相同账号
- [ ] 验证连接状态（`tailscale status`）
- [ ] 获取 Tailscale IP

**访问测试**：
- [ ] 通过浏览器测试后端访问
- [ ] 访问 API 文档（`http://100.x.x.1:8000/docs`）
- [ ] 通过命令行测试（`curl 100.x.x.1:8000/api/v1/health`）
- [ ] 测试 PC 应用连接后端

### 7.4 多设备管理检查清单

**管理控制台**：
- [ ] 登录 Tailscale 管理控制台
- [ ] 查看所有已连接设备
- [ ] 重命名设备（使用规范命名）
- [ ] 配置设备审批策略（可选）
- [ ] 配置 ACL（可选）
- [ ] 启用审计日志（可选）

**文档记录**：
- [ ] 记录所有 Tailscale IP 地址
- [ ] 记录设备命名规范
- [ ] 记录管理员账号信息
- [ ] 记录设备移除流程

---

## 8. 故障排查

### 8.1 常见问题

#### 问题 1：无法连接到服务器

**症状**：
- 移动端显示"未连接"
- 浏览器无法访问 `http://100.x.x.1:8000`

**排查步骤**：

1. **检查 Tailscale 连接状态**：
   ```bash
   # 服务端
   tailscale status

   # 移动端打开 Tailscale App 查看状态
   ```

2. **检查后端服务是否运行**：
   ```bash
   # 服务端
   curl localhost:8000/api/v1/health
   ```

3. **检查防火墙规则**：
   ```powershell
   # 查看 8000 端口规则
   Get-NetFirewallRule -DisplayName "*BDC-AI*"
   ```

4. **检查网络连通性**：
   ```bash
   # 移动端/PC 端
   ping 100.x.x.1

   telnet 100.x.x.1 8000
   ```

**解决方案**：
- 确保后端服务监听 `0.0.0.0`
- 确保防火墙允许 Tailscale 网络访问 8000 端口
- 重启 Tailscale 服务：
  ```powershell
  # 服务端
  tailscale down
  tailscale up
  ```

#### 问题 2：Tailscale IP 获取失败

**症状**：
- `tailscale ip -4` 无输出
- Tailscale App 显示 "No IP address"

**排查步骤**：

1. **检查登录状态**：
   ```bash
   tailscale status
   ```

2. **重新登录**：
   ```bash
   tailscale logout
   tailscale up
   ```

3. **检查网络连接**：
   - 确保设备已连接到互联网
   - 尝试切换网络（WiFi/移动数据）

**解决方案**：
- 重新登录 Tailscale
- 重启设备
- 更新 Tailscale 客户端到最新版本

#### 问题 3：移动端连接不稳定

**症状**：
- 网络状态指示器频繁变化
- API 请求间歇性失败

**排查步骤**：

1. **检查 Tailscale App 状态**：
   - 确保始终在后台运行
   - 禁用电池优化

2. **检查网络切换**：
   - WiFi 和移动数据切换时是否断开
   - Tailscale 应自动重连

**解决方案**：
- 在 Tailscale App 设置中启用 "Override local DNS"
- 在 Flutter 应用中增加重试机制
- 调整网络检查间隔（`NetworkService._checkInterval`）

#### 问题 4：防火墙阻止连接

**症状**：
- 本地可以访问（`localhost:8000`）
- Tailscale IP 无法访问（`100.x.x.1:8000`）

**排查步骤**：

1. **检查 Windows 防火墙**：
   ```powershell
   Get-NetFirewallRule | Where-Object {$_.LocalPort -eq 8000}
   ```

2. **测试端口连通性**：
   ```bash
   telnet 100.x.x.1 8000
   ```

**解决方案**：
```powershell
# 添加防火墙规则
New-NetFirewallRule -DisplayName "BDC-AI Backend (Tailscale)" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# 或临时禁用防火墙测试（不推荐）
Set-NetFirewallProfile -Enabled False
```

#### 问题 5：后端服务无法访问

**症状**：
- Tailscale 连接正常
- 无法访问后端服务

**排查步骤**：

1. **检查后端进程**：
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*python*"}
   ```

2. **检查端口占用**：
   ```powershell
   netstat -ano | findstr :8000
   ```

3. **查看后端日志**：
   ```bash
   # 查看控制台输出
   # 或查看日志文件
   ```

**解决方案**：
- 重启后端服务
- 确保使用 `--host 0.0.0.0` 启动
- 检查数据库连接是否正常

### 8.2 调试工具

#### Tailscale 管理控制台

访问：https://login.tailscale.com/admin/machines

**功能**：
- 查看所有已连接设备
- 查看设备详细信息（IP、版本、最后活跃时间）
- 移除设备
- 重命名设备
- 查看连接状态

#### ping 测试

```bash
# 从移动端/PC 端测试
ping 100.x.x.1

# 预期输出
# Reply from 100.x.x.1: bytes=32 time<1ms TTL=64
```

#### telnet 测试

```bash
# 测试端口连通性
telnet 100.x.x.1 8000

# 预期输出
# Connected to 100.x.x.1
```

#### 日志查看

**Windows Tailscale 日志**：
1. 打开 "事件查看器"（eventvwr.msc）
2. 导航到 "Windows 日志" → "应用程序"
3. 筛选 "Tailscale"

**Android/iOS Tailscale 日志**：
1. 打开 Tailscale App
2. 进入 "Settings" → "Debugging"
3. 启用 "Log viewer"

#### 抓包工具（高级）

**使用 Wireshark**：
1. 安装 Wireshark
2. 选择 Tailscale 接口（通常名为 `tailscale0`）
3. 过滤器：`ip.addr == 100.x.x.1 && tcp.port == 8000`
4. 分析数据包

### 8.3 问题报告模板

**报告问题时，请提供以下信息**：

```
问题描述：
[简要描述问题]

复现步骤：
1.
2.
3.

预期结果：
[应该发生什么]

实际结果：
[实际发生了什么]

环境信息：
- 操作系统：
- Tailscale 版本：
- Tailscale IP：
- 网络环境（WiFi/移动网络）：

日志：
[粘贴相关日志]

截图：
[提供截图]
```

---

## 9. 安全最佳实践

### 9.1 账号安全

**启用两步验证（2FA）**：

1. 登录 Tailscale 管理控制台
2. 进入个人设置
3. 启用 "Two-factor authentication"
4. 使用 Authenticator App 扫描二维码
5. 保存备用代码

**推荐**：
- 使用 Google Authenticator 或 Authy
- 将备用代码保存在安全位置
- 定期更换验证器

### 9.2 设备审批

**强制设备审批**：

1. 登录 Tailscale 管理控制台
2. 进入 "Settings" → "ACLs"
3. 启用 "Require approvals for new devices"

**效果**：
- 新设备登录后需要管理员审批
- 审批前设备无法访问 Tailnet
- 防止未授权设备接入

**审批流程**：
1. 新设备登录后，管理员会收到通知
2. 管理员进入 "Machines" → "Pending approvals"
3. 审核设备信息（名称、位置、登录时间）
4. 批准或拒绝设备

### 9.3 密钥管理

**定期轮换密钥**（推荐每 90 天）：

1. 登录 Tailscale 管理控制台
2. 进入 "Settings" → "Keys"
3. 撤销旧密钥
4. 生成新密钥
5. 重新登录所有设备

**密钥类型**：
- **Personal key**：个人使用，永久有效
- **Reusable key**：可重复使用，用于自动化部署
- **Ephemeral key**：临时密钥，有过期时间

**推荐**：
- 为不同设备使用不同密钥
- 定期审计活跃密钥
- 撤销不再使用的密钥

### 9.4 定期审计

**审计清单**：

- [ ] 每月检查设备列表
- [ ] 移除不活跃设备（超过 30 天未登录）
- [ ] 审查 ACL 配置
- [ ] 检查审计日志
- [ ] 验证设备名称规范
- [ ] 检查是否有异常登录

**审计报告模板**：

```
Tailscale 审计报告
日期：YYYY-MM-DD
审计人：XXX

设备列表：
- 总数：XX
- 活跃：XX
- 不活跃：XX

异常设备：
[列出需要调查的设备]

建议操作：
[列出建议的改进措施]
```

### 9.5 网络隔离

**使用标签隔离不同角色**：

```json
{
  "tagOwners": {
    "tag:server": ["group:admins"],
    "tag:client": ["group:users"],
    "tag:auditor": ["group:auditors"]
  }
}
```

**使用 ACL 限制访问**：

```json
{
  "acls": [
    // 审计员只能访问日志端口
    {
      "action": "accept",
      "src": ["tag:auditor"],
      "dst": ["tag:server:8080"]
    }
  ]
}
```

**使用多个 Tailnet**（高级）：
- 为不同项目创建不同的 Tailnet
- 物理隔离，提高安全性
- 需要付费计划（$5/月/用户）

---

## 10. 性能优化

### 10.1 DERP 中继配置

**DERP（Detour Encrypted Routing Protocol）** 是 Tailscale 的中继服务器，当 P2P 连接不可用时使用。

**查看当前 DERP 配置**：
```bash
tailscale derp-map
```

**自定义 DERP 服务器**（高级）：
1. 部署自己的 DERP 服务器
2. 在 ACL 中配置
3. 降低延迟，提高性能

**推荐**：
- 大多数情况下使用默认 DERP 即可
- 默认 DERP 服务器全球分布，性能良好
- 仅在有特殊需求时自定义

### 10.2 本地缓存策略

**移动端缓存 API 响应**：

```dart
// 使用 dio_cache_interceptor
final dio = Dio();
dio.interceptors.add(DioCacheInterceptor(
  options: CacheOptions(
    store: MemCacheStore(),
    policy: CachePolicy.requestFirst,
    maxStale: Duration(minutes: 30),
  ),
));
```

**缓存策略**：
- 健康检查：不缓存
- 项目列表：缓存 5 分钟
- 资产列表：缓存 1 分钟
- 静态数据：缓存 30 分钟

### 10.3 连接池优化

**后端连接池配置**（SQLAlchemy）：

```python
# shared/config/settings.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,          # 连接池大小
    max_overflow=10,       # 最大溢出连接数
    pool_pre_ping=True,    # 连接前检查
    pool_recycle=3600,     # 连接回收时间（秒）
)
```

**HTTP 客户端连接池**（Dio）：

```dart
final dio = Dio(
  BaseOptions(
    connectTimeout: Duration(seconds: 5),
    receiveTimeout: Duration(seconds: 10),
    sendTimeout: Duration(seconds: 5),
  ),
);

// 配置连接池
dio.httpClientAdapter = IOHttpClientAdapter(
  onHttpClientCreate: () {
    final client = HttpClient();
    client.idleTimeout = Duration(seconds: 30);
    return client;
  },
);
```

### 10.4 带宽监控

**Tailscale 管理控制台**：
1. 进入 "Statistics" 页面
2. 查看带宽使用情况
3. 查看连接质量

**监控指标**：
- 上下行带宽
- 连接延迟
- 丢包率
- P2P vs DERP 连接比例

**优化建议**：
- 优先使用 P2P 连接（延迟更低）
- 减少不必要的数据传输
- 使用压缩（图片、视频）
- 分页加载大量数据

---

## 11. 成本评估

### 11.1 免费版

**适用场景**：
- 5-10 人团队
- 100 设备以内
- 基本功能需求

**功能**：
- 无限带宽
- 无限数据传输
- 100 设备
- 基本 ACL
- 设备审批
- 审计日志
- 客户端支持（全平台）

**限制**：
- 无 SSO 集成
- 无自定义 DERP
- 无多 Tailnet
- 无高级报告

### 11.2 付费版

**Premium Plan**：
- 价格：$5/月/用户（年付）
- 所有免费版功能
- 无限设备
- SSO 集成
- 自定义 DERP
- 多 Tailnet
- 高级报告
- 优先支持

**Enterprise Plan**：
- 价格：$20/月/用户（年付）
- 所有 Premium 功能
- 审计日志导出
- 策略强制执行
- 专属支持

### 11.3 BDC-AI 项目成本

**推荐方案**：免费版

**理由**：
- 5-10 人团队，100 设备完全满足
- 基本功能齐全
- 无带宽限制
- 节省成本

**总成本**：
- Tailscale：$0/月
- 带宽：$0（使用现有网络）
- 总计：**$0**

**未来升级时机**：
- 团队超过 100 人
- 需要 SSO 集成
- 需要自定义 DERP
- 需要多 Tailnet 隔离

---

## 12. 维护指南

### 12.1 日常维护任务

**每日**：
- [ ] 检查后端服务状态
- [ ] 检查 Tailscale 连接状态
- [ ] 查看错误日志

**每周**：
- [ ] 审查设备列表
- [ ] 移除不活跃设备
- [ ] 检查带宽使用情况

**每月**：
- [ ] 全面审计
- [ ] 检查 ACL 配置
- [ ] 验证设备名称规范
- [ ] 检查密钥有效期

**每季度**：
- [ ] 轮换密钥
- [ ] 更新客户端版本
- [ ] 审查安全策略

### 12.2 监控指标

**关键指标**：
1. **可用性**：后端服务正常运行时间
2. **连接质量**：Tailscale P2P 连接比例
3. **响应时间**：API 平均响应时间
4. **错误率**：API 请求失败率

**监控工具**：
- Tailscale 管理控制台（内置）
- FastAPI 自带监控（`/api/v1/health`）
- 数据库监控（PostgreSQL 日志）

**告警配置**：
- 后端服务宕机
- Tailscale 连接断开超过 5 分钟
- API 错误率超过 5%

### 12.3 备份策略

**配置备份**：

1. **Tailscale ACL 备份**：
   ```bash
   # 导出 ACL 配置
   tailscale acl export > acl-backup-$(date +%Y%m%d).json
   ```

2. **设备列表备份**：
   - 从管理控制台导出设备列表
   - 保存到版本控制

3. **应用配置备份**：
   - 后端配置（`shared/config/settings.py`）
   - 环境变量（`.env` 文件）
   - 数据库配置

**备份频率**：
- ACL 配置：每次变更后立即备份
- 设备列表：每周备份
- 应用配置：每次部署前备份

**存储位置**：
- Git 仓库（配置文件）
- 云存储（设备列表）
- 本地备份（数据库）

### 12.4 升级流程

**Tailscale 客户端升级**：

1. **检查更新**：
   ```bash
   tailscale version
   ```

2. **下载新版本**：
   - 访问 https://tailscale.com/download
   - 下载最新版

3. **安装更新**：
   - 运行安装程序
   - 自动覆盖旧版本

4. **验证功能**：
   - 检查连接状态
   - 测试 API 访问

**后端服务升级**：

1. **备份数据库**：
   ```bash
   pg_dump bdc_ai > backup-$(date +%Y%m%d).sql
   ```

2. **拉取最新代码**：
   ```bash
   git pull origin master
   ```

3. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

4. **重启服务**：
   ```bash
   # 停止旧服务
   # 启动新服务
   python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **验证功能**：
   - 检查健康检查接口
   - 测试关键 API

**移动端升级**：

1. **更新依赖**：
   ```bash
   flutter pub upgrade
   ```

2. **测试新版本**：
   ```bash
   flutter test
   ```

3. **构建发布**：
   ```bash
   flutter build apk --release
   flutter build ios --release
   ```

4. **分发安装**：
   - Android：上传到应用商店或内部分发
   - iOS：TestFlight 或 Ad Hoc 分发

---

## 13. 附录

### 13.1 完整代码示例

#### 13.1.1 network_service.dart（完整实现）

```dart
import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 网络状态
enum NetworkStatus {
  connected,      // 已连接到后端
  disconnected,   // 未连接
  checking,       // 正在检测
}

/// 网络服务
class NetworkService {
  static final NetworkService _instance = NetworkService._internal();
  factory NetworkService() => _instance;
  NetworkService._internal();

  final Connectivity _connectivity = Connectivity();
  final Dio _dio = Dio();

  // 配置
  static const String _tailscaleIpKey = 'tailscale_backend_ip';
  static const String _defaultTailscaleIp = '100.x.x.1'; // 替换为实际 IP
  static const int _backendPort = 8000;
  static const Duration _checkInterval = Duration(seconds: 30);

  // 状态流
  final _statusController = StreamController<NetworkStatus>.broadcast();
  Stream<NetworkStatus> get statusStream => _statusController.stream;

  NetworkStatus _currentStatus = NetworkStatus.checking;
  NetworkStatus get currentStatus => _currentStatus;

  String? _backendUrl;
  String? get backendUrl => _backendUrl;

  Timer? _checkTimer;
  bool _isInitialized = false;

  /// 初始化网络服务
  Future<void> initialize() async {
    if (_isInitialized) return;
    _isInitialized = true;

    // 加载保存的 Tailscale IP
    final prefs = await SharedPreferences.getInstance();
    final savedIp = prefs.getString(_tailscaleIpKey);
    _backendUrl = 'http://${savedIp ?? _defaultTailscaleIp}:$_backendPort';

    // 监听网络变化
    _connectivity.onConnectivityChanged.listen((_) {
      _checkConnection();
    });

    // 启动定时检查
    _startPeriodicCheck();

    // 立即检查一次
    await _checkConnection();
  }

  /// 启动定时检查
  void _startPeriodicCheck() {
    _checkTimer?.cancel();
    _checkTimer = Timer.periodic(_checkInterval, (_) {
      _checkConnection();
    });
  }

  /// 检查后端连接
  Future<bool> _checkConnection() async {
    _updateStatus(NetworkStatus.checking);

    try {
      final response = await _dio.get(
        '$_backendUrl/api/v1/health',
        options: Options(
          receiveTimeout: const Duration(seconds: 5),
          sendTimeout: const Duration(seconds: 5),
        ),
      );

      final isConnected = response.statusCode == 200;
      _updateStatus(isConnected ? NetworkStatus.connected : NetworkStatus.disconnected);
      return isConnected;
    } catch (e) {
      _updateStatus(NetworkStatus.disconnected);
      return false;
    }
  }

  /// 更新状态
  void _updateStatus(NetworkStatus status) {
    if (_currentStatus != status) {
      _currentStatus = status;
      _statusController.add(status);
    }
  }

  /// 更新 Tailscale IP
  Future<void> updateTailscaleIp(String ip) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tailscaleIpKey, ip);
    _backendUrl = 'http://$ip:$_backendPort';
    await _checkConnection();
  }

  /// 获取当前连接类型
  Future<List<ConnectivityResult>> getConnectivityType() async {
    return await _connectivity.checkConnectivity();
  }

  /// 手动触发连接检查
  Future<bool> checkConnectionNow() async {
    return await _checkConnection();
  }

  /// 释放资源
  void dispose() {
    _checkTimer?.cancel();
    _statusController.close();
  }
}
```

#### 13.1.2 tailscale_guide_screen.dart（用户引导页面）

```dart
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class TailscaleGuideScreen extends StatelessWidget {
  const TailscaleGuideScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tailscale 安装指南'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildHeader(),
          const SizedBox(height: 24),
          _buildStepCard(
            1,
            '下载 Tailscale App',
            '从应用商店搜索 "Tailscale" 并安装',
            Icons.download,
          ),
          const SizedBox(height: 16),
          _buildStepCard(
            2,
            '登录账号',
            '使用团队账号登录（与服务器相同）',
            Icons.login,
          ),
          const SizedBox(height: 16),
          _buildStepCard(
            3,
            '等待连接',
            '确认连接状态为 "Connected"',
            Icons.cloud_done,
          ),
          const SizedBox(height: 16),
          _buildStepCard(
            4,
            '返回本应用',
            '连接成功后，点击下方按钮重新检测',
            Icons.check_circle,
          ),
          const SizedBox(height: 24),
          _buildInfoCard(),
          const SizedBox(height: 24),
          _buildActions(context),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      children: [
        Icon(Icons.wifi_off, size: 64, color: Colors.orange),
        const SizedBox(height: 16),
        const Text(
          '无法连接到服务器',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        const Text(
          '请按以下步骤配置 Tailscale',
          style: TextStyle(color: Colors.grey),
        ),
      ],
    );
  }

  Widget _buildStepCard(int step, String title, String description, IconData icon) {
    return Card(
      elevation: 2,
      child: ListTile(
        leading: CircleAvatar(
          child: Text('$step'),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(description),
        trailing: Icon(icon),
      ),
    );
  }

  Widget _buildInfoCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.blue.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.info_outline, color: Colors.blue.shade700),
              const SizedBox(width: 8),
              Text(
                '为什么需要 Tailscale？',
                style: TextStyle(
                  color: Colors.blue.shade700,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            'Tailscale 是一个安全的虚拟局域网工具，\n'
            '让您在不同网络环境下也能安全访问\n'
            '项目服务器，无需配置路由器。',
            style: TextStyle(fontSize: 14, height: 1.5),
          ),
        ],
      ),
    );
  }

  Widget _buildActions(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () => _openTailscaleDownload(),
            child: const Text('下载 Tailscale'),
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
            ),
            child: const Text('我已连接，重新检测'),
          ),
        ),
      ],
    );
  }

  void _openTailscaleDownload() async {
    final url = 'https://tailscale.com/download';
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}
```

#### 13.1.3 main.dart（启动检查集成）

```dart
import 'package:flutter/material.dart';
import 'services/network_service.dart';
import 'widgets/tailscale_guide_screen.dart';
import 'widgets/network_status_indicator.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 初始化网络服务
  final networkService = NetworkService();
  await networkService.initialize();

  runApp(MyApp(networkService: networkService));
}

class MyApp extends StatelessWidget {
  final NetworkService networkService;

  const MyApp({super.key, required this.networkService});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BDC-AI 移动端',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: SplashScreen(networkService: networkService),
    );
  }
}

/// 启动屏幕
class SplashScreen extends StatefulWidget {
  final NetworkService networkService;

  const SplashScreen({super.key, required this.networkService});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkNetworkAndNavigate();
  }

  Future<void> _checkNetworkAndNavigate() async {
    // 等待 2 秒以显示启动画面
    await Future.delayed(const Duration(seconds: 2));

    if (!mounted) return;

    final isConnected = widget.networkService.currentStatus == NetworkStatus.connected;

    if (isConnected) {
      // 已连接，进入主界面
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => MainScreen(networkService: widget.networkService),
          ),
        );
      }
    } else {
      // 未连接，显示引导页面
      if (mounted) {
        final shouldRetry = await Navigator.of(context).push<bool>(
          MaterialPageRoute(
            builder: (context) => const TailscaleGuideScreen(),
          ),
        );

        if (shouldRetry == true && mounted) {
          // 重新检测
          await widget.networkService.checkConnectionNow();
          final retryConnected = widget.networkService.currentStatus == NetworkStatus.connected;

          if (retryConnected && mounted) {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (context) => MainScreen(networkService: widget.networkService),
              ),
            );
          }
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.energy_savings_leaf, size: 80, color: Colors.green),
            const SizedBox(height: 24),
            const Text(
              'BDC-AI',
              style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text('建筑节能诊断与能源管理平台'),
            const SizedBox(height: 48),
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            const Text('正在检测网络连接...'),
          ],
        ),
      ),
    );
  }
}

/// 主屏幕
class MainScreen extends StatelessWidget {
  final NetworkService networkService;

  const MainScreen({super.key, required this.networkService});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BDC-AI'),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Center(
              child: NetworkStatusIndicator(),
            ),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle, size: 64, color: Colors.green),
            const SizedBox(height: 24),
            const Text(
              '连接成功！',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Text(
              '后端地址: ${networkService.backendUrl}',
              style: TextStyle(color: Colors.grey.shade600),
            ),
          ],
        ),
      ),
    );
  }
}
```

### 13.2 配置文件示例

#### 13.2.1 Tailscale ACL 示例

```json
{
  // 访问控制列表
  "acls": [
    // 允许所有设备互访（简单配置）
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["*:*"]
    },

    // 或使用更细粒度的控制
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["tag:server:8000"]
    }
  ],

  // 标签所有者
  "tagOwners": {
    "tag:server": ["group:admins"],
    "tag:client": ["group:users"]
  },

  // 用户组
  "groups": {
    "group:admins": ["admin@example.com"],
    "group:users": ["user1@example.com", "user2@example.com"]
  },

  // 主机别名
  "hosts": {
    "bdc-server": "100.x.x.1",
    "bdc-manager": "100.x.x.2"
  }
}
```

#### 13.2.2 后端配置示例

**启动脚本** (`scripts/start_backend.bat`)：

```batch
@echo off
echo Starting BDC-AI Backend Service...
cd /d "D:\Huawei Files\华为家庭存储\Programs\program-bdc-ai"
python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
```

**环境变量** (`.env`)：

```bash
# Tailscale 后端 IP
TAILSCALE_IP=100.x.x.1

# 数据库连接
DATABASE_URL=postgresql://admin:password@localhost:5432/bdc_ai

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### 13.3 命令速查

#### Windows Tailscale 常用命令

```powershell
# 查看连接状态
tailscale status

# 查看 Tailscale IP
tailscale ip -4

# 退出登录
tailscale logout

# 重新登录
tailscale up

# 查看 DERP 配置
tailscale derp-map

# 查看版本
tailscale version

# 查看帮助
tailscale --help
```

#### 移动端测试命令

```bash
# 测试后端连接
curl http://100.x.x.1:8000/api/v1/health

# 测试端口连通性
telnet 100.x.x.1 8000

# 测试网络延迟
ping 100.x.x.1
```

#### 防火墙命令

```powershell
# 添加防火墙规则
New-NetFirewallRule -DisplayName "BDC-AI Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# 查看防火墙规则
Get-NetFirewallRule -DisplayName "*BDC-AI*"

# 删除防火墙规则
Remove-NetFirewallRule -DisplayName "BDC-AI Backend"
```

### 13.4 参考资料

**官方文档**：
- Tailscale 官方文档：https://tailscale.com/kb/
- Tailscale ACL 指南：https://tailscale.com/kb/1018/acls/
- Tailscale DERP 配置：https://tailscale.com/kb/1118/derps/
- Flutter 网络编程：https://docs.flutter.dev/cookbook/networking

**社区资源**：
- Tailscale GitHub：https://github.com/tailscale/tailscale
- Tailscale Discourse：https://forum.tailscale.com/
- Flutter 中文社区：https://flutter.cn/

**相关技术**：
- WireGuard：https://www.wireguard.com/
- DERP：https://tailscale.com/kb/1118/derps/
- PostgreSQL：https://www.postgresql.org/docs/

---

## 总结

本文档提供了 BDC-AI 项目使用 Tailscale 虚拟局域网的完整实施方案。通过 Tailscale，团队可以安全、便捷地实现跨网络的设备互联，无需复杂的网络配置和公网 IP。

**关键优势**：
- 零配置部署
- 企业级安全
- 跨平台支持
- 永久免费（100 设备）
- 适合小团队使用

**实施时间**：
- 服务端配置：20 分钟
- 移动端配置（每台设备）：10 分钟
- PC 端配置（每台设备）：10 分钟
- 代码集成：2 小时
- **总计：约 4 小时（建议分 2 天完成）**

**后续维护**：
- 每月设备审计
- 定期检查连接状态
- 及时移除不活跃设备
- 保持客户端更新

如有任何问题，请参考本文档的故障排查章节，或访问 Tailscale 官方文档获取更多帮助。
