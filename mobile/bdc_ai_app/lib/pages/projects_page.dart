import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/project.dart';
import '../providers/project_provider.dart';
import '../providers/app_provider.dart';
import '../providers/auth_provider.dart';

/// 项目列表页面（首页）
class ProjectsPage extends StatefulWidget {
  const ProjectsPage({super.key});

  @override
  State<ProjectsPage> createState() => _ProjectsPageState();
}

class _ProjectsPageState extends State<ProjectsPage> {
  @override
  void initState() {
    super.initState();
    // 页面初始化时加载项目列表
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadProjects();
    });
  }

  /// 加载项目列表
  Future<void> _loadProjects() async {
    final provider = context.read<ProjectProvider>();
    await provider.loadProjects();
  }

  /// 刷新项目列表
  Future<void> _refreshProjects() async {
    final provider = context.read<ProjectProvider>();
    await provider.refreshProjects();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('工程列表'),
        actions: [
          /// 用户信息菜单
          Consumer<AuthProvider>(
            builder: (context, auth, child) {
              return PopupMenuButton<String>(
                icon: Row(
                  children: [
                    const Icon(Icons.person),
                    const SizedBox(width: 4),
                    Text(
                      auth.user?.displayName ?? '用户',
                      style: const TextStyle(fontSize: 14),
                    ),
                  ],
                ),
                onSelected: (value) async {
                  if (value == 'logout') {
                    // 确认登出
                    final confirmed = await showDialog<bool>(
                      context: context,
                      builder: (context) => AlertDialog(
                        title: const Text('确认登出'),
                        content: const Text('确定要登出吗？'),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.of(context).pop(false),
                            child: const Text('取消'),
                          ),
                          TextButton(
                            onPressed: () => Navigator.of(context).pop(true),
                            child: const Text('确定'),
                          ),
                        ],
                      ),
                    );

                    if (confirmed == true && context.mounted) {
                      await context.read<AuthProvider>().logout();
                      // 登出后自动跳转到登录页
                      if (context.mounted) {
                        Navigator.of(context).pushReplacementNamed('/login');
                      }
                    }
                  }
                },
                itemBuilder: (context) => [
                  PopupMenuItem<String>(
                    value: 'info',
                    enabled: false,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          auth.user?.displayName ?? '用户',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          auth.user?.roleNames.join(' | ') ?? '无角色',
                          style: TextStyle(
                            fontSize: 12,
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const PopupMenuDivider(),
                  const PopupMenuItem<String>(
                    value: 'logout',
                    child: Row(
                      children: [
                        Icon(Icons.logout, size: 20),
                        SizedBox(width: 8),
                        Text('登出'),
                      ],
                    ),
                  ),
                ],
              );
            },
          ),
        ],
      ),
      body: Consumer<ProjectProvider>(
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
                    onPressed: _loadProjects,
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
                    Icons.folder_open,
                    size: 64,
                    color: Colors.grey,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '暂无项目',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: Colors.grey,
                        ),
                  ),
                ],
              ),
            );
          }

          /// 项目列表
          return RefreshIndicator(
            onRefresh: _refreshProjects,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: provider.projects.length,
              itemBuilder: (context, index) {
                final project = provider.projects[index];
                return ProjectCard(
                  project: project,
                  onTap: () => _openProject(project),
                );
              },
            ),
          );
        },
      ),
    );
  }

  /// 打开项目详情（跳转到工程结构树页）
  void _openProject(Project project) {
    // 保存当前项目
    context.read<AppProvider>().selectProject(project);

    // 跳转到工程结构树页
    Navigator.pushNamed(context, '/structure');
  }
}

/// 项目卡片组件
class ProjectCard extends StatelessWidget {
  final Project project;
  final VoidCallback onTap;

  const ProjectCard({
    super.key,
    required this.project,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              /// 项目名称
              Text(
                project.name,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 8),

              /// 客户名称
              if (project.client != null) ...[
                Row(
                  children: [
                    const Icon(
                      Icons.business,
                      size: 16,
                      color: Colors.grey,
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        project.client!,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.grey[700],
                            ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
              ],

              /// 项目地址
              if (project.address != null) ...[
                Row(
                  children: [
                    const Icon(
                      Icons.location_on,
                      size: 16,
                      color: Colors.grey,
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        project.address!,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.grey[700],
                            ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
              ],

              /// 状态标签
              Row(
                children: [
                  _buildStatusChip(context, project.status),
                  const Spacer(),
                  const Icon(
                    Icons.chevron_right,
                    color: Colors.grey,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// 构建状态标签
  Widget _buildStatusChip(BuildContext context, String status) {
    Color color;
    String label;

    switch (status) {
      case 'planning':
        color = Colors.orange;
        label = '规划中';
        break;
      case 'active':
        color = Colors.green;
        label = '进行中';
        break;
      case 'completed':
        color = Colors.blue;
        label = '已完成';
        break;
      case 'archived':
        color = Colors.grey;
        label = '已归档';
        break;
      default:
        color = Colors.grey;
        label = status;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color, width: 1),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
