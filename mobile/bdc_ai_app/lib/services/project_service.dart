import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'api_service.dart';
import 'auth_service.dart';
import '../models/project.dart';
import '../models/structure.dart';
import '../config/constants.dart';

/// 项目服务
///
/// 负责项目与工程结构相关的 API 调用
class ProjectService {
  final ApiService _api;

  ProjectService({ApiService? api}) : _api = api ?? ApiService();

  /// 为需要认证的请求构建带 Authorization 头的请求头
  Map<String, String> _buildAuthHeaders() {
    final token = AuthService().currentToken;
    if (token != null && token.isNotEmpty) {
      return {'Authorization': 'Bearer $token'};
    }
    return <String, String>{};
  }

  /// 获取项目列表
  ///
  /// API: GET /api/v1/projects/
  ///
  /// 参数:
  /// - [status] 项目状态过滤 (planning/active/completed/archived)
  /// - [type] 项目类型过滤
  /// - [client] 客户名称模糊搜索
  /// - [name] 项目名称模糊搜索
  ///
  /// 返回项目列表
  Future<List<Project>> getProjects({
    String? status,
    String? type,
    String? client,
    String? name,
  }) async {
    // 构建查询参数
    final queryParams = <String, String>{};
    if (status != null && status.isNotEmpty) {
      queryParams['status'] = status;
    }
    if (type != null && type.isNotEmpty) {
      queryParams['type'] = type;
    }
    if (client != null && client.isNotEmpty) {
      queryParams['client'] = client;
    }
    if (name != null && name.isNotEmpty) {
      queryParams['name'] = name;
    }

    // 拼接查询字符串
    final queryString = queryParams.entries
        .map((e) => '${e.key}=${Uri.encodeComponent(e.value)}')
        .join('&');

    final endpoint = queryString.isEmpty
        ? ApiEndpoints.projects
        : '${ApiEndpoints.projects}?$queryString';

    try {
      final response = await _api.get(
        endpoint,
        headers: _buildAuthHeaders(),
      );
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((json) => Project.fromJson(json)).toList();
    } catch (e) {
      debugPrint('获取项目列表失败: $e');
      rethrow;
    }
  }

  /// 获取项目详情
  ///
  /// API: GET /api/v1/projects/{id}
  ///
  /// 参数:
  /// - [id] 项目 UUID
  ///
  /// 返回项目详情
  Future<Project> getProjectDetail(String id) async {
    try {
      final response = await _api.get(
        ApiEndpoints.projectDetail(id),
        headers: _buildAuthHeaders(),
      );
      final data = jsonDecode(response.body);
      return Project.fromJson(data);
    } catch (e) {
      debugPrint('获取项目详情失败: $e');
      rethrow;
    }
  }

  /// 获取工程结构树
  ///
  /// API: GET /api/v1/projects/{id}/structure_tree
  ///
  /// {
  ///   "project_id": "...",
  ///   "tree": {
  ///     "id": "project-root",
  ///     "name": "项目根",
  ///     "type": "project_root",
  ///     "children": [
  ///       {
  ///         "id": "...",
  ///         "name": "1号厂房",
  ///         "type": "building",
  ///         "children": [...]
  ///       }
  ///     ]
  ///   }
  /// }
  /// ```
  ///
  /// 参数:
  /// - [projectId] 项目 UUID
  ///
  /// 返回完整工程结构树（楼栋 → 系统 → 设备 + 区域）
  Future<List<Building>> getStructureTree(String projectId) async {
    try {
      final response = await _api.get(
        ApiEndpoints.structureTree(projectId),
        headers: _buildAuthHeaders(),
      );
      final Map<String, dynamic> data = jsonDecode(response.body);

      // 从 tree.children 中提取 Building 列表 ⭐
      final Map<String, dynamic>? tree = data['tree'];
      if (tree == null) {
        debugPrint('错误：响应中缺少 tree 字段');
        return [];
      }

      final List<dynamic> children = tree['children'] ?? [];
      debugPrint('成功解析工程结构树：${children.length} 个楼栋');

      return children
          .map((json) => Building.fromJson(json as Map<String, dynamic>))
          .toList();
    } catch (e) {
      debugPrint('获取工程结构树失败: $e');
      rethrow;
    }
  }

  /// 创建设备
  ///
  /// API: POST /api/v1/systems/{system_id}/devices
  ///
  /// 参数:
  /// - [systemId] 系统 UUID
  /// - [device] 设备创建请求
  ///
  /// 返回创建的设备信息
  Future<Device> createDevice(String systemId, DeviceCreate device) async {
    try {
      final response = await _api.post(
        ApiEndpoints.createDevice(systemId),
        headers: _buildAuthHeaders(),
        body: device.toJson(),
      );
      final data = jsonDecode(response.body);
      return Device.fromJson(data);
    } catch (e) {
      debugPrint('创建设备失败: $e');
      rethrow;
    }
  }
}
