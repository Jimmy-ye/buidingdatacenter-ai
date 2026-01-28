import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';
import '../models/asset.dart';
import '../providers/asset_provider.dart';
import '../providers/app_provider.dart';
import '../services/asset_service.dart';
import '../services/auth_service.dart';

/// 资产快捷视图页
///
/// **支持的视图类型**：
/// - 设备视图：`viewType='device'`, `targetId=device_id`
/// - 系统视图：`viewType='system'`, `targetId=system_id` ⭐
///
/// **核心功能**：
/// - 默认只显示最近 5 张资产图片
/// - 网格展示缩略图
/// - "查看更多"按钮加载历史记录
/// - 快速拍照上传
/// - 删除移动端上传的资产 ⭐
class AssetsPage extends StatefulWidget {
  const AssetsPage({super.key});

  @override
  State<AssetsPage> createState() => _AssetsPageState();
}

/// 资产类型选择结果⭐
class ContentTypeSelection {
  final String type;
  final bool autoRoute;

  ContentTypeSelection({
    required this.type,
    required this.autoRoute,
  });
}

class _AssetsPageState extends State<AssetsPage> {
  final AssetService _assetService = AssetService();
  @override
  void initState() {
    super.initState();
    // 页面初始化时加载资产列表
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadAssets();
    });
  }

  /// 从路由参数获取视图信息
  Map<String, String>? getRouteArgs() {
    final args = ModalRoute.of(context)?.settings.arguments as Map<String, String>?;
    return args;
  }

  /// 加载资产列表
  Future<void> _loadAssets() async {
    final args = getRouteArgs();
    if (args == null) {
      setState(() {
        _errorMessage = '缺少路由参数';
      });
      return;
    }

    final viewTypeStr = args['viewType'] ?? 'device';
    final targetId = args['targetId']!;
    final name = args['name'] ?? '未知';

    setState(() {
      _targetName = name;
      _viewType = viewTypeStr;
    });

    final provider = context.read<AssetProvider>();

    // 转换视图类型
    final viewType = viewTypeStr == 'system'
        ? AssetViewType.system
        : AssetViewType.device;

    await provider.loadAssets(
      targetId: targetId,
      viewType: viewType,
      limit: 5,
      offset: 0,
    );
  }

  /// 刷新资产列表
  Future<void> _refreshAssets() async {
    final provider = context.read<AssetProvider>();
    await provider.refreshAssets();
  }

  /// 加载更多资产
  Future<void> _loadMoreAssets() async {
    final provider = context.read<AssetProvider>();
    await provider.loadMoreAssets();
  }

  /// 上传图片（完整实现）
  ///
  /// 流程：
  /// 1. 显示来源选择对话框（相机/相册）
  /// 2. 请求相应权限
  /// 3. 选择图片
  /// 4. 选择资产类型 + 自动解析选项⭐ 合并
  /// 5. 输入备注（可选）
  /// 6. 上传到后端
  Future<void> _pickAndUploadImage() async {
    // 1. 显示来源选择对话框
    final source = await _showImageSourceDialog();
    if (source == null) return;

    // 2. 请求权限
    final hasPermission = await _requestPermission(source);
    if (!hasPermission) {
      _showError('权限被拒绝，请在设置中开启相机/存储权限');
      return;
    }

    // 3. 选择图片
    final XFile? image = await _pickImage(source);
    if (image == null) return;

    // 4. ⭐ 选择资产类型 + 自动解析选项（合并对话框）
    final selection = await _showContentTypeDialog();
    if (selection == null) return;

    // 5. 输入备注（可选）
    final note = await _showNoteInputDialog();

    // 6. 上传图片
    await _uploadImageWithProgress(
      image.path,
      note,
      selection.type,
      selection.autoRoute,
    );
  }

  /// 显示图片来源选择对话框
  ///
  /// 返回：ImageSource.camera 或 ImageSource.gallery，取消返回 null
  Future<ImageSource?> _showImageSourceDialog() async {
    return showModalBottomSheet<ImageSource>(
      context: context,
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.camera_alt),
                title: const Text('拍照'),
                onTap: () => Navigator.of(context).pop(ImageSource.camera),
              ),
              ListTile(
                leading: const Icon(Icons.photo_library),
                title: const Text('从相册选择'),
                onTap: () => Navigator.of(context).pop(ImageSource.gallery),
              ),
            ],
          ),
        );
      },
    );
  }

  /// 请求相机或存储权限
  ///
  /// 参数：[source] 图片来源
  /// 返回：是否获得权限
  Future<bool> _requestPermission(ImageSource source) async {
    Permission permission;
    if (source == ImageSource.camera) {
      permission = Permission.camera;
    } else {
      // 相册需要存储权限
      if (Platform.isAndroid) {
        // Android 13+ 使用 READ_MEDIA_IMAGES
        permission = Permission.photos;
      } else {
        permission = Permission.photos;
      }
    }

    final status = await permission.request();
    return status.isGranted;
  }

  /// 选择图片
  ///
  /// 参数：[source] 图片来源（相机/相册）
  /// 返回：选择的图片文件，取消返回 null
  Future<XFile?> _pickImage(ImageSource source) async {
    try {
      final ImagePicker picker = ImagePicker();
      final XFile? image = await picker.pickImage(
        source: source,
        imageQuality: 85, // 压缩质量
      );
      return image;
    } catch (e) {
      debugPrint('选择图片失败: $e');
      _showError('选择图片失败: $e');
      return null;
    }
  }

  /// 显示备注输入对话框
  ///
  /// 返回：用户输入的备注（可为空字符串）
  Future<String> _showNoteInputDialog() async {
    final TextEditingController controller = TextEditingController();
    String note = '';

    final result = await showDialog<String>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('添加备注'),
          content: TextField(
            controller: controller,
            decoration: const InputDecoration(
              hintText: '输入工程师备注（可选）',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
            maxLength: 500,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(''),
              child: const Text('跳过'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.of(context).pop(controller.text),
              child: const Text('确定'),
            ),
          ],
        );
      },
    );

    return result ?? '';
  }

  /// 显示资产类型选择对话框（含自动解析选项）⭐
  ///
  /// 返回：ContentTypeSelection 对象（包含类型和自动解析标志），取消返回 null
  Future<ContentTypeSelection?> _showContentTypeDialog() async {
    bool autoRoute = true; // 默认启用自动解析

    return showDialog<ContentTypeSelection>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('选择资产类型'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // 资产类型选项
                  ListTile(
                    leading: const Icon(Icons.warning, color: Colors.orange),
                    title: const Text('现场问题'),
                    subtitle: const Text('记录现场发现的问题'),
                    onTap: () => Navigator.of(context).pop(
                      ContentTypeSelection(type: 'scene_issue', autoRoute: autoRoute),
                    ),
                  ),
                  const Divider(),
                  ListTile(
                    leading: const Icon(Icons.badge, color: Colors.blue),
                    title: const Text('铭牌'),
                    subtitle: const Text('设备铭牌和参数信息'),
                    onTap: () => Navigator.of(context).pop(
                      ContentTypeSelection(type: 'nameplate', autoRoute: autoRoute),
                    ),
                  ),
                  const Divider(),
                  ListTile(
                    leading: const Icon(Icons.speed, color: Colors.green),
                    title: const Text('仪表'),
                    subtitle: const Text('仪表读数和状态'),
                    onTap: () => Navigator.of(context).pop(
                      ContentTypeSelection(type: 'meter', autoRoute: autoRoute),
                    ),
                  ),
                  const Divider(),
                  // ⭐ 自动解析勾选框
                  CheckboxListTile(
                    title: const Text('自动解析'),
                    subtitle: const Text(
                      '上传后自动识别图片内容（OCR、场景分析等）',
                      style: TextStyle(fontSize: 12),
                    ),
                    value: autoRoute,
                    onChanged: (value) {
                      setDialogState(() {
                        autoRoute = value ?? true;
                      });
                    },
                    controlAffinity: ListTileControlAffinity.leading,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 4,
                    ),
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(null),
                  child: const Text('取消'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  /// 上传图片并显示进度
  ///
  /// 参数：
  /// - [filePath] 图片文件路径
  /// - [note] 工程师备注
  /// - [contentType] 资产类型（scene_issue/nameplate/meter）
  /// - [autoRoute] 是否自动解析⭐
  Future<void> _uploadImageWithProgress(
    String filePath,
    String note,
    String contentType,
    bool autoRoute,
  ) async {
    // 显示加载对话框
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return const Center(
          child: CircularProgressIndicator(),
        );
      },
    );

    try {
      // 获取当前项目和目标信息
      final appProvider = context.read<AppProvider>();
      final args = getRouteArgs();

      if (args == null) {
        throw Exception('缺少路由参数');
      }

      final projectId = appProvider.getCurrentProjectId();
      final viewType = args['viewType'] ?? 'device';
      final targetId = args['targetId']!;

      // 准备上传参数
      final deviceId = viewType == 'device' ? targetId : null;
      final systemId = viewType == 'system' ? targetId : null;

      // 调用 Provider 上传
      final provider = context.read<AssetProvider>();
      final asset = await provider.uploadImage(
        projectId: projectId,
        deviceId: deviceId,
        systemId: systemId,
        filePath: filePath,
        note: note.isEmpty ? null : note,
        contentRole: contentType,
        autoRoute: autoRoute, // ⭐ 添加自动解析选项
      );

      // 关闭加载对话框
      if (context.mounted) {
        Navigator.of(context).pop();
      }

      // 显示成功提示
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('上传成功'),
            backgroundColor: Colors.green,
          ),
        );
      }

      // 如果开启了自动解析，则在后台轮询 LLM 结果
      if (autoRoute && asset.id.isNotEmpty && context.mounted) {
        // 不阻塞当前函数，直接在异步任务中轮询
        (() async {
          final detail = await provider.waitForLlmResult(asset.id);

          if (!context.mounted) return;

          if (detail != null &&
              detail.llmSummary != null &&
              detail.llmSummary!.isNotEmpty) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('LLM 分析已完成，可点击照片查看详情'),
                backgroundColor: Colors.blue,
              ),
            );
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('LLM 分析仍在进行中，稍后可在详情中查看'),
                backgroundColor: Colors.grey,
              ),
            );
          }
        })();
      }
    } catch (e) {
      debugPrint('上传失败: $e');

      // 关闭加载对话框
      if (context.mounted) {
        Navigator.of(context).pop();
      }

      // 显示错误提示
      _showError('上传失败: $e');
    }
  }

  /// 显示错误提示
  void _showError(String message) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  /// 进入选择模式⭐
  void _enterSelectionMode() {
    // ⭐ 检查权限
    if (!_canDeleteAssets) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('权限不足：需要 assets:delete 权限'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() {
      _selectionMode = true;
      _selectedAssetIds.clear();
    });
  }

  /// 退出选择模式⭐
  void _exitSelectionMode() {
    setState(() {
      _selectionMode = false;
      _selectedAssetIds.clear();
    });
  }

  /// 切换资产选择状态⭐
  void _toggleAssetSelection(String assetId, bool canDelete) {
    setState(() {
      if (_selectedAssetIds.contains(assetId)) {
        _selectedAssetIds.remove(assetId);
      } else if (canDelete) {
        _selectedAssetIds.add(assetId);
      }
    });
  }

  /// 删除选中的资产⭐
  Future<void> _deleteSelectedAssets() async {
    if (_selectedAssetIds.isEmpty) return;

    // ⭐ 检查权限
    if (!_canDeleteAssets) {
      _exitSelectionMode();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('权限不足：需要 assets:delete 权限'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    // 确认对话框
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('确认删除'),
          content: Text('确定要删除选中的 ${_selectedAssetIds.length} 个资产吗？\n此操作不可撤销。'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('取消'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.of(context).pop(true),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: Colors.white,
              ),
              child: const Text('删除'),
            ),
          ],
        );
      },
    );

    if (confirmed != true) return;

    // 执行删除
    final provider = context.read<AssetProvider>();
    final selectedAssets = provider.assets
        .where((a) => _selectedAssetIds.contains(a.id))
        .toList();

    try {
      final result = await provider.deleteAssets(selectedAssets);
      final successCount = result['successCount'] as int;
      final failedIds = result['failedIds'] as List<String>;

      // 退出选择模式
      _exitSelectionMode();

      // 显示结果
      if (context.mounted) {
        if (failedIds.isEmpty) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('成功删除 $successCount 个资产'),
              backgroundColor: Colors.green,
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('删除 $successCount 个资产，${failedIds.length} 个失败'),
              backgroundColor: Colors.orange,
            ),
          );
        }
      }
    } catch (e) {
      _showError('删除失败: $e');
    }
  }

  /// 查看资产大图
  void _viewAssetDetail(Asset asset) {
    showDialog(
      context: context,
      builder: (context) {
        final media = MediaQuery.of(context);
        return Dialog(
          insetPadding: const EdgeInsets.all(16),
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxHeight: media.size.height * 0.85,
              maxWidth: media.size.width * 0.95,
            ),
            child: FutureBuilder<Asset>(
              future: _assetService.getAssetDetail(asset.id),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: Colors.red),
                        const SizedBox(height: 8),
                        Text(
                          '加载资产详情失败',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 16),
                        TextButton(
                          onPressed: () => Navigator.of(context).pop(),
                          child: const Text('关闭'),
                        ),
                      ],
                    ),
                  );
                }

                final detail = snapshot.data ?? asset;
                final uploadedAt = detail.createdAt.toLocal();
                String two(int v) => v.toString().padLeft(2, '0');
                final uploadTime =
                    '${uploadedAt.year}-${two(uploadedAt.month)}-${two(uploadedAt.day)} ${two(uploadedAt.hour)}:${two(uploadedAt.minute)}';

                return Column(
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // 图片区域
                            AspectRatio(
                              aspectRatio: 3 / 4,
                              child: detail.rawUrl != null
                                  ? InteractiveViewer(
                                      child: Image.network(
                                        detail.rawUrl!,
                                        fit: BoxFit.contain,
                                      ),
                                    )
                                  : Container(
                                      color: Colors.grey[200],
                                      child: const Center(
                                        child: Icon(
                                          Icons.image_not_supported,
                                          size: 64,
                                          color: Colors.grey,
                                        ),
                                      ),
                                    ),
                            ),
                            const SizedBox(height: 8),
                            // 基本信息：标题 + 上传时间
                            Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 8,
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    detail.title,
                                    style: const TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    '上传时间：$uploadTime',
                                    style: const TextStyle(
                                      fontSize: 12,
                                      color: Colors.grey,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            // 备注
                            if (detail.note != null && detail.note!.isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 4,
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text(
                                      '备注',
                                      style: TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      detail.note!,
                                      style: const TextStyle(fontSize: 13),
                                    ),
                                  ],
                                ),
                              ),
                            // AI 解析结果摘要
                            if (detail.llmSummary != null &&
                                detail.llmSummary!.isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 4,
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text(
                                      'AI 解析',
                                      style: TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      detail.llmSummary!,
                                      style: const TextStyle(fontSize: 13),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text('关闭'),
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        );
      },
    );
  }

  String _targetName = '';
  String _viewType = 'device';
  String? _errorMessage;
  bool _selectionMode = false; // ⭐ 选择模式
  final Set<String> _selectedAssetIds = {}; // ⭐ 已选择的资产ID

  /// ⭐ 权限检查：是否有删除资产权限
  bool get _canDeleteAssets {
    final authService = AuthService();
    return authService.hasPermission('assets:delete');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_targetName.isEmpty ? '资产列表' : _targetName),
            if (_viewType == 'system')
              const Text(
                '系统视图',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              )
            else
              const Text(
                '设备视图',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
          ],
        ),
        actions: [
          // ⭐ 选择模式下的操作按钮
          if (_selectionMode) ...[
            // 已选择数量提示
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Text(
                  '已选择 ${_selectedAssetIds.length} 项',
                  style: const TextStyle(fontSize: 14),
                ),
              ),
            ),
            // 批量删除按钮
            if (_selectedAssetIds.isNotEmpty)
              IconButton(
                icon: const Icon(Icons.delete),
                onPressed: _deleteSelectedAssets,
                tooltip: '删除选中项',
              ),
            // 取消选择按钮
            IconButton(
              icon: const Icon(Icons.close),
              onPressed: _exitSelectionMode,
              tooltip: '取消选择',
            ),
          ] else ...[
            // 正常模式下的操作按钮
            // ⭐ 只对有权限用户显示"选择删除"按钮
            if (_canDeleteAssets)
              IconButton(
                icon: const Icon(Icons.check_circle_outline),
                onPressed: _enterSelectionMode,
                tooltip: '批量管理',
              ),
            // 拍照上传按钮
            IconButton(
              icon: const Icon(Icons.camera_alt),
              onPressed: _pickAndUploadImage,
              tooltip: '拍照上传',
            ),
          ],
        ],
      ),
      body: Consumer<AssetProvider>(
        builder: (context, provider, child) {
          /// 错误状态
          if (_errorMessage != null) {
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
                    _errorMessage!,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ],
              ),
            );
          }

          /// 加载状态
          if (provider.isLoading && provider.assets.isEmpty) {
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
                    onPressed: _loadAssets,
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
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.photo_library_outlined,
                      size: 64,
                      color: Colors.grey,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '暂无照片',
                      style:
                          Theme.of(context).textTheme.titleLarge?.copyWith(
                                color: Colors.grey,
                              ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '点击右上角相机图标或下方按钮上传照片',
                      textAlign: TextAlign.center,
                      style:
                          Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: Colors.grey[600],
                              ),
                    ),
                    const SizedBox(height: 32),
                    SizedBox(
                      width: double.infinity,
                      height: 64,
                      child: ElevatedButton.icon(
                        onPressed: _pickAndUploadImage,
                        icon: const Icon(Icons.camera_alt, size: 28),
                        label: const Text(
                          '拍照上传',
                          style: TextStyle(fontSize: 18),
                        ),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 24, vertical: 16),
                          backgroundColor: Colors.blue,
                          foregroundColor: Colors.white,
                          elevation: 4,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }

          /// 资产网格列表
          return RefreshIndicator(
            onRefresh: _refreshAssets,
            child: Column(
              children: [
                /// 头部统计
                Container(
                  padding: const EdgeInsets.all(16),
                  color: Colors.grey[100],
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '最近照片 (共 ${provider.totalCount} 张)',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      if (_viewType == 'system')
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.blue.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.blue, width: 1),
                          ),
                          child: const Text(
                            '系统级',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.blue,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),

                /// ⭐ 拍照上传按钮（放大版）
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  child: SizedBox(
                    width: double.infinity,
                    height: 64, // ⭐ 增加按钮高度
                    child: ElevatedButton.icon(
                      onPressed: _pickAndUploadImage,
                      icon: const Icon(Icons.camera_alt, size: 28), // ⭐ 图标更大
                      label: const Text(
                        '拍照上传',
                        style: TextStyle(fontSize: 18), // ⭐ 字体更大
                      ),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                        backgroundColor: Colors.blue,
                        foregroundColor: Colors.white,
                        elevation: 4, // ⭐ 添加阴影
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12), // ⭐ 圆角
                        ),
                      ),
                    ),
                  ),
                ),

                /// 图片网格
                Expanded(
                  child: GridView.builder(
                    padding: const EdgeInsets.all(8),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 8,
                      mainAxisSpacing: 8,
                      childAspectRatio: 1.0,
                    ),
                    itemCount: provider.assets.length,
                    itemBuilder: (context, index) {
                      final asset = provider.assets[index];
                      final isSelected = _selectedAssetIds.contains(asset.id);
                      final canDelete = asset.source == 'mobile'; // ⭐ 只能删除移动端上传的

                      return AssetGridItem(
                        asset: asset,
                        isSelected: isSelected,
                        canDelete: canDelete,
                        selectionMode: _selectionMode,
                        onTap: () {
                          if (_selectionMode) {
                            _toggleAssetSelection(asset.id, canDelete);
                          } else {
                            _viewAssetDetail(asset);
                          }
                        },
                        onLongPress: canDelete
                            ? () {
                                _enterSelectionMode();
                                _toggleAssetSelection(asset.id, true);
                              }
                            : null,
                      );
                    },
                  ),
                ),

                /// "查看更多"按钮
                if (provider.hasMore)
                  Container(
                    padding: const EdgeInsets.all(16),
                    child: SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: provider.isLoadingMore
                            ? null
                            : _loadMoreAssets,
                        icon: provider.isLoadingMore
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(Icons.expand_more),
                        label: Text(provider.isLoadingMore ? '加载中...' : '查看更多'),
                      ),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}

/// 资产网格项
class AssetGridItem extends StatelessWidget {
  final Asset asset;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;
  final bool isSelected;
  final bool canDelete;
  final bool selectionMode;

  const AssetGridItem({
    super.key,
    required this.asset,
    required this.onTap,
    this.onLongPress,
    this.isSelected = false,
    this.canDelete = false,
    this.selectionMode = false,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      onLongPress: onLongPress,
      borderRadius: BorderRadius.circular(8),
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: Stack(
          fit: StackFit.expand,
          children: [
            /// 图片缩略图
            if (asset.rawUrl != null)
              Image.network(
                asset.rawUrl!,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return Container(
                    color: Colors.grey[200],
                    child: const Icon(
                      Icons.broken_image,
                      size: 48,
                      color: Colors.grey,
                    ),
                  );
                },
                loadingBuilder: (context, child, loadingProgress) {
                  if (loadingProgress == null) return child;
                  return Container(
                    color: Colors.grey[100],
                    child: Center(
                      child: CircularProgressIndicator(
                        value: loadingProgress.expectedTotalBytes != null
                            ? loadingProgress.cumulativeBytesLoaded /
                                loadingProgress.expectedTotalBytes!
                            : null,
                      ),
                    ),
                  );
                },
              )
            else
              Container(
                color: Colors.grey[200],
                child: const Icon(
                  Icons.image,
                  size: 48,
                  color: Colors.grey,
                ),
              ),

            /// ⭐ 选择模式下半透明遮罩
            if (isSelected)
              Container(
                color: Colors.blue.withOpacity(0.3),
              ),

            /// ⭐ 选择指示器（选择模式或已选中时显示）
            if (selectionMode || isSelected)
              Positioned(
                top: 8,
                left: 8,
                child: Container(
                  decoration: BoxDecoration(
                    color: isSelected ? Colors.blue : Colors.white,
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                  ),
                  child: Icon(
                    isSelected ? Icons.check_circle : Icons.circle_outlined,
                    color: isSelected ? Colors.white : Colors.grey,
                    size: 28,
                  ),
                ),
              ),

            /// ⭐ 不可删除标记（非移动端来源）
            if (!canDelete && selectionMode)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(0.9),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text(
                    '不可删除',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),

            /// 时间标签
            Positioned(
              bottom: 0,
              left: 0,
              right: 0,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 8,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.bottomCenter,
                    end: Alignment.topCenter,
                    colors: [
                      Colors.black.withOpacity(0.7),
                      Colors.transparent,
                    ],
                  ),
                ),
                child: Text(
                  asset.formattedTime,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 11,
                  ),
                ),
              ),
            ),

            /// ⭐ 模态标签（选择模式下隐藏）
            if (!selectionMode)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.6),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.image,
                        size: 12,
                        color: Colors.white,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        asset.modality.toUpperCase(),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
