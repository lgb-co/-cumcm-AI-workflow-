#!/usr/bin/env python3
"""Offline structural checks for Codex reviews; never validates mathematical truth.
JSON paths resolve from the record's directory. See references/review-schema.md.
"""
import argparse
import datetime
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
from urllib.parse import urlparse

OUTPUT_FOLDER = "数学模型评价"
REPORT_FILENAME = "数学模型评价报告.md"
WEIGHTS = {"fit":20,"coverage":10,"data":15,"assumptions":10,"rigor":10,
           "algorithm":10,"feasibility":10,"validation":5,"interpretability":5,"necessity":5}
LABELS = dict(zip(WEIGHTS, ["赛题目标与硬约束契合度","小问覆盖与方案完整性","模型前提与数据适配性","假设合理性","数学表达与逻辑严谨性","求解算法适配性","算法链条与实施可行性","验证与稳健性计划","可解释性与适用边界","方法必要性与针对性改进"]))
EVIDENCE_STATES = {"supported","partial","conflict","unverified"}

def score_items(scores):
    for dimension in scores:
        dim = dimension.get("dimension")
        if "items" in dimension:
            for item in dimension["items"]:
                yield dim, item, item.get("weight")
        else:
            yield dim, dimension, WEIGHTS.get(dim,0)

def intake(record, base):
    inputs = record.get("inputs", {})
    if not isinstance(inputs,dict):
        return {"ready":False,"missing":["inputs: 必须为对象"]}
    missing = []
    def exists(value):
        return isinstance(value,str) and bool(value.strip()) and (Path(base)/value).is_file() and (Path(base)/value).stat().st_size>0
    output_root=inputs.get("output_root")
    if not isinstance(output_root,str) or not output_root.strip():
        missing.append("output_root: 必须指定报告保存路径；将在该路径下创建“数学模型评价”文件夹")
    for key in ("problem","plan"):
        if not exists(inputs.get(key)):
            missing.append(key + ": 未提供可读取文件")
    if inputs.get("attachments_declared") is not True:
        missing.append("attachments_declared: 必须根据赛题确认全部附件清单；无附件也需确认")
    expected = inputs.get("expected_attachments")
    supplied = inputs.get("attachments", [])
    if not isinstance(expected,list) or any(not isinstance(x,str) or not x.strip() for x in expected):
        missing.append("expected_attachments: 需要附件名称列表")
        expected = []
    if not isinstance(supplied,list):
        missing.append("attachments: 需要路径列表")
        supplied = []
    actual = {Path(p).name for p in supplied if exists(p)}
    for name in expected:
        if Path(name).name not in actual:
            missing.append("缺附件: " + name)
    for path in supplied:
        if not exists(path):
            missing.append("附件不可读取: " + str(path))
    return {"ready":not missing,"missing":missing}

def validate(record, base):
    errors = []
    gate = intake(record,base)
    if record.get("status","draft") not in {"missing_inputs","draft","provisional","complete"}:
        errors.append("无效记录状态")
    methods = record.get("methods", [])
    evidence = record.get("evidence", [])
    issues = record.get("issues", [])
    scores = record.get("scores", [])
    if scores:
        for key in ("rubric_version","requirements"):
            if not isinstance(record.get(key),str) or not record[key].strip():
                errors.append("评分前必须冻结 "+key)
    for key in ("methods","evidence","issues","scores"):
        if not isinstance(record.get(key,[]),list) or any(not isinstance(x,dict) for x in record.get(key,[])):
            return {"valid":False,"errors":[key+": 必须为对象列表"],"input_check":gate,"evidence_coverage":0,"evidence_complete":False}
    ids = set()
    claims = set()
    for m in methods:
        mid = m.get("id")
        if not isinstance(mid,str) or not mid or mid in ids:
            errors.append("模型/算法 id 缺失或重复")
            continue
        ids.add(mid)
        if m.get("kind") not in {"model","algorithm","variant"} or not m.get("name"):
            errors.append(mid+": 缺少名称或有效 kind")
        cs = m.get("claims",[])
        if not isinstance(cs,list) or not cs or any(not isinstance(c,str) or not c for c in cs):
            errors.append(mid+": 必须列出待查证主张 id")
            continue
        if len(cs)!=len(set(cs)):
            errors.append(mid+": 主张 id 重复")
        claims.update((mid,c) for c in cs)
    seen = set()
    resolved = set()
    for e in evidence:
        pair = (e.get("method_id"),e.get("claim_id"))
        if not all(isinstance(x,str) and x for x in pair):
            errors.append("证据 method_id/claim_id 必须为非空字符串")
            continue
        if pair not in claims:
            errors.append("证据指向未知模型/主张: "+str(pair))
        seen.add(pair)
        status = e.get("status")
        if status not in EVIDENCE_STATES:
            errors.append("无效证据状态: "+str(pair))
        for key in ("claim","applicability"):
            if not e.get(key): errors.append(str(pair)+": 缺少 "+key)
        if status != "unverified":
            parsed=urlparse(str(e.get("url","")))
            if parsed.scheme not in ('https','http') or not parsed.hostname or re_whitespace(str(e.get('url',''))) or not e.get("locator"):
                errors.append(str(pair)+": 已查证记录需要 URL 和具体支持位置")
            try: datetime.date.fromisoformat(e.get("accessed",""))
            except (ValueError,TypeError): errors.append(str(pair)+": 访问日期须为 YYYY-MM-DD")
            resolved.add(pair)
        elif not e.get("reason"):
            errors.append(str(pair)+": 未核验必须说明原因")
    for pair in sorted(claims-seen): errors.append("缺少证据卡: "+str(pair))
    issue_ids = set()
    for issue in issues:
        iid = issue.get("id")
        if not isinstance(iid,str) or not iid or iid in issue_ids:
            errors.append("问题 id 缺失或重复")
            continue
        issue_ids.add(iid)
        if issue.get("severity") not in {"critical","high","medium","low"}:
            errors.append(iid+": severity 无效")
        for key in ("severity","location","problem","cause","impact","fix","acceptance"):
            if not issue.get(key): errors.append(iid+": 缺少 "+key)
    dims = set()
    charged = set()
    for s in scores:
        dim = s.get("dimension")
        if dim not in WEIGHTS or dim in dims:
            errors.append("评分维度未知或重复: "+str(dim))
            continue
        dims.add(dim)
        if "items" in s:
            items=s["items"]
            if not isinstance(items,list) or not items or any(not isinstance(i,dict) for i in items):
                errors.append(dim+": items 须为非空对象列表")
                continue
            if "ratio" in s: errors.append(dim+": items 与整维 ratio 不能混用")
            weights=[i.get("weight") for i in items]
            if any(isinstance(w,bool) or not isinstance(w,(int,float)) or not math.isfinite(w) or w<=0 for w in weights):
                errors.append(dim+": 子项 weight 须为正数")
            elif not math.isclose(sum(weights),WEIGHTS[dim],abs_tol=1e-8):
                errors.append(dim+": 子项权重合计必须等于维度权重")
            item_ids=[i.get("id") for i in items]
            if any(not isinstance(i,str) or not i for i in item_ids) or len(item_ids)!=len(set(str(i) for i in item_ids)):
                errors.append(dim+": 子项 id 缺失或重复")
    if errors:
        return {"valid":False,"errors":errors,"input_check":gate,"evidence_coverage":round(100*len(claims&resolved)/len(claims),2) if claims else 0,"evidence_complete":False}
    for dim,s,weight in score_items(scores):
        if 'ratio' not in s:errors.append(dim+": 必须明确提供 ratio，未知用 null")
        ratio = s.get("ratio")
        if ratio is not None and (isinstance(ratio,bool) or not isinstance(ratio,(int,float)) or not math.isfinite(ratio) or not 0<=ratio<=1):
            errors.append(dim+": ratio 须为 0..1 或 null")
        for key in ("rationale","location","requirement","improvement"):
            if not s.get(key): errors.append(dim+": 缺少 "+key)
        if not isinstance(s.get("issue_ids",[]),list):
            errors.append(dim+": issue_ids 须为列表")
            continue
        for iid in s.get("issue_ids",[]):
            if not isinstance(iid,str):
                errors.append(dim+": issue_ids 必须为字符串列表")
                continue
            if iid not in issue_ids: errors.append(dim+": 引用未知问题 "+str(iid))
            if iid in charged: errors.append("同一问题重复扣分: "+str(iid))
            charged.add(iid)
    if scores and dims != set(WEIGHTS): errors.append("scores 必须列出全部十个维度，未决维度 ratio=null")
    complete = bool(claims) and claims <= resolved and not any(e.get("status")=="unverified" for e in evidence)
    if record.get("status") == "complete" and (not gate["ready"] or not complete or len(dims)!=10 or any(s.get("ratio") is None for _,s,_ in score_items(scores))):
        errors.append("记录宣称 complete，但输入、证据或评分尚未完成")
    return {"valid":not errors,"errors":errors,"input_check":gate,"evidence_coverage":round(100*len(claims&resolved)/len(claims),2) if claims else 0,"evidence_complete":complete}

def re_whitespace(value):
    return any(c.isspace() for c in value)

def score(record, base):
    check = validate(record,base)
    result = {"status":"draft","score":None,"assessed_weight":0,"coverage_percent":0,"validation":check}
    if not check["input_check"]["ready"]:
        result["status"]="missing_inputs"
        return result
    if not check["valid"] or not record.get("scores"): return result
    assessed = [(s,w) for _,s,w in score_items(record["scores"]) if s.get("ratio") is not None]
    weight = sum(w for s,w in assessed)
    result.update(assessed_weight=weight,coverage_percent=weight)
    if weight:
        result["score"] = round(sum(w*s["ratio"] for s,w in assessed)/weight*100,2)
    result["status"] = "complete" if weight==100 and check["evidence_complete"] else "provisional"
    return result

def report_check(record,base):
    check=validate(record,base)
    errors=list(check["errors"])
    if not check["input_check"]["ready"]:
        return {"valid":False,"errors":check["input_check"]["missing"],"status":"missing_inputs"}
    for key in ("rubric_version","requirements","summary","data_profile","question_reviews","method_reviews","chain_review","optimized_outline","validation_plan","unresolved"):
        value=record.get(key)
        if not isinstance(value,str) or not value.strip() or value.strip()=="待补充":
            errors.append("报告缺少实质内容: "+key)
    if not record.get("methods"): errors.append("报告必须登记所有模型和算法")
    if not record.get("scores"): errors.append("报告必须填写十维评分，未知可为 null")
    return {"valid":not errors,"errors":errors,"status":score(record,base)["status"]}

def report(record,base):
    result=score(record,base)
    state_labels={'complete':'已完成查证与评分','provisional':'暂定评价','draft':'待补充审查记录','missing_inputs':'缺少必交材料'}
    lines=["# 数学建模方案评价报告","","非官方方案诊断；不预测奖项，不证明尚未实施的实验结果。","", "状态："+state_labels[result["status"]]]
    if result["status"]=="missing_inputs":
        return "\n".join(lines+["","## 缺件清单",""]+["- "+x for x in result["validation"]["input_check"]["missing"]])+"\n"
    readiness=report_check(record,base)
    if not readiness["valid"]:
        return "\n".join(lines+["","## 记录校验失败（不出分）",""]+["- "+x for x in readiness["errors"]])+"\n"
    lines += ["",f"评分：{result['score'] if result['score'] is not None else '无可评分项'}；可评权重：{result['coverage_percent']}%；证据核查覆盖：{result['validation']['evidence_coverage']}%。"]
    if result["status"]!="complete": lines += ["暂定评价，不能与完整评价直接比较；未决项不按零分处理。"]
    for key,title in [("summary","总体结论"),("data_profile","输入与数据画像"),("question_reviews","逐问契合度"),("method_reviews","逐模型与算法评价"),("chain_review","链条与影响")]:
        lines += ["","## "+title,"",str(record.get(key,"待补充"))]
    lines += ["","## 评分明细",""]
    for dim,s,weight in score_items(record.get("scores",[])):
        lines += [f"### {LABELS[dim]} / {s.get('id','整维')}（权重 {weight}）","",f"得分比例：{s['ratio'] if s['ratio'] is not None else '未决'}"]
        labels={'location':'方案位置','requirement':'题目要求','rationale':'评分依据','improvement':'修改建议'}
        lines += [f"- {labels[k]}：{s[k]}" for k in labels]
    lines += ["","## 联网证据",""]
    for e in record.get("evidence",[]):
        states={'supported':'支持','partial':'部分支持','conflict':'冲突','unverified':'未核验'}
        lines += [f"### {e['method_id']} / {e['claim_id']}：{states[e['status']]} ({e['status']})",""]
        labels={'claim':'核查主张','locator':'支持位置','accessed':'访问日期','applicability':'本题适用性','reason':'未决原因'}
        if e.get('url'):lines += [f"- 来源：[查看原始依据](<{e['url']}>)"]
        lines += [f"- {labels[k]}：{e.get(k,'—')}" for k in labels]
    lines += ["","## 修改方案（按严重程度排序）",""]
    rank={"critical":0,"high":1,"medium":2,"low":3}
    for i in sorted(record.get("issues",[]),key=lambda i:rank.get(i.get("severity"),4)):
        severity={'critical':'关键错误','high':'高优先级','medium':'中优先级','low':'低优先级'}
        lines += [f"### {i['id']} · {severity[i['severity']]}：{i['problem']}",""]
        labels={'location':'方案位置','cause':'原因','impact':'影响','fix':'具体改法','acceptance':'验收方法'}
        lines += [f"- {labels[k]}：{i[k]}" for k in labels]
    for key,title in [("optimized_outline","优化后的完整脉络"),("validation_plan","建议验证实验"),("unresolved","待核验事项")]:
        lines += ["","## "+title,"",str(record.get(key,"待补充"))]
    return "\n".join(lines)+"\n"

def environment():
    return {"python":sys.version.split()[0],"python_supported":sys.version_info>=(3,11),"standard_library_engine":True,"network":"由宿主 Codex 搜索工具提供，此脚本不测试联网", "optional_modules":{m:importlib.util.find_spec(m) is not None for m in ("pypdf","openpyxl","pymupdf","xlrd","rapidocr_onnxruntime")},"optional_commands":{m:shutil.which(m) for m in ("pdftotext","tesseract","7z","soffice")}}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["intake","validate","score","report","report-check","environment"])
    parser.add_argument("record",nargs="?")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--output-root",type=Path,help="报告保存根路径；其下自动创建“数学模型评价”文件夹")
    args=parser.parse_args()
    failed_report=False
    if args.command=="environment": output=environment()
    else:
        if not args.record: parser.error("此命令需要 JSON 工作记录")
        path=Path(args.record).resolve()
        try:
            record=json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(record,dict): raise ValueError("JSON 顶层必须为对象")
            if args.command=="report" and args.output_root:
                record.setdefault("inputs",{})["output_root"]=str(args.output_root)
            output=globals()[args.command.replace('-','_')](record,path.parent)
            if args.command=="report": failed_report=not report_check(record,path.parent)["valid"]
        except (OSError,ValueError,TypeError) as exc: parser.exit(2,"记录读取/结构错误: "+str(exc)+"\n")
    text=output if isinstance(output,str) else json.dumps(output,ensure_ascii=False,indent=2)
    if args.command=="report":
        if args.output: parser.exit(2,"report 不接受 --output；请用 --output-root，程序会建立“数学模型评价”文件夹\n")
        stored_root=record.get("inputs",{}).get("output_root") if isinstance(record.get("inputs"),dict) else None
        if args.output_root: raw_root=args.output_root
        elif isinstance(stored_root,str) and stored_root.strip(): raw_root=Path(stored_root)
        else: parser.exit(2,"必须用 --output-root 指定报告保存路径\n")
        root=raw_root if raw_root.is_absolute() else path.parent/raw_root
        report_dir=root.resolve()/OUTPUT_FOLDER
        if report_dir.exists() and not report_dir.is_dir(): parser.exit(2,"报告目录位置已被同名文件占用\n")
        report_dir.mkdir(parents=True,exist_ok=True)
        destination=report_dir/REPORT_FILENAME
        if destination.exists():
            stamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            destination=report_dir/f"数学模型评价报告-{stamp}.md"
        destination.write_text(text,encoding="utf-8")
        print(json.dumps({"report":str(destination),"folder":str(report_dir)},ensure_ascii=False,indent=2))
    elif args.output:
        if args.record and args.output.resolve()==Path(args.record).resolve():parser.exit(2,"输出不能覆盖输入工作记录\n")
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else: print(text)
    if failed_report: return 1
    if isinstance(output,dict) and (output.get("valid") is False or output.get("ready") is False or output.get("status") in {"draft","missing_inputs"}): return 1
    return 0

if __name__=="__main__": sys.exit(main())
