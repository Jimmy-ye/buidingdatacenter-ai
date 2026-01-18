import argparse
import sys
from pathlib import Path

import requests


BASE_URL = "http://127.0.0.1:8000"


def create_project(name: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/api/v1/projects/",
        json={"name": name, "description": "Smoke test project"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["id"]


def upload_image_with_auto_route(project_id: str, image_path: Path, content_role: str) -> dict:
    files = {"file": (image_path.name, image_path.read_bytes(), "image/jpeg")}
    params = {
        "project_id": project_id,
        "source": "smoke_test",
        "content_role": content_role,
        "auto_route": True,
    }
    data = {
        "note": f"Smoke test for {content_role}",
        "title": f"Smoke {content_role}",
    }
    resp = requests.post(
        f"{BASE_URL}/api/v1/assets/upload_image_with_note",
        params=params,
        data=data,
        files=files,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def get_asset_detail(asset_id: str) -> dict:
    resp = requests.get(f"{BASE_URL}/api/v1/assets/{asset_id}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test for image auto routing (OCR vs scene LLM)")
    parser.add_argument("meter_image", type=Path, help="Path to a meter/nameplate image")
    parser.add_argument(
        "scene_image",
        type=Path,
        nargs="?",
        help="Optional path to a scene_issue image (problems / status photo)",
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL,
        help="Backend base URL (default: http://127.0.0.1:8000)",
    )

    args = parser.parse_args()
    global BASE_URL
    BASE_URL = args.base_url.rstrip("/")

    for p in [args.meter_image, args.scene_image] if args.scene_image else [args.meter_image]:
        if p and not p.is_file():
            print(f"File not found: {p}", file=sys.stderr)
            sys.exit(1)

    print("[1] Creating smoke test project...")
    project_id = create_project("image-routing-smoke-test")
    print(f"    Project ID: {project_id}")

    print("[2] Uploading meter/nameplate image with auto_route=true...")
    meter_resp = upload_image_with_auto_route(project_id, args.meter_image, "meter")
    meter_id = meter_resp["id"]
    print(f"    Asset ID (meter): {meter_id}, status={meter_resp.get('status')}")

    meter_detail = get_asset_detail(meter_id)
    payload_types = [p["schema_type"] for p in meter_detail.get("structured_payloads", [])]
    print(f"    Structured payload types: {payload_types}")

    if "image_annotation" not in payload_types:
        print("    [WARN] No image_annotation payload found for meter image", file=sys.stderr)
    else:
        print("    [OK] image_annotation payload present for meter image")

    if args.scene_image:
        print("[3] Uploading scene_issue image with auto_route=true...")
        scene_resp = upload_image_with_auto_route(project_id, args.scene_image, "scene_issue")
        scene_id = scene_resp["id"]
        print(f"    Asset ID (scene_issue): {scene_id}, status={scene_resp.get('status')}")

        scene_detail = get_asset_detail(scene_id)
        scene_payload_types = [p["schema_type"] for p in scene_detail.get("structured_payloads", [])]
        print(f"    Structured payload types: {scene_payload_types}")

        if "image_route_decision_v1" not in scene_payload_types:
            print("    [WARN] No image_route_decision_v1 payload found for scene_issue image", file=sys.stderr)
        else:
            print("    [OK] image_route_decision_v1 payload present for scene_issue image")

    print("[DONE] Smoke test completed.")


if __name__ == "__main__":
    main()
