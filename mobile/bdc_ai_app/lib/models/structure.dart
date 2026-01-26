/// 工程结构数据模型
///
/// **正确的层级关系**：
/// - Building → System → Device（主树，System 是 Device 的主归属）
/// - Building → Zone（与 System 同级，作为位置属性）
/// - Device 归属于 System，位于 Zone（Ownership vs Location）
///
/// **核心原则**：
/// - System 是资产的主挂接点
/// - Device 是可选的细化挂接点
/// - Zone 是物理位置属性

/// 楼栋模型
class Building {
  final String id;
  final String name;
  final String? usageType; // office/commercial/datacenter/mixed_use
  final double? floorArea;
  final double? gfaArea;
  final int? yearBuilt;
  final List<String>? tags;

  /// 系统列表（与 zones 同级）⭐
  final List<System> systems;

  /// 区域列表（与 systems 同级，不含设备）⭐
  final List<ZoneInfo> zones;

  Building({
    required this.id,
    required this.name,
    this.usageType,
    this.floorArea,
    this.gfaArea,
    this.yearBuilt,
    this.tags,
    required this.systems,
    required this.zones,
  });

  factory Building.fromJson(Map<String, dynamic> json) {
    // 优先从 children 中解析 systems 和 zones（structure_tree 返回格式），
    // 若不存在 children，则兼容旧的扁平字段 systems/zones
    List<System> systems = [];
    List<ZoneInfo> zones = [];

    final children = json['children'] as List<dynamic>?;
    if (children != null) {
      for (final child in children) {
        if (child is Map<String, dynamic>) {
          final type = child['type']?.toString();
          if (type == 'system') {
            systems.add(System.fromJson(child));
          } else if (type == 'zone') {
            zones.add(ZoneInfo.fromJson(child));
          }
        }
      }
    } else {
      systems = (json['systems'] as List<dynamic>?)
              ?.map((e) => System.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [];
      zones = (json['zones'] as List<dynamic>?)
              ?.map((e) => ZoneInfo.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [];
    }

    return Building(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '未命名建筑',
      usageType: json['usage_type']?.toString(),
      floorArea: (json['floor_area'] as num?)?.toDouble(),
      gfaArea: (json['gfa_area'] as num?)?.toDouble(),
      yearBuilt: json['year_built'] as int?,
      tags: (json['tags'] as List<dynamic>?)?.cast<String>(),
      systems: systems,
      zones: zones,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'usage_type': usageType,
      'floor_area': floorArea,
      'gfa_area': gfaArea,
      'year_built': yearBuilt,
      'tags': tags,
      'systems': systems.map((s) => s.toJson()).toList(),
      'zones': zones.map((z) => z.toJson()).toList(),
    };
  }
}

/// 系统模型（Building 的直接子节点，与 Zone 同级）
class System {
  final String id;
  final String name;
  final String type; // system_type: HVAC/ChilledWater/Lighting/Elevator 等
  final String? description;
  final List<String>? tags;

  /// 设备列表（Device 归属于 System）⭐
  final List<Device> devices;

  System({
    required this.id,
    required this.name,
    required this.type,
    this.description,
    this.tags,
    required this.devices,
  });

  factory System.fromJson(Map<String, dynamic> json) {
    // 优先从 children 中解析 devices（structure_tree 返回格式），
    // 若不存在 children，则兼容旧的 devices 字段
    List<Device> devices = [];

    final children = json['children'] as List<dynamic>?;
    if (children != null) {
      for (final child in children) {
        if (child is Map<String, dynamic>) {
          final type = child['type']?.toString();
          if (type == 'device') {
            devices.add(Device.fromJson(child));
          }
        }
      }
    } else {
      devices = (json['devices'] as List<dynamic>?)
              ?.map((e) => Device.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [];
    }

    return System(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? json['type']?.toString() ?? '未命名系统',
      type: json['type']?.toString() ?? 'unknown',
      description: json['description']?.toString(),
      tags: (json['tags'] as List<dynamic>?)?.cast<String>(),
      devices: devices,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'type': type,
      'description': description,
      'tags': tags,
      'devices': devices.map((d) => d.toJson()).toList(),
    };
  }

  /// 获取系统类型显示文本
  String get typeText {
    switch (type) {
      case 'envelope':
        return '围护结构';
      case 'cooling':
        return '制冷系统';
      case 'heating':
        return '制热系统';
      case 'terminal_hvac':
        return '空调末端';
      case 'lighting':
        return '照明系统';
      case 'elevator':
        return '电梯系统';
      case 'power':
        return '动力系统';
      case 'ems':
        return '电力监控';
      case 'energy_platform':
        return '能管平台';
      case 'HVAC':
        return '暖通空调';
      case 'ChilledWater':
        return '冷冻水系统';
      case 'HotWater':
        return '热水系统';
      case 'Boiler':
        return '锅炉系统';
      case 'CoolingTower':
        return '冷却塔';
      default:
        return type;
    }
  }

  /// 获取系统图标
  String get icon {
    switch (type.toLowerCase()) {
      case 'envelope':
        return '🏢';
      case 'cooling':
      case 'chilledwater':
        return '❄️';
      case 'heating':
      case 'hotwater':
      case 'boiler':
        return '🔥';
      case 'terminal_hvac':
      case 'hvac':
        return '🌬️';
      case 'lighting':
        return '💡';
      case 'elevator':
        return '🛗';
      case 'power':
        return '⚡';
      case 'ems':
        return '📊';
      case 'energy_platform':
        return '🖥️';
      default:
        return '⚙️';
    }
  }
}

/// 设备模型（归属于 System）
class Device {
  final String id;
  final String name;
  final String? deviceType;
  final String? model;
  final double? ratedPower;
  final String? serialNo;
  final List<String>? tags;
  final int? assetCount;

  /// 所属 Zone（可选，位置属性）⭐
  final ZoneLocation? zone;

  /// 工程路径（自动生成）
  final String? engineerPath;

  Device({
    required this.id,
    required this.name,
    this.deviceType,
    this.model,
    this.ratedPower,
    this.serialNo,
    this.tags,
    this.assetCount,
    this.zone,
    this.engineerPath,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? json['model']?.toString() ?? '未命名设备',
      deviceType: json['device_type']?.toString(),
      model: json['model']?.toString(),
      ratedPower: (json['rated_power'] as num?)?.toDouble(),
      serialNo: json['serial_no']?.toString(),
      tags: (json['tags'] as List<dynamic>?)?.cast<String>(),
      assetCount: json['asset_count'] as int?,
      zone: json['zone'] != null
          ? ZoneLocation.fromJson(json['zone'] as Map<String, dynamic>)
          : null,
      engineerPath: json['engineer_path']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'device_type': deviceType,
      'model': model,
      'rated_power': ratedPower,
      'serial_no': serialNo,
      'tags': tags,
      'asset_count': assetCount,
      'zone': zone?.toJson(),
      'engineer_path': engineerPath,
    };
  }

  /// 获取设备类型显示文本
  String get deviceTypeText {
    switch (deviceType?.toLowerCase()) {
      case 'chiller':
        return '冷水机组';
      case 'pump':
        return '水泵';
      case 'fan':
        return '风机';
      case 'ahu':
        return '空气处理机组';
      case 'fcu':
        return '风机盘管';
      case 'cooling_tower':
        return '冷却塔';
      case 'boiler':
        return '锅炉';
      case 'lighting':
        return '照明灯具';
      case 'elevator':
        return '电梯';
      case 'meter':
        return '电表';
      case 'sensor':
        return '传感器';
      default:
        return deviceType ?? '未知';
    }
  }

  /// 获取设备图标
  String get icon {
    switch (deviceType?.toLowerCase()) {
      case 'chiller':
        return '❄️';
      case 'pump':
        return '🔄';
      case 'fan':
        return '🌀';
      case 'ahu':
        return '🌬️';
      case 'fcu':
        return '💨';
      case 'cooling_tower':
        return '🗼';
      case 'boiler':
        return '🔥';
      case 'lighting':
        return '💡';
      case 'elevator':
        return '🛗';
      case 'meter':
        return '⚡';
      case 'sensor':
        return '📡';
      default:
        return '🔧';
    }
  }
}

/// 区域信息（Zone 作为独立实体，与 System 同级）
class ZoneInfo {
  final String id;
  final String name;
  final String? type; // office/public/parking/datacenter_room
  final String? geometryRef;
  final List<String>? tags;
  final int? deviceCount; // 该区域的设备数量（统计字段）

  ZoneInfo({
    required this.id,
    required this.name,
    this.type,
    this.geometryRef,
    this.tags,
    this.deviceCount,
  });

  factory ZoneInfo.fromJson(Map<String, dynamic> json) {
    // 后端可能使用 type 或 zone_type 表示区域类型，这里做兼容
    final dynamic rawType = json['type'] ?? json['zone_type'];
    return ZoneInfo(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '未命名区域',
      type: rawType?.toString(),
      geometryRef: json['geometry_ref']?.toString(),
      tags: (json['tags'] as List<dynamic>?)?.cast<String>(),
      deviceCount: json['device_count'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'type': type,
      'geometry_ref': geometryRef,
      'tags': tags,
      'device_count': deviceCount,
    };
  }

  /// 获取区域类型显示文本
  String get typeText {
    switch (type) {
      case 'office':
        return '办公区';
      case 'public':
        return '公共区';
      case 'parking':
        return '停车场';
      case 'datacenter_room':
        return '机房';
      default:
        return type ?? '未知';
    }
  }
}

/// 区域位置（Device 的位置属性，不是树节点）
class ZoneLocation {
  final String id;
  final String name;

  ZoneLocation({
    required this.id,
    required this.name,
  });

  factory ZoneLocation.fromJson(Map<String, dynamic> json) {
    return ZoneLocation(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '未知位置',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
    };
  }
}

/// 设备创建模型（用于添加设备）
class DeviceCreate {
  final String? zoneId;
  final String? deviceType;
  final String model; // 必填，作为设备名称
  final double? ratedPower;
  final String? serialNo;
  final List<String>? tags;

  DeviceCreate({
    this.zoneId,
    this.deviceType,
    required this.model,
    this.ratedPower,
    this.serialNo,
    this.tags,
  });

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{
      'model': model,
    };
    if (zoneId != null) json['zone_id'] = zoneId;
    if (deviceType != null) json['device_type'] = deviceType;
    if (ratedPower != null) json['rated_power'] = ratedPower;
    if (serialNo != null) json['serial_no'] = serialNo;
    if (tags != null && tags!.isNotEmpty) json['tags'] = tags;
    return json;
  }
}
