"""抓取并登记算法方法的权威依据，生成《来源与方法依据》索引。

用法：
    python collect_method_references.py --plan      # 只列出待抓取清单
    python collect_method_references.py --fetch     # 抓取并生成索引

产出：
    references/来源与方法依据.md          # 算法 id ↔ 依据来源 ↔ 抓取时间 ↔ 内容校验值
    references/_methods/<id>.md           # 每个来源的标题与短摘录（仅存必要片段）

说明：只登记公开可访问的方法说明与实现文档，用于核对公式口径；不复制受版权保护的正文，
每条只保留标题、链接、抓取时间与不超过 400 字的摘要片段。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import LIBRARY_DIR, REFERENCES_DIR, rel  # noqa: E402

SOURCE_CSV = LIBRARY_DIR / "method_sources.csv"
EXCERPT_DIR = REFERENCES_DIR / "_methods"
INDEX_FILE = REFERENCES_DIR / "来源与方法依据.md"
USER_AGENT = "Mozilla/5.0 (compatible; CodexResearch/1.0; +local reference check)"
EXCERPT_LIMIT = 400


def load_sources() -> list[dict]:
    with SOURCE_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<sup[^>]*>.*?</sup>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    text = unescape(html)
    return re.sub(r"\s+", " ", text).strip()


def fetch(url: str, timeout: int = 30) -> tuple[str, str, str, int]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    text = raw.decode("utf-8", errors="replace")
    digest = hashlib.sha256(raw).hexdigest()
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", text)
    title = strip_html(title_match.group(1)) if title_match else ""
    body = strip_html(text)
    return title, body, digest, len(raw)


def plan(rows: list[dict]) -> int:
    print(f"{'算法 id':<28}{'类型':<16}{'来源'}")
    for row in rows:
        print(f"{row['id']:<28}{row['kind']:<16}{row['url']}")
    print(f"共 {len(rows)} 条。使用 --fetch 执行抓取。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="抓取算法方法依据并生成索引")
    parser.add_argument("--plan", action="store_true", help="只列出清单")
    parser.add_argument("--fetch", action="store_true", help="执行抓取")
    parser.add_argument("--only", default="", help="只抓取指定算法 id")
    args = parser.parse_args()

    rows = load_sources()
    if args.only:
        rows = [row for row in rows if row["id"] == args.only]
    if args.plan or not args.fetch:
        return plan(rows)

    EXCERPT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for row in rows:
        record = {**row, "status": "", "title": "", "digest": "", "bytes": 0, "note": ""}
        try:
            title, body, digest, size = fetch(row["url"])
            excerpt = body[:EXCERPT_LIMIT] + ("…" if len(body) > EXCERPT_LIMIT else "")
            record.update({"status": "ok", "title": title, "digest": digest[:16], "bytes": size})
            (EXCERPT_DIR / f"{row['id']}.md").write_text(
                "\n".join([
                    f"# {row['name_zh']}（{row['id']}）方法依据",
                    "",
                    f"- 来源：{row['url']}",
                    f"- 标题：{title}",
                    f"- 抓取时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    f"- 内容 SHA256：{digest}",
                    f"- 关注点：{row['key_point']}",
                    "",
                    "## 摘要片段（仅用于核对口径）",
                    "",
                    excerpt,
                    "",
                ]),
                encoding="utf-8",
            )
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError) as exc:
            record.update({"status": "failed", "note": str(exc)[:120]})
        records.append(record)
        flag = "OK  " if record["status"] == "ok" else "FAIL"
        print(f"{flag} {row['id']:<28}{record['title'][:50]}")

    ok_count = sum(1 for item in records if item["status"] == "ok")
    lines = [
        "# 来源与方法依据",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}；成功 {ok_count}/{len(records)} 条。",
        "> 用途：核对每个算法的方法定义与公式口径来源，供写码与评审时引用；正文只保存短摘要，不复制原文。",
        "",
        "| 算法 id | 方法 | 类型 | 来源 | 抓取 | 内容校验（SHA256 前 16 位） |",
        "|---|---|---|---|---|---|",
    ]
    for item in records:
        status = "成功" if item["status"] == "ok" else f"失败（{item['note']}）"
        lines.append(
            f"| `{item['id']}` | {item['name_zh']} | {item['kind']} | {item['url']} | {status} | "
            f"{item['digest'] or '-'} |"
        )
    lines += [
        "",
        "## 使用方式",
        "",
        "1. 写码前在该表里查对应算法的方法依据，核对公式口径（例如 Moran's I 的权重矩阵定义、",
        "   Erlang-C 的分母形式、CFL 条件的表达）。",
        "2. 摘要片段存于 `references/_methods/<id>.md`，只作口径核对，不作为代码来源。",
        "3. 参考实现本身见 `algorithm_library/`，其来源与许可记录在 `registry.csv`。",
        "",
    ]
    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"[写出] {rel(INDEX_FILE)}；摘要目录 {rel(EXCERPT_DIR)}")
    return 0 if ok_count == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
