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

> 2026-01-27 更新：在本次修复后，版本号进一步提升为 `PC UI v0.3.10-permission-fix2`，用于明显区分“仅修到 0.3.9”与“包含资产点击/上传修复”的版本。

---

## 8. 资产表行点击与详情面板不联动问题（2026-01-27）

### 8.1 问题现象

- 使用 `yerui`（superadmin）登录远程 PC-UI，左侧工程树与资产列表可正常加载；
- 点击资产表中的某一行时：
  - 右侧“资产详情”面板完全无变化；
  - 控制台没有后端请求日志，也没有明显报错；
- 打印 `rowClick` 事件调试信息后，发现 `e.args` 结构为：

```text
e.args == [mouse_event_dict, row_dict, row_index]
```

而旧版事件处理只取了第一个元素（鼠标事件），导致完全拿不到资产 `id`。

### 8.2 修复措施（ui/tables.py）

在 `desktop/nicegui_app/ui/tables.py` 中扩展 `AssetTableRowClickHandler.extract_row_id` 的兼容性：

- 支持多种 `rowClick` 事件形态：
  - `e.args == row_dict`
  - `e.args == [row_dict]`
  - `e.args == [mouse_event, row_dict, row_index]`
  - `e.args == {"row": row_dict, ...}`
- 统一将 `e.args` 展开为候选列表 `candidates`，遍历寻找真正包含 `id` 的行对象：

```python
args = e.args
print(f"[DEBUG] asset_table rowClick raw args: {args!r}")

if isinstance(args, list):
    if not args:
        print("[DEBUG] asset_table rowClick: empty list args")
        return None
    candidates = list(args)
else:
    candidates = [args]

row_obj = None
asset_id = None

for item in candidates:
    if isinstance(item, dict) and "id" in item:
        row_obj = item
        asset_id = item.get("id")
        break
    if isinstance(item, dict) and "row" in item:
        inner = item.get("row")
        if isinstance(inner, dict) and "id" in inner:
            row_obj = inner
            asset_id = inner.get("id")
            break

if not row_obj or not asset_id:
    print(f"[DEBUG] asset_table rowClick: no usable row with 'id' found in args {args!r}")
    return None

print(f"[DEBUG] asset_table rowClick resolved asset_id={asset_id}")
return str(asset_id)
```

修复后：

- `events/asset_events.on_asset_row_click` 能正确解析 `asset_id`；
- 会调用后端 `/assets/{id}` 获取详情，并刷新右侧详情面板与预览图片。

---

## 9. 上传图片资产对话框的 inspect NameError 修复（2026-01-27）

### 9.1 问题现象

在 PC-UI 中点击“上传图片资产”，选择图片后控制台输出：

```text
[DEBUG] on_file_upload: 使用 e.content 读取
[DEBUG] on_file_upload 处理异常: name 'inspect' is not defined
[DEBUG] handle_upload: 未找到已缓存的文件内容
```

导致前端认为“没有已上传的文件内容”，无法将图片真正提交到后端。

### 9.2 修复措施（ui/dialogs.py）

问题根因：

- `desktop/nicegui_app/ui/dialogs.py` 中上传对话框的 `on_file_upload` 使用了 `inspect.iscoroutine` 判断 `read()` 返回值是否为协程；
- 但文件顶部忘记导入 `inspect`，在实际执行时抛出 `NameError`。

修复方法：

- 在文件顶部补充导入：

```python
from typing import Any, Callable, Dict, Optional
import inspect
import httpx
from nicegui import ui
from desktop.nicegui_app.auth_manager import auth_manager
```

修复后：

- `on_file_upload` 能正确读取 `e.content` / `e.file` / `e.files[0]` 中的字节流；
- `selected_file["content"]` 被正确缓存，`handle_upload` 可以将文件与元数据提交到后端 `/assets/upload_image_with_note`；
- 控制台日志会显示：

```text
[DEBUG] 已接收到上传文件: xxx.png, 大小=... bytes, type=image/png
[DEBUG] 开始上传文件到后端: xxx.png, size=... bytes, type=image/png
```

---

## 10. 版本与部署注意事项（防止旧代码覆盖修复版本）

在本次远程联调中，曾出现如下情况：

- 文档中记录的修复（结构树按钮判空、节点编辑事件绑定、AuthManager 权限修复等）已经在某一台环境完成；
- 但服务器上的 `pc_app.py` / `auth_manager.py` 被旧版本文件覆盖，导致同一批问题再次出现。

为避免类似情况，建议：

1. 以 Git 仓库为唯一“真源”
   - 所有修复完成后推送到远端仓库；
   - 在其他服务器部署时一律使用 `git pull` 同步，而不是手工复制单个 `.py` 文件。

2. 通过 UI 版本号快速校验
   - 当前包含全部 PC-UI 修复（权限 + 资产点击 + 上传）的版本标记为：
     
     ```python
     UI_VERSION = "PC UI v0.3.10-permission-fix2"
     ```
   - 远程浏览器右上角若显示旧版本（例如 `v0.3.9-*`），说明前端代码尚未升级或浏览器缓存未刷新。

3. 避免本地修改覆盖远端修复
   - 在服务器上直接编辑 `pc_app.py` 前，先确认本地与远端分支是否一致；
   - 若需要临时调试，建议新建分支或在本地改完后再统一合并，而不是“复制旧文件上去”。
