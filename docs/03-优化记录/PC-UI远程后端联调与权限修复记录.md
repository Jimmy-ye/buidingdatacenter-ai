# PC-UI 远程后端联调与权限修复记录

> 日期：2026-01-26  
> 相关模块：desktop/nicegui_app（PC-UI）、services/backend（FastAPI 后端）

---

## 1. 开发环境与依赖安装

### 1.1 虚拟环境激活

```powershell
& "d:/Huawei Files/华为家庭存储/Programs/program-bdc-ai/.venv/Scripts/Activate.ps1"
(.venv) cd "D:\Huawei Files\华为家庭存储\Programs\program-bdc-ai"
```

### 1.2 解决中文 Windows 下 pip 读取 requirements 的编码问题

现象：安装 `requirements.txt` 报错：

```text
UnicodeDecodeError: 'gbk' codec can't decode byte ... illegal multibyte sequence
```

处理方法：在当前 PowerShell 会话中启用 UTF-8 读取模式，再执行安装命令。

```powershell
$env:PYTHONUTF8 = "1"
python -m pip install -r desktop/nicegui_app/requirements.txt
python -m pip install -r services/backend/requirements.txt   # 如需安装后端依赖
```

---

## 2. PC-UI 启动与远程后端配置

### 2.1 指定远程后端 API 地址

```powershell
$env:BDC_API_URL = "http://<后端IP>:8000/api/v1"
```

PC-UI 通过 `desktop/nicegui_app/config.py` 读取该环境变量，自动指向远程 FastAPI 服务。

### 2.2 启动 PC-UI（NiceGUI）

```powershell
(.venv) python desktop/nicegui_app/pc_app.py
```

启动后控制台会输出：

```text
NiceGUI ready to go on http://localhost:8080, ...
```

浏览器访问 `http://localhost:8080` 或通过 Tailscale / 远程 IP 访问其他地址即可。

---

## 3. NoneType 错误修复（按钮未创建）

### 3.1 pc_app.py：结构树按钮默认禁用逻辑

**问题现象**

登录后访问主页时报错：

```text
AttributeError: 'NoneType' object has no attribute 'disable'
```

堆栈定位到：

```python
system_add_btn.disable()
zone_add_btn.disable()
device_add_btn.disable()
node_edit_btn.disable()
node_delete_btn.disable()
```

这些按钮是按权限动态创建的，某些权限不存在时变量为 `None`，直接调用 `disable()` 会抛异常。

**修复措施**

在 `main_page()` 中创建树区域后，将默认禁用逻辑改为带判空：

```python
if system_add_btn is not None:
    system_add_btn.disable()
if zone_add_btn is not None:
    zone_add_btn.disable()
if device_add_btn is not None:
    device_add_btn.disable()
if node_edit_btn is not None:
    node_edit_btn.disable()
if node_delete_btn is not None:
    node_delete_btn.disable()
```

### 3.2 ui/panels.py：资产详情面板的按钮/Label 判空

**问题现象**

登录后 500 错误，堆栈：

```text
ui_elements["run_ocr_button"].disabled = True
AttributeError: 'NoneType' object has no attribute 'disabled'
```

原因同样是：`run_ocr_button` / `run_llm_button` 只有在具备相应权限时才会创建，否则为 `None`。

**修复措施**

在 `AssetDetailHelper.update_inference_status` 和 `AssetDetailHelper.update_detail_panel` 中，访问 UI 元素前统一通过 `ui_elements.get()` 获取并判空，例如：

```python
label = ui_elements.get("inference_status_label")
if label is not None:
    label.text = ""

run_ocr_button = ui_elements.get("run_ocr_button")
if run_ocr_button is not None:
    run_ocr_button.disabled = True

run_llm_button = ui_elements.get("run_llm_button")
if run_llm_button is not None:
    run_llm_button.disabled = True
```

以及在清空 / 写入 OCR 文本和 LLM 文本时，同样使用 `get()` + 判空，避免在某些 UI 元素未创建时访问其属性。

---

## 4. 节点编辑/删除事件绑定修复

**问题现象**

登录后访问主页时，NiceGUI 报 500：

```text
NameError: name 'on_edit_building_click' is not defined
```

`pc_app.py` 中按钮事件绑定引用了不存在的函数：

```python
if node_edit_btn:
    node_edit_btn.on_click(on_edit_building_click)
if node_delete_btn:
    node_delete_btn.on_click(on_delete_building_click)
```

而同一作用域内真正实现的是：

```python
async def on_edit_node_click() -> None: ...
async def on_delete_node_click() -> None: ...
```

**修复措施**

将事件绑定改为已存在的处理函数：

```python
if node_edit_btn:
    node_edit_btn.on_click(on_edit_node_click)
if node_delete_btn:
    node_delete_btn.on_click(on_delete_node_click)
```

---

## 5. 权限加载与按钮显示修复（AuthManager）

**问题现象**

- 后端日志：`DEBUG: Superuser yerui, permissions count: 33`
- PC-UI 顶部显示角色为 `superadmin`，但左侧“＋项目 / ＋楼栋 / ＋系统 / ＋区域 / ＋设备”等按钮均不显示。

**原因分析**

`AuthManager` 的权限加载逻辑存在两点问题：

1. `_fetch_user_details` 虽然从 `/auth/me` 获取了用户详情，但没有把 `is_superuser` 同步回 `self._user`，导致：
   ```python
   if self._user and self._user.get('is_superuser', False):
       return True
   ```
   永远为 False，超级管理员无法在前端被识别。

2. `_permissions` 列表里直接塞入了权限对象，而 `has_permission()` 用的是字符串包含判断：
   ```python
   return permission_code in self._permissions
   ```
   导致普通用户的精确权限检查也不生效。

**修复措施**

在 `desktop/nicegui_app/auth_manager.py` 的 `_fetch_user_details` 中：

1. 同步 `is_superuser` 标志：

```python
if user_detail.get('is_superuser') is not None:
    if self._user is None:
        self._user = {}
    self._user['is_superuser'] = bool(user_detail.get('is_superuser'))
```

2. 仅存储权限 code 字符串：

```python
self._roles = user_detail.get('roles', [])
self._permissions = []

for role in self._roles:
    role_permissions = role.get('permissions', [])
    if not isinstance(role_permissions, list):
        continue
    for perm in role_permissions:
        code = None
        if isinstance(perm, dict):
            code = perm.get('code') or perm.get('name')
        else:
            code = str(perm)
        if code and code not in self._permissions:
            self._permissions.append(code)
```

`has_permission()` 不需要改动，即可同时支持：

- 超级管理员：`is_superuser=True`，直接拥有全部权限；
- 普通用户：按权限 code 精确匹配。

---

## 6. 项目创建 403 Forbidden 修复

**问题现象**

在 PC-UI 中点击“＋项目”，对话框填写信息后提交，前端提示：

```text
创建项目失败: Client error '403 Forbidden' for url 'http://<后端IP>:8000/api/v1/projects/'
```

后端为 `POST /api/v1/projects/`，依赖 `get_current_user`（HTTP Bearer 认证）。

**原因分析**

`desktop/nicegui_app/ui/dialogs.py` 中项目创建对话框使用裸 `httpx.AsyncClient` 请求，没有附带前端登录后获取的 Bearer token：

```python
resp = await client.post(
    f"{self.backend_base_url}/projects/",
    json=payload,
)
```

后端无法识别当前用户身份，直接返回 403 Forbidden。

**修复措施**

1. 在文件顶部引入前端认证管理器：

```python
from desktop.nicegui_app.auth_manager import auth_manager
```

2. 在 `ProjectDialog` 中新增获取认证头方法：

```python
def _get_auth_headers(self) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    try:
        if auth_manager and auth_manager.token:
            headers["Authorization"] = f"Bearer {auth_manager.token}"
    except Exception:
        # 认证不可用时退化为匿名请求
        pass
    return headers
```

3. 创建 / 更新项目时补上 `Authorization` 头：

```python
# 创建项目
resp = await client.post(
    f"{self.backend_base_url}/projects/",
    json=payload,
    headers=self._get_auth_headers() or None,
)

# 更新项目
resp = await client.patch(
    f"{self.backend_base_url}/projects/{project_id}",
    json=payload,
    headers=self._get_auth_headers() or None,
)
```

验证：

- 使用 `yerui`（superadmin）登录 PC-UI；
- 点击“＋项目”创建新项目，后端不再返回 403，项目成功写入数据库并在左侧工程结构树与项目列表中可见。

---

## 7. 版本号与验证

为便于确认前端代码是否为最新版本，在 `pc_app.py` 中更新了 UI 版本号标记：

```python
UI_VERSION = "PC UI v0.3.9-system-primary"
```

PC-UI 右上角会显示当前版本号，可用于快速验证修改是否生效（尤其是在远程部署或浏览器缓存场景下）。
