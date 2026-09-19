# -*- coding: utf-8 -*-
"""把 Markdown 里的 Mermaid 代码块渲染成 PNG（kroki.io 优先，mermaid.ink 兜底）。

用法：
    python render_mermaid.py --md "<交付目录>/01_建模方案_模型与公式.md" [--outdir diagrams] [--embed]

--embed 会在每个 Mermaid 块后插入/刷新一行图片引用（用 HTML 注释标记，可重复运行）。
渲染失败时保留 Mermaid 源码并打印告警，不影响文档正文。
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FENCE_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
MARK_RE = re.compile(r"<!-- mermaid-render: (.*?) -->")
CLEAN_RE = re.compile(r"<!-- mermaid-render: [^\n]*? -->\n!\[[^\]]*\]\([^)]*\)\n?")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) modeling-skill/1.0"


def slugify(text: str, fallback: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text).strip("-")
    return (cleaned or fallback)[:40]


def post_kroki(code: str, timeout: int) -> bytes:
    req = urllib.request.Request(
        "https://kroki.io/mermaid/png",
        data=code.encode("utf-8"),
        headers={"Content-Type": "text/plain", "User-Agent": UA, "Accept": "image/png"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def get_mermaid_ink(code: str, timeout: int) -> bytes:
    payload = json.dumps({"code": code, "mermaid": {"theme": "default"}}).encode("utf-8")
    token = base64.urlsafe_b64encode(payload).decode("ascii")
    req = urllib.request.Request(f"https://mermaid.ink/img/{token}?type=png",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def render(code: str, timeout: int, engine: str) -> tuple[bytes | None, str]:
    order = ["kroki", "mermaid.ink"] if engine == "auto" else [engine]
    errors: list[str] = []
    for name in order:
        try:
            data = post_kroki(code, timeout) if name == "kroki" else get_mermaid_ink(code, timeout)
            if data[:8] == b"\x89PNG\r\n\x1a\n":
                return data, name
            errors.append(f"{name}: 返回内容不是 PNG")
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    print("     [WARN] 渲染失败：" + "；".join(errors))
    return None, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="渲染 Markdown 中的 Mermaid 块为 PNG")
    ap.add_argument("--md", required=True)
    ap.add_argument("--outdir", default="diagrams")
    ap.add_argument("--engine", default="auto", choices=["auto", "kroki", "mermaid.ink"])
    ap.add_argument("--embed", action="store_true", help="在代码块后插入图片引用")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    md_path = Path(args.md)
    if not md_path.is_file():
        print(f"[FAIL] 找不到文件：{md_path}")
        return 1
    md_path = md_path.resolve()  # 解析为绝对路径，便于写出可移植的相对图片链接
    text = md_path.read_text(encoding="utf-8")
    out_dir = Path(args.outdir)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    blocks = list(FENCE_RE.finditer(text))
    if not blocks:
        print("[WARN] 文档中没有 ```mermaid 代码块，无需渲染")
        return 0

    ok = 0
    written: set[Path] = set()
    inserts: list[tuple[int, str, str]] = []  # (end_pos, rel_path, title)
    for idx, match in enumerate(blocks, 1):
        code = match.group(1).strip("\n")
        head_text = ""
        for h in HEADING_RE.finditer(text[: match.start()]):
            head_text = h.group(1)
        title = head_text or md_path.stem
        name = f"{idx:02d}_{slugify(title, 'diagram')}.png"
        print(f"[..] 渲染第 {idx} 个 Mermaid 块：{title}")
        data, engine = render(code, args.timeout, args.engine)
        if data is None:
            continue
        target = out_dir / name
        if target in written:  # 同一文件内的重名图才加序号；跨次运行按名覆盖，保持幂等
            target = out_dir / f"{target.stem}_{idx}{target.suffix}"
        written.add(target)
        target.write_bytes(data)
        ok += 1
        try:
            rel = target.relative_to(md_path.parent).as_posix()
        except ValueError:
            rel = target.as_posix()
        inserts.append((match.end(), rel, title))
        print(f"     [OK] {target.name}（{engine}）")

    if args.embed and inserts:
        # 关键：先去旧标记，再在“清洗后的文本”上重新定位代码块，否则插入位置会错位（曾把图片插进公式中间）
        cleaned = CLEAN_RE.sub("", text)
        blocks2 = list(FENCE_RE.finditer(cleaned))
        if len(blocks2) != len(inserts):
            print(f"     [WARN] 清洗后代码块数 {len(blocks2)} 与渲染数 {len(inserts)} 不一致，按顺序对齐插入")
        out = cleaned
        offset = 0
        for (end_pos, rel, title), m2 in zip(inserts, blocks2):
            snippet = f"\n\n<!-- mermaid-render: {rel} -->\n![{title}]({rel})\n"
            idx = m2.end() + offset
            out = out[:idx] + snippet + out[idx:]
            offset += len(snippet)
        md_path.write_text(out, encoding="utf-8")
        print(f"[OK] 已在文档中插入 {len(inserts)} 处图片引用（已按清洗后位置对齐）")

    print(f"完成：成功 {ok} / {len(blocks)}，输出目录 {out_dir}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
