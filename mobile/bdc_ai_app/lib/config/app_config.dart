/// BDC-AI 移动端应用配置
///
/// 集中管理应用配置，支持环境变量

class AppConfig {
  /// API 基础 URL
  ///
  /// 优先级：环境变量 > 编译时常量 > 默认值
  static String get apiBaseUrl {
    // 从编译时常量读取（通过 --dart-define 设置）
    const apiBaseUrl = String.fromEnvironment('API_BASE_URL',
      defaultValue: 'http://127.0.0.1:8000'
    );

    return apiBaseUrl;
  }

  /// 完整的 API 基础地址（包含 /api/v1）
  static String get apiBaseAddress {
    return '$apiBaseUrl/api/v1';
  }

  /// 是否为调试模式
  static const bool isDebugMode = bool.fromEnvironment('DEBUG_MODE', defaultValue: true);

  /// 应用版本
  static const String appVersion = '1.0.0';

  /// 应用名称
  static const String appName = 'BDC-AI 移动端';

  /// Token 默认过期时间（秒）
  /// 后端设置为 15 分钟（900秒）
  static const int defaultTokenExpiresIn = 900;

  /// Refresh Token 默认过期时间（秒）
  /// 后端设置为 7 天（604800秒）
  static const int defaultRefreshTokenExpiresIn = 604800;

  /// Token 自动刷新提前时间（秒）
  /// 提前 5 分钟刷新
  static const int tokenRefreshBuffer = 300;
}
