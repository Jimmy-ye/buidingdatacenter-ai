import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:provider/provider.dart';
import 'providers/app_provider.dart';
import 'providers/project_provider.dart';
import 'providers/structure_provider.dart';
import 'providers/asset_provider.dart';
import 'pages/projects_page.dart';
import 'pages/structure_tree_page.dart';
import 'pages/assets_page.dart';

void main() {
  runApp(const BdcAiApp());
}

/// BDC-AI 移动端应用
class BdcAiApp extends StatelessWidget {
  const BdcAiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
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
        routes: {
          /// 项目列表页（首页）
          '/': (context) => const ProjectsPage(),

          /// 工程结构树页（Building → System → Device）
          '/structure': (context) => const StructureTreePage(),

          /// 资产快捷视图页（支持设备级和系统级）⭐
          '/assets': (context) => const AssetsPage(),
        },
      ),
    );
  }
}
