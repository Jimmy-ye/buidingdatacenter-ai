"""
权限查看页面
"""

from nicegui import ui
from typing import Dict, Any, List
from services.api_client import api_client


class PermissionsPage:
    """权限查看页面类"""

    def __init__(self):
        self.permissions_data: List[Dict[str, Any]] = []

    def load_permissions(self):
        """加载权限列表"""
        self.permissions_data = api_client.get_permissions()
        self.refresh_table()

    def refresh_table(self):
        """刷新表格数据"""
        if hasattr(self, 'table'):
            self.table.rows = self.format_permissions_for_table()
            self.table.update()

    def format_permissions_for_table(self) -> List[Dict[str, Any]]:
        """格式化权限数据用于表格显示"""
        formatted = []
        for perm in self.permissions_data:
            formatted.append({
                'id': perm.get('id'),
                'code': perm.get('code'),
                'name': perm.get('name'),
                'resource': perm.get('resource'),
                'action': perm.get('action'),
                'description': perm.get('description') or '-',
            })
        return formatted


# 全局实例
permissions_page = PermissionsPage()


def show_permissions_page():
    """注册权限查看页面"""

    @ui.page('/admin/permissions')
    def page():
        # 加载数据
        permissions_page.load_permissions()

        with ui.column().classes('w-full p-4 gap-4'):
            # 标题
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('权限查看').classes('text-2xl font-bold')
                ui.button(icon='refresh', on_click=permissions_page.load_permissions).props('flat').tooltip('刷新')

            # 统计信息
            ui.label(f'共 {len(permissions_page.permissions_data)} 个权限').classes('text-gray-600')

            # 权限列表表格
            with ui.card().classes('w-full'):
                columns = [
                    {'name': 'code', 'label': '权限代码', 'field': 'code', 'align': 'left'},
                    {'name': 'name', 'label': '权限名称', 'field': 'name', 'align': 'left'},
                    {'name': 'resource', 'label': '资源', 'field': 'resource', 'align': 'center'},
                    {'name': 'action', 'label': '操作', 'field': 'action', 'align': 'center'},
                    {'name': 'description', 'label': '描述', 'field': 'description', 'align': 'left'},
                ]

                permissions_page.table = ui.table(
                    columns=columns,
                    rows=permissions_page.format_permissions_for_table(),
                    row_key='id',
                    pagination=20
                ).classes('w-full')

            # 按资源分组的统计
            ui.label('按资源统计').classes('text-lg font-bold mt-4')

            # 统计权限数量
            from collections import Counter
            resource_counts = Counter([p.get('resource') for p in permissions_page.permissions_data])

            with ui.row().classes('gap-2 w-full flex-wrap'):
                for resource, count in sorted(resource_counts.items()):
                    with ui.card().classes('p-3'):
                        ui.label(resource.upper()).classes('text-xs text-gray-600')
                        ui.label(str(count)).classes('text-xl font-bold text-blue-600')
