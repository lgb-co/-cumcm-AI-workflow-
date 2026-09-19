# -*- coding: utf-8 -*-
"""
extract_code.py — 从国赛论文/PDF 提取"代码相关内容"为带页码 Markdown。

用途（CUMCM 代码编写评价 Skill 的一部分）：
  输入可能是：(a) 含代码附录的论文 PDF（扫描版或文本层版）
              (b) 直接给代码文件（.py/.m/.ipynb）——此时仅做转写/汇总，不做 OCR
规则：
  1. PDF 先取文本层；若判定为扫描件/编码损坏（字符过少、乱码、中英文占比低），逐页渲染 OCR。
  2. OCR 保留行结构与每行置信度；低置信行标记 [OCR-LOW]（转人工复核，禁止自动脑补）。
  3. 对论文，定位"代码区"：优先附录页；再按代码关键词密度标记正文中的代码块。
  4. 输出为 Markdown：页标题 + 文本行（带置信度）；纯文本层 PDF 直接输出其文本。
依赖：pymupdf, rapidocr-onnxruntime（本地 CPU，见 工具\\ocr_env）
用法：
  python extract_code.py <论文.pdf> <输出.md> [--dpi 200] [--force-ocr] [--no-code-filter] [--pages 45-60]
  python extract_code.py <代码文件.py|.m> <输出.md>   # 转写模式
"""
import argparse
import os
import re
import sys
import tempfile

CODE_KEYWORDS = re.compile(
    r"(^|[^A-Za-z_])(def |class |import |from |return |if |elif |else|for |while |"
    r"function |clear|clc|end|global |fprintf|disp\(|print\(|read_excel|readtable|"
    r"csvread|xlsread|load\(|save\(|lambda |self\.|np\.|pd\.|plt\.|cv2\.|scipy|"
    r"matplotlib|pandas|numpy|break|continue|try:|except|with |open\(|range\()",
    re.MULTILINE,
)


def looks_broken(text, n_chars):
    """文本层不可用时返回 True（扫描件 / CID 乱码）。"""
    if n_chars < 30:
        return True
    if "\ufffd" in text:
        return True
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    ascii_ok = sum(
        1 for ch in text if ch.isascii() and (ch.isalnum() or ch in " .,;:!?()[]{}<>+-=*/%#$&_|")
    )
    if cjk + ascii_ok < max(20, n_chars * 0.5):
        return True
    return False


def page_sel(spec, total):
    """解析 '1-3,5' 为 0-based 页索引列表；spec 为空返回 None(全部)。"""
    if not spec:
        return None
    sel = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            for i in range(int(a), int(b) + 1):
                sel.add(i - 1)
        else:
            sel.add(int(part) - 1)
    return sorted(i for i in sel if 0 <= i < total)


def ocr_lines(engine, page, dpi):
    """整页 OCR，返回 [(line_text, avg_conf)]。"""
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
    for box, text, score in res:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        boxes.append((min(ys), max(ys), min(xs), text, float(score)))
    if not boxes:
        return []
    band_h = max(
        8.0,
        (max(b[1] for b in boxes) - min(b[0] for b in boxes)) / max(1, len(boxes)) * 0.9,
    )
    boxes.sort(key=lambda b: (b[0], b[2]))
    lines = []
    cur_band = None
    for y0, y1, x0, text, score in boxes:
        band = int(y0 // band_h) if band_h else 0
        if cur_band is None or band != cur_band:
            lines.append([])
            cur_band = band
        lines[-1].append((x0, text, score))
    out = []
    for row in lines:
        row.sort(key=lambda t: t[0])
        joined = " ".join(t[1] for t in row)
        avg = sum(t[2] for t in row) / len(row)
        out.append((joined, avg))
    return out


def code_score(line):
    """粗略估计一行像不像代码（0~1）。"""
    if not line.strip():
        return 0.0
    hits = 0
    if CODE_KEYWORDS.search(line):
        hits += 1
    if re.search(r"[=+\-*/<>\[\]{}()]{2,}", line):
        hits += 1
    if re.search(r"^\s{2,}\S", line):
        hits += 1
    if re.search(r"\b\d+\.?\d*\s*[=<>]", line):
        hits += 1
    return min(1.0, hits / 3.0)


def extract_pdf(pdf_path, out_md, dpi=200, force_ocr=False, code_filter=True, pages=None):
    import pymupdf
    from rapidocr_onnxruntime import RapidOCR

    doc = pymupdf.open(pdf_path)
    n = doc.page_count
    page_texts = []
    for i in range(n):
        page_texts.append(doc[i].get_text("text"))
    has_text_layer = any(len(t.strip()) > 30 for t in page_texts)
    engine = RapidOCR() if (force_ocr or not has_text_layer) else None

    md = []
    md.append("# 代码提取：" + os.path.basename(pdf_path))
    md.append("> 页数 %d | 文本层可用: %s | dpi %d | 工具: extract_code.py" % (n, has_text_layer, dpi))
    md.append("> 行规则：`[LOW]` 开头=低置信行需人工复核；`[CODE]` 开头=疑似代码行；其余为正文/描述。")

    idxs = page_sel(pages, n) if pages else list(range(n))
    for i in idxs:
        page = doc[i]
        raw = page_texts[i]
        if not force_ocr and not looks_broken(raw, len(raw.strip())):
            lines = [ln.rstrip() for ln in raw.splitlines() if ln.strip()]
            if code_filter and not any(code_score(ln) >= 0.5 for ln in lines):
                continue
            md.append("\n## 第 %d 页（文本层）" % (i + 1))
            for ln in lines:
                if code_filter and code_score(ln) >= 0.5:
                    md.append("[CODE] " + ln)
                else:
                    md.append(ln)
            continue
        lines = ocr_lines(engine, page, dpi)
        if code_filter and not any(code_score(t) >= 0.5 for t, _s in lines):
            continue
        md.append("\n## 第 %d 页（OCR）" % (i + 1))
        for text, score in lines:
            if code_filter and code_score(text) < 0.5:
                continue
            flag = "[LOW] " if score < 0.6 else ("[CODE] " if code_score(text) >= 0.5 else "")
            md.append("%s%s  (conf=%.2f)" % (flag, text, score))
    doc.close()
    os.makedirs(os.path.dirname(os.path.abspath(out_md)) or ".", exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("written:", out_md)


def transcribe_code(code_path, out_md):
    """代码文件转写（供 Skill 读入统一格式；不做 OCR）。"""
    ext = os.path.splitext(code_path)[1].lower()
    with open(code_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    if ext == ".ipynb":
        try:
            import json
            nb = json.loads(text)
            cells = []
            for c in nb.get("cells", []):
                src = "".join(c.get("source", []))
                if c.get("cell_type") == "code":
                    cells.append("```python\n" + src + "\n```")
                elif c.get("cell_type") == "markdown":
                    cells.append(src)
            text = "\n\n".join(cells)
        except Exception:
            pass
    lang = "matlab" if ext == ".m" else "python"
    md = [
        "# 代码文件：" + os.path.basename(code_path),
        "> 语言类型: " + ("MATLAB" if ext == ".m" else ("Jupyter Notebook" if ext == ".ipynb" else "Python/其它")),
        "",
        "```" + lang,
        text,
        "```",
    ]
    os.makedirs(os.path.dirname(os.path.abspath(out_md)) or ".", exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("written:", out_md)


def main():
    ap = argparse.ArgumentParser(description="从论文PDF提取代码 / 转写代码文件")
    ap.add_argument("input", help="PDF 或代码文件路径")
    ap.add_argument("output", nargs="?", help="输出 .md 路径")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--force-ocr", action="store_true")
    ap.add_argument("--no-code-filter", action="store_true", help="不做代码行过滤，输出全文")
    ap.add_argument("--pages", default=None, help="页码选择，如 45-60 或 1,3,5（1-based，默认全部）")
    args = ap.parse_args()

    ext = os.path.splitext(args.input)[1].lower()
    out = args.output or os.path.splitext(args.input)[0] + "_code.md"
    if ext == ".pdf":
        extract_pdf(args.input, out, dpi=args.dpi, force_ocr=args.force_ocr,
                    code_filter=not args.no_code_filter, pages=args.pages)
    else:
        transcribe_code(args.input, out)


if __name__ == "__main__":
    main()
