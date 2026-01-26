import 'package:flutter/foundation.dart';
import '../models/structure.dart';
import '../services/project_service.dart';

/// 工程结构状态管理
///
/// 管理工程结构树的加载状态、展开/折叠状态
///
/// **正确的层级关系**：
/// - Building → System → Device（主树）
/// - Building → Zone（与 System 同级，位置属性）
class StructureProvider extends ChangeNotifier {
  final ProjectService _service = ProjectService();

  /// 楼栋列表（工程结构树）
  List<Building> _buildings = [];

  /// 是否正在加载
  bool _isLoading = false;

  /// 错误消息
  String? _errorMessage;

  /// 展开的楼栋 ID 集合
  final Set<String> _expandedBuildings = {};

  /// 展开的系统 ID 集合
  final Set<String> _expandedSystems = {};

  /// 获取楼栋列表
  List<Building> get buildings => _buildings;

  /// 是否正在加载
  bool get isLoading => _isLoading;

  /// 是否有错误
  bool get hasError => _errorMessage != null;

  /// 错误消息
  String? get errorMessage => _errorMessage;

  /// 是否为空列表
  bool get isEmpty => _buildings.isEmpty;

  /// 加载工程结构树
  ///
  /// 参数:
  /// - [projectId] 项目 UUID
  Future<void> loadStructureTree(String projectId) async {
    _setLoading(true);
    _clearError();

    try {
      _buildings = await _service.getStructureTree(projectId);
      debugPrint('成功加载工程结构: ${_buildings.length} 个楼栋');
    } catch (e) {
      _setError('加载工程结构失败: $e');
      debugPrint('错误: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// 刷新工程结构树
  Future<void> refreshStructureTree(String projectId) async {
    debugPrint('刷新工程结构树');
    await loadStructureTree(projectId);
  }

  /// 切换楼栋展开/折叠状态
  void toggleBuilding(String buildingId) {
    if (_expandedBuildings.contains(buildingId)) {
      _expandedBuildings.remove(buildingId);
      debugPrint('折叠楼栋: $buildingId');
    } else {
      _expandedBuildings.add(buildingId);
      debugPrint('展开楼栋: $buildingId');
    }
    notifyListeners();
  }

  /// 切换系统展开/折叠状态 ⭐
  void toggleSystem(String systemId) {
    if (_expandedSystems.contains(systemId)) {
      _expandedSystems.remove(systemId);
      debugPrint('折叠系统: $systemId');
    } else {
      _expandedSystems.add(systemId);
      debugPrint('展开系统: $systemId');
    }
    notifyListeners();
  }

  /// 检查楼栋是否展开
  bool isBuildingExpanded(String buildingId) {
    return _expandedBuildings.contains(buildingId);
  }

  /// 检查系统是否展开 ⭐
  bool isSystemExpanded(String systemId) {
    return _expandedSystems.contains(systemId);
  }

  void expandSystem(String systemId) {
    _expandedSystems.add(systemId);
    debugPrint('展开系统: $systemId');
    notifyListeners();
  }

  /// 展开所有节点
  void expandAll() {
    for (var building in _buildings) {
      _expandedBuildings.add(building.id);
      for (var system in building.systems) {
        _expandedSystems.add(system.id);
      }
    }
    notifyListeners();
    debugPrint('展开所有节点');
  }

  /// 折叠所有节点
  void collapseAll() {
    _expandedBuildings.clear();
    _expandedSystems.clear();
    notifyListeners();
    debugPrint('折叠所有节点');
  }

  /// 设置加载状态
  void _setLoading(bool value) {
    _isLoading = value;
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

  /// 创建设备
  ///
  /// 参数:
  /// - [systemId] 系统 UUID
  /// - [device] 设备创建请求
  /// - [projectId] 项目 UUID（用于刷新树）
  ///
  /// 返回创建的设备
  Future<Device> createDevice(
    String systemId,
    DeviceCreate device,
    String projectId,
  ) async {
    _setLoading(true);
    _clearError();

    try {
      final newDevice = await _service.createDevice(systemId, device);
      debugPrint('成功创建设备: ${newDevice.name}');

      // 刷新工程结构树
      await refreshStructureTree(projectId);

      expandSystem(systemId);

      return newDevice;
    } catch (e) {
      _setError('创建设备失败: $e');
      debugPrint('错误: $e');
      rethrow;
    } finally {
      _setLoading(false);
    }
  }

  @override
  void dispose() {
    _expandedBuildings.clear();
    _expandedSystems.clear();
    super.dispose();
  }
}
