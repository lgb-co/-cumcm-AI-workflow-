#!/usr/bin/env python3
"""Read documents/data without executing submitted code. Optional packages by format.
python extract.py INPUT --out OUTPUT.json [--ocr]
JSON retains page/sheet provenance and extraction limitations. It is not a review.
"""
import argparse, collections, csv, io, json, math, pathlib, re, sys, zipfile
import xml.etree.ElementTree as ET

def clean_unicode(value):
    """Replace isolated UTF-16 surrogate code points emitted by damaged PDF maps."""
    if isinstance(value, str):
        return value.encode('utf-8', errors='replace').decode('utf-8')
    if isinstance(value, list):
        return [clean_unicode(item) for item in value]
    if isinstance(value, dict):
        return {clean_unicode(key): clean_unicode(item) for key, item in value.items()}
    return value

def decode(raw):
    for enc in ('utf-8-sig','gb18030','utf-16'):
        try:return raw.decode(enc),enc
        except UnicodeError:pass
    return raw.decode('utf-8',errors='replace'),'utf-8-replacement'

def profile_rows(rows, name):
    count=0; width=0; missing=collections.Counter(); observed=collections.Counter(); types={}; samples=[]
    numeric={}
    for row in rows:
        row=list(row);width=max(width,len(row));count+=1
        if len(samples)<5:samples.append([str(v) if v is not None else None for v in row])
        for j,v in enumerate(row):
            if v is None or v=='':missing[j]+=1;continue
            observed[j]+=1;types.setdefault(j,set()).add(type(v).__name__)
            if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v):
                a=numeric.setdefault(j,[v,v,0]);a[0]=min(a[0],v);a[1]=max(a[1],v);a[2]+=1
    return {'sheet':name,'physical_rows':count,'max_columns':width,'sample_rows':samples,
            'columns':[{'column_1based':j+1,'nonempty':observed[j],
                        'empty_or_absent':count-observed[j],'types':sorted(types.get(j,set())),
                        'numeric_min_max_count':numeric.get(j)} for j in range(width)],
            'note':'Counts include headers, notes and template rows; identify the analytical sample explicitly. Empty cells are not automatically zeros. Units and joins require reading headers and the task.'}

def extract(path,ocr=False):
    p=pathlib.Path(path);ext=p.suffix.lower()
    out={'file':p.name,'format':ext,'status':'read','warnings':[]}
    if ext=='.pdf':
        from pypdf import PdfReader
        reader=PdfReader(str(p));pages=[];engine=None;fitzdoc=None
        for i,page in enumerate(reader.pages):
            try:text=page.extract_text() or ''
            except Exception as exc:
                text='';out['warnings'].append(f'Page {i+1}: native text extraction failed ({type(exc).__name__}).')
            mode='text';uncertain=len(re.sub(r'\s','',text))<30 or '\ufffd' in text or '(cid:' in text
            # A watermark can supply a short text layer over an entirely scanned page.
            if len(text.strip())<250:
                try:
                    resources=page.get('/Resources',{}).get_object()
                    objects=resources.get('/XObject',{}).get_object()
                    if any(obj.get_object().get('/Subtype')=='/Image' for obj in objects.values()):uncertain=True
                except Exception:pass
            if uncertain and ocr:
                import pymupdf
                import numpy as np
                from rapidocr_onnxruntime import RapidOCR
                if engine is None:engine=RapidOCR()
                if fitzdoc is None:fitzdoc=pymupdf.open(str(p))
                pix=fitzdoc[i].get_pixmap(dpi=160,alpha=False)
                array=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
                result,_=engine(array)
                text='\n'.join(r[1] for r in result) if result else ''
                mode='ocr';uncertain=True
            pages.append({'page':i+1,'mode':mode,'needs_visual_check':uncertain,'text':text})
        if fitzdoc is not None:fitzdoc.close()
        out['pages']=pages
        if any(p['needs_visual_check'] for p in pages):
            out['status']='partial';out['warnings'].append('Some pages need OCR or visual confirmation; formulas/tables are not certified by extracted text.')
    elif ext in ('.docx','.pptx'):
        with zipfile.ZipFile(p) as z:
            names=['word/document.xml'] if ext=='.docx' else sorted((n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+.xml',n)),key=lambda n:int(re.search(r'(\d+)\.xml',n).group(1)))
            sections=[]
            for n in names:
                root=ET.fromstring(z.read(n))
                lines=[]
                for para in root.iter():
                    if para.tag.rsplit('}',1)[-1]=='p':
                        lines.append(''.join(t.text or '' for t in para.iter() if t.tag.rsplit('}',1)[-1] in ('t','tab')))
                sections.append({'part':n,'text':'\n'.join(lines)})
            out['sections']=sections
            out['warnings'].append('Embedded images, equation layout and page locations require visual review.')
    elif ext in ('.xlsx','.xlsm'):
        import openpyxl
        wb=openpyxl.load_workbook(p,read_only=True,data_only=True)
        try:out['sheets']=[profile_rows(s.iter_rows(values_only=True),s.title) for s in wb]
        finally:wb.close()
        out['warnings'].append('Cached formula values only; workbook macros are never run. Formula cells without cached results may appear empty.')
    elif ext=='.xls':
        import xlrd
        wb=xlrd.open_workbook(p,on_demand=True)
        try:out['sheets']=[profile_rows((s.row_values(i) for i in range(s.nrows)),s.name) for s in wb.sheets()]
        finally:wb.release_resources()
    elif ext in ('.csv','.tsv'):
        text,encoding=decode(p.read_bytes());out['encoding']=encoding
        try:dialect=csv.Sniffer().sniff(text[:16000],delimiters=',\t;')
        except csv.Error:dialect=csv.excel_tab if ext=='.tsv' else csv.excel
        out['sheets']=[profile_rows(csv.reader(io.StringIO(text),dialect),p.stem)]
    elif ext in ('.doc','.ppt'):
        out['status']='needs_conversion';out['warnings'].append('Use convert-office.ps1 on Windows with Microsoft Office, or a local LibreOffice conversion, then inspect the converted document. Never execute macros.')
    else:
        text,encoding=decode(p.read_bytes());out.update(text=text,encoding=encoding)
        if encoding.endswith('replacement'):out['status']='partial';out['warnings'].append('Text encoding was not reliably recognized.')
    return clean_unicode(out)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input');ap.add_argument('--out',required=True);ap.add_argument('--ocr',action='store_true');a=ap.parse_args()
    try:result=extract(a.input,a.ocr)
    except Exception as e:result={'file':pathlib.Path(a.input).name,'status':'error','error':f'{type(e).__name__}: {e}'}
    dst=pathlib.Path(a.out);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({'output':str(dst),'status':result['status']},ensure_ascii=False));return 1 if result['status']=='error' else 0
if __name__=='__main__':sys.exit(main())
