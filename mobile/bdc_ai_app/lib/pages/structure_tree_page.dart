import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/structure.dart';
import '../providers/structure_provider.dart';
import '../providers/app_provider.dart';
import '../providers/asset_provider.dart';
import '../services/auth_service.dart';

/// 工程结构树页面
///
/// **正确的层级关系**：
/// - Building → System → Device（主树，System 是 Device 的主归属）
/// - Building → Zone（与 System 同级，位置属性）
/// - System 是资产的主挂接点
///
/// **核心交互**：
/// - 点击 Device → 跳转到设备资产页（device_id）
/// - 点击 System → 跳转到系统资产页（system_id）⭐
class StructureTreePage extends StatefulWidget {
  const StructureTreePage({super.key});

  @override
  State<StructureTreePage> createState() => _StructureTreePageState();
}

class _StructureTreePageState extends State<StructureTreePage> {
  @override
  void initState() {
    super.initState();
    // 页面初始化时加载工程结构树
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadStructureTree();
    });
  }

  /// 加载工程结构树
  Future<void> _loadStructureTree() async {
    final appProvider = context.read<AppProvider>();

    // 如果尚未选择项目，则不发起请求，避免抛出 StateError
    if (!appProvider.hasProject) {
      debugPrint('当前未选择项目，跳过工程结构树加载');
      return;
    }

    final projectId = appProvider.getCurrentProjectId();
    final provider = context.read<StructureProvider>();
    await provider.loadStructureTree(projectId);
  }

  /// 刷新工程结构树
  Future<void> _refreshStructureTree() async {
    final appProvider = context.read<AppProvider>();
    final projectId = appProvider.getCurrentProjectId();

    final provider = context.read<StructureProvider>();
    await provider.refreshStructureTree(projectId);
  }

  /// 打开设备资产页
  void _openDeviceAssets(Device device) {
    // 清空之前的资产数据
    context.read<AssetProvider>().clearAssets();

    // 跳转到资产列表页（设备视图）
    Navigator.pushNamed(
      context,
      '/assets',
      arguments: {
        'viewType': 'device',
        'targetId': device.id,
        'name': device.name,
      },
    );
  }

  /// 打开系统资产页 ⭐
  void _openSystemAssets(System system) {
    // 清空之前的资产数据
    context.read<AssetProvider>().clearAssets();

    // 跳转到资产列表页（系统视图）
    Navigator.pushNamed(
      context,
      '/assets',
      arguments: {
        'viewType': 'system',
        'targetId': system.id,
        'name': system.name,
      },
    );
  }

  /// 显示添加设备对话框
  void _showAddDeviceDialog(System system) {
    final authService = AuthService();

    // 检查权限
    if (!authService.hasPermission('structures:create')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('权限不足：需要 structures:create 权限'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    showDialog(
      context: context,
      builder: (context) => AddDeviceDialog(system: system),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Consumer<AppProvider>(
          builder: (context, appProvider, child) {
            final project = appProvider.currentProject;
            return Text(project?.name ?? '工程结构');
          },
        ),
        actions: [
          /// 展开/折叠全部按钮
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert),
            onSelected: (value) {
              final provider = context.read<StructureProvider>();
              if (value == 'expand') {
                provider.expandAll();
              } else if (value == 'collapse') {
                provider.collapseAll();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'expand',
                child: Row(
                  children: [
                    Icon(Icons.unfold_more, size: 20),
                    SizedBox(width: 8),
                    Text('展开全部'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'collapse',
                child: Row(
                  children: [
                    Icon(Icons.compress, size: 20),
                    SizedBox(width: 8),
                    Text('折叠全部'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: Consumer<StructureProvider>(
        builder: (context, provider, child) {
          /// 加载状态
          if (provider.isLoading) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          /// 错误状态
          if (provider.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.error_outline,
                    size: 64,
                    color: Colors.red,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    provider.errorMessage ?? '加载失败',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: _loadStructureTree,
                    icon: const Icon(Icons.refresh),
                    label: const Text('重试'),
                  ),
                ],
              ),
            );
          }

          /// 空列表状态
          if (provider.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.account_tree,
                    size: 64,
                    color: Colors.grey,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '暂无工程结构',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: Colors.grey,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '请先在后端添加建筑和系统',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.grey[600],
                        ),
                  ),
                ],
              ),
            );
          }

          /// 工程结构树
          return RefreshIndicator(
            onRefresh: _refreshStructureTree,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: provider.buildings.length,
              itemBuilder: (context, index) {
                final building = provider.buildings[index];
                return BuildingNode(
                  building: building,
                  isExpanded: provider.isBuildingExpanded(building.id),
                  onToggle: () => provider.toggleBuilding(building.id),
                  onDeviceTap: _openDeviceAssets,
                  onSystemTap: _openSystemAssets,
                  provider: provider,
                  onAddDevice: _showAddDeviceDialog,
                );
              },
            ),
          );
        },
      ),
    );
  }
}

/// 楼栋节点
class BuildingNode extends StatelessWidget {
  final Building building;
  final bool isExpanded;
  final VoidCallback onToggle;
  final Function(Device) onDeviceTap;
  final Function(System) onSystemTap;
  final StructureProvider provider;
  final Function(System)? onAddDevice; // ⭐ 添加设备回调

  const BuildingNode({
    super.key,
    required this.building,
    required this.isExpanded,
    required this.onToggle,
    required this.onDeviceTap,
    required this.onSystemTap,
    required this.provider,
    this.onAddDevice,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        children: [
          /// 楼栋标题
          ListTile(
            leading: Icon(
              isExpanded ? Icons.expand_more : Icons.chevron_right,
              color: Theme.of(context).primaryColor,
            ),
            title: Text(
              building.name,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: _buildSubtitle(),
            trailing: _buildTrailing(),
            onTap: onToggle,
          ),

          /// 系统列表（与 zones 同级）⭐
          if (isExpanded && building.systems.isNotEmpty)
            ...building.systems.map((system) {
              return SystemNode(
                system: system,
                isExpanded: provider.isSystemExpanded(system.id),
                onToggle: () => provider.toggleSystem(system.id),
                onDeviceTap: onDeviceTap,
                onSystemTap: onSystemTap,
                onAddDevice: onAddDevice,
              );
            }),

          /// 区域列表（与 systems 同级，不含设备）⭐
          if (isExpanded && building.zones.isNotEmpty)
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Divider(),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    child: Text(
                      '区域（${building.zones.length}）',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  ...building.zones.map((zone) {
                    return ZoneInfoTile(zone: zone);
                  }),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget? _buildSubtitle() {
    final parts = <String>[];
    if (building.systems.isNotEmpty) {
      parts.add('${building.systems.length} 个系统');
    }
    if (building.zones.isNotEmpty) {
      parts.add('${building.zones.length} 个区域');
    }
    if (building.usageType != null) {
      parts.add(building.usageType!.split('_').join(' ')); // office -> office
    }
    if (parts.isEmpty) {
      return null;
    }
    return Text(parts.join(' · '));
  }

  Widget? _buildTrailing() {
    int count = building.systems.length + building.zones.length;
    if (count == 0) return null;
    return Text(
      '$count',
      style: TextStyle(
        fontSize: 16,
        color: Colors.grey[600],
        fontWeight: FontWeight.bold,
      ),
    );
  }
}

/// 系统节点（Building 的直接子节点）⭐
class SystemNode extends StatelessWidget {
  final System system;
  final bool isExpanded;
  final VoidCallback onToggle;
  final Function(Device) onDeviceTap;
  final Function(System) onSystemTap;
  final Function(System)? onAddDevice; // ⭐ 添加设备回调

  const SystemNode({
    super.key,
    required this.system,
    required this.isExpanded,
    required this.onToggle,
    required this.onDeviceTap,
    required this.onSystemTap,
    this.onAddDevice,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Card(
        color: Colors.grey[50],
        child: Column(
          children: [
            /// 系统标题（可点击查看系统级资产）⭐
            InkWell(
              onTap: () => onSystemTap(system),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                child: Row(
                  children: [
                    Icon(
                      isExpanded ? Icons.expand_more : Icons.chevron_right,
                      size: 20,
                      color: Theme.of(context).primaryColor.withOpacity(0.7),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      system.icon,
                      style: const TextStyle(fontSize: 18),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            system.name,
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                              color: onSystemTap != null
                                  ? Theme.of(context).primaryColor
                                  : Colors.black87,
                            ),
                          ),
                          if (system.type != system.name && system.type.isNotEmpty)
                            Text(
                              system.typeText,
                              style: TextStyle(
                                fontSize: 11,
                                color: Colors.grey[600],
                              ),
                            ),
                        ],
                      ),
                    ),
                    /// ⭐ 添加设备按钮
                    if (onAddDevice != null)
                      IconButton(
                        icon: const Icon(Icons.add_circle_outline),
                        onPressed: () => onAddDevice?.call(system),
                        tooltip: '添加设备',
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints(),
                        iconSize: 20,
                      ),
                    if (system.devices.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.blue.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: Colors.blue, width: 1),
                        ),
                        child: Text(
                          '${system.devices.length}',
                          style: const TextStyle(fontSize: 11, color: Colors.blue),
                        ),
                      ),
                    const SizedBox(width: 8),
                    Icon(
                      Icons.chevron_right,
                      size: 18,
                      color: Theme.of(context).primaryColor.withOpacity(0.5),
                    ),
                  ],
                ),
              ),
            ),

            /// 设备列表（归属于该 System）⭐
            if (isExpanded && system.devices.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(left: 36, right: 8, bottom: 8),
                child: Column(
                  children: system.devices.map((device) {
                    return DeviceListItem(
                      device: device,
                      onTap: () => onDeviceTap(device),
                    );
                  }).toList(),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// 设备列表项（归属于 System，位于 Zone）
class DeviceListItem extends StatelessWidget {
  final Device device;
  final VoidCallback onTap;

  const DeviceListItem({
    super.key,
    required this.device,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          border: Border(
            left: BorderSide(
              color: Colors.grey[300]!,
              width: 2,
            ),
          ),
        ),
        child: Row(
          children: [
            Text(
              device.icon,
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    device.name,
                    style: const TextStyle(fontSize: 13),
                  ),
                  if (device.model != null || device.deviceType != null)
                    Row(
                      children: [
                        if (device.deviceType != null)
                          Text(
                            device.deviceTypeText,
                            style: TextStyle(
                              fontSize: 11,
                              color: Colors.grey[600],
                            ),
                          ),
                        if (device.deviceType != null && device.model != null)
                          const Text(' · ', style: TextStyle(fontSize: 11, color: Colors.grey)),
                        if (device.model != null)
                          Expanded(
                            child: Text(
                              device.model!,
                              style: TextStyle(
                                fontSize: 11,
                                color: Colors.grey[600],
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                      ],
                    ),
                  /// Zone 位置信息（属性，不是树节点）⭐
                  if (device.zone != null)
                    Row(
                      children: [
                        const Icon(
                          Icons.location_on,
                          size: 10,
                          color: Colors.grey,
                        ),
                        const SizedBox(width: 2),
                        Text(
                          device.zone!.name,
                          style: const TextStyle(
                            fontSize: 10,
                            color: Colors.grey,
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ),
            if (device.assetCount != null && device.assetCount! > 0)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.green, width: 1),
                ),
                child: Text(
                  '${device.assetCount}',
                  style: const TextStyle(fontSize: 11, color: Colors.green),
                ),
              ),
            const SizedBox(width: 8),
            Icon(
              Icons.chevron_right,
              size: 16,
              color: Theme.of(context).primaryColor,
            ),
          ],
        ),
      ),
    );
  }
}

/// 区域信息卡片（与 System 同级，不含设备）
class ZoneInfoTile extends StatelessWidget {
  final ZoneInfo zone;

  const ZoneInfoTile({
    super.key,
    required this.zone,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.grey[100],
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey[300]!, width: 1),
        ),
        child: Row(
          children: [
            const Icon(
              Icons.place,
              size: 16,
              color: Colors.grey,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    zone.name,
                    style: const TextStyle(fontSize: 13),
                  ),
                  if (zone.type != null)
                    Text(
                      zone.typeText,
                      style: TextStyle(
                        fontSize: 11,
                        color: Colors.grey[600],
                      ),
                    ),
                ],
              ),
            ),
            if (zone.deviceCount != null && zone.deviceCount! > 0)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.orange.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.orange, width: 1),
                ),
                child: Text(
                  '${zone.deviceCount} 设备',
                  style: const TextStyle(fontSize: 10, color: Colors.orange),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// 添加设备对话框
class AddDeviceDialog extends StatefulWidget {
  final System system;

  const AddDeviceDialog({
    super.key,
    required this.system,
  });

  @override
  State<AddDeviceDialog> createState() => _AddDeviceDialogState();
}

class _AddDeviceDialogState extends State<AddDeviceDialog> {
  final _formKey = GlobalKey<FormState>();
  final _modelController = TextEditingController();
  final _deviceTypeController = TextEditingController();
  final _ratedPowerController = TextEditingController();
  final _serialNoController = TextEditingController();
  final _tagsController = TextEditingController();

  bool _isLoading = false;

  @override
  void dispose() {
    _modelController.dispose();
    _deviceTypeController.dispose();
    _ratedPowerController.dispose();
    _serialNoController.dispose();
    _tagsController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final appProvider = context.read<AppProvider>();
      final structureProvider = context.read<StructureProvider>();
      final projectId = appProvider.getCurrentProjectId();

      // 解析标签
      final tags = _tagsController.text.isNotEmpty
          ? _tagsController.text.split(',').map((e) => e.trim()).toList()
          : null;

      // 创建设备请求
      final deviceCreate = DeviceCreate(
        model: _modelController.text.trim(),
        deviceType: _deviceTypeController.text.trim().isEmpty
            ? null
            : _deviceTypeController.text.trim(),
        ratedPower: _ratedPowerController.text.trim().isEmpty
            ? null
            : double.tryParse(_ratedPowerController.text.trim()),
        serialNo: _serialNoController.text.trim().isEmpty
            ? null
            : _serialNoController.text.trim(),
        tags: tags,
      );

      // 调用 Provider 创建设备
      await structureProvider.createDevice(
        widget.system.id,
        deviceCreate,
        projectId,
      );

      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('设备创建成功'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('创建失败: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(
        children: [
          const Icon(Icons.add_circle_outline),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('添加设备'),
                Text(
                  '系统: ${widget.system.name}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 型号（必填）
              TextFormField(
                controller: _modelController,
                decoration: const InputDecoration(
                  labelText: '型号 *',
                  hintText: '例如: FCU-03',
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return '请输入设备型号';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // 设备类型（可选）
              TextFormField(
                controller: _deviceTypeController,
                decoration: const InputDecoration(
                  labelText: '设备类型',
                  hintText: '例如: fcu, chiller, pump',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),

              // 额定功率（可选）
              TextFormField(
                controller: _ratedPowerController,
                decoration: const InputDecoration(
                  labelText: '额定功率（kW）',
                  hintText: '例如: 5.5',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),

              // 序列号（可选）
              TextFormField(
                controller: _serialNoController,
                decoration: const InputDecoration(
                  labelText: '序列号',
                  hintText: '设备序列号（可选）',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),

              // 标签（可选）
              TextFormField(
                controller: _tagsController,
                decoration: const InputDecoration(
                  labelText: '标签',
                  hintText: '多个标签用逗号分隔',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
          child: const Text('取消'),
        ),
        ElevatedButton(
          onPressed: _isLoading ? null : _submit,
          child: _isLoading
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('创建'),
        ),
      ],
    );
  }
}
