# -*- coding: utf-8 -*-
"""下载公开数据到交付目录的 data/raw，并登记来源、时间、HTTP 状态与 sha256。

用法示例：
    python fetch_data.py --url "https://example.com/a.csv" --out "<交付目录>/data/raw" --source "国家统计局"
    python fetch_data.py --list urls.txt --out "<交付目录>/data/raw"

urls.txt 每行可写 url、url+来源、url+来源+备注（用制表符分隔）。
原始文件只增不改：同名但内容不同的文件会写成 name.1、name.2，不覆盖已有文件。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-modeling-skill/1.0"
MANIFEST_FIELDS = ["文件", "URL", "来源", "抓取时间", "HTTP状态", "字节数", "sha256", "备注"]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def guess_name(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    name = Path(urllib.parse.unquote(path)).name
    return name or ("download_" + datetime.now().strftime("%Y%m%d_%H%M%S"))


def unique_path(target: Path) -> Path:
    if not target.exists():
        return target
    for i in range(1, 1000):
        cand = target.with_name(f"{target.stem}.{i}{target.suffix}")
        if not cand.exists():
            return cand
    raise RuntimeError(f"无法为 {target} 找到可用文件名")


def download(url: str, out_dir: Path, name: str | None, timeout: int, retries: int) -> tuple[Path, int, int]:
    target = out_dir / (name or guess_name(url))
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".part")
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = getattr(resp, "status", 200) or 200
                data = resp.read()
            tmp.write_bytes(data)
            final = unique_path(target)
            tmp.replace(final)
            return final, int(status), len(data)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429 and attempt < retries:
                time.sleep(3 * (attempt + 1))
                continue
            break
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            break
    raise RuntimeError(f"下载失败 {url} -> {last_error}")


def append_manifest(manifest: Path, row: dict) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    new_file = not manifest.exists()
    with manifest.open("a", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def load_list(path: Path) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("\t")]
        items.append((parts[0], parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else ""))
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description="下载公开数据并登记来源")
    ap.add_argument("--url", action="append", default=[], help="可重复，下载单个 URL")
    ap.add_argument("--list", help="批量列表文件")
    ap.add_argument("--out", required=True, help="原始数据目录")
    ap.add_argument("--source", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--name", default=None, help="保存文件名（仅单 URL 时）")
    ap.add_argument("--manifest", default=None, help="来源清单，默认 <out>/../sources.csv")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()

    jobs: list[tuple[str, str, str, str | None]] = [(u, args.source, args.note, args.name) for u in args.url]
    if args.list:
        for url, source, note in load_list(Path(args.list)):
            jobs.append((url, args.source or source, args.note or note, None))
    if not jobs:
        print("[FAIL] 没有可下载的 URL，请用 --url 或 --list")
        return 2

    out_dir = Path(args.out)
    manifest = Path(args.manifest) if args.manifest else out_dir.parent / "sources.csv"
    failures = 0
    for index, (url, source, note, name) in enumerate(jobs):
        if index and args.delay > 0:
            time.sleep(args.delay)
        stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S%z")
        try:
            path, status, size = download(url, out_dir, name, args.timeout, args.retries)
            digest = sha256_of(path)
            append_manifest(manifest, {"文件": path.name, "URL": url, "来源": source, "抓取时间": stamp,
                                       "HTTP状态": status, "字节数": size, "sha256": digest, "备注": note})
            print(f"[OK] {path.name}  {size} 字节  {digest[:12]}")
        except Exception as exc:
            failures += 1
            append_manifest(manifest, {"文件": "", "URL": url, "来源": source, "抓取时间": stamp,
                                       "HTTP状态": "FAILED", "字节数": "", "sha256": "",
                                       "备注": f"{note} | {exc}".strip(" |")})
            print(f"[FAIL] {url} -> {exc}")

    print(f"完成：成功 {len(jobs) - failures}，失败 {failures}，清单 {manifest}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
