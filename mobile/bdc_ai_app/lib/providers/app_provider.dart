import 'package:flutter/foundation.dart';
import '../models/project.dart';
import '../config/constants.dart';

/// 应用全局状态管理
///
/// 管理应用级别的状态，如当前选中的项目
class AppProvider extends ChangeNotifier {
  /// 当前选中的项目
  Project? _currentProject;

  /// 获取当前项目
  Project? get currentProject => _currentProject;

  /// 是否已选择项目
  bool get hasProject => _currentProject != null;

  /// API 基础 URL
  String get baseUrl => AppConfig.baseUrl;

  /// 选择项目
  ///
  /// 参数:
  /// - [project] 选中的项目对象
  void selectProject(Project project) {
    _currentProject = project;
    notifyListeners();
    debugPrint('已选择项目: ${project.name}');
  }

  /// 清除当前项目
  void clearProject() {
    _currentProject = null;
    notifyListeners();
    debugPrint('已清除项目选择');
  }

  /// 获取当前项目 ID
  ///
  /// 如果未选择项目，抛出异常
  String getCurrentProjectId() {
    if (_currentProject == null) {
      throw StateError('未选择项目，请先选择一个项目');
    }
    return _currentProject!.id;
  }
}
