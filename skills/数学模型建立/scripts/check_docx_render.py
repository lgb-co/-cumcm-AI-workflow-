# -*- coding: utf-8 -*-
"""页面级版式校验：页数、空白页、文字量、图片数量、内容是否贴边（疑似溢出）。

用法：python check_docx_render.py <存放 PDF 的目录>
前置：先用办公软件（Word/WPS/LibreOffice）把 DOCX 导成 PDF，再跑本脚本；
没有导出工具时按 references/文档导出与工具检测.md 的规则如实告知用户，不要跳过校验又声称已检查。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image  # noqa: E402
from pypdf import PdfReader  # noqa: E402

def find_poppler() -> Path | None:
    """定位 pdftoppm：环境变量 MODELING_POPPLER/CUMCM_POPPLER → PATH；都没有返回 None。"""
    for key in ("MODELING_POPPLER", "CUMCM_POPPLER"):
        value = os.environ.get(key)
        if value and Path(value).exists():
            return Path(value)
    found = shutil.which("pdftoppm") or shutil.which("pdftoppm.exe")
    return Path(found) if found else None


POPPLER = find_poppler()
EDGE_BAND = 12  # 距页面边缘多少像素内出现墨迹视为可能溢出


def ink_stats(png: Path) -> tuple[float, bool]:
    with Image.open(png) as im:
        gray = im.convert("L")
        w, h = gray.size
        pixels = gray.load()
        dark = 0
        total = 0
        edge_dark = 0
        step = 2
        for y in range(0, h, step):
            for x in range(0, w, step):
                total += 1
                if pixels[x, y] < 200:
                    dark += 1
                    if x < EDGE_BAND or y < EDGE_BAND or x > w - EDGE_BAND or y > h - EDGE_BAND:
                        edge_dark += 1
        ratio = dark / max(total, 1)
        return ratio, edge_dark > 6


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python check_docx_render.py <存放 PDF 的目录>")
        return 2
    folder = Path(sys.argv[1])
    if not folder.is_dir():
        print("目录不存在：" + str(folder))
        return 2
    if POPPLER is None:
        print("未找到 pdftoppm（poppler）：设置 MODELING_POPPLER 指向 pdftoppm.exe，或把它加入 PATH 后再做页面级校验。")
        return 2
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        print("未找到 PDF")
        return 1
    for pdf in pdfs:
        reader = PdfReader(str(pdf))
        print("=" * 72)
        print(f"{pdf.name}  页数 {len(reader.pages)}  {pdf.stat().st_size / 1024:.0f} KB")
        pics_total = 0
        for i, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            try:
                images = len(page.images)
            except Exception:
                images = 0
            pics_total += images
            with tempfile.TemporaryDirectory() as td:
                subprocess.run([str(POPPLER), "-png", "-r", "60", "-f", str(i), "-l", str(i),
                                str(pdf), str(Path(td) / "page")], capture_output=True, timeout=120)
                rendered = sorted(Path(td).glob("page*.png"))
                if rendered:
                    ratio, touching = ink_stats(rendered[0])
                else:
                    ratio, touching = -1.0, False
            flag = []
            if not text and images == 0:
                flag.append("空白页")
            if touching:
                flag.append("内容贴边")
            if ratio > 0.55:
                flag.append("墨迹过密")
            print(f"  第 {i:2d} 页：文字 {len(text):5d} 字符，图片 {images:3d}，墨迹占比 {ratio:.2%} "
                  + ("← " + "、".join(flag) if flag else ""))
        print(f"  合计内嵌图片 {pics_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
