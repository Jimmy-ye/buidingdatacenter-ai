/// 项目模型
class Project {
  final String id;
  final String name;
  final String? client;
  final String? address;
  final String? description;
  final String status; // planning, active, completed, archived
  final DateTime createdAt;

  Project({
    required this.id,
    required this.name,
    this.client,
    this.address,
    this.description,
    required this.status,
    required this.createdAt,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '未命名项目',
      client: json['client']?.toString(),
      address: json['address']?.toString(),
      description: json['description']?.toString(),
      status: json['status']?.toString() ?? 'planning',
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'].toString())
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'client': client,
      'address': address,
      'description': description,
      'status': status,
      'created_at': createdAt.toIso8601String(),
    };
  }

  /// 获取状态显示文本
  String get statusText {
    switch (status) {
      case 'planning':
        return '规划中';
      case 'active':
        return '进行中';
      case 'completed':
        return '已完成';
      case 'archived':
        return '已归档';
      default:
        return status;
    }
  }
}
