# -*- coding: utf-8 -*-
"""国际文献检索：并发查询 OpenAlex / Crossref / arXiv / DOAJ，去重后输出可直接使用的来源表。

用法：
    python search_literature.py --query "sequential probability ratio test" --out sources.md
    python search_literature.py --query "grey relational analysis" --query "TOPSIS evaluation" \
        --from-year 2020 --limit 6 --out 建模方案/<题目>/data/国际文献来源表.md

输出：Markdown 表格（可直接粘进方案文档的“来源与证据”小节）+ 同名 .csv。

说明：OpenAlex 匿名检索可能被服务端临时暂停（返回 503「Anonymous search is paused」），
此时设置环境变量 OPENALEX_API_KEY（免费申请）即可恢复；Crossref / arXiv / DOAJ 不受影响，
因此任一引擎失败都不影响其余引擎出结果。
只读网络，不修改任何既有文件（--out 指向的文件会被覆盖写入）。
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-modeling-skill/1.0"
FIELDS = ["引擎", "标题", "作者", "年份", "期刊或来源", "DOI或链接", "语言", "类型", "被引", "支撑结论（待填）"]


def get(url: str, timeout: int = 30, retries: int = 2) -> bytes:
    """带退避重试；403/429/503 常见于限流或反爬，重试后再失败则交由调用方记录。"""
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/xml, */*"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:160]
            except Exception:
                detail = ""
            last = RuntimeError(f"HTTP {exc.code} {detail}".strip())
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
                continue
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
                continue
    raise last  # type: ignore[misc]


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def shrink(text: str, limit: int = 90) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def search_openalex(query: str, limit: int, from_year: int | None) -> list[dict]:
    params = {"search": query, "per-page": str(limit),
              "select": "title,publication_year,doi,authorships,primary_location,cited_by_count,language,type"}
    if from_year:
        params["filter"] = f"from_publication_date:{from_year}-01-01"
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key  # 免费 key 可避免匿名检索被暂停
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = json.loads(get(url).decode("utf-8"))
    rows = []
    for work in data.get("results", []):
        authors = [a["author"]["display_name"] for a in (work.get("authorships") or [])[:3]]
        src = ((work.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
        rows.append({"引擎": "OpenAlex", "标题": work.get("title") or "", "作者": "; ".join(authors),
                     "年份": work.get("publication_year") or "", "期刊或来源": src,
                     "DOI或链接": work.get("doi") or "", "语言": work.get("language") or "",
                     "类型": work.get("type") or "", "被引": work.get("cited_by_count") or 0,
                     "支撑结论（待填）": ""})
    return rows


def search_crossref(query: str, limit: int, from_year: int | None) -> list[dict]:
    # Crossref 的 select 只接受其白名单字段（language 不在内，会导致 400）
    params = {"query.bibliographic": query, "rows": str(limit),
              "select": "title,author,issued,container-title,DOI,type"}
    if from_year:
        params["filter"] = f"from-pub-date:{from_year}-01-01"
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = json.loads(get(url).decode("utf-8"))
    rows = []
    for item in data.get("message", {}).get("items", []):
        authors = [f"{a.get('family','')} {a.get('given','')}".strip() for a in (item.get("author") or [])[:3]]
        issued = (item.get("issued", {}).get("date-parts") or [[None]])[0][0]
        rows.append({"引擎": "Crossref", "标题": (item.get("title") or [""])[0], "作者": "; ".join(authors),
                     "年份": issued or "", "期刊或来源": (item.get("container-title") or [""])[0],
                     "DOI或链接": f"https://doi.org/{item.get('DOI','')}" if item.get("DOI") else "",
                     "语言": item.get("language") or "", "类型": item.get("type") or "",
                     "被引": "", "支撑结论（待填）": ""})
    return rows


def search_arxiv(query: str, limit: int, from_year: int | None) -> list[dict]:
    url = ("https://export.arxiv.org/api/query?" +
           urllib.parse.urlencode({"search_query": f"all:{query}", "max_results": str(limit), "sortBy": "relevance"}))
    root = ET.fromstring(get(url).decode("utf-8"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    rows = []
    for entry in root.findall("a:entry", ns):
        title = shrink(strip_tags(entry.findtext("a:title", "", ns)), 200)
        authors = [a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns)[:3]]
        published = entry.findtext("a:published", "", ns)[:4]
        link = entry.findtext("a:id", "", ns)
        if from_year and published.isdigit() and int(published) < from_year:
            continue
        rows.append({"引擎": "arXiv", "标题": title, "作者": "; ".join(authors), "年份": published,
                     "期刊或来源": "arXiv 预印本", "DOI或链接": link, "语言": "en", "类型": "preprint",
                     "被引": "", "支撑结论（待填）": ""})
    return rows


def search_doaj(query: str, limit: int, from_year: int | None) -> list[dict]:
    url = f"https://doaj.org/api/search/articles/{urllib.parse.quote(query)}?pageSize={limit}"
    data = json.loads(get(url).decode("utf-8"))
    rows = []
    for item in data.get("results", []):
        bib = item.get("bibjson", {})
        year = bib.get("year") or ""
        if from_year and str(year).isdigit() and int(year) < from_year:
            continue
        authors = [a.get("name", "") for a in (bib.get("author") or [])[:3]]
        links = bib.get("link") or []
        rows.append({"引擎": "DOAJ", "标题": bib.get("title", ""), "作者": "; ".join(authors), "年份": year,
                     "期刊或来源": (bib.get("journal") or {}).get("title", ""),
                     "DOI或链接": (links[0].get("url") if links else ""), "语言": "en",
                     "类型": "journal-article", "被引": "", "支撑结论（待填）": ""})
    return rows


ENGINES = {"openalex": search_openalex, "crossref": search_crossref, "arxiv": search_arxiv, "doaj": search_doaj}


def dedupe(rows: list[dict]) -> list[dict]:
    seen_doi: set[str] = set()
    seen_title: set[str] = set()
    out: list[dict] = []
    for row in rows:
        doi = (row.get("DOI或链接") or "").lower()
        key = re.sub(r"[\s\-—_：:，,。.（）()\[\]]+", "", (row.get("标题") or "").lower())[:60]
        if doi and doi in seen_doi:
            continue
        if key and key in seen_title:
            continue
        if doi:
            seen_doi.add(doi)
        if key:
            seen_title.add(key)
        out.append(row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="国际文献检索并生成来源表")
    ap.add_argument("--query", action="append", required=True, help="可重复；建议中英各写一条")
    ap.add_argument("--out", required=True, help="输出 Markdown 路径（同目录写同名 .csv）")
    ap.add_argument("--limit", type=int, default=6, help="每个引擎每条查询的返回条数")
    ap.add_argument("--from-year", type=int, default=None, help="仅保留该年及以后（arXiv/DOAJ 本地过滤）")
    ap.add_argument("--engines", default="openalex,crossref,arxiv,doaj")
    args = ap.parse_args()

    engines = [e.strip() for e in args.engines.split(",") if e.strip() in ENGINES]
    today = date.today().isoformat()
    all_rows: list[dict] = []
    stats: list[str] = []
    for query in args.query:
        for name in engines:
            try:
                rows = ENGINES[name](query, args.limit, args.from_year)
                stats.append(f"{name}('{shrink(query, 28)}') → {len(rows)} 条")
                all_rows.extend(rows)
            except Exception as exc:
                stats.append(f"{name}('{shrink(query, 28)}') → 失败：{exc}")
            time.sleep(0.5)

    rows = dedupe(all_rows)
    out_md = Path(args.out)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# 国际文献检索结果（{today}）", "",
             f"- 查询式：{' / '.join(args.query)}",
             f"- 引擎：{', '.join(engines)}；起始年份：{args.from_year or '不限'}",
             f"- 去重后共 {len(rows)} 条（原始 {len(all_rows)} 条）", "",
             "| " + " | ".join(FIELDS) + " |",
             "|" + "---|" * len(FIELDS)]
    for row in rows:
        cells = [str(row.get(f, "")) .replace("|", "/") for f in FIELDS]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## 引擎返回统计", ""] + [f"- {s}" for s in stats]
    lines += ["", "> 使用提醒：本表只是检索结果，引用前必须按 `检索与引用规范.md` 核对标题/作者/年份/DOI，",
              "> 并在“支撑结论（待填）”列写明它支撑方案的哪条判断；不可核实的一律不引用。"]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    csv_path = out_md.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] 去重后 {len(rows)} 条 → {out_md}")
    print(f"     同名 CSV：{csv_path}")
    for s in stats:
        print(f"     {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
