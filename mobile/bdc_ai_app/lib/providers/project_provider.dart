import 'package:flutter/foundation.dart';
import '../models/project.dart';
import '../services/project_service.dart';

/// 项目列表状态管理
///
/// 管理项目列表的加载状态和数据
class ProjectProvider extends ChangeNotifier {
  final ProjectService _service = ProjectService();

  /// 项目列表
  List<Project> _projects = [];

  /// 是否正在加载
  bool _isLoading = false;

  /// 错误消息
  String? _errorMessage;

  /// 获取项目列表
  List<Project> get projects => _projects;

  /// 是否正在加载
  bool get isLoading => _isLoading;

  /// 是否有错误
  bool get hasError => _errorMessage != null;

  /// 错误消息
  String? get errorMessage => _errorMessage;

  /// 是否为空列表
  bool get isEmpty => _projects.isEmpty;

  /// 加载项目列表
  ///
  /// 参数:
  /// - [status] 项目状态过滤
  /// - [type] 项目类型过滤
  /// - [client] 客户名称模糊搜索
  /// - [name] 项目名称模糊搜索
  Future<void> loadProjects({
    String? status,
    String? type,
    String? client,
    String? name,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      _projects = await _service.getProjects(
        status: status,
        type: type,
        client: client,
        name: name,
      );
      debugPrint('成功加载 ${_projects.length} 个项目');
    } catch (e) {
      _setError('加载项目列表失败: $e');
      debugPrint('错误: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// 刷新项目列表
  Future<void> refreshProjects({
    String? status,
    String? type,
    String? client,
    String? name,
  }) async {
    debugPrint('刷新项目列表');
    await loadProjects(
      status: status,
      type: type,
      client: client,
      name: name,
    );
  }

  /// 根据索引获取项目
  Project? getProjectById(int index) {
    if (index >= 0 && index < _projects.length) {
      return _projects[index];
    }
    return null;
  }

  /// 根据ID查找项目
  Project? findProjectById(String id) {
    try {
      return _projects.firstWhere((project) => project.id == id);
    } catch (e) {
      return null;
    }
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

  @override
  void dispose() {
    super.dispose();
  }
}
