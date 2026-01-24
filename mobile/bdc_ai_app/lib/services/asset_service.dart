import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'api_service.dart';
import '../models/asset.dart';
import '../config/constants.dart';

/// 资产服务
///
/// 负责资产相关 API 调用（支持系统级和设备级视图）
class AssetService {
  final ApiService _api;

  AssetService({ApiService? api}) : _api = api ?? ApiService();

  /// 获取设备资产列表（设备视图）
  ///
  /// API: GET /api/v1/assets/?device_id={id}&limit=5&offset=0
  ///
  /// 参数:
  /// - [deviceId] 设备 UUID
  /// - [limit] 返回数量，默认 5
  /// - [offset] 偏移量，用于分页
  ///
  /// 返回资产列表（按 created_at desc 排序）
  Future<List<Asset>> getDeviceAssets(
    String deviceId, {
    int limit = 5,
    int offset = 0,
  }) async {
    final endpoint =
        '${ApiEndpoints.assets}?device_id=$deviceId&limit=$limit&offset=$offset';

    try {
      final response = await _api.get(endpoint);
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((json) => Asset.fromJson(json)).toList();
    } catch (e) {
      debugPrint('获取设备资产列表失败: $e');
      rethrow;
    }
  }

  /// 获取系统资产列表（系统视图）⭐
  ///
  /// API: GET /api/v1/assets/?system_id={id}&limit=5&offset=0
  ///
  /// 参数:
  /// - [systemId] 系统 UUID
  /// - [limit] 返回数量，默认 5
  /// - [offset] 偏移量，用于分页
  ///
  /// 返回资产列表（按 created_at desc 排序）
  Future<List<Asset>> getSystemAssets(
    String systemId, {
    int limit = 5,
    int offset = 0,
  }) async {
    final endpoint =
        '${ApiEndpoints.assets}?system_id=$systemId&limit=$limit&offset=$offset';

    try {
      final response = await _api.get(endpoint);
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((json) => Asset.fromJson(json)).toList();
    } catch (e) {
      debugPrint('获取系统资产列表失败: $e');
      rethrow;
    }
  }

  /// 上传图片+备注（支持设备级或系统级）⭐
  ///
  /// API: POST /api/v1/assets/upload_image_with_note
  ///
  /// 参数:
  /// - [projectId] 项目 UUID（必填）
  /// - [deviceId] 设备 UUID（可选，与 systemId 二选一）
  /// - [systemId] 系统 UUID（可选，与 deviceId 二选一）⭐
  /// - [filePath] 图片文件路径（必填）
  /// - [note] 工程师备注（可选）
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
    // 验证必填参数
    if (projectId.isEmpty) {
      throw ArgumentError('projectId 不能为空');
    }
    if (filePath.isEmpty) {
      throw ArgumentError('filePath 不能为空');
    }

    // 检查文件是否存在
    final file = File(filePath);
    if (!file.existsSync()) {
      throw FileSystemException('文件不存在', filePath);
    }

    try {
      // 读取文件字节
      final fileBytes = await file.readAsBytes();
      final fileMime = _lookupMimeType(filePath);

      // 创建 multipart 文件
      final multipartFile = http.MultipartFile.fromBytes(
        'file',
        fileBytes,
        filename: filePath.split('/').last,
        contentType: http.MediaType.parse(fileMime),
      );

      // ⭐ 构建端点 URL（Query 参数在 URL 中）
      var endpoint = '${ApiEndpoints.uploadImage}?project_id=$projectId&source=mobile';
      if (deviceId != null && deviceId.isNotEmpty) {
        endpoint += '&device_id=$deviceId';
      }
      if (systemId != null && systemId.isNotEmpty) {
        endpoint += '&system_id=$systemId';
      }
      if (contentRole != null && contentRole.isNotEmpty) {
        endpoint += '&content_role=$contentRole';
      }
      endpoint += '&auto_route=${autoRoute ? "true" : "false"}'; // ⭐ 添加自动解析选项

      // ⭐ 表单字段只保留 note 和 title（Form 参数）
      final fields = <String, String>{
        if (note != null && note.isNotEmpty) 'note': note,
      };

      // 发送请求
      final response = await _api.postMultipart(
        endpoint,
        fields: fields,
        files: [multipartFile],
      );

      // 解析响应
      final data = jsonDecode(response.body);
      return Asset.fromJson(data);
    } catch (e) {
      debugPrint('上传图片失败: $e');
      rethrow;
    }
  }

  /// 获取资产详情
  ///
  /// API: GET /api/v1/assets/{asset_id}
  ///
  /// 参数:
  /// - [assetId] 资产 UUID
  ///
  /// 返回资产详情（含结构化内容）
  Future<Asset> getAssetDetail(String assetId) async {
    try {
      final response = await _api.get('${ApiEndpoints.assets}$assetId');
      final data = jsonDecode(response.body);
      return Asset.fromJson(data);
    } catch (e) {
      debugPrint('获取资产详情失败: $e');
      rethrow;
    }
  }

  /// 删除资产⭐
  ///
  /// API: DELETE /api/v1/assets/{asset_id}?delete_file=true
  ///
  /// 参数:
  /// - [assetId] 资产 UUID
  /// - [deleteFile] 是否删除底层文件（默认 true）
  ///
  /// 注意：只能删除移动端上传的资产（source='mobile'）
  Future<void> deleteAsset(String assetId, {bool deleteFile = true}) async {
    try {
      final endpoint = '${ApiEndpoints.assets}$assetId?delete_file=$deleteFile';
      await _api.delete(endpoint);
      debugPrint('删除资产成功: $assetId');
    } catch (e) {
      debugPrint('删除资产失败: $e');
      rethrow;
    }
  }

  /// 批量删除资产⭐
  ///
  /// 参数:
  /// - [assetIds] 资产 UUID 列表
  /// - [deleteFile] 是否删除底层文件（默认 true）
  ///
  /// 返回：成功删除的数量和失败的资产ID列表
  Future<Map<String, dynamic>> deleteAssets(
    List<String> assetIds, {
    bool deleteFile = true,
  }) async {
    int successCount = 0;
    List<String> failedIds = [];

    for (final assetId in assetIds) {
      try {
        await deleteAsset(assetId, deleteFile: deleteFile);
        successCount++;
      } catch (e) {
        debugPrint('删除资产失败: $assetId, 错误: $e');
        failedIds.add(assetId);
      }
    }

    return {
      'successCount': successCount,
      'failedIds': failedIds,
    };
  }

  /// 根据文件路径推断 MIME 类型
  String _lookupMimeType(String path) {
    final extension = path.split('.').last.toLowerCase();
    switch (extension) {
      case 'jpg':
      case 'jpeg':
        return 'image/jpeg';
      case 'png':
        return 'image/png';
      case 'gif':
        return 'image/gif';
      case 'webp':
        return 'image/webp';
      default:
        return 'image/jpeg'; // 默认
    }
  }
}
