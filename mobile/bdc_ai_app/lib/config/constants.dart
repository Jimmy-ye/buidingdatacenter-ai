import 'app_config.dart' as app_config;

/// 应用配置常量
class AppConfig {
  /// API 基础 URL（从 app_config 读取）
  static String get baseUrl => app_config.AppConfig.apiBaseUrl;

  /// API 超时时间（毫秒）
  static const int apiTimeout = 30000;

  /// 资产列表默认加载数量
  static const int defaultAssetLimit = 5;

  /// 离线缓存时长（小时）
  static const int cacheDurationHours = 24;
}

/// API 端点路径
class ApiEndpoints {
  /// 项目列表
  static const String projects = '/api/v1/projects/';

  /// 项目详情
  static String projectDetail(String id) => '/api/v1/projects/$id';

  /// 工程结构树
  static String structureTree(String id) => '/api/v1/projects/$id/structure_tree';

  /// 资产列表（支持过滤）
  static const String assets = '/api/v1/assets/';

  /// 设备资产列表（设备视图）
  static String deviceAssets(String deviceId) => '/api/v1/assets/?device_id=$deviceId';

  /// 系统资产列表（系统视图）
  static String systemAssets(String systemId) => '/api/v1/assets/?system_id=$systemId';

  /// 上传图片（支持设备级或系统级）
  static const String uploadImage = '/api/v1/assets/upload_image_with_note';

  /// 健康检查
  static const String health = '/api/v1/health/';

  /// 创建设备
  static String createDevice(String systemId) => '/api/v1/systems/$systemId/devices';
}
