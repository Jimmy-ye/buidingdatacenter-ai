/// BDC-AI 认证状态管理 Provider
///
/// 使用 Provider 模式管理应用认证状态

import 'package:flutter/foundation.dart';

import '../models/auth.dart';
import '../services/auth_service.dart';

/// 认证状态管理
class AuthProvider extends ChangeNotifier {
  /// 认证服务
  final AuthService _authService = AuthService();

  /// 当前用户
  UserInfo? get user => _authService.currentUser;

  /// 是否已登录
  bool get isAuthenticated => _authService.isAuthenticated;

  /// 认证状态
  AuthStatus _authStatus = AuthStatus.unknown;

  AuthStatus get authStatus => _authStatus;

  /// 加载状态
  bool _isLoading = false;

  bool get isLoading => _isLoading;

  /// 错误信息
  String? _errorMessage;

  String? get errorMessage => _errorMessage;

  /// 构造函数
  AuthProvider() {
    // 监听认证状态变化
    _authService.authStatusStream.listen((status) {
      _authStatus = status;
      notifyListeners();
    });
  }

  /// 初始化（应用启动时调用）
  Future<void> initialize() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      await _authService.initialize();
      _authStatus = _authService.isAuthenticated
          ? AuthStatus.authenticated
          : AuthStatus.unauthenticated;
    } catch (e) {
      _errorMessage = '初始化失败: $e';
      _authStatus = AuthStatus.unauthenticated;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 用户登录
  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final user = await _authService.login(username, password);
      _authStatus = AuthStatus.authenticated;
      _errorMessage = null;
      notifyListeners();
      return true;
    } on InvalidCredentialsException catch (e) {
      _errorMessage = e.message;
      _authStatus = AuthStatus.unauthenticated;
      notifyListeners();
      return false;
    } on NetworkException catch (e) {
      _errorMessage = '网络连接失败，请检查网络设置';
      _authStatus = AuthStatus.unauthenticated;
      notifyListeners();
      return false;
    } catch (e) {
      _errorMessage = '登录失败，请稍后重试';
      _authStatus = AuthStatus.unauthenticated;
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 用户登出
  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _authService.logout();
      _authStatus = AuthStatus.unauthenticated;
      _errorMessage = null;
    } catch (e) {
      _errorMessage = '登出失败: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 刷新 Token
  Future<bool> refreshToken() async {
    try {
      return await _authService.refreshToken();
    } catch (e) {
      _errorMessage = 'Token 刷新失败';
      notifyListeners();
      return false;
    }
  }

  /// 获取当前用户信息
  Future<UserInfo?> getCurrentUser() async {
    try {
      return await _authService.getCurrentUser();
    } catch (e) {
      _errorMessage = '获取用户信息失败';
      notifyListeners();
      return null;
    }
  }

  /// 权限检查方法
  bool hasPermission(String permissionCode) {
    return _authService.hasPermission(permissionCode);
  }

  bool hasAnyPermission(List<String> permissionCodes) {
    return _authService.hasAnyPermission(permissionCodes);
  }

  bool hasRole(String roleName) {
    return _authService.hasRole(roleName);
  }

  bool get isAdmin => _authService.isAdmin;

  /// 清除错误信息
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _authService.dispose();
    super.dispose();
  }
}
