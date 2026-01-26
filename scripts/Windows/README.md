# Windows 脚本工具集

**最后更新**: 2026-01-25

---

## 📋 脚本列表

### 服务管理脚本

| 脚本 | 说明 | 运行方式 |
|------|------|----------|
| `启动后端服务.bat` | 启动 FastAPI 后端服务 | 双击运行 |
| `创建数据库.bat` | 初始化 PostgreSQL 数据库 | 双击运行 |
| `启动服务监控.bat` | 启动后端服务监控（英文版） | 双击运行 |
| `start_monitor.bat` | 启动后端服务监控（备用） | 双击运行 |

### 监控脚本

| 脚本 | 说明 | 运行方式 |
|------|------|----------|
| `监控后端服务.py` | 实时监控后端服务状态（增强版） | Python 脚本 |

---

## 🚀 快速开始

### 1. 启动后端服务

**双击运行**:
```
启动后端服务.bat
```

**命令行运行**:
```bash
cd D:\BDC-AI
venv\Scripts\python.exe -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**验证服务**:
```bash
curl http://localhost:8000/api/v1/health
```

### 2. 创建数据库

**双击运行**:
```
创建数据库.bat
```

**说明**:
- 创建 `bdc_ai` 数据库
- 创建 `admin` 用户（密码：password）
- 初始化数据库表结构

### 3. 启动监控

**双击运行**:
```
启动服务监控.bat
# 或
start_monitor.bat
```

**命令行运行**:
```bash
# 基本监控（5秒间隔）
venv\Scripts\python.exe scripts\Windows\监控后端服务.py

# 快速监控（2秒间隔）
venv\Scripts\python.exe scripts\Windows\监控后端服务.py --interval 2

# 监控远程服务
venv\Scripts\python.exe scripts\Windows\监控后端服务.py --url http://100.93.101.76:8000
```

---

## 📊 后端服务监控

### 监控功能

**实时监控**:
- 定期检查后端服务健康状态
- 测试多个 API 端点
- 计算响应时间
- 显示详细通讯信息

**统计数据**:
- 总请求数统计
- 成功/失败计数
- 成功率计算
- 平均响应时间
- 数据传输大小

**历史记录**:
- 保存最近 100 次请求结果
- 显示最近 10 次请求详情
- 最近 60 秒统计分析

### 监控输出示例

```
================================================================================
BDC-AI 后端服务监控
服务地址: http://localhost:8000
开始时间: 2026-01-25 18:25:00
================================================================================

每 5 秒检查一次服务状态...
按 Ctrl+C 停止监控

实时监控统计
--------------------------------------------------------------------------------
总体统计（全部）:
  总请求数: 120
  成功: 118 | 失败: 2
  成功率: 98.3%
  平均响应: 145 ms

最近 60 秒:
  请求数: 12
  成功: 12 | 失败: 0
  成功率: 100.0%

最近 10 次请求详情:
      时间      状态      响应时间         大小      内容
  --------  ------  ----------  ----------  ----------------------------------------
  18:25:00  [OK]      2030ms      0.12KB     status=ok
  18:25:05  [OK]      1987ms      0.15KB     status=ok
  18:25:10  [OK]      2102ms      1.23KB     count=3 items
  18:25:15  [OK]      2055ms      0.08KB     status=ok
  18:25:20  [OK]      1998ms      0.11KB     status=ok
  18:25:25  [OK]      2088ms      0.13KB     status=ok
  18:25:30  [OK]      2034ms      0.14KB     status=ok
  18:25:35  [OK]      2076ms      0.12KB     status=ok
  18:25:40  [OK]      2012ms      0.15KB     status=ok
  18:25:45  [OK]      2055ms      0.13KB     status=ok

当前状态: [正常]
--------------------------------------------------------------------------------
```

### 监控信息说明

| 字段 | 说明 | 示例 |
|------|------|------|
| **时间** | 请求时间戳 | 18:25:00 |
| **状态** | 请求状态（带颜色） | [OK] / [FAIL] |
| **响应时间** | 服务器响应时间 | 2030ms |
| **大小** | 响应数据大小 | 0.12KB |
| **内容** | 响应内容摘要 | `status=ok`, `count=3 items` |

### 内容类型识别

**JSON 响应**:
- `status=ok` - 单字段响应
- `count=3 items` - 列表数据
- `keys=['id', 'name']` - 对象字段

**错误响应**:
- `Connection refused` - 连接被拒绝
- `Timeout` - 请求超时
- `404 Not Found` - 页面未找到

### 服务状态指示

| 状态 | 成功率 | 说明 |
|------|--------|------|
| `[正常]` | ≥ 90% | 服务运行正常 |
| `[不稳定]` | 50-89% | 服务存在问题 |
| `[异常]` | < 50% | 服务严重异常 |

---

## 🛠️ 故障排查

### 问题 1: 后端服务无法启动

**错误**: 端口被占用

**解决方案**:
```bash
# 查找占用进程
netstat -ano | findstr :8000

# 终止进程
taskkill /PID <PID> /F

# 重新启动
启动后端服务.bat
```

### 问题 2: 数据库连接失败

**错误**: `psycopg2.OperationalError`

**解决方案**:
```bash
# 检查 PostgreSQL 服务
# Windows 服务管理器 → PostgreSQL 18

# 测试连接
psql -U admin -d bdc_ai

# 如果密码错误，使用正确的密码
# admin 用户密码: password
# postgres 用户密码: JIM88514
```

### 问题 3: 监控脚本无法运行

**错误**: `ModuleNotFoundError: No module named 'requests'`

**解决方案**:
```bash
# 安装依赖
venv\Scripts\pip.exe install requests

# 或安装所有依赖
venv\Scripts\pip.exe install -r services/backend/requirements.txt
```

### 问题 4: 显示乱码

**错误**: 中文显示为乱码

**解决方案**:
```bash
# 在 PowerShell 中设置编码
chcp 65001

# 或使用英文脚本
start_monitor.bat
```

---

## 📈 监控使用场景

### 场景 1: 本地开发监控

```bash
# 监控本地开发服务器（2秒间隔）
venv\Scripts\python.exe scripts\Windows\监控后端服务.py --interval 2
```

**用途**: 快速发现开发中的问题

### 场景 2: 生产环境监控

```bash
# 通过 Tailscale 监控生产服务器（10秒间隔）
venv\Scripts\python.exe scripts\Windows\监控后端服务.py --url http://100.93.101.76:8000 --interval 10
```

**用途**: 减少服务器负载，长期监控

### 场景 3: 问题排查

```bash
# 使用最短间隔，实时观察（1秒）
venv\Scripts\python.exe scripts\Windows\监控后端服务.py --interval 1
```

**用途**: 实时观察问题发生时的服务状态

---

## 🎯 性能分析

### 识别性能瓶颈

**正常情况**:
```
18:30:00  [OK]      2000ms      0.12KB     status=ok
18:30:05  [OK]      2010ms      0.13KB     status=ok
```

**性能问题**:
```
18:30:10  [OK]      4500ms      0.12KB     status=ok  ← 响应变慢
18:30:15  [OK]      5200ms      0.13KB     status=ok  ← 继续慢
```

**可能原因**:
- 数据库查询慢
- 网络延迟
- 服务器负载高

### 数据量异常检测

**正常情况**:
```
18:35:00  [OK]      2100ms      0.15KB     status=ok
```

**异常情况**:
```
18:35:05  [OK]      3500ms     125.40KB    count=1000 items  ← 数据暴增
```

**可能原因**:
- 未使用分页
- 查询范围过大
- 数据导出操作

---

## 🔧 命令行参数

### 监控脚本参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--url` | http://localhost:8000 | 后端服务地址 |
| `--interval` | 5 | 检查间隔（秒） |

### 使用示例

```bash
# 使用默认配置
python 监控后端服务.py

# 监控本地服务（2秒间隔）
python 监控后端服务.py --interval 2

# 监控 Tailscale 远程服务
python 监控后端服务.py --url http://100.93.101.76:8000 --interval 10

# 监控自定义地址
python 监控后端服务.py --url http://192.168.1.100:8000
```

---

## 📝 脚本维护

### 更新日志

**v2.0 (2026-01-25)**:
- ✅ 添加响应数据大小显示
- ✅ 添加响应内容摘要
- ✅ 改进表格化显示
- ✅ 增强错误信息显示
- ✅ 优化颜色编码
- ✅ 合并说明文档

**v1.0 (2026-01-25)**:
- 基础监控功能
- 成功率统计
- 响应时间统计

### 依赖要求

- Python 3.9+
- requests 库
- 运行中的后端服务

### 安装依赖

```bash
# 安装监控脚本依赖
venv\Scripts\pip.exe install requests

# 或安装完整的后端依赖
venv\Scripts\pip.exe install -r services/backend/requirements.txt
```

---

## 🎓 最佳实践

### 开发环境

```bash
# 使用较短间隔，快速发现问题
python 监控后端服务.py --interval 3
```

### 生产环境

```bash
# 使用较长间隔，减少服务器负载
python 监控后端服务.py --url http://100.93.101.76:8000 --interval 10
```

### 长期监控

```bash
# 将输出保存到日志文件
python 监控后端服务.py > monitor_%date:~0,10%.log 2>&1
```

---

## 📞 相关文档

- **scripts/README.md** - 脚本总览
- **scripts/服务管理/README.md** - 服务管理说明
- **TAILSCALE通讯指南.md** - 远程访问配置
- **部署完成总结.md** - 系统部署文档

---

## 🎯 快速参考

### 常用命令

```bash
# 启动后端
启动后端服务.bat

# 启动监控
启动服务监控.bat

# 测试服务
curl http://localhost:8000/api/v1/health

# 查看端口
netstat -ano | findstr :8000

# 查看进程
tasklist | findstr python
```

### 服务地址

| 环境 | 地址 | 说明 |
|------|------|------|
| **本地** | http://localhost:8000 | 本机访问 |
| **API 文档** | http://localhost:8000/docs | Swagger UI |
| **Tailscale** | http://100.93.101.76:8000 | 远程访问 |

---

**Windows 脚本工具集已整合！** 🎉
