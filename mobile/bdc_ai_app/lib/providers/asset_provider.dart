import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import '../models/asset.dart';
import '../services/asset_service.dart';
import '../services/api_service.dart';

/// 视图类型枚举
enum AssetViewType {
  /// 设备级视图
  device,

  /// 系统级视图 ⭐
  system,
}

/// 资产列表状态管理
///
/// 管理资产列表的加载状态和数据（支持设备级和系统级视图）
class AssetProvider extends ChangeNotifier {
  final AssetService _service = AssetService();

  /// 资产列表
  List<Asset> _assets = [];

  /// 后端返回的完整资产列表（按时间倒序），用于本地分页
  List<Asset> _allAssets = [];

  /// 是否正在加载
  bool _isLoading = false;

  /// 是否正在加载更多
  bool _isLoadingMore = false;

  /// 错误消息
  String? _errorMessage;

  /// 总资产数量
  int _totalCount = 0;

  /// 当前视图类型
  AssetViewType? _currentViewType;

  /// 当前目标 ID（device_id 或 system_id）
  String? _currentTargetId;

  /// 当前页码（用于分页）
  int _currentPage = 0;

  /// 每页数量
  final int _pageSize = 5;

  /// 是否还有更多数据
  bool _hasMore = true;

  /// 获取资产列表
  List<Asset> get assets => _assets;

  /// 是否正在加载
  bool get isLoading => _isLoading;

  /// 是否正在加载更多
  bool get isLoadingMore => _isLoadingMore;

  /// 是否有错误
  bool get hasError => _errorMessage != null;

  /// 错误消息
  String? get errorMessage => _errorMessage;

  /// 是否为空列表
  bool get isEmpty => _assets.isEmpty;

  /// 总资产数量
  int get totalCount => _totalCount;

  /// 是否还有更多数据
  bool get hasMore => _hasMore;

  /// 当前视图类型
  AssetViewType? get currentViewType => _currentViewType;

  /// 加载资产（设备视图或系统视图）⭐
  ///
  /// 参数:
  /// - [targetId] 目标 ID（device_id 或 system_id）
  /// - [viewType] 视图类型（设备级或系统级）
  /// - [limit] 返回数量，默认 5
  /// - [offset] 偏移量，默认 0
  Future<void> loadAssets({
    required String targetId,
    required AssetViewType viewType,
    int limit = 5,
    int offset = 0,
  }) async {
    _setLoading(true);
    _clearError();

    // 更新当前视图状态
    _currentViewType = viewType;
    _currentTargetId = targetId;
    _currentPage = offset ~/ _pageSize;

    try {
      List<Asset> result;

      if (viewType == AssetViewType.device) {
        // 设备级视图（后端当前不支持 limit/offset，始终返回完整列表）
        debugPrint('加载设备资产: device_id=$targetId');
        result = await _service.getDeviceAssets(
          targetId,
          limit: limit,
          offset: offset,
        );
      } else {
        // 系统级视图 ⭐（同样视为返回完整列表）
        debugPrint('加载系统资产: system_id=$targetId');
        result = await _service.getSystemAssets(
          targetId,
          limit: limit,
          offset: offset,
        );
      }

      // 记录完整列表，按“只显示最近 limit 条，查看更多再展开”的策略本地分页
      _allAssets = result;

      // 默认只显示最近 [limit] 条资产
      final initialCount = min(limit, _allAssets.length);
      _assets = _allAssets.take(initialCount).toList();

      _totalCount = _allAssets.length;
      _hasMore = _assets.length < _allAssets.length;
      _currentPage = 0;

      debugPrint('成功加载 ${_assets.length} 个资产（共 $_totalCount 个）');
    } catch (e) {
      if (e is ApiException && (e.statusCode == 401 || e.statusCode == 403)) {
        // 认证失败交由全局认证逻辑处理，这里不再展示错误页
        debugPrint('资产列表请求认证失败: $e');
        return;
      }
      _setError('加载资产列表失败: $e');
      debugPrint('错误: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// 加载更多资产
  Future<void> loadMoreAssets() async {
    if (_isLoadingMore || !_hasMore || _currentTargetId == null) {
      debugPrint('无法加载更多：isLoadingMore=$isLoadingMore, hasMore=$_hasMore');
      return;
    }

    _setLoadingMore(true);
    _clearError();

    try {
      // 本地分页：在 _allAssets 基础上，每次多展示一页数据
      final nextPage = _currentPage + 1;
      final nextEnd = min(_allAssets.length, (nextPage + 1) * _pageSize);

      // 如果已经全部展示，则不再增加
      if (nextEnd <= _assets.length) {
        _hasMore = false;
        debugPrint('没有更多资产可以加载');
      } else {
        _assets = _allAssets.sublist(0, nextEnd);
        _currentPage = nextPage;
        _hasMore = _assets.length < _allAssets.length;
        debugPrint('成功加载更多资产，当前共 ${_assets.length} 个');
      }
    } catch (e) {
      _setError('加载更多失败: $e');
      debugPrint('错误: $e');
    } finally {
      _setLoadingMore(false);
    }
  }

  /// 上传图片（支持设备级或系统级）⭐
  ///
  /// 参数:
  /// - [projectId] 项目 UUID（必填）
  /// - [deviceId] 设备 UUID（可选）
  /// - [systemId] 系统 UUID（可选）⭐
  /// - [filePath] 图片文件路径
  /// - [note] 工程师备注
  /// - [contentRole] 资产类型（scene_issue/nameplate/meter）
  /// - [autoRoute] 是否自动解析⭐
  ///
  /// 返回上传后的资产对象
  Future<Asset> uploadImage({
    required String projectId,
    String? deviceId,
    String? systemId,
    required String filePath,
    String? note,
    String? contentRole,
    bool autoRoute = false, // ⭐ 添加自动解析参数
  }) async {
    try {
      debugPrint('上传图片: projectId=$projectId, '
          'deviceId=$deviceId, systemId=$systemId, '
          'contentRole=$contentRole, autoRoute=$autoRoute');

      final asset = await _service.uploadImage(
        projectId: projectId,
        deviceId: deviceId,
        systemId: systemId,
        filePath: filePath,
        note: note,
        contentRole: contentRole,
        autoRoute: autoRoute, // ⭐ 传递自动解析选项
      );

      // 上传成功后，刷新列表
      if (_currentTargetId != null && _currentViewType != null) {
        await refreshAssets();
      }

      debugPrint('上传成功: ${asset.id}');
      return asset;
    } catch (e) {
      debugPrint('上传失败: $e');
      rethrow;
    }
  }

  /// 刷新资产列表
  Future<void> refreshAssets() async {
    if (_currentTargetId == null || _currentViewType == null) {
      debugPrint('无法刷新：未选择目标');
      return;
    }

    debugPrint('刷新资产列表');
    await loadAssets(
      targetId: _currentTargetId!,
      viewType: _currentViewType!,
      limit: _pageSize,
      offset: 0,
    );
  }

  /// 获取资产详情
  Future<Asset> getAssetDetail(String assetId) async {
    try {
      return await _service.getAssetDetail(assetId);
    } catch (e) {
      debugPrint('获取资产详情失败: $e');
      rethrow;
    }
  }

  /// 轮询等待 LLM 结果就绪
  Future<Asset?> waitForLlmResult(
    String assetId, {
    int maxAttempts = 6,
    Duration interval = const Duration(seconds: 5),
  }) async {
    for (var i = 0; i < maxAttempts; i++) {
      try {
        final detail = await getAssetDetail(assetId);
        if (detail.llmSummary != null && detail.llmSummary!.isNotEmpty) {
          return detail;
        }
      } catch (e) {
        debugPrint('轮询 LLM 结果失败: $e');
      }

      if (i < maxAttempts - 1) {
        await Future.delayed(interval);
      }
    }

    return null;
  }

  /// 删除资产⭐
  ///
  /// 参数:
  /// - [asset] 要删除的资产
  ///
  /// 注意：只能删除移动端上传的资产（source='mobile'）
  Future<void> deleteAsset(Asset asset) async {
    try {
      // 验证只能删除移动端上传的资产
      if (asset.source != 'mobile') {
        throw Exception('只能删除移动端上传的资产');
      }

      await _service.deleteAsset(asset.id);

      // 从列表中移除
      _assets.removeWhere((a) => a.id == asset.id);
      _allAssets.removeWhere((a) => a.id == asset.id);
      _totalCount--;

      notifyListeners();
      debugPrint('删除资产成功: ${asset.id}');
    } catch (e) {
      debugPrint('删除资产失败: $e');
      rethrow;
    }
  }

  /// 批量删除资产⭐
  ///
  /// 参数:
  /// - [assets] 要删除的资产列表
  ///
  /// 返回：删除结果
  Future<Map<String, dynamic>> deleteAssets(List<Asset> assets) async {
    try {
      // 过滤出移动端上传的资产
      final mobileAssets = assets.where((a) => a.source == 'mobile').toList();

      if (mobileAssets.length != assets.length) {
        debugPrint('警告：部分资产不是移动端上传，将被跳过');
      }

      final assetIds = mobileAssets.map((a) => a.id).toList();
      final result = await _service.deleteAssets(assetIds);

      // 从列表中移除已删除的资产
      final deletedIds = assetIds.toSet();
      _assets.removeWhere((a) => deletedIds.contains(a.id));
      _allAssets.removeWhere((a) => deletedIds.contains(a.id));
      _totalCount -= result['successCount'] as int;

      notifyListeners();
      return result;
    } catch (e) {
      debugPrint('批量删除资产失败: $e');
      rethrow;
    }
  }

  /// 清空资产列表
  void clearAssets() {
    _assets.clear();
    _allAssets.clear();
    _totalCount = 0;
    _currentPage = 0;
    _hasMore = true;
    _currentViewType = null;
    _currentTargetId = null;
    notifyListeners();
    debugPrint('清空资产列表');
  }

  /// 设置加载状态
  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }

  /// 设置加载更多状态
  void _setLoadingMore(bool value) {
    _isLoadingMore = value;
    notifyListeners();
  }

  /// 设置错误消息
  void _setError(String message) {
    _errorMessage = message;
    notifyListeners();
  }

  /// 清除错误消息
  void _clearError() {
    _errorMessage = null;
  }

  @override
  void dispose() {
    _assets.clear();
    super.dispose();
  }
}
