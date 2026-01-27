import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/constants.dart';
import '../models/project.dart';
import '../services/project_service.dart';
import '../services/api_service.dart';

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

    // 仅在无过滤条件时启用缓存
    final bool enableCache =
        status == null && type == null && client == null && name == null;

    List<Project>? cachedData;

    try {
      if (enableCache) {
        // 1. 先尝试从缓存加载
        cachedData = await _loadFromCache();

        if (cachedData != null) {
          debugPrint('使用缓存的项目列表');
          _projects = cachedData;
          notifyListeners();

          final isExpired = await _isCacheExpired();
          if (!isExpired) {
            debugPrint('项目列表缓存未过期，跳过网络请求');
            return;
          }

          debugPrint('项目列表缓存已过期，尝试从网络刷新');
        }
      }

      // 2. 从网络加载最新数据
      _projects = await _service.getProjects(
        status: status,
        type: type,
        client: client,
        name: name,
      );
      debugPrint('成功加载 ${_projects.length} 个项目');

      // 3. 保存到缓存（仅无过滤条件时）
      if (enableCache) {
        await _saveToCache(_projects);
      }

      notifyListeners();
    } catch (e) {
      if (e is ApiException && (e.statusCode == 401 || e.statusCode == 403)) {
        // 认证失败交由全局认证逻辑处理，这里不再展示错误页
        debugPrint('项目列表请求认证失败: $e');
        return;
      }

      // 网络等异常时，如果有缓存数据则降级使用缓存
      if (enableCache && cachedData != null) {
        debugPrint('项目列表请求失败，使用缓存数据: $e');
        _projects = cachedData;
        // 不设置错误消息，避免打断用户
        notifyListeners();
        return;
      }

      _setError('加载项目列表失败: $e');
      debugPrint('错误: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// 从缓存加载项目列表
  Future<List<Project>?> _loadFromCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonString = prefs.getString(CacheKeys.projectList);

      if (jsonString == null) {
        debugPrint('项目列表无缓存数据');
        return null;
      }

      final List<dynamic> jsonData = jsonDecode(jsonString) as List<dynamic>;
      return jsonData
          .map((item) => Project.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      debugPrint('读取项目列表缓存失败: $e');
      return null;
    }
  }

  /// 将项目列表写入缓存
  Future<void> _saveToCache(List<Project> data) async {
    try {
      final prefs = await SharedPreferences.getInstance();

      final jsonString = jsonEncode(
        data.map((p) => p.toJson()).toList(),
      );
      await prefs.setString(CacheKeys.projectList, jsonString);

      await prefs.setInt(
        CacheKeys.projectListTimestamp,
        DateTime.now().millisecondsSinceEpoch,
      );

      debugPrint('已缓存项目列表，有效期 ${AppConfig.cacheDurationHours} 小时');
    } catch (e) {
      debugPrint('保存项目列表缓存失败: $e');
    }
  }

  /// 检查项目列表缓存是否过期
  Future<bool> _isCacheExpired() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final timestamp = prefs.getInt(CacheKeys.projectListTimestamp);

      if (timestamp == null) {
        return true;
      }

      final cacheTime = DateTime.fromMillisecondsSinceEpoch(timestamp);
      final now = DateTime.now();
      final difference = now.difference(cacheTime);

      final isExpired = difference.inHours >= AppConfig.cacheDurationHours;

      debugPrint('项目列表缓存时间: $cacheTime');
      debugPrint('当前时间: $now');
      debugPrint('缓存时长: ${difference.inHours} 小时');
      debugPrint('项目列表缓存是否过期: $isExpired');

      return isExpired;
    } catch (e) {
      debugPrint('检查项目列表缓存过期失败: $e');
      return true;
    }
  }

  /// 清除项目列表缓存
  Future<void> clearProjectCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(CacheKeys.projectList);
      await prefs.remove(CacheKeys.projectListTimestamp);
      debugPrint('已清除项目列表缓存');
    } catch (e) {
      debugPrint('清除项目列表缓存失败: $e');
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
