"""参考库联网补充：按清单抓取宽松许可实现，登记来源与许可。

用法：
    python fetch_reference_library.py --plan                  # 只打印清单，不联网
    python fetch_reference_library.py --fetch                 # 下载允许的来源
    python fetch_reference_library.py --fetch --only toposis  # 只取某一条

规则：
    - 只下载 MIT/BSD/Apache/CC0/公共领域来源，写入 `_vendors/` 并登记 `manifest_sources.csv`；
    - GPL/AGPL 类只在清单里标 `index_only`，不复制代码；
    - 网络失败不改动已有文件，只把状态标为 failed 供重试。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import LIBRARY_DIR, rel  # noqa: E402

SOURCES_FILE = LIBRARY_DIR / "sources.json"
RECORD_FILE = LIBRARY_DIR / "manifest_sources.csv"
ALLOWED_LICENSES = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "CC0-1.0", "public-domain"}
RECORD_FIELDS = ["name", "url", "license", "target", "status", "note", "fetched_at"]


def load_sources() -> list[dict]:
    if not SOURCES_FILE.exists():
        SOURCES_FILE.write_text(json.dumps({"sources": []}, ensure_ascii=False, indent=2), encoding="utf-8")
    return json.loads(SOURCES_FILE.read_text(encoding="utf-8")).get("sources", [])


def load_records() -> dict[str, dict]:
    if not RECORD_FILE.exists():
        return {}
    with RECORD_FILE.open(encoding="utf-8-sig", newline="") as handle:
        return {row["name"]: row for row in csv.DictReader(handle)}


def save_records(records: dict[str, dict]) -> None:
    with RECORD_FILE.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECORD_FIELDS)
        writer.writeheader()
        for row in records.values():
            writer.writerow(row)


def plan(sources: list[dict]) -> int:
    if not sources:
        print("sources.json 为空：当前没有待补充的外部来源。")
        print("添加方式：在 sources.json 的 sources 数组里写入 {name, url, license, target, note}。")
        return 0
    print(f"{'名称':<28}{'许可':<16}{'动作':<12}目标")
    for item in sources:
        license_name = item.get("license", "unknown")
        action = "下载" if license_name in ALLOWED_LICENSES else "仅登记"
        print(f"{item['name'][:26]:<28}{license_name:<16}{action:<12}{item.get('target', '-')}")
    return 0


def fetch_one(item: dict, timeout: int = 60) -> dict:
    name = item["name"]
    license_name = item.get("license", "unknown")
    record = {
        "name": name,
        "url": item.get("url", ""),
        "license": license_name,
        "target": item.get("target", f"_vendors/{name}"),
        "status": "",
        "note": item.get("note", ""),
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    if license_name not in ALLOWED_LICENSES:
        record["status"] = "index_only"
        record["note"] = (record["note"] + "；非宽松许可，仅登记不复制").strip("；")
        return record
    if not item.get("url"):
        record["status"] = "failed"
        record["note"] = "缺少 url"
        return record
    target_dir = LIBRARY_DIR / record["target"]
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = item.get("filename") or Path(item["url"]).name or "download.txt"
    target = target_dir / filename
    try:
        with urllib.request.urlopen(item["url"], timeout=timeout) as response:
            payload = response.read()
        target.write_bytes(payload)
        record["status"] = "fetched"
        record["note"] = (record["note"] + f"；{len(payload)} bytes").strip("；")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        record["status"] = "failed"
        record["note"] = (record["note"] + f"；{exc}").strip("；")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="参考库来源清单与抓取")
    parser.add_argument("--plan", action="store_true", help="只打印清单")
    parser.add_argument("--fetch", action="store_true", help="执行下载/登记")
    parser.add_argument("--only", default="", help="只处理指定名称")
    args = parser.parse_args()

    sources = load_sources()
    if args.only:
        sources = [s for s in sources if s["name"] == args.only]
    if args.plan or not args.fetch:
        return plan(sources)

    records = load_records()
    for item in sources:
        record = fetch_one(item)
        records[record["name"]] = record
        print(f"[{record['status']}] {record['name']} -> {rel(LIBRARY_DIR / record['target'])}")
    save_records(records)
    print(f"[完成] 登记 {len(records)} 条来源记录：{rel(RECORD_FILE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
