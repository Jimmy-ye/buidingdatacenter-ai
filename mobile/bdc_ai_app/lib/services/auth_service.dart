/// BDC-AI 移动端认证服务
///
/// 负责用户登录、Token 管理、自动刷新、权限检查等功能

import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/app_config.dart';
import '../models/auth.dart';

/// 认证服务类（单例）
class AuthService {
  /// Dio 实例
  late Dio _dio;

  /// 安全存储（用于存储 Token）
  final _secureStorage = const FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
  );

  /// 共享存储（用于存储用户信息）
  SharedPreferences? _prefs;

  /// Token 过期定时器
  Timer? _tokenExpiryTimer;

  /// Token 刷新锁（防止并发刷新）
  bool _isRefreshing = false;

  /// 当前用户信息
  UserInfo? _currentUser;

  /// 认证状态流控制器
  final _authStatusController = StreamController<AuthStatus>.broadcast();

  /// 认证状态流
  Stream<AuthStatus> get authStatusStream => _authStatusController.stream;

  /// 当前用户
  UserInfo? get currentUser => _currentUser;

  /// 是否已登录
  bool get isAuthenticated => _currentUser != null;

  /// 当前 Token
  String? get currentToken => _currentAccessToken;
  String? _currentAccessToken;

  /// 认证状态
  AuthStatus _authStatus = AuthStatus.unknown;

  /// 单例模式
  static final AuthService _instance = AuthService._internal();

  factory AuthService() {
    return _instance;
  }

  AuthService._internal() {
    _initDio();
  }

  /// 初始化 Dio
  void _initDio() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiBaseAddress,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      sendTimeout: const Duration(seconds: 10),
      headers: {
        'Content-Type': 'application/json',
      },
    ));

    // 添加拦截器
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // 自动添加 Token
        final token = await _secureStorage.read(key: 'access_token');
        if (token != null) {
          _currentAccessToken = token;
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        // 处理 401 错误
        if (error.response?.statusCode == 401) {
          // 检查是否有 refresh_token
          final refreshToken = await _secureStorage.read(key: 'refresh_token');

          if (refreshToken != null && !_isRefreshing) {
            try {
              // 尝试刷新 Token
              final success = await _refreshTokenInternal();
              if (success) {
                // Token 刷新成功，重试原请求
                final newToken = await _secureStorage.read(key: 'access_token');
                error.requestOptions.headers['Authorization'] = 'Bearer $newToken';

                // 重试请求
                final cloneReq = await _dio.fetch(error.requestOptions);
                return handler.resolve(cloneReq);
              } else {
                // Token 刷新失败，登出
                await _clearAuthData();
                _authStatusController.add(AuthStatus.tokenExpired);
              }
            } catch (e) {
              // Token 刷新失败，登出
              await _clearAuthData();
              _authStatusController.add(AuthStatus.tokenExpired);
            }
          } else {
            // 没有 refresh_token，直接登出
            await _clearAuthData();
            _authStatusController.add(AuthStatus.unauthenticated);
          }
        }
        return handler.next(error);
      },
    ));
  }

  /// 初始化（应用启动时调用）
  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();

    // 尝试从缓存恢复用户信息
    final userJson = _prefs?.getString('current_user');
    if (userJson != null) {
      try {
        // TODO: 反序列化用户信息
        // _currentUser = UserInfo.fromJson(jsonDecode(userJson));
        _authStatus = AuthStatus.authenticated;
        _authStatusController.add(AuthStatus.authenticated);

        // 检查 Token 是否即将过期
        final expiryStr = _prefs?.getString('token_expiry');
        if (expiryStr != null) {
          final expiry = DateTime.parse(expiryStr);
          final now = DateTime.now();
          final timeUntilExpiry = expiry.difference(now);

          if (timeUntilExpiry.inMinutes < 5 && timeUntilExpiry.inSeconds > 0) {
            // Token 即将过期，自动刷新
            await refreshToken();
          } else if (timeUntilExpiry.inSeconds <= 0) {
            // Token 已过期
            await _clearAuthData();
            _authStatusController.add(AuthStatus.tokenExpired);
          } else {
            // 设置定时器，在 Token 过期前 5 分钟刷新
            _scheduleTokenRefresh(timeUntilExpiry - const Duration(seconds: AppConfig.tokenRefreshBuffer));
          }
        }
      } catch (e) {
        // 缓存数据无效，清除
        await _clearAuthData();
      }
    } else {
      _authStatus = AuthStatus.unauthenticated;
      _authStatusController.add(AuthStatus.unauthenticated);
    }
  }

  /// 用户登录
  Future<UserInfo> login(String username, String password) async {
    try {
      final response = await _dio.post(
        '/auth/login',
        data: LoginRequest(username: username, password: password).toJson(),
      );

      final tokenResponse = TokenResponse.fromJson(response.data);

      // 存储 Token
      await _secureStorage.write(key: 'access_token', value: tokenResponse.accessToken);
      await _secureStorage.write(key: 'refresh_token', value: tokenResponse.refreshToken);

      // 存储 Token 过期时间（15分钟）
      final expiryTime = DateTime.now().add(const Duration(seconds: AppConfig.defaultTokenExpiresIn));
      await _prefs?.setString('token_expiry', expiryTime.toIso8601String());

      // 更新当前用户
      _currentUser = tokenResponse.user;

      // 缓存用户信息
      // await _prefs?.setString('current_user', jsonEncode(tokenResponse.user.toJson()));

      // 更新认证状态
      _authStatus = AuthStatus.authenticated;
      _authStatusController.add(AuthStatus.authenticated);

      // 设置 Token 自动刷新定时器
      final timeUntilRefresh = AppConfig.defaultTokenExpiresIn - AppConfig.tokenRefreshBuffer;
      if (timeUntilRefresh > 0) {
        _scheduleTokenRefresh(Duration(seconds: timeUntilRefresh));
      }

      return _currentUser!;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw InvalidCredentialsException('用户名或密码错误');
      }
      throw NetworkException('网络请求失败: ${e.message}');
    }
  }

  /// 用户登出
  Future<void> logout() async {
    // 取消定时器
    _tokenExpiryTimer?.cancel();
    _tokenExpiryTimer = null;

    // 清除存储的数据
    await _clearAuthData();

    // 清除当前用户
    _currentUser = null;
    _authStatus = AuthStatus.unauthenticated;
    _authStatusController.add(AuthStatus.unauthenticated);
  }

  /// 清除认证数据
  Future<void> _clearAuthData() async {
    await _secureStorage.delete(key: 'access_token');
    await _secureStorage.delete(key: 'refresh_token');
    await _prefs?.remove('current_user');
    await _prefs?.remove('token_expiry');
    _currentAccessToken = null;
  }

  /// 刷新 Token（公开方法）
  Future<bool> refreshToken() async {
    return _refreshTokenInternal();
  }

  /// 内部刷新 Token 实现
  Future<bool> _refreshTokenInternal() async {
    // 防止并发刷新
    if (_isRefreshing) {
      return false;
    }

    _isRefreshing = true;

    try {
      final refreshToken = await _secureStorage.read(key: 'refresh_token');
      if (refreshToken == null) {
        return false;
      }

      final response = await _dio.post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      final tokenResponse = TokenResponse.fromJson(response.data);

      // 更新存储的 Token
      await _secureStorage.write(key: 'access_token', value: tokenResponse.accessToken);

      // 如果返回了新的 refresh_token，也更新
      if (tokenResponse.refreshToken.isNotEmpty) {
        await _secureStorage.write(key: 'refresh_token', value: tokenResponse.refreshToken);
      }

      // 更新过期时间
      final expiryTime = DateTime.now().add(const Duration(seconds: AppConfig.defaultTokenExpiresIn));
      await _prefs?.setString('token_expiry', expiryTime.toIso8601String());

      // 重新设置定时器
      final timeUntilRefresh = AppConfig.defaultTokenExpiresIn - AppConfig.tokenRefreshBuffer;
      if (timeUntilRefresh > 0) {
        _scheduleTokenRefresh(Duration(seconds: timeUntilRefresh));
      }

      print('[AuthService] Token 刷新成功');
      return true;
    } catch (e) {
      print('[AuthService] Token 刷新失败: $e');
      return false;
    } finally {
      _isRefreshing = false;
    }
  }

  /// 获取当前用户信息
  Future<UserInfo> getCurrentUser() async {
    if (_currentUser != null) {
      return _currentUser!;
    }

    try {
      final response = await _dio.get('/auth/me');
      final user = UserInfo.fromJson(response.data);

      _currentUser = user;

      // 更新缓存
      // await _prefs?.setString('current_user', jsonEncode(user.toJson()));

      return user;
    } catch (e) {
      throw NetworkException('获取用户信息失败');
    }
  }

  /// 安排 Token 刷新定时器
  void _scheduleTokenRefresh(Duration duration) {
    _tokenExpiryTimer?.cancel();
    _tokenExpiryTimer = Timer(duration, () async {
      print('[AuthService] 定时刷新 Token');
      await _refreshTokenInternal();
    });
  }

  /// 释放资源
  void dispose() {
    _tokenExpiryTimer?.cancel();
    _authStatusController.close();
  }

  /// 检查权限（便捷方法）
  bool hasPermission(String permissionCode) {
    return _currentUser?.hasPermission(permissionCode) ?? false;
  }

  bool hasAnyPermission(List<String> permissionCodes) {
    return _currentUser?.hasAnyPermission(permissionCodes) ?? false;
  }

  bool hasRole(String roleName) {
    return _currentUser?.hasRole(roleName) ?? false;
  }

  bool get isAdmin => _currentUser?.isAdmin ?? false;
}
