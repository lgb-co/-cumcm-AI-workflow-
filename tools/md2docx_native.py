"""Markdown → DOCX：数学公式转为 Word 原生公式（OMML，可在 Word 公式编辑器里直接编辑），不使用图片。

用法：python md2docx_native.py <输入.md> <输出.docx>
说明：把 `\\tag{n}` 改写为 `\\qquad (n)`，使编号随公式一起渲染；表格转 Word 原生表格。
     依赖 pypandoc + python-docx：先运行同目录 setup-md2docx.ps1 建立 工具\\md2docx_env，
     或把 CUMCM_PYTHON / MODELING_PY 指向已装这些依赖的解释器。
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import zipfile

try:
    import pypandoc
except ModuleNotFoundError:  # 面向使用者的可操作报错，而不是裸 traceback
    sys.stderr.write(
        "缺少 pypandoc，无法导出 Word 原生公式。\n"
        "请先运行本工具同目录的 setup-md2docx.ps1 建立导出环境，\n"
        "或把 CUMCM_PYTHON / MODELING_PY 指向已装 pypandoc 的解释器后重试。\n"
        "当前解释器：" + sys.executable + "\n"
    )
    raise SystemExit(3)


def prepare(md: str) -> str:
    md = re.sub(r"\\tag\{(\d+)\}", r"\\qquad (\1)", md)
    md = re.sub(r"\\rm\s+([A-Za-z]+)", r"\\mathrm{\1}", md)
    return md


def reference_docx() -> str | None:
    """取 pandoc 自带 reference.docx 并做最小中文字体调整；取不到就返回 None。"""
    try:
        pandoc = pypandoc.get_pandoc_path()
        data_dir = os.path.normpath(os.path.join(os.path.dirname(pandoc), "..", "data"))
        cand = os.path.join(data_dir, "reference.docx")
        if not os.path.exists(cand):
            out = subprocess.run([pandoc, "--print-default-data-file", "reference.docx"],
                                 capture_output=True, check=False)
            if out.returncode != 0 or not out.stdout:
                return None
            cand = os.path.join(os.environ.get("TEMP", "."), "pandoc_reference.docx")
            io.open(cand, "wb").write(out.stdout)
        from docx import Document
        from docx.oxml.ns import qn
        from docx.shared import Pt
        d = Document(cand)
        normal = d.styles["Normal"]
        normal.font.name = "Times New Roman"
        normal.font.size = Pt(12)
        normal.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        for name, east in (("Heading 1", "黑体"), ("Heading 2", "黑体"), ("Heading 3", "黑体")):
            st = d.styles[name]
            st.font.name = "Times New Roman"
            st.element.rPr.rFonts.set(qn("w:eastAsia"), east)
        out_path = os.path.join(os.environ.get("TEMP", "."), "pandoc_reference_cn.docx")
        d.save(out_path)
        return out_path
    except Exception as e:
        print("[warn] reference.docx 准备失败，将用 pandoc 默认样式:", e)
        return None


def main() -> int:
    src_md, out_docx = sys.argv[1], sys.argv[2]
    raw = io.open(src_md, encoding="utf-8").read()
    tmp = os.path.join(os.environ.get("TEMP", "."), "md2docx_native_tmp.md")
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(prepare(raw))

    args = ["--from=markdown+tex_math_dollars+pipe_tables+raw_tex"]
    ref = reference_docx()
    if ref:
        args += ["--reference-doc", ref]
    pypandoc.convert_file(tmp, "docx", outputfile=out_docx, extra_args=args)

    with zipfile.ZipFile(out_docx) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    n_math = xml.count("<m:oMath")
    n_img = xml.count("<w:drawing") + xml.count("<w:pict")
    print(f"[OK] {os.path.basename(src_md)} -> {os.path.basename(out_docx)}；Word 原生公式 {n_math} 处；图片 {n_img} 处；{os.path.getsize(out_docx)//1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
