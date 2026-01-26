import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:provider/provider.dart';

import 'config/app_config.dart';
import 'providers/auth_provider.dart';
import 'providers/app_provider.dart';
import 'providers/project_provider.dart';
import 'providers/structure_provider.dart';
import 'providers/asset_provider.dart';
import 'pages/login_page.dart';
import 'pages/projects_page.dart';
import 'pages/structure_tree_page.dart';
import 'pages/assets_page.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 初始化认证服务
  final authProvider = AuthProvider();
  await authProvider.initialize();

  runApp(BdcAiApp(authProvider: authProvider));
}

/// BDC-AI 移动端应用
class BdcAiApp extends StatelessWidget {
  final AuthProvider authProvider;

  const BdcAiApp({
    super.key,
    required this.authProvider,
  });

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        /// 认证状态（必须首先提供）
        ChangeNotifierProvider.value(value: authProvider),

        /// 应用全局状态
        ChangeNotifierProvider(create: (_) => AppProvider()),

        /// 项目列表状态
        ChangeNotifierProvider(create: (_) => ProjectProvider()),

        /// 工程结构状态
        ChangeNotifierProvider(create: (_) => StructureProvider()),

        /// 资产列表状态
        ChangeNotifierProvider(create: (_) => AssetProvider()),
      ],
      child: MaterialApp(
        title: 'BDC-AI 移动端',
        debugShowCheckedModeBanner: false,

        /// 主题配置
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.blue,
            brightness: Brightness.light,
          ),
          appBarTheme: const AppBarTheme(
            centerTitle: true,
            elevation: 0,
          ),
          cardTheme: const CardThemeData(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(12)),
            ),
          ),
        ),

        /// 路由配置
        initialRoute: '/',
        onGenerateRoute: (settings) {
          // 根据认证状态决定路由
          switch (settings.name) {
            case '/':
              // 主页：检查认证状态
              return MaterialPageRoute(
                builder: (context) {
                  return Consumer<AuthProvider>(
                    builder: (context, auth, child) {
                      // 如果正在加载，显示加载页
                      if (auth.isLoading || auth.authStatus == AuthStatus.unknown) {
                        return const _SplashScreen();
                      }

                      // 如果已认证，显示主页
                      if (auth.isAuthenticated) {
                        return const ProjectsPage();
                      }

                      // 未认证，显示登录页
                      return const LoginPage();
                    },
                  );
                },
              );

            case '/login':
              // 登录页
              return MaterialPageRoute(
                builder: (context) => const LoginPage(),
              );

            case '/structure':
              // 工程结构页（需要认证）
              return MaterialPageRoute(
                builder: (context) {
                  return Consumer<AuthProvider>(
                    builder: (context, auth, child) {
                      if (!auth.isAuthenticated) {
                        // 未认证，重定向到登录页
                        Future.microtask(() {
                          Navigator.of(context).pushReplacementNamed('/login');
                        });
                        return const SizedBox.shrink();
                      }
                      return const StructureTreePage();
                    },
                  );
                },
              );

            case '/assets':
              // 资产页（需要认证）
              return MaterialPageRoute(
                builder: (context) {
                  return Consumer<AuthProvider>(
                    builder: (context, auth, child) {
                      if (!auth.isAuthenticated) {
                        // 未认证，重定向到登录页
                        Future.microtask(() {
                          Navigator.of(context).pushReplacementNamed('/login');
                        });
                        return const SizedBox.shrink();
                      }
                      return const AssetsPage();
                    },
                  );
                },
              );

            default:
              // 未知路由，返回主页
              return MaterialPageRoute(
                builder: (context) => const ProjectsPage(),
              );
          }
        },
      ),
    );
  }
}

/// 启动加载页面
class _SplashScreen extends StatelessWidget {
  const _SplashScreen();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.energy_savings_leaf,
              size: 80,
              color: Colors.green,
            ),
            SizedBox(height: 24),
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('正在加载...'),
          ],
        ),
      ),
    );
  }
}
