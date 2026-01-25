# BDC-AI PC-UI 和移动端认证系统整合实施方案

生成时间：2026-01-25
版本：v1.0

---

## 📋 目录

1. [项目概述](#项目概述)
2. [技术架构](#技术架构)
3. [实施计划](#实施计划)
4. [移动端整合](#移动端整合)
5. [PC-UI 整合](#pc-ui-整合)
6. [测试与验证](#测试与验证)
7. [部署上线](#部署上线)
8. [时间估算](#时间估算)

---

## 项目概述

### 目标

将 BDC-AI 的账号权限系统整合到现有的移动端（Flutter）和 PC-UI（NiceGUI）中，实现：
- ✅ 统一的认证机制
- ✅ 自动 Token 管理
- ✅ 权限控制
- ✅ 良好的用户体验

### 当前状态

| 组件 | 状态 | 说明 |
|-----|------|------|
| 后端认证 API | ✅ 完成 | 所有接口已实现并通过测试 |
| 移动端框架 | ⏸ 存在 | 需要添加认证逻辑 |
| PC-UI 框架 | ⏸ 存在 | 需要添加认证逻辑 |
| 认证中间件 | ❌ 缺失 | 需要开发 |

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
│  - 自动刷新  │  │  自动刷新   │  会话管理  │        │
└──────┬───────┴──────────────┴────────────┘        │
       │                                              │
       │ HTTP/HTTPS                                   │
       ▼                                              │
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
│  │  - /projects/                            │     │
│  │  - /buildings/                           │     │
│  │  - /assets/                              │     │
│  │  - ...                                   │     │
│  └──────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

### 认证流程

```
1. 用户登录
   ┌─> 输入用户名密码
   │
   ├─> 调用 POST /api/v1/auth/login
   │
   ├─> 接收 access_token 和 refresh_token
   │
   └─> 安全存储 Token（移动端：flutter_secure_storage）
                     （PC-UI：app.storage.user）

2. 访问 API
   ┌─> 从存储读取 Token
   │
   ├─> 添加到请求头 Authorization: Bearer {token}
   │
   ├─> 调用业务 API
   │
   ├─> 如果 401：
   │   ├─> 尝试用 refresh_token 刷新
   │   ├─> 如果刷新成功，重试原请求
   │   └─> 如果刷新失败，跳转登录页
   │
   └─> 返回数据

3. 用户登出
   ┌─> 清除本地 Token
   │
   └─> 跳转登录页
```

---

## 实施计划

### 阶段划分

| 阶段 | 内容 | 预计时间 | 优先级 |
|-----|------|---------|--------|
| **阶段 1** | 移动端认证整合 | 4 小时 | 🔴 高 |
| **阶段 2** | PC-UI 认证整合 | 3 小时 | 🔴 高 |
| **阶段 3** | 联调测试 | 2 小时 | 🟡 中 |
| **阶段 4** | 文档编写 | 1 小时 | 🟢 低 |
| **总计** | | **10 小时** | |

---

## 移动端整合

### 技术栈

- **框架**：Flutter
- **状态管理**：Provider / Riverpod
- **HTTP 客户端**：Dio
- **安全存储**：flutter_secure_storage
- **本地缓存**：shared_preferences

### 实施步骤

#### 步骤 1：添加依赖（5 分钟）

```yaml
# mobile/pubspec.yaml

dependencies:
  # 现有依赖...
  dio: ^5.3.0
  flutter_secure_storage: ^8.0.0
  shared_preferences: ^2.2.0
  provider: ^6.0.0
  json_annotation: ^4.8.0

dev_dependencies:
  json_serializable: ^6.7.0
  build_runner: ^2.4.0
```

安装依赖：
```bash
cd mobile
flutter pub get
```

#### 步骤 2：创建数据模型（30 分钟）

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
  final bool is_active;
  final bool is_superuser;

  User({
    required this.id,
    required this.username,
    required this.email,
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
flutter pub run build_runner build
```

#### 步骤 3：创建认证服务（1 小时）

**文件**：`mobile/lib/services/auth_service.dart`

```dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/auth.dart';

class AuthService {
  final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  static const String _tokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userKey = 'user';

  String? _accessToken;
  String? _refreshToken;
  User? _currentUser;

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

  /// 刷新 Token
  Future<bool> _refreshAccessToken() async {
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
}

// 全局单例
late AuthService authService;
```

#### 步骤 4：创建 Provider（30 分钟）

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
}
```

#### 步骤 5：创建登录页面（1 小时）

**文件**：`mobile/lib/screens/login_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final authProvider = context.read<AuthProvider>();

    final success = await authProvider.login(
      _usernameController.text,
      _passwordController.text,
    );

    if (success && mounted) {
      // 登录成功，导航到主页面
      Navigator.pushReplacementNamed(context, '/home');
    } else if (mounted) {
      // 显示错误
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(authProvider.errorMessage ?? '登录失败'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Consumer<AuthProvider>(
          builder: (context, authProvider, child) {
            if (authProvider.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }

            return Padding(
              padding: const EdgeInsets.all(24.0),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Logo 和标题
                    const Icon(
                      Icons.energy_savings_leaf,
                      size: 80,
                      color: Colors.green,
                    ),
                    const SizedBox(height: 24),
                    const Text(
                      'BDC-AI',
                      style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const Text(
                      '建筑节能管理平台',
                      style: TextStyle(fontSize: 16, color: Colors.grey),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 48),

                    // 用户名输入框
                    TextFormField(
                      controller: _usernameController,
                      decoration: const InputDecoration(
                        labelText: '用户名',
                        prefixIcon: Icon(Icons.person),
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return '请输入用户名';
                        }
                        return null;
                      },
                      autofillHints: const [AutofillHints.username],
                    ),
                    const SizedBox(height: 16),

                    // 密码输入框
                    TextFormField(
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      decoration: InputDecoration(
                        labelText: '密码',
                        prefixIcon: const Icon(Icons.lock),
                        suffixIcon: IconButton(
                          icon: Icon(_obscurePassword
                              ? Icons.visibility_off
                              : Icons.visibility),
                          onPressed: () {
                            setState(() {
                              _obscurePassword = !_obscurePassword;
                            });
                          },
                        ),
                        border: const OutlineInputBorder(),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return '请输入密码';
                        }
                        return null;
                      },
                      autofillHints: const [AutofillHints.password],
                    ),
                    const SizedBox(height: 24),

                    // 登录按钮
                    ElevatedButton(
                      onPressed: _handleLogin,
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: const Text(
                        '登录',
                        style: TextStyle(fontSize: 18),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
```

#### 步骤 6：更新主应用（30 分钟）

**文件**：`mobile/lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/auth_service.dart';
import 'providers/auth_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 初始化认证服务
  authService = AuthService(
    baseUrl: 'http://localhost:8000', // 开发环境
    // baseUrl: 'https://api.example.com', // 生产环境
  );

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider(authService),
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
    return const Scaffold(
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
- **UI 组件**：内置组件

### 实施步骤

#### 步骤 1：创建认证工具类（30 分钟）

**文件**：`pc_ui/auth/auth_manager.py`

```python
"""
PC-UI 认证管理器
"""
import requests
from typing import Optional
from nicegui import app


class AuthManager:
    """认证管理器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.user: Optional[dict] = None

        # 尝试从存储恢复会话
        self._restore_session()

    def _restore_session(self) -> bool:
        """从存储恢复会话"""
        if 'user' in app.storage.user:
            self.token = app.storage.user.get('token')
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
        app.storage.user['user'] = self.user

    def _clear_session(self):
        """清除会话"""
        self.token = None
        self.user = None
        if 'user' in app.storage.user:
            del app.storage.user['token']
            del app.storage.user['user']

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

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET 请求"""
        return self.session.get(f"{self.base_url}{endpoint}", **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST 请求"""
        return self.session.post(f"{self.base_url}{endpoint}", **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """PUT 请求"""
        return self.session.put(f"{self.base_url}{endpoint}", **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE 请求"""
        return self.session.delete(f"{self.base_url}{endpoint}", **kwargs)


# 全局实例
auth_manager = AuthManager()
```

#### 步骤 2：创建登录页面（1 小时）

**文件**：`pc_ui/pages/login.py`

```python
"""
登录页面
"""
from nicegui import ui, app
from ..auth.auth_manager import auth_manager


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
                placeholder='admin',
                validation=lambda x: True if x else '请输入用户名'
            ).props('outlined').classes('w-full mb-4')

            password = ui.input(
                '密码',
                placeholder='admin123',
                password=True,
                validation=lambda x: True if x else '请输入密码'
            ).props('outlined').classes('w-full mb-4')

            message = ui.label('').classes('text-red-600 mb-4')

            async def do_login():
                """执行登录"""
                message.text = ''
                username.value = username.value or 'admin'
                password.value = password.value or 'admin123'

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

            # 记住我选项
            # checkbox = ui.checkbox('记住我').classes('mt-4')


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

#### 步骤 3：创建主页面（1 小时）

**文件**：`pc_ui/pages/home.py`

```python
"""
主页面
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

                ui.button(
                    icon='logout',
                    on_click=lambda: (
                        auth_manager.logout(),
                        ui.notify('已登出', type='info'),
                        ui.navigate('/login')
                    )
                ).props('outline round')

    # 侧边栏
    with ui.left_drawer().classes('bg-white'):
        ui.label('菜单').classes('text-lg font-bold mb-4')

        ui.menu_item(
            '项目列表',
            icon='folder',
            on_click=lambda: load_projects()
        )

        ui.menu_item(
            '建筑管理',
            icon='apartment',
            on_click=lambda: ui.notify('开发中...')
        )

        ui.menu_item(
            '资产管理',
            icon='inventory_2',
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
                    response.raise_for_status()
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

#### 步骤 4：更新主应用（30 分钟）

**文件**：`pc_ui/main.py`

```python
"""
BDC-AI PC-UI 主应用
"""
from nicegui import ui
from auth.auth_manager import auth_manager
from pages.login import register_login_route
from pages.home import register_home_route


def create_app():
    """创建应用"""

    # 注册路由
    register_login_route()
    register_home_route()

    # 根路由重定向
    @ui.page('/')
    def index():
        """根路由"""
        if auth_manager.is_authenticated():
            return show_home_page()
        else:
            return ui.navigate('/login')

    # 启动应用
    ui.run(
        port=8080,
        title='BDC-AI 管理平台',
        dark=None,
        storage_secret='bdc-ai-secret-key-change-in-production'
    )


if __name__ == '__main__':
    create_app()
```

---

## 测试与验证

### 移动端测试清单

- [ ] 登录功能测试
  - [ ] 正确凭证登录成功
  - [ ] 错误凭证显示错误
  - [ ] Token 正确存储
- [ ] 自动 Token 刷新
  - [ ] 401 错误自动刷新
  - [ ] 刷新成功后重试请求
  - [ ] 刷新失败跳转登录页
- [ ] 登出功能
  - [ ] 清除本地 Token
  - [ ] 返回登录页
- [ ] API 调用
  - [ ] 自动添加认证头
  - [ ] 数据正确加载

### PC-UI 测试清单

- [ ] 登录功能
  - [ ] 正确凭证登录成功
  - [ ] 错误凭证显示错误
  - [ ] 会话正确保存
- [ ] 会话保持
  - [ ] 刷新页面保持登录
  - [ ] 关闭浏览器重开保持登录
- [ ] 登出功能
  - [ ] 清除会话
  - [ ] 跳转登录页
- [ ] API 调用
  - [ ] 自动添加认证头
  - [ ] 401 错误处理

### 联调测试

- [ ] 移动端和 PC-UI 同时登录同一账号
- [ ] Token 刷新不影响其他端
- [ ] 登出后其他端仍可用

---

## 部署上线

### 移动端部署

```bash
# 1. 更新 API 地址
# mobile/lib/main.dart
authService = AuthService(
  baseUrl: 'https://api.example.com', // 生产环境
);

# 2. 构建发布版本
flutter build apk --release
flutter build ios --release

# 3. 签名和发布
# Android: 上传 .apk 到 Google Play
# iOS: 上传 .ipa 到 App Store
```

### PC-UI 部署

```bash
# 1. 配置生产环境 URL
# pc_ui/auth/auth_manager.py
auth_manager = AuthManager(base_url="https://api.example.com")

# 2. 启动服务
python pc_ui/main.py

# 3. 使用 systemd 管理进程
# 4. 配置 Nginx 反向代理
# 5. 启用 HTTPS
```

---

## 时间估算

| 阶段 | 任务 | 预计时间 | 负责人 |
|-----|------|---------|--------|
| **阶段 1：移动端** | | | |
| 1.1 | 添加依赖 | 5 分钟 | 移动端开发 |
| 1.2 | 创建数据模型 | 30 分钟 | 移动端开发 |
| 1.3 | 创建认证服务 | 1 小时 | 移动端开发 |
| 1.4 | 创建 Provider | 30 分钟 | 移动端开发 |
| 1.5 | 创建登录页面 | 1 小时 | 移动端开发 |
| 1.6 | 更新主应用 | 30 分钟 | 移动端开发 |
| **小计** | | **4 小时** | |
| **阶段 2：PC-UI** | | | |
| 2.1 | 创建认证管理器 | 30 分钟 | 后端开发 |
| 2.2 | 创建登录页面 | 1 小时 | 后端开发 |
| 2.3 | 创建主页面 | 1 小时 | 后端开发 |
| 2.4 | 更新主应用 | 30 分钟 | 后端开发 |
| **小计** | | **3 小时** | |
| **阶段 3：测试** | | | |
| 3.1 | 移动端测试 | 1 小时 | QA |
| 3.2 | PC-UI 测试 | 1 小时 | QA |
| **小计** | | **2 小时** | |
| **阶段 4：文档** | | | |
| 4.1 | 编写用户文档 | 1 小时 | 技术写作 |
| **小计** | | **1 小时** | |
| **总计** | | **10 小时** | |

---

## 附录

### A. 配置文件

**移动端配置**：`mobile/lib/config.dart`

```dart
class Config {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  static const bool enableDebug = bool.fromEnvironment('DEBUG', defaultValue: true);
}
```

**PC-UI 配置**：`pc_ui/config.py`

```python
import os

class Config:
    API_BASE_URL = os.getenv(
        'BDC_API_URL',
        'http://localhost:8000'
    )
```

### B. 错误处理

**常见错误及处理**：

| 错误 | 原因 | 处理方式 |
|-----|------|---------|
| 401 Unauthorized | Token 过期 | 自动刷新或跳转登录 |
| 403 Forbidden | 权限不足 | 提示用户权限不足 |
| 500 Server Error | 服务器错误 | 显示友好错误信息 |
| Network Error | 网络问题 | 提示检查网络连接 |

---

**文档维护**：BDC-AI 开发团队
**最后更新**：2026-01-25
**版本**：v1.0
