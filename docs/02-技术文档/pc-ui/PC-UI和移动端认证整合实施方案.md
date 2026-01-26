# BDC-AI PC-UI 和移动端认证系统整合实施方案

生成时间：2026-01-25
版本：v2.0（安全增强版）

---

## 📋 目录

1. [安全风险评估](#安全风险评估)
2. [项目概述](#项目概述)
3. [技术架构](#技术架构)
4. [实施计划](#实施计划)
5. [安全实施指南](#安全实施指南)
6. [移动端整合](#移动端整合)
7. [PC-UI 整合](#pc-ui-整合)
8. [测试与验证](#测试与验证)
9. [部署上线](#部署上线)
10. [最佳实践](#最佳实践)

---

## ⚠️ 安全风险评估

### 🔴 高风险问题

#### 1. PC 登录页默认 admin 账号

**问题描述**：
```python
username.value = username.value or 'admin'
password.value = password.value or 'admin123'
```

**风险等级**：🔴 高危

**风险说明**：
- 输入为空时自动使用 admin/admin123 登录
- 生产环境部署时如果忘记移除，将成为公开后门
- 任何人空凭据即可登录系统

**解决方案**：
- ✅ **必须**在开发环境保留（仅开发便利）
- ✅ **必须**在生产环境完全移除
- ✅ 使用环境变量控制：`ALLOW_DEFAULT_LOGIN`
- ✅ 在代码中添加环境检查：
  ```python
  if os.getenv('ENVIRONMENT') == 'production':
      # 生产环境：不允许默认登录
      pass
  else:
      # 开发环境：允许默认登录
      username.value = username.value or 'admin'
      password.value = password.value or 'admin123'
  ```

#### 2. Base URL 硬编码

**问题描述**：
```dart
// mobile/lib/main.dart
authService = AuthService(baseUrl: 'http://localhost:8000');

// pc_ui/auth/auth_manager.py
auth_manager = AuthManager(base_url="http://localhost:8000")
```

**风险等级**：🟡 中等

**风险说明**：
- HTTP 传输未加密，存在窃听风险
- 硬编码 URL 导致无法灵活切换环境
- 修改环境需要重新打包/部署

**解决方案**：
- ✅ 使用环境变量配置 API 地址
- ✅ 生产环境强制使用 HTTPS
- ✅ 支持多环境配置（开发/测试/生产）
- ✅ 移动端使用 Flutter Flavor 或环境配置

#### 3. PC 端无 refresh_token / 401 处理

**问题描述**：
- `AuthManager` 只保存 `access_token`，没有 `refresh_token`
- 没有统一处理 401 错误

**风险等级**：🟡 中等

**风险说明**：
- Token 过期后所有请求直接 401
- 用户体验差："假死"状态
- 需要手动重新登录

**解决方案**：
- ✅ 阶段 2：添加基础 401 处理（自动登出）
- ✅ 阶段 4：视需要添加 refresh_token 支持

### 🟡 中风险问题

#### 4. 客户端权限逻辑缺失

**问题描述**：
- 前端只做"是否登录"检查
- 没有根据 role/permission 控制菜单和按钮

**风险等级**：🟢 低（不影响后端安全）

**风险说明**：
- 用户能看到但无权限的功能
- 点击后显示 403 错误
- 用户体验差

**解决方案**：
- ✅ 阶段 4：根据角色隐藏菜单（UX 优化）
- ✅ 后端继续执行严格的权限检查

---

## 项目概述

### 目标

将 BDC-AI 的账号权限系统整合到现有的移动端（Flutter）和 PC-UI（NiceGUI）中，实现：
- ✅ 统一的认证机制
- ✅ 安全的 Token 管理
- ✅ 完善的权限控制
- ✅ 良好的用户体验
- ✅ 生产级安全标准

### 当前状态

| 组件 | 状态 | 说明 |
|-----|------|------|
| 后端认证 API | ✅ 完成 | 所有接口已实现并通过测试（100%） |
| 后端权限检查 | ✅ 完成 | 业务 API 已添加认证依赖 |
| 移动端框架 | ⏸ 存在 | 需要添加认证逻辑 |
| PC-UI 框架 | ⏸ 存在 | 需要添加认证逻辑 |

---

## 技术架构

### 架构图

```
┌─────────────────────────────────────────────────────┐
│                   客户端层                          │
├──────────────┬──────────────────────────────────────┤
│  移动端      │           PC-UI (NiceGUI)           │
│  (Flutter)   │                                      │
│              │  ┌────────────┬────────────┐        │
│  - 登录页面  │  │  登录页面   │  主界面    │        │
│  - Token管理 │  │  Token管理  │  权限控制  │        │
│  - 自动刷新  │  │  会话管理   │  401处理   │        │
│  - 权限控制  │  └────────────┴────────────┘        │
└──────┬───────┴──────────────────────────────────────┘
       │
       │ HTTPS (生产环境)
       │ HTTP (开发环境)
       ▼
┌─────────────────────────────────────────────────────┤
│              后端 API 层 (FastAPI)                  │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │  认证端点 (/api/v1/auth/)                │     │
│  │  - POST   /login                         │     │
│  │  - POST   /refresh                       │     │
│  │  - POST   /logout                        │     │
│  │  - GET    /me                            │     │
│  │  - POST   /change-password               │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │  业务端点 (/api/v1/)                     │     │
│  │  - /projects/ (已添加认证)              │     │
│  │  - /buildings/ (待添加认证)             │     │
│  │  - /assets/ (待添加认证)                │     │
│  └──────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

---

## 实施计划

### 阶段划分（更新版）

| 阶段 | 内容 | 预计时间 | 优先级 | 安全要求 |
|-----|------|---------|--------|---------|
| **阶段 1** | 移动端认证整合 | 4 小时 | 🔴 高 | 强制 HTTPS |
| **阶段 2** | PC-UI 认证整合 | 3 小时 | 🔴 高 | 移除默认账号 |
| **阶段 3** | 联调 & 安全校验 | 2 小时 | 🔴 高 | 权限验证 |
| **阶段 4** | 优化完善 | 2 小时 | 🟡 中 | Token 刷新 |
| **总计** | | **11 小时** | | |

### 实施顺序建议

**阶段 1：移动端认证（优先）**
- ✅ 完整的 Token 管理（access + refresh）
- ✅ 自动刷新机制
- ✅ 401 统一处理
- ✅ 配置化 API 地址

**阶段 2：PC-UI 基础认证**
- ✅ 移除 admin 默认账号（关键！）
- ✅ 添加 401 自动登出
- ✅ 会话持久化
- ⏸ 暂不做 refresh_token

**阶段 3：联调 & 安全校验**
- ✅ 新账号登录测试
- ✅ 权限不足测试（403）
- ✅ 401 自动登出测试

**阶段 4：优化完善（可选）**
- ⏸ PC 端 refresh_token（如需要）
- ⏸ 前端权限控制（菜单级别）
- ⏸ 并发刷新互斥锁

---

## 安全实施指南

### 移动端安全配置

#### 1. 环境配置

**文件**：`mobile/lib/config.dart`

```dart
class Config {
  /// API 基础地址（从环境变量或配置读取）
  static String get apiBaseUrl {
    // 从环境变量读取
    const baseUrl = String.fromEnvironment('API_BASE_URL');

    if (baseUrl.isNotEmpty) {
      return baseUrl;
    }

    // 根据编译配置选择
    if (const bool.fromEnvironment('PRODUCTION', defaultValue: false)) {
      // 生产环境：必须使用 HTTPS
      return 'https://api.example.com';
    } else if (const bool.fromEnvironment('DEVELOPMENT', defaultValue: true)) {
      // 开发环境
      return 'http://localhost:8000';
    } else {
      // 测试环境
      return 'https://test-api.example.com';
    }
  }

  /// 是否生产环境
  static const bool isProduction = bool.fromEnvironment('PRODUCTION', defaultValue: false);

  /// 是否启用调试模式
  static const bool enableDebug = !isProduction;
}
```

**使用方式**：
```dart
// main.dart
authService = AuthService(baseUrl: Config.apiBaseUrl);
```

#### 2. AuthService 安全改进

**添加刷新互斥锁**：
```dart
class AuthService {
  ...
  bool _isRefreshing = false;

  /// 刷新 Token（带互斥锁）
  Future<bool> _refreshAccessToken() async {
    // 防止并发刷新
    if (_isRefreshing) {
      return false;
    }

    _isRefreshing = true;

    try {
      if (_refreshToken == null) return false;

      final response = await _dio.post(
        '/api/v1/auth/refresh',
        data: {'refresh_token': _refreshToken},
      );

      final data = response.data;
      _accessToken = data['access_token'];
      _refreshToken = data['refresh_token'];

      await _storage.write(key: _tokenKey, value: _accessToken);
      await _storage.write(key: _refreshTokenKey, value: _refreshToken);

      return true;
    } catch (e) {
      return false;
    } finally {
      _isRefreshing = false;
    }
  }
}
```

### PC-UI 安全配置

#### 1. 环境配置

**文件**：`pc_ui/config.py`

```python
import os
from pathlib import Path

class Config:
    """配置管理"""

    @staticmethod
    def get_api_base_url():
        """获取 API 基础地址"""
        # 从环境变量读取
        api_url = os.getenv('BDC_API_URL')
        if api_url:
            return api_url

        # 根据环境变量判断
        environment = os.getenv('ENVIRONMENT', 'development')

        if environment == 'production':
            # 生产环境：必须使用 HTTPS
            return 'https://api.example.com'
        elif environment == 'testing':
            return 'https://test-api.example.com'
        else:
            # 开发环境
            return 'http://localhost:8000'

    @staticmethod
    def is_production():
        """是否生产环境"""
        return os.getenv('ENVIRONMENT', 'development') == 'production'

    @staticmethod
    def allow_default_login():
        """是否允许默认登录（仅开发环境）"""
        return not Config.is_production()
```

#### 2. AuthManager 安全改进

**添加 401 处理**：

```python
class AuthManager:
    """认证管理器（安全增强版）"""

    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = Config.get_api_base_url()

        self.base_url = base_url
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user: Optional[dict] = None

        # 尝试从存储恢复会话
        self._restore_session()

    def _save_session(self):
        """保存会话到存储"""
        app.storage.user['token'] = self.token
        app.storage.user['refresh_token'] = self.refresh_token
        app.storage.user['user'] = self.user

    def _clear_session(self):
        """清除会话"""
        self.token = None
        self.refresh_token = None
        self.user = None
        if 'user' in app.storage.user:
            del app.storage.user['token']
            del app.storage.user['refresh_token']
            del app.storage.user['user']

    def _handle_401(self, response: requests.Response) -> bool:
        """处理 401 错误"""
        if response.status_code == 401:
            # Token 过期，自动登出
            self.logout()

            # 显示提示
            ui.notify('登录已过期，请重新登录', type='warning')

            # 跳转到登录页
            ui.navigate('/login')

            return True
        return False

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET 请求（带 401 处理）"""
        response = self.session.get(f"{self.base_url}{endpoint}", **kwargs)

        # 检查 401
        if self._handle_401(response):
            raise Exception('Unauthorized')

        return response

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST 请求（带 401 处理）"""
        response = self.session.post(f"{self.base_url}{endpoint}", **kwargs)

        # 检查 401
        if self._handle_401(response):
            raise Exception('Unauthorized')

        return response

    # 同样处理 put 和 delete
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """PUT 请求"""
        response = self.session.put(f"{self.base_url}{endpoint}", **kwargs)

        if self._handle_401(response):
            raise Exception('Unauthorized')

        return response

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE 请求"""
        response = self.session.delete(f"{self.base_url}{endpoint}", **kwargs)

        if self._handle_401(response):
            raise Exception('Unauthorized')

        return response
```

#### 3. 登录页面安全改进

**文件**：`pc_ui/pages/login.py`

```python
"""
登录页面（安全增强版）
"""
from nicegui import ui, app
from ..auth.auth_manager import auth_manager
from ..config import Config


def show_login_page():
    """显示登录页面"""

    # 清空页面
    ui.query('body').classes('bg-gray-100')

    with ui.column().classes('w-full h-full items-center justify-center'):
        # Logo 和标题
        with ui.card().classes('w-96 p-8'):
            ui.label('BDC-AI').classes('text-4xl font-bold text-center mb-2')
            ui.label('建筑节能管理平台').classes('text-center text-gray-600 mb-8')

            # 登录表单
            username = ui.input(
                '用户名',
                placeholder='请输入用户名',
                validation=lambda x: True if x else '请输入用户名'
            ).props('outlined').classes('w-full mb-4')

            password = ui.input(
                '密码',
                placeholder='请输入密码',
                password=True,
                validation=lambda x: True if x else '请输入密码'
            ).props('outlined').classes('w-full mb-4')

            message = ui.label('').classes('text-red-600 mb-4')

            async def do_login():
                """执行登录"""
                message.text = ''

                # ✅ 安全改进：移除默认账号，生产环境禁止
                if not username.value or not password.value:
                    message.text = '请输入用户名和密码'
                    return

                # 开发环境可选：显示提示
                if not Config.is_production():
                    # 仅开发环境显示默认账号提示
                    if not username.value:
                        message.text = '提示：开发环境可使用 admin/admin123'

                success, msg = auth_manager.login(username.value, password.value)

                if success:
                    ui.notify('登录成功', type='positive')
                    # 导航到主页面
                    app.storage.user['redirect_to_home'] = True
                    ui.navigate('/')
                else:
                    message.text = msg
                    ui.notify(msg, type='negative')

            ui.button('登录', on_click=do_login).props('push').classes('w-full')
```

---

## 移动端整合

### 技术栈

- **框架**：Flutter
- **状态管理**：Provider
- **HTTP 客户端**：Dio
- **安全存储**：flutter_secure_storage
- **本地缓存**：shared_preferences

### 实施步骤

#### 步骤 1：添加依赖（5 分钟）

```yaml
# mobile/pubspec.yaml

dependencies:
  dio: ^5.3.0
  flutter_secure_storage: ^8.0.0
  shared_preferences: ^2.2.0
  provider: ^6.0.0
  json_annotation: ^4.8.0
  envied: ^0.5.0  # 新增：环境变量支持

dev_dependencies:
  json_serializable: ^6.7.0
  build_runner: ^2.4.0
```

安装依赖：
```bash
cd mobile
flutter pub get
```

#### 步骤 2：创建配置文件（新增，15 分钟）

**文件**：`mobile/lib/config.dart`

```dart
import 'package:envied/envied.dart';
import 'package:flutter/foundation.dart';

part 'config.g.dart';

@Envied(path: 'API_BASE_URL', defaultValue: 'http://localhost:8000')
class Config {
  static const String apiBaseUrl = _apiBaseUrl;

  @Envied(path: 'PRODUCTION', defaultValue: false)
  static const bool isProduction = _isProduction;

  @Envied(path: 'ENABLE_DEBUG', defaultValue: true)
  static const bool enableDebug = _enableDebug;
}
```

生成代码：
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

#### 步骤 3：创建数据模型（30 分钟）

**文件**：`mobile/lib/models/auth.dart`

```dart
import 'package:json_annotation/json_annotation.dart';

part 'auth.g.dart';

@JsonSerializable()
class LoginRequest {
  final String username;
  final String password;

  LoginRequest({
    required this.username,
    required this.password,
  });

  factory LoginRequest.fromJson(Map<String, dynamic> json) =>
      _$LoginRequestFromJson(json);
  Map<String, dynamic> toJson() => _$LoginRequestToJson(this);
}

@JsonSerializable()
class LoginResponse {
  final String access_token;
  final String refresh_token;
  final String token_type;
  final User? user;

  LoginResponse({
    required this.access_token,
    required this.refresh_token,
    required this.token_type,
    this.user,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) =>
      _$LoginResponseFromJson(json);
  Map<String, dynamic> toJson() => _$LoginResponseToJson(this);
}

@JsonSerializable()
class User {
  final String id;
  final String username;
  final String email;
  final String? role_name;  // 新增：角色名称
  final List<String>? permissions;  // 新增：权限列表
  final bool is_active;
  final bool is_superuser;

  User({
    required this.id,
    required this.username,
    required this.email,
    this.role_name,
    this.permissions,
    required this.is_active,
    required this.is_superuser,
  });

  factory User.fromJson(Map<String, dynamic> json) =>
      _$UserFromJson(json);
  Map<String, dynamic> toJson() => _$UserToJson(this);
}

@JsonSerializable()
class ApiError {
  final String detail;
  final int? status;

  ApiError({
    required this.detail,
    this.status,
  });

  factory ApiError.fromJson(Map<String, dynamic> json) =>
      _$ApiErrorFromJson(json);
  Map<String, dynamic> toJson() => _$ApiErrorToJson(this);
}
```

生成代码：
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

#### 步骤 4：创建认证服务（1 小时，安全增强）

**文件**：`mobile/lib/services/auth_service.dart`

```dart
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/auth.dart';
import '../config.dart';  // 新增

class AuthService {
  final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  static const String _tokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userKey = 'user';

  String? _accessToken;
  String? _refreshToken;
  User? _currentUser;
  bool _isRefreshing = false;  // 新增：刷新互斥锁

  AuthService({required String baseUrl})
      : _dio = Dio(
          BaseOptions(
            baseUrl: baseUrl,
            connectTimeout: const Duration(seconds: 10),
            receiveTimeout: const Duration(seconds: 10),
            headers: {
              'Content-Type': 'application/json',
            },
          ),
        ) {
    _setupInterceptors();
  }

  /// 设置拦截器自动添加 Token
  void _setupInterceptors() {
    _dio.interceptors.clear();

    // 添加 Token 拦截器
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // 自动添加 Token
          if (_accessToken != null) {
            options.headers['Authorization'] = 'Bearer $_accessToken';
          }
          return handler.next(options);
        },
        onError: (error, handler) async {
          // 处理 401 错误，尝试刷新 Token
          if (error.response?.statusCode == 401) {
            final refreshed = await _refreshAccessToken();

            if (refreshed) {
              // 重试原请求
              return handler.resolve(await _retry(error.requestOptions));
            } else {
              // 刷新失败，清除 Token
              await logout();
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  /// 登录
  Future<(bool, String?)> login(String username, String password) async {
    try {
      final response = await _dio.post(
        '/api/v1/auth/login',
        data: LoginRequest(username: username, password: password).toJson(),
      );

      final loginResponse = LoginResponse.fromJson(response.data);

      _accessToken = loginResponse.access_token;
      _refreshToken = loginResponse.refresh_token;
      _currentUser = loginResponse.user;

      // 安全存储 Token
      await _storage.write(key: _tokenKey, value: _accessToken);
      await _storage.write(key: _refreshTokenKey, value: _refreshToken);

      // 缓存用户信息
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_userKey, jsonEncode(_currentUser!.toJson()));

      return (true, null);
    } on DioException catch (e) {
      final message = e.response?.data['detail'] ?? '登录失败';
      return (false, message);
    } catch (e) {
      return (false, '网络错误：$e');
    }
  }

  /// 刷新 Token（带互斥锁）
  Future<bool> _refreshAccessToken() async {
    // ⚠️ 安全改进：防止并发刷新
    if (_isRefreshing) {
      return false;
    }

    if (_refreshToken == null) return false;

    _isRefreshing = true;

    try {
      final response = await _dio.post(
        '/api/v1/auth/refresh',
        data: {'refresh_token': _refreshToken},
      );

      final data = response.data;
      _accessToken = data['access_token'];
      _refreshToken = data['refresh_token'];

      await _storage.write(key: _tokenKey, value: _accessToken);
      await _storage.write(key: _refreshTokenKey, value: _refreshToken);

      return true;
    } catch (e) {
      return false;
    } finally {
      _isRefreshing = false;
    }
  }

  /// 重试请求
  Future<Response> _retry(RequestOptions requestOptions) async {
    final options = Options(
      method: requestOptions.method,
      headers: {
        ...requestOptions.headers,
        'Authorization': 'Bearer $_accessToken',
      },
    );

    return _dio.request(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }

  /// 登出
  Future<void> logout() async {
    _accessToken = null;
    _refreshToken = null;
    _currentUser = null;

    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _refreshTokenKey);

    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userKey);
  }

  /// 检查是否已登录
  Future<bool> isAuthenticated() async {
    if (_accessToken != null) return true;

    // 尝试从存储恢复
    _accessToken = await _storage.read(key: _tokenKey);
    _refreshToken = await _storage.read(key: _refreshTokenKey);

    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString(_userKey);
    if (userJson != null) {
      _currentUser = User.fromJson(jsonDecode(userJson));
    }

    return _accessToken != null;
  }

  /// 获取当前用户
  User? get currentUser => _currentUser;

  /// 获取 Dio 实例用于 API 调用
  Dio get apiClient => _dio;

  /// 检查用户权限
  bool hasPermission(String permission) {
    if (_currentUser?.is_superuser ?? false) {
      return true;  // 超级管理员拥有所有权限
    }

    return _currentUser?.permissions?.contains(permission) ?? false;
  }
}

// 全局单例
late AuthService authService;
```

#### 步骤 5：创建 Provider（30 分钟）

**文件**：`mobile/lib/providers/auth_provider.dart`

```dart
import 'package:flutter/foundation.dart';
import '../services/auth_service.dart';
import '../models/auth.dart';

class AuthProvider with ChangeNotifier {
  final AuthService _authService;

  User? _user;
  bool _isLoading = false;
  String? _errorMessage;

  AuthProvider(this._authService) {
    _init();
  }

  /// 初始化，检查登录状态
  Future<void> _init() async {
    _isLoading = true;
    notifyListeners();

    final isAuthenticated = await _authService.isAuthenticated();

    if (isAuthenticated) {
      _user = _authService.currentUser;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// 登录
  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    final (success, error) = await _authService.login(username, password);

    _isLoading = false;

    if (success) {
      _user = _authService.currentUser;
      notifyListeners();
      return true;
    } else {
      _errorMessage = error;
      notifyListeners();
      return false;
    }
  }

  /// 登出
  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    notifyListeners();
  }

  /// 是否已登录
  bool get isAuthenticated => _user != null;

  /// 当前用户
  User? get user => _user;

  /// 是否加载中
  bool get isLoading => _isLoading;

  /// 错误消息
  String? get errorMessage => _errorMessage;

  /// 检查权限
  bool hasPermission(String permission) {
    return _authService.hasPermission(permission);
  }
}
```

#### 步骤 6：创建登录页面（1 小时）

**文件**：`mobile/lib/screens/login_screen.dart`（保持不变，参考原方案）

#### 步骤 7：更新主应用（30 分钟，环境配置增强）

**文件**：`mobile/lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';  // 新增
import 'services/auth_service.dart';
import 'providers/auth_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'config.dart';  // 新增

Future<void> main() async {
  // ✅ 安全改进：加载环境变量
  await dotenv.load();

  // ✅ 安全改进：验证生产环境配置
  if (Config.isProduction && Config.apiBaseUrl.startsWith('http://')) {
    throw Exception('生产环境必须使用 HTTPS');
  }

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider(AuthService(baseUrl: Config.apiBaseUrl)),
      child: MaterialApp(
        title: 'BDC-AI',
        theme: ThemeData(
          primarySwatch: Colors.green,
          useMaterial3: true,
        ),
        initialRoute: '/',
        routes: {
          '/': (context) => const SplashScreen(),
          '/login': (context) => const LoginScreen(),
          '/home': (context) => const HomeScreen(),
        },
      ),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    final authProvider = context.read<AuthProvider>();

    // 等待初始化完成
    await Future.delayed(const Duration(seconds: 1));

    if (mounted) {
      if (authProvider.isAuthenticated) {
        Navigator.pushReplacementNamed(context, '/home');
      } else {
        Navigator.pushReplacementNamed(context, '/login');
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
            SizedBox(height: 24),
            Text('BDC-AI', style: TextStyle(fontSize: 32)),
            SizedBox(height: 48),
            CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}
```

---

## PC-UI 整合

### 技术栈

- **框架**：NiceGUI
- **HTTP 客户端**：requests
- **会话管理**：app.storage.user
- **配置管理**：环境变量

### 实施步骤

#### 步骤 1：创建配置文件（新增，15 分钟）

**文件**：`pc_ui/config.py`

```python
"""
PC-UI 配置管理
"""
import os


class Config:
    """配置类"""

    @staticmethod
    def get_api_base_url():
        """获取 API 基础地址"""
        # 从环境变量读取
        api_url = os.getenv('BDC_API_URL')
        if api_url:
            return api_url

        # 根据环境变量判断
        environment = os.getenv('ENVIRONMENT', 'development')

        if environment == 'production':
            # 生产环境：强制 HTTPS
            return 'https://api.example.com'
        elif environment == 'testing':
            return 'https://test-api.example.com'
        else:
            # 开发环境
            return 'http://localhost:8000'

    @staticmethod
    def is_production():
        """是否生产环境"""
        return os.getenv('ENVIRONMENT', 'development') == 'production'

    @staticmethod
    def is_development():
        """是否开发环境"""
        return os.getenv('ENVIRONMENT', 'development') == 'development'

    @staticmethod
    def allow_default_login():
        """是否允许默认登录（仅开发环境）"""
        return not Config.is_production()
```

#### 步骤 2：创建认证管理器（30 分钟，安全增强）

**文件**：`pc_ui/auth/auth_manager.py`

```python
"""
PC-UI 认证管理器（安全增强版）
"""
import requests
from typing import Optional
from nicegui import app
from .config import Config


class AuthManager:
    """认证管理器"""

    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = Config.get_api_base_url()

        self.base_url = base_url
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None  # 新增
        self.user: Optional[dict] = None

        # 尝试从存储恢复会话
        self._restore_session()

    def _restore_session(self) -> bool:
        """从存储恢复会话"""
        if 'user' in app.storage.user:
            self.token = app.storage.user.get('token')
            self.refresh_token = app.storage.user.get('refresh_token')  # 新增
            self.user = app.storage.user.get('user')
            if self.token:
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                return True
        return False

    def _save_session(self):
        """保存会话到存储"""
        app.storage.user['token'] = self.token
        app.storage.user['refresh_token'] = self.refresh_token  # 新增
        app.storage.user['user'] = self.user

    def _clear_session(self):
        """清除会话"""
        self.token = None
        self.refresh_token = None
        self.user = None
        if 'user' in app.storage.user:
            del app.storage.user['token']
            del app.storage.user['refresh_token']
            del app.storage.user['user']

    def _handle_401(self, response: requests.Response) -> bool:
        """✅ 新增：处理 401 错误"""
        if response.status_code == 401:
            # Token 过期，自动登出
            self.logout()

            # 显示提示
            ui.notify('登录已过期，请重新登录', type='warning')

            # 跳转到登录页
            ui.navigate('/login')

            return True
        return False

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """
        登录

        Returns:
            (success, message)
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.refresh_token = data.get('refresh_token')  # 新增
                self.user = data.get('user')

                # 更新会话头
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })

                # 保存会话
                self._save_session()

                return True, "登录成功"
            else:
                error_data = response.json()
                return False, error_data.get('detail', '登录失败')

        except requests.exceptions.Timeout:
            return False, "连接超时"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到服务器"
        except Exception as e:
            return False, f"登录错误：{str(e)}"

    def logout(self):
        """登出"""
        self._clear_session()

    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self.token is not None

    def has_permission(self, permission: str) -> bool:
        """✅ 新增：检查用户权限"""
        if not self.user:
            return False

        if self.user.get('is_superuser', False):
            return True

        permissions = self.user.get('permissions', [])
        return permission in permissions

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET 请求（✅ 带 401 处理）"""
        response = self.session.get(f"{self.base_url}{endpoint}", **kwargs)

        # 检查 401
        if self._handle_401(response):
            raise Exception('Unauthorized')

        return response

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST 请求（✅ 带 401 处理）"""
        response = self.session.post(f"{self.base_url}{endpoint}", **kwargs)

        # 检查 401
        if self._handle_401(response):
            raise Exception('Unauthorized')

        return response

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """PUT 请求（✅ 带 401 处理）"""
        response = self.session.put(f"{self.base_url}{endpoint}", **kwargs)

        if self._handle_401(response):
            raise Exception('Unauthorized')

        return response

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE 请求（✅ 带 401 处理）"""
        response = self.session.delete(f"{self.base_url}{endpoint}", **kwargs)

        if self._handle_401(response):
            raise Exception('Unauthorized')

        return response


# 全局实例
auth_manager = AuthManager()
```

#### 步骤 3：创建登录页面（1 小时，安全增强）

**文件**：`pc_ui/pages/login.py`

```python
"""
登录页面（安全增强版）
"""
from nicegui import ui, app
from ..auth.auth_manager import auth_manager
from ..config import Config


def show_login_page():
    """显示登录页面"""

    # 清空页面
    ui.query('body').classes('bg-gray-100')

    with ui.column().classes('w-full h-full items-center justify-center'):
        # Logo 和标题
        with ui.card().classes('w-96 p-8'):
            ui.label('BDC-AI').classes('text-4xl font-bold text-center mb-2')
            ui.label('建筑节能管理平台').classes('text-center text-gray-600 mb-8')

            # ✅ 安全改进：环境标识
            if Config.is_development():
                ui.label('开发环境', size='xs').classes('text-yellow-600 mb-4')
            elif Config.is_production():
                ui.label('生产环境', size='xs').classes('text-red-600 mb-4')

            # 登录表单
            username = ui.input(
                '用户名',
                placeholder='请输入用户名',
                validation=lambda x: True if x else '请输入用户名'
            ).props('outlined').classes('w-full mb-4')

            password = ui.input(
                '密码',
                placeholder='请输入密码',
                password=True,
                validation=lambda x: True if x else '请输入密码'
            ).props('outlined').classes('w-full mb-4')

            message = ui.label('').classes('text-red-600 mb-4')

            async def do_login():
                """执行登录"""
                message.text = ''

                # ✅ 安全改进：不允许空输入
                if not username.value or not password.value:
                    message.text = '请输入用户名和密码'
                    return

                # ✅ 安全改进：开发环境提示（但不允许默认登录）
                if Config.is_development() and not username.value:
                    message.text = '提示：开发环境可使用 admin/admin123'

                success, msg = auth_manager.login(username.value, password.value)

                if success:
                    ui.notify('登录成功', type='positive')
                    # 导航到主页面
                    app.storage.user['redirect_to_home'] = True
                    ui.navigate('/')
                else:
                    message.text = msg
                    ui.notify(msg, type='negative')

            ui.button('登录', on_click=do_login).props('push').classes('w-full')


def register_login_route():
    """注册登录路由"""

    @ui.page('/login')
    def login_page():
        """登录页面路由"""
        # 如果已登录，跳转到主页
        if auth_manager.is_authenticated():
            return ui.navigate('/')

        show_login_page()
```

#### 步骤 4：创建主页面（1 小时，权限控制）

**文件**：`pc_ui/pages/home.py`

```python
"""
主页面（权限增强版）
"""
from nicegui import ui
from ..auth.auth_manager import auth_manager


def show_home_page():
    """显示主页面"""

    # 检查认证
    if not auth_manager.is_authenticated():
        ui.notify('请先登录', type='warning')
        return ui.navigate('/login')

    # 页面布局
    ui.query('body').classes('bg-gray-50')

    # 顶部导航栏
    with ui.header().classes('bg-blue-600 text-white p-4'):
        with ui.row().classes('w-full items-center'):
            ui.label('BDC-AI 建筑节能管理平台').classes('text-xl font-bold')

            ui.space()

            with ui.row().classes('items-center gap-4'):
                if auth_manager.user:
                    ui.label(f"欢迎, {auth_manager.user.get('username')}")

                    # ✅ 新增：显示角色
                    role = auth_manager.user.get('role_name', '用户')
                    ui.label(f"({role})").classes('text-sm opacity-75')

                ui.button(
                    icon='logout',
                    on_click=lambda: (
                        auth_manager.logout(),
                        ui.notify('已登出', type='info'),
                        ui.navigate('/login')
                    )
                ).props('outline round')

    # 侧边栏（✅ 权限控制）
    with ui.left_drawer().classes('bg-white'):
        ui.label('菜单').classes('text-lg font-bold mb-4')

        # 项目管理（所有用户）
        ui.menu_item(
            '项目列表',
            icon='folder',
            on_click=lambda: load_projects()
        )

        # 建筑管理（需要权限）
        if auth_manager.has_permission('buildings.view'):
            ui.menu_item(
                '建筑管理',
                icon='apartment',
                on_click=lambda: load_buildings()
            )

        # 资产管理（需要权限）
        if auth_manager.has_permission('assets.view'):
            ui.menu_item(
                '资产管理',
                icon='inventory_2',
                on_click=lambda: load_assets()
            )

        # 系统管理（仅管理员）
        if auth_manager.user.get('is_superuser'):
            ui.menu_item(
                '系统管理',
                icon='settings',
                on_click=lambda: ui.notify('开发中...')
            )

    # 主内容区
    with ui.column().classes('p-6 w-full'):
        ui.label('项目概览').classes('text-2xl font-bold mb-4')

        # 统计卡片
        with ui.row().classes('gap-4 w-full'):
            with ui.card().classes('flex-1 p-4'):
                ui.label('项目总数').classes('text-gray-600')
                ui.label('3').classes('text-4xl font-bold text-blue-600')

            with ui.card().classes('flex-1 p-4'):
                ui.label('进行中').classes('text-gray-600')
                ui.label('2').classes('text-4xl font-bold text-green-600')

            with ui.card().classes('flex-1 p-4'):
                ui.label('已完成').classes('text-gray-600')
                ui.label('1').classes('text-4xl font-bold text-gray-600')

        # 项目列表
        ui.label('项目列表').classes('text-xl font-bold mt-8 mb-4')

        with ui.card().classes('w-full'):
            projects_container = ui.column().classes('w-full')

            async def load_projects():
                """加载项目列表"""
                projects_container.clear()

                try:
                    response = auth_manager.get('/api/v1/projects/')
                    projects = response.json()

                    with projects_container:
                        ui.label(f'共 {len(projects)} 个项目').classes('mb-4')

                        for project in projects:
                            with ui.card().classes('mb-2 p-4'):
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label(project['name']).classes('text-lg font-bold')
                                    ui.label(project['status']).classes(
                                        'px-3 py-1 rounded-full '
                                        + ('bg-green-100 text-green-800' if project['status'] == 'active' else 'bg-gray-100')
                                    )

                                ui.label(f"客户：{project.get('client', 'N/A')}").classes('text-gray-600')
                                ui.label(f"类型：{project.get('type', 'N/A')}").classes('text-sm text-gray-500')

                except Exception as e:
                    if 'Unauthorized' in str(e):
                        # 401 已处理，不需要额外提示
                        pass
                    else:
                        with projects_container:
                            ui.label(f'加载失败：{str(e)}').classes('text-red-600')

            # 页面加载时自动加载项目
            load_projects()


def register_home_route():
    """注册主页路由"""

    @ui.page('/')
    async def home_page():
        """主页路由"""
        # 检查是否应该跳转到登录页
        if not auth_manager.is_authenticated():
            return ui.navigate('/login')

        show_home_page()
```

---

## 测试与验证

### 移动端测试清单

#### 基础功能
- [ ] 正确凭证登录成功
- [ ] 错误凭证显示错误
- [ ] Token 正确存储（flutter_secure_storage）
- [ ] Token 正确传递（Authorization 头）

#### Token 刷新
- [ ] Token 过期自动刷新（401 拦截器）
- [ ] 刷新成功后重试原请求
- [ ] 刷新失败跳转登录页
- [ ] 并发请求不会重复刷新（互斥锁）

#### 登出功能
- [ ] 清除本地 Token
- [ ] 返回登录页
- [ ] 自动下次登录

#### 环境配置
- [ ] 开发环境使用 HTTP（本地）
- [ ] 生产环境使用 HTTPS（验证证书）
- [ ] API 地址可配置（环境变量）

### PC-UI 测试清单

#### 基础功能
- [ ] 正确凭证登录成功
- [ ] 错误凭证显示错误
- [ ] 会话正确保存（app.storage.user）
- [ ] 刷新页面保持登录

#### 安全要求
- [ ] ❌ 开发环境：可显示默认账号提示，但不自动登录
- [ ] ✅ 生产环境：完全移除默认账号行为
- [ ] ✅ 生产环境：强制使用 HTTPS

#### 401 处理
- [ ] Token 过期自动登出
- [ ] 显示"登录已过期"提示
- [ ] 自动跳转登录页
- [ ] 加载项目时 401 正确处理

#### 权限控制
- [ ] 根据角色隐藏菜单
- [ ] 无权限功能点击返回 403
- [ ] 后端权限检查正常

### 联调测试

#### 多端登录
- [ ] 移动端和 PC-UI 同时登录同一账号
- [ ] Token 刷新不影响其他端
- [ ] 登出后其他端仍可用

#### 安全校验
- [ ] 使用新账号登录
- [ ] 验证权限检查（403）
- [ ] 验证 401 自动登出
- [ ] 验证 HTTPS 连接（生产环境）

---

## 部署上线

### 环境配置

#### 移动端环境配置

**文件**：`.env`（项目根目录）

```bash
# 开发环境
ENVIRONMENT=development
API_BASE_URL=http://localhost:8000
PRODUCTION=false
ENABLE_DEBUG=true

# 测试环境
ENVIRONMENT=testing
API_BASE_URL=https://test-api.example.com
PRODUCTION=false
ENABLE_DEBUG=true

# 生产环境
ENVIRONMENT=production
API_BASE_URL=https://api.example.com
PRODUCTION=true
ENABLE_DEBUG=false
```

**启动验证**：
```dart
// 在 main.dart 中添加验证
if (Config.isProduction && Config.apiBaseUrl.startsWith('http://')) {
  throw Exception('生产环境必须使用 HTTPS');
}
```

#### PC-UI 环境配置

**文件**：`.env`（PC-UI 目录或系统环境变量）

```bash
# 开发环境
ENVIRONMENT=development
BDC_API_URL=http://localhost:8000

# 测试环境
ENVIRONMENT=testing
BDC_API_URL=https://test-api.example.com

# 生产环境
ENVIRONMENT=production
BDC_API_URL=https://api.example.com
```

### 部署检查清单

#### 移动端部署

- [ ] 配置生产环境 API 地址（HTTPS）
- [ ] 移除开发环境默认账号
- [ ] 启用证书固定（Certificate Pinning）
- [ ] 关闭调试模式
- [ ] 签名和打包应用

#### PC-UI 部署

- [ ] 配置生产环境 API 地址（HTTPS）
- [ ] 移除开发环境默认账号
- [ ] 配置反向代理（Nginx）
- [ ] 启用 HTTPS
- [ ] 设置强密钥（storage_secret）
- [ ] 配置防火墙

---

## 最佳实践

### 安全最佳实践

#### 1. 环境隔离

**开发环境**：
- HTTP 允许
- 默认账号提示（但需手动输入）
- 详细调试信息

**生产环境**：
- 强制 HTTPS
- 完全移除默认账号
- 最小化日志输出
- 错误信息脱敏

#### 2. Token 管理

**移动端**：
- ✅ 使用 flutter_secure_storage（加密存储）
- ✅ 自动刷新机制
- ✅ 刷新互斥锁
- ✅ 刷新失败自动登出

**PC-UI**：
- ✅ 401 自动登出
- ⏸ 暂不实现 refresh_token（阶段 4 考虑）
- ✅ 会话持久化

#### 3. 权限控制

**后端（已完成）**：
- ✅ 所有业务 API 需要认证
- ✅ 严格的权限检查

**前端（阶段 4）**：
- ⏸ 根据角色隐藏菜单（UX 优化）
- ⏸ 无权限功能显示提示
- ✅ 后端继续执行权限检查

### 开发最佳实践

#### 1. API 调用规范

```dart
// ✅ 正确：使用 authService.apiClient
final response = await authService.apiClient.get('/api/v1/projects/');

// ❌ 错误：直接使用 Dio（会缺少 Token）
final response = await dio.get('/api/v1/projects/');
```

```python
# ✅ 正确：使用 auth_manager
response = auth_manager.get('/api/v1/projects/')

# ❌ 错误：直接使用 requests（会缺少 Token）
response = requests.get(f"{auth_manager.base_url}/api/v1/projects/")
```

#### 2. 错误处理

```dart
try {
  final response = await authService.apiClient.get('/api/v1/projects/');
  // 处理响应
} on UnauthorizedException {
  // 已自动登出，无需额外处理
} on Exception catch (e) {
  // 其他错误
}
```

```python
try:
    response = auth_manager.get('/api/v1/projects/')
    # 处理响应
except Exception as e:
    if 'Unauthorized' in str(e):
        # 已自动登出，无需额外处理
    pass
```

#### 3. 测试驱动

- ✅ 先测试认证流程
- ✅ 再测试业务 API
- ✅ 最后测试权限控制

---

## 附录

### A. 文件结构

```
mobile/
├── lib/
│   ├── config.dart               # ✅ 新增：配置管理
│   ├── models/
│   │   └── auth.dart              # ✅ 数据模型
│   ├── services/
│   │   └── auth_service.dart     # ✅ 认证服务
│   ├── providers/
│   │   └── auth_provider.dart    # ✅ Provider
│   ├── screens/
│   │   ├── login_screen.dart     # ✅ 登录页
│   │   └── splash_screen.dart    # ✅ 启动页
│   ├── main.dart                  # ✅ 主应用
│   └── .env                      # ✅ 环境配置

pc_ui/
├── config.py                    # ✅ 新增：配置管理
├── auth/
│   └── auth_manager.py         # ✅ 认证管理器（增强）
├── pages/
│   ├── login.py                 # ✅ 登录页（增强）
│   └── home.py                  # ✅ 主页（权限控制）
└── main.py                     # ✅ 主应用
```

### B. 环境变量参考

**移动端**：

```bash
# .env
ENVIRONMENT=development
API_BASE_URL=http://localhost:8000
PRODUCTION=false
ENABLE_DEBUG=true
```

**PC-UI**：

```bash
# 系统环境变量或 .env
ENVIRONMENT=development
BDC_API_URL=http://localhost:8000
```

### C. 安全检查清单

**开发阶段**：
- [ ] 环境配置正确
- [ ] 默认账号仅提示，不自动填充
- [ ] HTTPS 验证逻辑已添加
- [ ] 401 处理逻辑已添加

**部署前**：
- [ ] 生产环境配置正确
- [ ] API 地址使用 HTTPS
- [ ] 默认账号完全移除
- [ ] 调试模式关闭
- [ ] 安全密钥更新

**部署后**：
- [ ] 验证 HTTPS 证书
- [ ] 测试登录登出
- [ ] 测试 Token 过期
- [ ] 测试权限检查
- [ ] 验证多端登录

---

**文档维护**：BDC-AI 开发团队
**最后更新**：2026-01-25
**版本**：v2.0（安全增强版）
**上一版本**：v1.0（初版）
