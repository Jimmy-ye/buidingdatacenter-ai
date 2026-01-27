"""
审计日志页面
"""

from nicegui import ui
from typing import Dict, Any, List
from services.backend.app.admin.services.api_client import api_client


class AuditPage:
    """审计日志页面类"""

    def __init__(self):
        self.logs_data: List[Dict[str, Any]] = []

    def load_logs(self):
        """加载审计日志"""
        self.logs_data = api_client.get_audit_logs(limit=200)
        self.refresh_table()

    def refresh_table(self):
        """刷新表格数据"""
        if hasattr(self, 'table'):
            self.table.rows = self.format_logs_for_table()
            self.table.update()

    def format_logs_for_table(self) -> List[Dict[str, Any]]:
        """格式化日志数据用于表格显示"""
        formatted = []
        for log in self.logs_data:
            formatted.append({
                'id': log.get('id'),
                'timestamp': log.get('created_at', '-')[:19].replace('T', ' '),
                'username': log.get('user', {}).get('username') if log.get('user') else '-',
                'action': log.get('action', '-'),
                'resource_type': log.get('resource_type', '-'),
                'ip_address': log.get('ip_address', '-'),
                'details': log.get('details', {}) or {},
            })
        return formatted


# 全局实例
audit_page = AuditPage()


def show_audit_page():
    """注册审计日志页面"""

    @ui.page('/admin/audit')
    def page():
        # 加载数据
        audit_page.load_logs()

        with ui.column().classes('w-full p-4 gap-4'):
            # 标题
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('审计日志').classes('text-2xl font-bold')
                ui.button(icon='refresh', on_click=audit_page.load_logs).props('flat').tooltip('刷新')

            # 统计信息
            ui.label(f'共 {len(audit_page.logs_data)} 条日志').classes('text-gray-600')

            # 日志列表表格
            with ui.card().classes('w-full'):
                columns = [
                    {'name': 'timestamp', 'label': '时间', 'field': 'timestamp', 'align': 'left'},
                    {'name': 'username', 'label': '用户', 'field': 'username', 'align': 'left'},
                    {'name': 'action', 'label': '操作', 'field': 'action', 'align': 'left'},
                    {'name': 'resource_type', 'label': '资源类型', 'field': 'resource_type', 'align': 'left'},
                    {'name': 'ip_address', 'label': 'IP 地址', 'field': 'ip_address', 'align': 'left'},
                ]

                audit_page.table = ui.table(
                    columns=columns,
                    rows=audit_page.format_logs_for_table(),
                    row_key='id',
                    pagination=20
                ).classes('w-full')
