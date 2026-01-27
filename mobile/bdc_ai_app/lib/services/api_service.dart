import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/constants.dart';
import 'auth_service.dart';

/// API 基础服务
class ApiService {
  final String baseUrl;
  final http.Client _client;

  ApiService({
    String? baseUrl,
    http.Client? client,
  })  : baseUrl = baseUrl ?? AppConfig.baseUrl,
        _client = client ?? http.Client();

  /// GET 请求
  Future<http.Response> get(
    String endpoint, {
    Map<String, String>? headers,
  }) async {
    final url = Uri.parse('$baseUrl$endpoint');
    final response = await _client
        .get(
          url,
          headers: _buildHeaders(headers),
        )
        .timeout(
          const Duration(milliseconds: AppConfig.apiTimeout),
    );

    return _handleResponse(response);
  }

  /// POST 请求
  Future<http.Response> post(
    String endpoint, {
    Map<String, dynamic>? body,
    Map<String, String>? headers,
  }) async {
    final url = Uri.parse('$baseUrl$endpoint');
    final response = await _client
        .post(
          url,
          headers: _buildHeaders(headers),
          body: body != null ? jsonEncode(body) : null,
        )
        .timeout(
          const Duration(milliseconds: AppConfig.apiTimeout),
    );

    return _handleResponse(response);
  }

  /// POST 表单数据（文件上传）
  Future<http.Response> postMultipart(
    String endpoint, {
    Map<String, String>? fields,
    List<http.MultipartFile>? files,
    Map<String, String>? headers,
  }) async {
    final url = Uri.parse('$baseUrl$endpoint');
    final request = http.MultipartRequest('POST', url);

    // 添加字段
    if (fields != null) {
      request.fields.addAll(fields);
    }

    // 添加文件
    if (files != null) {
      request.files.addAll(files);
    }

    // 添加请求头
    request.headers.addAll(_buildHeaders(headers));

    // 发送请求
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    return _handleResponse(response);
  }

  /// PATCH 请求
  Future<http.Response> patch(
    String endpoint, {
    Map<String, dynamic>? body,
    Map<String, String>? headers,
  }) async {
    final url = Uri.parse('$baseUrl$endpoint');
    final response = await _client
        .patch(
          url,
          headers: _buildHeaders(headers),
          body: body != null ? jsonEncode(body) : null,
        )
        .timeout(
          const Duration(milliseconds: AppConfig.apiTimeout),
    );

    return _handleResponse(response);
  }

  /// DELETE 请求
  Future<http.Response> delete(
    String endpoint, {
    Map<String, String>? headers,
  }) async {
    final url = Uri.parse('$baseUrl$endpoint');
    final response = await _client
        .delete(
          url,
          headers: _buildHeaders(headers),
        )
        .timeout(
          const Duration(milliseconds: AppConfig.apiTimeout),
    );

    return _handleResponse(response);
  }

  /// 构建请求头
  Map<String, String> _buildHeaders(Map<String, String>? extra) {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    if (extra != null) {
      headers.addAll(extra);
    }

    return headers;
  }

  /// 处理响应
  http.Response _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return response;
    }

    // 认证失败（包括 Token 过期）时，触发全局登出逻辑
    if (response.statusCode == 401 || response.statusCode == 403) {
      // 异步执行，不阻塞当前响应处理
      AuthService().markTokenExpired();
    }

    throw ApiException(
      statusCode: response.statusCode,
      message: _parseErrorMessage(response),
    );
  }

  /// 解析错误消息
  String _parseErrorMessage(http.Response response) {
    try {
      final data = jsonDecode(response.body);
      return data['message'] ?? data['detail'] ?? '请求失败';
    } catch (e) {
      return '请求失败 (HTTP ${response.statusCode})';
    }
  }

  /// 关闭客户端
  void dispose() {
    _client.close();
  }
}

/// API 异常
class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException({required this.statusCode, required this.message});

  @override
  String toString() => 'ApiException: $message (HTTP $statusCode)';
}
