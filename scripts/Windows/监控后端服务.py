"""
BDC-AI 后端服务监控脚本

功能：
- 实时监控后端服务状态
- 统计请求成功/失败情况
- 计算响应时间
- 监控多个端点
- 显示实时统计信息
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import deque
import sys

# ANSI 颜色代码
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ServiceMonitor:
    """后端服务监控器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.results = deque(maxlen=100)  # 保存最近 100 次请求结果
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'total_time': 0.0,
            'last_error': None
        }

        # 监控的端点
        self.endpoints = [
            {'name': '健康检查', 'path': '/api/v1/health', 'method': 'GET'},
            {'name': '项目列表', 'path': '/api/v1/projects/', 'method': 'GET'},
            {'name': 'API 文档', 'path': '/docs', 'method': 'GET'},
        ]

    def check_endpoint(self, endpoint: Dict) -> Dict:
        """检查单个端点（详细版本）"""
        url = f"{self.base_url}{endpoint['path']}"

        try:
            start_time = time.time()
            response = requests.get(
                url,
                timeout=5,
                headers={'Accept': 'application/json'}
            )
            elapsed = time.time() - start_time

            # 获取响应大小
            response_size = len(response.content)
            response_size_kb = response_size / 1024

            # 解析响应内容
            content_preview = ""
            content_type = response.headers.get('content-type', 'unknown')

            try:
                if 'application/json' in content_type:
                    data = response.json()
                    if isinstance(data, dict):
                        # 提取关键字段
                        if 'status' in data:
                            content_preview = f"status={data.get('status')}"
                        elif 'message' in data:
                            content_preview = f"msg={data.get('message')[:30]}"
                        else:
                            content_preview = f"keys={list(data.keys())[:5]}"
                    elif isinstance(data, list):
                        content_preview = f"count={len(data)} items"
                elif 'text/html' in content_type:
                    content_preview = "HTML page"
                else:
                    content_preview = content_type.split(';')[0]
            except:
                content_preview = content_type.split(';')[0]

            return {
                'success': response.status_code == 200,
                'elapsed': elapsed,
                'status_code': response.status_code,
                'size': response_size_kb,
                'content_type': content_type,
                'content_preview': content_preview,
                'error': None
            }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'elapsed': 5.0,
                'status_code': None,
                'size': 0,
                'content_type': None,
                'content_preview': None,
                'error': '超时'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'elapsed': 0.0,
                'status_code': None,
                'size': 0,
                'content_type': None,
                'content_preview': None,
                'error': '连接失败'
            }
        except Exception as e:
            return {
                'success': False,
                'elapsed': 0.0,
                'status_code': None,
                'size': 0,
                'content_type': None,
                'content_preview': None,
                'error': str(e)[:50]
            }

    def check_service(self) -> None:
        """检查服务状态"""
        timestamp = datetime.now()

        # 检查健康检查端点
        result = self.check_endpoint(self.endpoints[0])

        # 更新统计
        self.stats['total'] += 1
        if result['success']:
            self.stats['success'] += 1
        else:
            self.stats['failed'] += 1
            self.stats['last_error'] = result['error']

        self.stats['total_time'] += result['elapsed']

        # 保存结果
        self.results.append({
            'timestamp': timestamp,
            **result
        })

    def get_success_rate(self) -> float:
        """计算成功率"""
        if self.stats['total'] == 0:
            return 0.0
        return (self.stats['success'] / self.stats['total']) * 100

    def get_avg_response_time(self) -> float:
        """计算平均响应时间"""
        if self.stats['success'] == 0:
            return 0.0
        return self.stats['total_time'] / self.stats['success']

    def get_recent_stats(self, seconds: int = 60) -> Dict:
        """获取最近 N 秒的统计"""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        recent = [r for r in self.results if r['timestamp'] > cutoff]

        if not recent:
            return {'count': 0, 'success': 0, 'failed': 0, 'success_rate': 0}

        success_count = sum(1 for r in recent if r['success'])

        return {
            'count': len(recent),
            'success': success_count,
            'failed': len(recent) - success_count,
            'success_rate': (success_count / len(recent)) * 100 if recent else 0
        }

    def print_header(self) -> None:
        """打印标题"""
        print("\n" + "=" * 80)
        print(f"{Colors.HEADER}{Colors.BOLD}BDC-AI 后端服务监控{Colors.ENDC}")
        print(f"{Colors.OKCYAN}服务地址: {self.base_url}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        print("=" * 80 + "\n")

    def print_stats(self) -> None:
        """打印统计信息"""
        # 清屏（可选）
        # os.system('cls' if os.name == 'nt' else 'clear')

        print(f"\n{Colors.BOLD}实时监控统计{Colors.ENDC}")
        print("-" * 80)

        # 总体统计
        success_rate = self.get_success_rate()
        avg_time = self.get_avg_response_time()

        print(f"{Colors.BOLD}总体统计（全部）:{Colors.ENDC}")
        print(f"  总请求数: {self.stats['total']}")
        print(f"  成功: {Colors.OKGREEN}{self.stats['success']}{Colors.ENDC} | "
              f"失败: {Colors.FAIL if self.stats['failed'] > 0 else ''}{self.stats['failed']}{Colors.ENDC}")
        print(f"  成功率: {self._get_rate_color(success_rate)}{success_rate:.1f}%{Colors.ENDC}")
        print(f"  平均响应: {avg_time*1000:.0f} ms")

        # 最近 60 秒统计
        recent = self.get_recent_stats(60)
        print(f"\n{Colors.BOLD}最近 60 秒:{Colors.ENDC}")
        print(f"  请求数: {recent['count']}")
        print(f"  成功: {Colors.OKGREEN}{recent['success']}{Colors.ENDC} | "
              f"失败: {Colors.FAIL if recent['failed'] > 0 else ''}{recent['failed']}{Colors.ENDC}")
        print(f"  成功率: {self._get_rate_color(recent['success_rate'])}{recent['success_rate']:.1f}%{Colors.ENDC}")

        # 最近 10 次请求（详细版）
        print(f"\n{Colors.BOLD}最近 10 次请求详情:{Colors.ENDC}")
        print(f"  {'时间':>8}  {'状态':>6}  {'响应时间':>10}  {'大小':>10}  {'内容'}")
        print(f"  {'-'*8}  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*40}")

        recent_results = list(self.results)[-10:]
        for i, result in enumerate(recent_results, 1):
            time_str = result['timestamp'].strftime('%H:%M:%S')

            # 状态
            if result['success']:
                status = f"{Colors.OKGREEN}[OK]{Colors.ENDC}"
            else:
                status = f"{Colors.FAIL}[FAIL]{Colors.ENDC}"

            # 响应时间
            if result['success']:
                response_time = f"{result['elapsed']*1000:.0f}ms"
            else:
                response_time = "---"

            # 数据大小
            if result['success'] and result['size'] > 0:
                size_str = f"{result['size']:.2f}KB"
            else:
                size_str = "---"

            # 内容预览
            if result['success']:
                content = result.get('content_preview', 'N/A')
            else:
                content = result.get('error', 'Unknown')

            print(f"  {time_str}  {status}  {response_time:>10s}  {size_str:>10s}  {content[:40]}")

        # 最后错误
        if self.stats['last_error']:
            print(f"\n{Colors.WARNING}最后错误: {self.stats['last_error']}{Colors.ENDC}")

        # 服务状态指示
        if recent['count'] > 0 and recent['success_rate'] >= 90:
            status_icon = f"{Colors.OKGREEN}[正常]{Colors.ENDC}"
        elif recent['count'] > 0 and recent['success_rate'] >= 50:
            status_icon = f"{Colors.WARNING}[不稳定]{Colors.ENDC}"
        else:
            status_icon = f"{Colors.FAIL}[异常]{Colors.ENDC}"

        print(f"\n{Colors.BOLD}当前状态: {status_icon}{Colors.ENDC}")
        print("-" * 80)

    def _get_rate_color(self, rate: float) -> str:
        """根据成功率返回颜色"""
        if rate >= 95:
            return Colors.OKGREEN
        elif rate >= 80:
            return Colors.OKCYAN
        elif rate >= 50:
            return Colors.WARNING
        else:
            return Colors.FAIL

    def run(self, interval: int = 5) -> None:
        """运行监控"""
        self.print_header()

        print(f"每 {interval} 秒检查一次服务状态...")
        print("按 Ctrl+C 停止监控\n")

        try:
            while True:
                self.check_service()
                self.print_stats()
                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.OKCYAN}监控已停止{Colors.ENDC}")

            # 打印最终统计
            print(f"\n{Colors.BOLD}最终统计:{Colors.ENDC}")
            print(f"  总运行时间: {(self.results[-1]['timestamp'] - self.results[0]['timestamp']).seconds if len(self.results) > 1 else 0} 秒")
            print(f"  总请求数: {self.stats['total']}")
            print(f"  成功率: {self.get_success_rate():.1f}%")
            print(f"  平均响应: {self.get_avg_response_time()*1000:.0f} ms")
            print()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='BDC-AI 后端服务监控')
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='后端服务地址（默认：http://localhost:8000）'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='检查间隔（秒，默认：5）'
    )

    args = parser.parse_args()

    monitor = ServiceMonitor(args.url)
    monitor.run(args.interval)


if __name__ == '__main__':
    main()
