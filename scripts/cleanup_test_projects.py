"""智能清理测试项目（基于 Project 软/硬删除策略）

- 默认以 DRY-RUN 方式运行，只打印将要删除的项目，不真正删除
- 仅匹配“测试项目”，避免误删正常项目：
  - name 中包含给定模式（默认: "test"）
  - 或 tags 中包含 environment == "test"
- 真正删除时使用 DELETE /projects/{id}?hard_delete=true&reason=...，
  触发后端的级联删除 Asset + 物理删除 Project
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

import httpx

BACKEND_BASE_URL = "http://127.0.0.1:8000/api/v1"


async def fetch_projects() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        # include_deleted=true 是为了也能清理已经软删但尚未物理删除的项目
        resp = await client.get(f"{BACKEND_BASE_URL}/projects/", params={"include_deleted": True})
        resp.raise_for_status()
        return resp.json()


def is_test_project(p: Dict[str, Any], name_pattern: str) -> bool:
    name = (p.get("name") or "").lower()
    tags = p.get("tags") or {}
    env = str(tags.get("environment", "")).lower()

    if name_pattern and name_pattern.lower() in name:
        return True
    if env == "test":
        return True
    return False


async def hard_delete_project(project_id: str, reason: str, operator: str = "cleanup_script") -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.delete(
            f"{BACKEND_BASE_URL}/projects/{project_id}",
            params={"hard_delete": True, "reason": reason},
            headers={"operator": operator},
        )
        resp.raise_for_status()


async def cleanup_test_projects(
    name_pattern: str = "test",
    days_old: int | None = None,
    dry_run: bool = True,
) -> None:
    """清理测试项目

    Args:
        name_pattern: 按名称模式筛选（默认匹配包含 "test" 的项目）
        days_old: 仅删除 N 天前创建的项目；为 None 时不按时间过滤
        dry_run: 预演模式，不实际删除
    """

    projects = await fetch_projects()

    cutoff_date: datetime | None = None
    if days_old is not None:
        cutoff_date = datetime.now() - timedelta(days=days_old)

    candidates: List[Dict[str, Any]] = []
    for p in projects:
        if not is_test_project(p, name_pattern=name_pattern):
            continue

        created_at_raw = p.get("start_date") or p.get("created_at")
        created_at_dt: datetime | None = None
        if created_at_raw:
            # start_date 可能是日期，created_at 可能是 datetime，统一转成 datetime
            try:
                created_at_dt = datetime.fromisoformat(str(created_at_raw))
            except Exception:
                created_at_dt = None

        if cutoff_date is not None and created_at_dt is not None:
            if created_at_dt >= cutoff_date:
                # 太新，不删
                continue

        candidates.append(p)

    if not candidates:
        print("未找到符合条件的测试项目，无需清理。")
        return

    print(f"找到 {len(candidates)} 个符合条件的测试项目：\n")
    for p in candidates:
        pid = p["id"]
        name = p.get("name")
        tags = p.get("tags") or {}
        created_at_raw = p.get("start_date") or p.get("created_at")
        print(f"  - {name} ({pid})")
        if created_at_raw:
            print(f"    created_at: {created_at_raw}")
        if tags:
            print(f"    tags: {tags}")
        print()

    if dry_run:
        print("[DRY RUN] 预演模式，不会实际删除项目。")
        print("如需实际删除，请将 dry_run=False 再运行脚本。")
        return

    confirm = input(f"确认硬删除以上 {len(candidates)} 个测试项目？(yes/NO): ")
    if confirm.strip().lower() != "yes":
        print("已取消删除。")
        return

    reason = f"cleanup_test_projects: pattern={name_pattern}, days_old={days_old}"
    success, fail = 0, 0

    for idx, p in enumerate(candidates, start=1):
        pid = p["id"]
        name = p.get("name")
        try:
            await hard_delete_project(pid, reason=reason)
            print(f"✅ [{idx}/{len(candidates)}] 删除成功: {name} ({pid})")
            success += 1
        except Exception as e:  # noqa: BLE001
            print(f"❌ [{idx}/{len(candidates)}] 删除失败: {name} ({pid})")
            print(f"   错误: {e}")
            fail += 1

    print("\n删除完成！")
    print(f"  成功: {success}")
    print(f"  失败: {fail}")


if __name__ == "__main__":
    # 默认使用 DRY-RUN，先观察将要删除哪些项目
    asyncio.run(
        cleanup_test_projects(
            name_pattern="test",  # 也可以改成 "demo" 等
            days_old=None,         # 也可以设为 7，只删 7 天前的测试项目
            dry_run=True,          # 首次强烈建议先用 DRY-RUN
        )
    )
