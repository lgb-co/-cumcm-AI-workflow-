# -*- coding: utf-8 -*-
"""
ocr_pdf.py — PDF -> 带页码 Markdown
规则：先取文本层；若字符过少或含乱码(U+FFFD)/无中文，判定为扫描或编码损坏，逐页渲染 OCR。
用法：python ocr_pdf.py <输入.pdf> [输出.md] [--force-ocr]
依赖：pymupdf, rapidocr-onnxruntime（本地 CPU）
"""
import argparse
import os
import sys
import tempfile

import pymupdf
from rapidocr_onnxruntime import RapidOCR

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = RapidOCR()
    return _engine


def looks_broken(text, n_chars):
    """文本层不可用时返回 True（扫描件 / CID 乱码）。"""
    if n_chars < 30:
        return True
    if "\ufffd" in text:
        return True
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    ascii_ok = sum(1 for ch in text if ch.isascii() and (ch.isalnum() or ch in " .,;:!?()[]{}<>+-=*/%#$&_|"))
    if cjk + ascii_ok < max(20, n_chars * 0.5):
        return True
    return False


def ocr_page_lines(engine, page, dpi):
    pix = page.get_pixmap(dpi=dpi)
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        pix.save(tmp)
        res, _ = engine(tmp)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    if not res:
        return []
    boxes = []
    for box, text, _score in res:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        boxes.append((min(ys), max(ys), min(xs), text))
    if not boxes:
        return []
    band_h = max(8.0, (max(b[1] for b in boxes) - min(b[0] for b in boxes)) / max(1, len(boxes)) * 0.9)
    boxes.sort(key=lambda b: (b[0], b[2]))
    rows = []
    cur_band = None
    for y0, y1, x0, text in boxes:
        band = int(y0 // band_h) if band_h else 0
        if cur_band is None or band != cur_band:
            rows.append([])
            cur_band = band
        rows[-1].append((x0, text))
    lines = []
    for row in rows:
        row.sort(key=lambda t: t[0])
        lines.append(" ".join(t[1] for t in row))
    return lines


def extract(pdf_path, out_md, dpi=200, force_ocr=False):
    doc = pymupdf.open(pdf_path)
    n_pages = doc.page_count

    use_ocr = force_ocr
    if not use_ocr:
        full = "\n".join(doc[i].get_text() for i in range(n_pages))
        full = full.strip()
        use_ocr = looks_broken(full, len(full))

    engine = get_engine() if use_ocr else None
    parts = []
    for i in range(n_pages):
        page = doc[i]
        if use_ocr:
            lines = ocr_page_lines(engine, page, dpi)
            body = "\n".join(lines) if lines else "（本页未识别到文字，可能为整页图/公式）"
            parts.append(f"## 第 {i+1} 页 [OCR]\n\n{body}\n")
        else:
            t = page.get_text().strip()
            parts.append(f"## 第 {i+1} 页 [文本层]\n\n{t}\n")
    doc.close()

    out = (f"# {os.path.basename(pdf_path)} 提取文本\n\n"
           f"> 方式：{'OCR（逐页渲染识别）' if use_ocr else '文本层直取'} | 页数 {n_pages}\n\n"
           + "\n".join(parts))
    if out_md:
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[ok] {out_md}  ({len(out)} chars, OCR={use_ocr})")
    else:
        sys.stdout.buffer.write(out.encode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out_md", nargs="?", default=None)
    ap.add_argument("--force-ocr", action="store_true")
    ap.add_argument("--dpi", type=int, default=200)
    a = ap.parse_args()
    extract(a.pdf, a.out_md, dpi=a.dpi, force_ocr=a.force_ocr)


if __name__ == "__main__":
    main()

