import '../config/constants.dart';
/// 资产模型
class Asset {
  final String id;
  final String title;
  final String modality; // image, audio, text, document
  final String source; // mobile, pc
  final String? contentRole; // scene_issue, nameplate, etc.
  final DateTime createdAt;
  final String? note;
  final String? rawUrl; // 图片 URL
  final String? deviceId;
  final String? systemId;
  final String? zoneId;
  final String? buildingId;

  /// LLM 结果摘要（仅在详情接口中可用，可选）
  final String? llmSummary;

  Asset({
    required this.id,
    required this.title,
    required this.modality,
    required this.source,
    this.contentRole,
    required this.createdAt,
    this.note,
    this.rawUrl,
    this.deviceId,
    this.systemId,
    this.zoneId,
    this.buildingId,
    this.llmSummary,
  });

  factory Asset.fromJson(Map<String, dynamic> json) {
    // 优先使用后端直接提供的 URL 字段（原始 URL 或显式 download_url），
    // 不直接使用 file_path 作为 URL，以避免在 Web 环境下被当作相对路径导致请求打到前端 dev server。
    final directUrl = json['raw_url']?.toString() ??
        json['download_url']?.toString();

    // 如果后端没有给出直接可用的 URL，则构造统一的下载地址：
    //   {baseUrl}/api/v1/assets/{id}/download
    final id = json['id']?.toString() ?? '';
    final fallbackUrl = id.isNotEmpty
        ? '${AppConfig.baseUrl}/api/v1/assets/$id/download'
        : null;

    // 解析 AI 结果摘要（仅在详情接口中有 structured_payloads 时可用）
    String? llmSummary;
    final payloads = json['structured_payloads'] as List<dynamic>?;
    if (payloads != null && payloads.isNotEmpty) {
      Map<String, Map<String, dynamic>> latestBySchema = {};

      for (final sp in payloads) {
        if (sp is! Map<String, dynamic>) continue;
        final schema = sp['schema_type']?.toString();
        if (schema == null || schema.isEmpty) continue;

        double version = 0;
        try {
          final v = sp['version'];
          if (v != null) {
            version = double.tryParse(v.toString()) ?? 0;
          }
        } catch (_) {
          version = 0;
        }

        final existing = latestBySchema[schema];
        if (existing == null) {
          latestBySchema[schema] = Map<String, dynamic>.from(sp);
        } else {
          double existingVersion = 0;
          try {
            final v = existing['version'];
            if (v != null) {
              existingVersion = double.tryParse(v.toString()) ?? 0;
            }
          } catch (_) {
            existingVersion = 0;
          }
          if (version >= existingVersion) {
            latestBySchema[schema] = Map<String, dynamic>.from(sp);
          }
        }
      }

      final buffer = StringBuffer();

      // 按固定顺序渲染：场景问题 → 铭牌 → 仪表
      for (final schema in [
        'scene_issue_report_v1',
        'nameplate_table_v1',
        'meter_reading_v1',
      ]) {
        final sp = latestBySchema[schema];
        if (sp == null) continue;
        final payload = sp['payload'] as Map<String, dynamic>? ?? {};

        // 现场问题解析结果
        if (schema == 'scene_issue_report_v1') {
          final title = payload['title']?.toString();
          final summary = payload['summary']?.toString();
          final actions = (payload['recommended_actions'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList();

          if (title != null && title.isNotEmpty) {
            buffer.writeln('【问题】$title');
          }
          if (summary != null && summary.isNotEmpty) {
            buffer.writeln('【摘要】$summary');
          }
          if (actions != null && actions.isNotEmpty) {
            buffer.writeln('【建议】');
            for (final a in actions.take(3)) {
              buffer.writeln('- $a');
            }
            buffer.writeln();
          }
        }

        // 铭牌表格解析结果（nameplate_table_v1）
        if (schema == 'nameplate_table_v1') {
          final equipmentType = payload['equipment_type']?.toString();
          final fields = payload['fields'] as List<dynamic>?;

          if (equipmentType != null && equipmentType.isNotEmpty) {
            buffer.writeln('【铭牌】设备类型：$equipmentType');
          } else {
            buffer.writeln('【铭牌】');
          }

          if (fields != null && fields.isNotEmpty) {
            final displayFields = fields.take(6);
            for (final f in displayFields) {
              if (f is! Map<String, dynamic>) continue;
              final label = (f['label'] ?? f['key'])?.toString();
              final value = f['value'];
              final unit = f['unit']?.toString();

              if (label == null || label.isEmpty) continue;

              var valueStr = value?.toString() ?? '';
              if (unit != null && unit.isNotEmpty) {
                valueStr = valueStr.isEmpty ? unit : '$valueStr $unit';
              }
              if (valueStr.isEmpty) continue;

              buffer.writeln('- $label: $valueStr');
            }
            buffer.writeln();
          }
        }

        // 仪表读数解析结果（meter_reading_v1）
        if (schema == 'meter_reading_v1') {
          final reading = payload['reading'];
          final preReading = payload['pre_reading'];
          final unit = payload['unit']?.toString() ?? '';
          final status = payload['status']?.toString();
          final summary = payload['summary']?.toString();

          buffer.writeln('【仪表读数】');

          if (reading != null) {
            buffer.writeln('当前读数: ${reading.toString()}$unit');
          }
          if (preReading != null) {
            buffer.writeln('预读数: ${preReading.toString()}$unit');
          }
          if (status != null && status.isNotEmpty) {
            buffer.writeln('状态: $status');
          }
          if (summary != null && summary.isNotEmpty) {
            buffer.writeln('说明: $summary');
          }
          buffer.writeln();
        }
      }

      final text = buffer.toString().trim();
      if (text.isNotEmpty) {
        llmSummary = text;
      }
    }

    return Asset(
      id: id,
      title: json['title']?.toString() ?? '未命名资产',
      modality: json['modality']?.toString() ?? 'unknown',
      source: json['source']?.toString() ?? 'unknown',
      contentRole: json['content_role']?.toString(),
      // ⭐ 优先使用 capture_time，兼容 created_at
      createdAt: _parseDateTime(json['capture_time'] ?? json['created_at']),
      // 备注优先使用后端的 description，兼容历史 note 字段
      note: json['description']?.toString() ?? json['note']?.toString(),
      // ⭐ 支持 raw_url、download_url、file_path（按优先级），否则回退到统一下载地址
      rawUrl: directUrl ?? fallbackUrl,
      deviceId: json['device_id']?.toString(),
      systemId: json['system_id']?.toString(),
      zoneId: json['zone_id']?.toString(),
      buildingId: json['building_id']?.toString(),
      llmSummary: llmSummary,
    );
  }

  /// 安全解析 DateTime ⭐
  ///
  /// 支持：
  /// - null → 返回当前时间
  /// - DateTime 对象 → 直接返回
  /// - 字符串 → 解析为 DateTime
  static DateTime _parseDateTime(dynamic value) {
    if (value == null) {
      return DateTime.now();
    }
    if (value is DateTime) {
      return value;
    }
    try {
      return DateTime.parse(value.toString());
    } catch (e) {
      // 解析失败时返回当前时间
      return DateTime.now();
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'modality': modality,
      'source': source,
      'content_role': contentRole,
      'created_at': createdAt.toIso8601String(),
      'note': note,
      'description': note,
      'raw_url': rawUrl,
      'device_id': deviceId,
      'system_id': systemId,
      'zone_id': zoneId,
      'building_id': buildingId,
      'llm_summary': llmSummary,
    };
  }

  /// 获取模态显示文本
  String get modalityText {
    switch (modality) {
      case 'image':
        return '图片';
      case 'audio':
        return '音频';
      case 'text':
        return '文本';
      case 'document':
        return '文档';
      default:
        return modality;
    }
  }

  /// 获取内容角色显示文本
  String? get contentRoleText {
    switch (contentRole) {
      case 'scene_issue':
        return '现场问题';
      case 'nameplate':
        return '铭牌';
      case 'maintenance':
        return '维护记录';
      case 'general':
        return '通用';
      default:
        return contentRole;
    }
  }

  /// 是否为图片类型
  bool get isImage => modality == 'image';

  /// 格式化时间显示
  String get formattedTime {
    final now = DateTime.now();
    final difference = now.difference(createdAt);

    if (difference.inMinutes < 1) {
      return '刚刚';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes} 分钟前';
    } else if (difference.inDays < 1) {
      return '${difference.inHours} 小时前';
    } else if (difference.inDays == 1) {
      return '昨天';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} 天前';
    } else {
      return '${createdAt.month}月${createdAt.day}日';
    }
  }
}
