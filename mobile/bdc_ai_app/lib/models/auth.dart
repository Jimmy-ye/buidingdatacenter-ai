/// BDC-AI 移动端认证模型
///
/// 与后端 API (/api/v1/auth/*) 对应的数据模型

/// Token 响应模型
class TokenResponse {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final UserInfo? user; // 可选字段：后端登录接口不返回用户信息

  TokenResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    this.user,
  });

  factory TokenResponse.fromJson(Map<String, dynamic> json) {
    return TokenResponse(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: json['token_type'] as String? ?? 'bearer',
      user: json.containsKey('user') && json['user'] != null
          ? UserInfo.fromJson(json['user'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    final json = {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'token_type': tokenType,
    };
    if (user != null) {
      json['user'] = user!.toJson();
    }
    return json;
  }
}

/// 用户信息模型
class UserInfo {
  final int id;
  final String username;
  final String? email;
  final bool isSuperuser;
  final List<RoleInfo> roles;

  UserInfo({
    required this.id,
    required this.username,
    this.email,
    required this.isSuperuser,
    required this.roles,
  });

  factory UserInfo.fromJson(Map<String, dynamic> json) {
    return UserInfo(
      id: json['id'] as int,
      username: json['username'] as String,
      email: json['email'] as String?,
      isSuperuser: json['is_superuser'] as bool? ?? false,
      roles: (json['roles'] as List<dynamic>?)
              ?.map((role) => RoleInfo.fromJson(role as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'is_superuser': isSuperuser,
      'roles': roles.map((role) => role.toJson()).toList(),
    };
  }

  /// 获取显示名称
  String get displayName {
    return username;
  }

  /// 获取角色名称列表
  List<String> get roleNames {
    return roles.map((role) => role.displayName).toList();
  }

  /// 获取所有权限代码
  List<String> get permissions {
    final Set<String> perms = {};
    for (final role in roles) {
      perms.addAll(role.permissions);
    }
    return perms.toList();
  }

  /// 检查是否有指定权限
  bool hasPermission(String permissionCode) {
    if (isSuperuser) return true;
    return permissions.contains(permissionCode);
  }

  /// 检查是否有任一权限
  bool hasAnyPermission(List<String> permissionCodes) {
    if (isSuperuser) return true;
    return permissionCodes.any((code) => permissions.contains(code));
  }

  /// 检查是否有所有权限
  bool hasAllPermissions(List<String> permissionCodes) {
    if (isSuperuser) return true;
    return permissionCodes.every((code) => permissions.contains(code));
  }

  /// 检查是否有指定角色
  bool hasRole(String roleName) {
    if (isSuperuser) return true;
    return roles.any((role) => role.name == roleName);
  }

  /// 检查是否是管理员
  bool get isAdmin {
    return isSuperuser || hasRole('admin');
  }
}

/// 角色信息模型
class RoleInfo {
  final int id;
  final String name;
  final String displayName;
  final int level;
  final List<String> permissions;

  RoleInfo({
    required this.id,
    required this.name,
    required this.displayName,
    required this.level,
    required this.permissions,
  });

  factory RoleInfo.fromJson(Map<String, dynamic> json) {
    return RoleInfo(
      id: json['id'] as int,
      name: json['name'] as String,
      displayName: json['display_name'] as String,
      level: json['level'] as int,
      permissions: (json['permissions'] as List<dynamic>?)
              ?.map((p) => p as String)
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'display_name': displayName,
      'level': level,
      'permissions': permissions,
    };
  }
}

/// 登录请求模型
class LoginRequest {
  final String username;
  final String password;

  LoginRequest({
    required this.username,
    required this.password,
  });

  Map<String, dynamic> toJson() {
    return {
      'username': username,
      'password': password,
    };
  }
}

/// 认证状态
enum AuthStatus {
  unknown,        // 未知状态（初始化中）
  authenticated,  // 已认证
  unauthenticated,// 未认证
  tokenExpired,   // Token过期
}

/// 认证异常
class AuthException implements Exception {
  final String message;
  final int? statusCode;

  AuthException(this.message, {this.statusCode});

  @override
  String toString() {
    return 'AuthException: $message (statusCode: $statusCode)';
  }
}

/// Token 过期异常
class TokenExpiredException extends AuthException {
  TokenExpiredException([String message = 'Token has expired'])
      : super(message, statusCode: 401);
}

/// 无效凭证异常
class InvalidCredentialsException extends AuthException {
  InvalidCredentialsException([String message = 'Invalid credentials'])
      : super(message, statusCode: 401);
}

/// 网络异常
class NetworkException extends AuthException {
  NetworkException([String message = 'Network error'])
      : super(message, statusCode: null);
}
