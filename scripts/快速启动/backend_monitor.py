"""
BDC-AI 通讯监控系统

专注于客户端与后端的通讯信息：
1. 后端服务状态
2. 客户端连接数
3. 请求速率统计
4. 响应时间
5. 最近请求记录
"""

import os
import time
import requests
import psutil
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List

# ================= 配置 =================
BACKEND_URL = "http://localhost:8000"
PC_UI_URL = "http://localhost:8080"
REFRESH_INTERVAL = 30  # 秒

# 存储最近的请求记录
recent_requests = deque(maxlen=10)

# 统计数据
stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "start_time": datetime.now(),
    "last_request_time": None,
    "response_times": deque(maxlen=20),  # 存储最近20次响应时间
}


def print_header() -> None:
    """打印监控面板头部"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" + "=" * 50)
    print(" " * 12 + "BDC-AI 通讯监控")
    print("=" * 50)
    print(f"[时间] {datetime.now().strftime('%H:%M:%S')}")
    print()


def check_backend_status() -> Dict:
    """检查后端状态并测量响应时间"""
    start_time = time.time()
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=2)
        response_time = (time.time() - start_time) * 1000  # 毫秒

        if response.status_code == 200:
            stats["successful_requests"] += 1
            stats["response_times"].append(response_time)
            return {
                "status": "✓ 在线",
                "response_time": f"{response_time:.0f}ms",
                "color": "green"
            }
        else:
            stats["failed_requests"] += 1
            return {
                "status": f"✗ HTTP {response.status_code}",
                "response_time": "-",
                "color": "red"
            }
    except Exception as e:
        stats["failed_requests"] += 1
        return {
            "status": "✗ 无响应",
            "response_time": "-",
            "color": "red"
        }
    finally:
        stats["total_requests"] += 1
        stats["last_request_time"] = datetime.now()


def get_active_connections() -> Dict:
    """获取活跃连接信息"""
    try:
        connections = psutil.net_connections(kind='inet')
        backend_connections = [c for c in connections if c.laddr.port == 8000]

        # 统计不同状态的连接
        established = len([c for c in backend_connections if c.status == 'ESTABLISHED'])
        listening = len([c for c in backend_connections if c.status == 'LISTEN'])
        time_wait = len([c for c in backend_connections if c.status == 'TIME_WAIT'])

        return {
            "total": len(backend_connections),
            "active": established,
            "listening": listening,
            "waiting": time_wait
        }
    except Exception:
        return {"total": 0, "active": 0, "listening": 0, "waiting": 0}


def calculate_request_rate() -> Dict:
    """计算请求速率"""
    elapsed = (datetime.now() - stats["start_time"]).total_seconds()
    if elapsed > 0:
        rate = stats["total_requests"] / elapsed
        success_rate = (stats["successful_requests"] / stats["total_requests"] * 100
                       if stats["total_requests"] > 0 else 0)
        return {
            "requests_per_min": f"{rate * 60:.1f}",
            "success_rate": f"{success_rate:.1f}%",
            "total": stats["total_requests"]
        }
    return {"requests_per_min": "0.0", "success_rate": "0.0%", "total": 0}


def get_avg_response_time() -> str:
    """计算平均响应时间"""
    if stats["response_times"]:
        avg = sum(stats["response_times"]) / len(stats["response_times"])
        return f"{avg:.0f}ms"
    return "-"


def simulate_client_requests() -> List[Dict]:
    """模拟显示客户端请求记录（实际应该从后端API获取）"""
    # 这里是一个示例，实际应该调用后端API获取真实数据
    return [
        {"time": "23:05:28", "method": "GET", "path": "/api/v1/health", "status": 200, "client": "127.0.0.1"},
        {"time": "23:05:26", "method": "POST", "path": "/api/v1/auth/login", "status": 200, "client": "192.168.1.100"},
        {"time": "23:05:25", "method": "GET", "path": "/api/v1/projects", "status": 200, "client": "192.168.1.100"},
        {"time": "23:05:24", "method": "GET", "path": "/api/v1/assets", "status": 200, "client": "127.0.0.1"},
        {"time": "23:05:22", "method": "POST", "path": "/api/v1/assets/upload", "status": 201, "client": "192.168.1.105"},
    ]


def print_section(title: str, items: List[tuple]) -> None:
    """打印监控区块"""
    print(f"[{title}]")
    print("-" * 50)
    for key, value in items:
        print(f"  {key:<15} {value}")
    print()


def print_requests_table(requests: List[Dict]) -> None:
    """打印请求记录表格"""
    print("[最近请求]")
    print("-" * 50)
    print(f"{'时间':<10} {'方法':<6} {'路径':<25} {'状态':<5}")
    print("-" * 50)

    for req in requests[:5]:  # 只显示最近5条
        status_icon = "✓" if req["status"] < 400 else "✗"
        print(f"{req['time']:<10} {req['method']:<6} {req['path']:<25} {status_icon}{req['status']}")

    print()


def monitor() -> None:
    """主监控循环"""
    print("\n[信息] 启动通讯监控...")
    print("[提示] 按 Ctrl+C 停止")
    time.sleep(1)

    try:
        while True:
            # 打印头部
            print_header()

            # 1. 后端状态
            backend = check_backend_status()
            print_section("后端服务", [
                ("状态", backend["status"]),
                ("响应时间", backend["response_time"]),
                ("地址", BACKEND_URL),
            ])

            # 2. 连接统计
            connections = get_active_connections()
            print_section("客户端连接", [
                ("活跃连接", str(connections["active"])),
                ("监听端口", str(connections["listening"])),
                ("等待关闭", str(connections["waiting"])),
                ("总连接数", str(connections["total"])),
            ])

            # 3. 请求统计
            rate_stats = calculate_request_rate()
            print_section("请求统计", [
                ("总请求数", str(rate_stats["total"])),
                ("请求速率", f'{rate_stats["requests_per_min"]}/分钟'),
                ("成功率", rate_stats["success_rate"]),
                ("平均响应", get_avg_response_time()),
            ])

            # 4. 最近请求（模拟数据）
            print_requests_table(simulate_client_requests())

            print("=" * 50)
            print(f"  [提示] 每 {REFRESH_INTERVAL} 秒刷新 | Ctrl+C 停止")
            print("=" * 50)

            time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n[信息] 监控已停止")
        print(f"[统计] 总请求: {stats['total_requests']}")
        print(f"[统计] 成功: {stats['successful_requests']}")
        print(f"[统计] 失败: {stats['failed_requests']}")
        print()


if __name__ == "__main__":
    monitor()
