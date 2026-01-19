import os
import sys
import time
from pathlib import Path
from typing import List

import requests

BACKEND_BASE_URL = os.getenv("BDC_BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
# 默认使用你提供的图片目录，如需更改可修改此常量或通过命令行参数传入
DEFAULT_IMAGE_DIR = r"C:\Users\86152\Downloads\设备"


def create_project(name: str) -> str:
    resp = requests.post(
        f"{BACKEND_BASE_URL}/api/v1/projects/",
        json={"name": name, "description": "scene_issue end-to-end test"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["id"]


def upload_scene_issue_images(project_id: str, image_dir: Path) -> List[str]:
    asset_ids: List[str] = []
    for path in sorted(image_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue

        files = {"file": (path.name, path.read_bytes(), "image/jpeg")}
        params = {
            "project_id": project_id,
            "source": "scene_issue_test",
            "content_role": "scene_issue",
            "auto_route": True,
        }
        data = {
            "note": f"Scene issue test image: {path.name}",
            "title": path.name,
        }
        print(f"[UPLOAD] {path} ...")
        resp = requests.post(
            f"{BACKEND_BASE_URL}/api/v1/assets/upload_image_with_note",
            params=params,
            data=data,
            files=files,
            timeout=60,
        )
        resp.raise_for_status()
        asset = resp.json()
        asset_ids.append(asset["id"])
        print(f"    -> asset_id={asset['id']}, status={asset.get('status')}")
    return asset_ids


def wait_for_llm_results(asset_ids: List[str], timeout_sec: int = 120) -> None:
    deadline = time.time() + timeout_sec
    pending = set(asset_ids)
    print("[WAIT] Polling for parsed_scene_llm ...")

    while pending and time.time() < deadline:
        for asset_id in list(pending):
            resp = requests.get(f"{BACKEND_BASE_URL}/api/v1/assets/{asset_id}", timeout=30)
            if resp.status_code != 200:
                continue
            detail = resp.json()
            status = detail.get("status")
            payload_types = [p["schema_type"] for p in detail.get("structured_payloads", [])]
            if status == "parsed_scene_llm" and "scene_issue_report_v1" in payload_types:
                print(f"[OK] asset {asset_id}: status={status}, payloads={payload_types}")
                pending.discard(asset_id)
        if pending:
            time.sleep(5)

    if pending:
        print(f"[WARN] The following assets did not reach parsed_scene_llm within timeout: {sorted(pending)}")


def main() -> None:
    image_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(DEFAULT_IMAGE_DIR)
    if not image_dir.is_dir():
        print(f"Image directory not found: {image_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Backend base URL: {BACKEND_BASE_URL}")
    print(f"Using image directory: {image_dir}")

    project_id = create_project("scene_issue_glm_pipeline_test")
    print(f"[PROJECT] Created project id={project_id}")

    asset_ids = upload_scene_issue_images(project_id, image_dir)
    if not asset_ids:
        print("No image files found to upload.")
        return

    print("Now ensure the GLM worker is running, then waiting for results...")
    wait_for_llm_results(asset_ids)


if __name__ == "__main__":
    main()
