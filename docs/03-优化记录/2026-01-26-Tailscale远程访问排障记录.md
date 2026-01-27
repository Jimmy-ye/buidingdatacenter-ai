# 2026-01-26 Tailscale 远程访问排障记录

## 一、背景与目标

- **服务器**：`desktop-bfpk00r`（Windows 11），安装 Tailscale，Tailscale IP：`100.93.101.76`。
- **客户端**：`laptop-0fcpukmh`（Windows 11），Tailscale IP：`100.115.106.115`。
- **后端**：FastAPI + Uvicorn，监听端口 `8000`：
  - 本地访问：`http://localhost:8000`
  - Tailscale 访问：`http://100.93.101.76:8000`
- **目标**：
  - 让 PC-UI、移动端等客户端通过 **Tailscale** 稳定访问后端：
    - `http://100.93.101.76:8000/api/v1/...`
  - 解决“能 `tailscale ping`，但 `TCP 8000` 连不上的问题”。

---

## 二、初始症状

### 1. 客户端测试脚本报错

运行客户端测试脚本：

```bash
python scripts\Windows\test_tailscale_client.py
```

输出（节选）：

```text
测试 1: TCP 端口连接 (8000)
[INFO] 目标: 100.93.101.76:8000
[FAIL] TCP 端口 8000 无法连接
[ERROR] TCP 端口无法连接，停止测试
```

### 2. curl 测试失败

在客户端上：

```powershell
curl http://100.93.101.76:8000/
# 或
curl http://100.93.101.76:8000/api/v1/health/
```

报错：

```text
curl : 无法连接到远程服务器
WebException: Unable to connect to the remote server
```

### 3. Tailscale 状态正常

```powershell
tailscale status
```

输出包含：

```text
100.115.106.115  laptop-0fcpukmh    ...
100.93.101.76    desktop-bfpk00r    ...
```

```powershell
tailscale ping 100.93.101.76
```

多次返回：

```text
pong from desktop-bfpk00r (100.93.101.76) via DERP(hkg) in 7x ms
```

> 结论：**Tailscale 隧道本身是通的**，但 TCP 8000 无法建立连接。

---

## 三、逐步诊断过程

### 1. 确认后端进程是否正常（服务器上）

在服务器 `desktop-bfpk00r` 上：

```powershell
# 1）本地回环
curl http://localhost:8000/api/v1/health/

# 2）通过本机 Tailscale IP
curl http://100.93.101.76:8000/api/v1/health/
```

实际结果：两条命令均返回：

```json
{"status":"ok"}
```

> 说明：FastAPI 后端在 8000 端口上 **工作正常**，并且服务器本机通过 Tailscale IP 访问自己也是正常的。

### 2. 检查客户端到服务器的 TCP 链路

在客户端 `laptop-0fcpukmh` 上执行：

```powershell
Test-NetConnection 100.93.101.76 -Port 8000
```

初始输出：

```text
ComputerName     : 100.93.101.76
RemoteAddress    : 100.93.101.76
RemotePort       : 8000
InterfaceAlias   : Tailscale
SourceAddress    : 100.115.106.115
PingSucceeded    : False
TcpTestSucceeded : False
```

同时查看路由：

```powershell
Get-NetRoute -DestinationPrefix 100.93.101.76/32
```

输出：

```text
ifIndex DestinationPrefix  NextHop
9       100.93.101.76/32   0.0.0.0
```

> 结论：
>
> - 流量确实通过 **Tailscale 网卡**（InterfaceAlias = `Tailscale`）发出；
> - 但 `TcpTestSucceeded=False`，说明 TCP 在到达服务器前的某一层被阻断。

### 3. 检查服务器防火墙（Windows Defender）

在服务器上添加 8000 入站规则：

```powershell
New-NetFirewallRule `
  -DisplayName "BDC-AI API 8000 (Any)" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 8000 `
  -Action Allow `
  -Profile Any
```

再次在客户端上测试，仍然：

```text
TcpTestSucceeded : False
curl : 无法连接到远程服务器
```

> 结论：**Windows Defender 规则本身不是唯一问题**，还有其它安全组件在拦截。

### 4. 关键实验：关闭服务器第三方防护软件

在服务器上临时关闭/退出第三方防护（例如校园网客户端/安全套件），保持：

- 后端进程仍在运行；
- Windows Defender 规则保留不变。

然后在客户端再次测试：

```powershell
curl http://100.93.101.76:8000/api/v1/health/
Test-NetConnection 100.93.101.76 -Port 8000
python scripts\Windows\test_tailscale_client.py
```

观察结果：

- `curl` 返回：`{"status":"ok"}`；
- `Test-NetConnection` 显示：`TcpTestSucceeded : True`；
- `test_tailscale_client.py` 所有测试项通过。

> 关键结论：
>
> - **Tailscale + 后端 + Windows 防火墙全部正常**；
> - 真正拦截来自 Tailscale 的 TCP 8000 的，是 **服务器上的第三方防护软件**。

---

## 四、最终解决方案

### 1. 保留 Windows 防火墙 8000 入站规则

保留之前添加的规则（可通过 `Get-NetFirewallRule` 查看）：

```powershell
New-NetFirewallRule `
  -DisplayName "BDC-AI API 8000 (Any)" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 8000 `
  -Action Allow `
  -Profile Any
```

### 2. 在第三方防护软件中添加后端进程白名单

> 目标：
>
> 即使 **重新开启防护软件**，也允许来自 Tailscale 接口的 8000 端口访问后端。

通用做法（以服务器上的 `venv311` 为例）：

1. 打开防护软件主界面。
2. 找到类似“**程序控制 / 应用控制 / 信任程序 / 防火墙**”的模块。
3. 将以下程序添加到“信任/允许访问网络”的列表：
   - `D:\BDC-AI\venv311\Scripts\python.exe`
   - （如存在）`D:\BDC-AI\venv311\Scripts\uvicorn.exe`
4. 权限建议：
   - 允许 **入站 + 出站** 网络连接；
   - 协议：至少 TCP；
   - 端口：可指定 TCP 8000，或全部端口（仅限该程序）。

之后重新开启防护软件，再次在客户端验证：

```powershell
curl http://100.93.101.76:8000/api/v1/health/
Test-NetConnection 100.93.101.76 -Port 8000
python scripts\Windows\test_tailscale_client.py
```

当：

- `curl` 稳定返回 `{"status":"ok"}`；
- `TcpTestSucceeded` 长期为 True；
- 自动化测试脚本全部 PASS；

即可认为 **Tailscale → 服务器后端链路已稳定打通**。

---

## 五、客户端配置收尾（PC-UI / 移动端）

### 1. PC-UI（NiceGUI）

PC-UI 使用 `Config.get_api_base_url()` 读取后端 API 地址：

```python
# desktop/nicegui_app/config.py
class Config:
    @staticmethod
    def get_api_base_url() -> str:
        api_url = os.getenv('BDC_API_URL')
        if api_url:
            return api_url
        # 默认开发环境
        return 'http://127.0.0.1:8000/api/v1'
```

在 **每台运行 PC-UI 的客户端** 上设置：

```powershell
$env:BDC_API_URL="http://100.93.101.76:8000/api/v1"
```

然后启动/重启 PC-UI（例如）：

```powershell
python tests\test_pc_app.py
# 或 scripts\start_pcui.bat
```

验证：

- 登录 admin/account 成功；
- `/api/v1/projects/`、`/api/v1/assets/` 等接口正常返回。

### 2. 移动端（Flutter App）

临时验证可以直接改 `AuthService` 的 baseUrl：

```dart
authService = AuthService(
  baseUrl: 'http://100.93.101.76:8000',
);
```

长期建议：

- 使用 `--dart-define` 或配置文件，将后端地址抽出为环境配置；
- 开发/测试环境统一使用 `http://100.93.101.76:8000`。

---

## 六、通用排障模板（今后遇到类似问题可复用）

### 步骤 1：确认后端服务是否正常

在 **服务器本机**：

```powershell
curl http://localhost:8000/api/v1/health/
```

- 若失败：优先检查后端启动命令、依赖、日志。

### 步骤 2：确认 Tailscale IP 访问

仍在服务器本机：

```powershell
curl http://<tailscale_ip>:8000/api/v1/health/
```

- 若 `localhost` OK 但 Tailscale IP 不 OK：
  - 检查监听地址是否 `0.0.0.0`；
  - 检查本机防火墙/防护软件是否拦截虚拟网卡流量。

### 步骤 3：在客户端检查 Tailscale 隧道

```powershell
tailscale status
tailscale ping <tailscale_ip>
```

- 若看不到服务器或 ping 不通：
  - 检查两端是否登录同一 tailnet；
  - 检查 tailnet ACL 配置。

### 步骤 4：在客户端检查 TCP 端口

```powershell
Test-NetConnection <tailscale_ip> -Port 8000
```

- `InterfaceAlias` 应为 `Tailscale`；
- `TcpTestSucceeded` 为 False 时，再回头看：
  - 服务器防火墙（Windows Defender + 第三方防护）；
  - 是否有安全软件/校园网客户端在本机做了出入站控制。

### 步骤 5：使用专用测试脚本回归

例如：

```bash
python scripts\Windows\test_tailscale_client.py
```

- 自动测试：Tailscale 状态、TCP 端口、健康检查、认证登录；
- 所有项 PASS 后，可以认为链路已稳定。

---

## 七、小结

- **问题本质**：
  - Tailscale 隧道 & 后端服务本身都正常；
  - 服务器上的第三方防护软件拦截了来自 Tailscale 的 TCP 8000 连接。
- **解决方案**：
  - 在 Windows 防火墙中放行 TCP 8000；
  - 在第三方防护软件中为 `python.exe`/`uvicorn.exe` 添加网络访问白名单；
  - 客户端通过 Tailscale IP 访问后端 API。
- **结果**：
  - `curl`、`Test-NetConnection`、`test_tailscale_client.py` 全部通过；
  - PC-UI / 移动端可以通过 `http://100.93.101.76:8000` 稳定访问后端。
