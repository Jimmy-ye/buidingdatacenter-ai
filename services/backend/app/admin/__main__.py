"""
管理界面启动入口
"""

import sys
from pathlib import Path
from nicegui import ui

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.backend.app.admin.main import admin_app

if __name__ == "__main__":
    # 运行应用初始化
    admin_app.run()

    # 启动 NiceGUI
    ui.run(
        title="BDC-AI 账号管理",
        port=8082,
        dark=None,
        binding_refresh_interval=0.5,
    )
