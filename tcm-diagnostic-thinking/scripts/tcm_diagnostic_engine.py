#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扁鹊·辨证思维引擎（tcm_diagnostic_engine.py）
输入一段症状/体质描述，输出：
  ① 急症红线判定（命中→强制就医，不给方向）
  ② 症状线索 → 证素方向匹配（基于《中医诊断学》证型库）
  ③ 五步思维提示（辨症→辨证→辨病→辨人→辨机）
  ④ 建议补充采集的四诊信息 + 红线声明
仅供辨证思路引导，非诊疗、非确诊。
"""
import sys
import os
import json
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, "resources", "syndromes.json")


def load_db():
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)


def check_red_flag(text, db):
    hits = [w for w in db.get("red_flags", []) if w in text]
    return hits


def match_syndromes(text, db, top=5):
    results = []
    for s in db.get("syndromes", []):
        score = sum(1 for c in s.get("clues", []) if c in text)
        if score > 0:
            results.append((score, s))
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top]


def run(text, as_json=False):
    db = load_db()
    text = (text or "").strip()
    out = {"input": text}

    rf = check_red_flag(text, db)
    out["red_flag"] = rf
    if rf:
        out["verdict"] = "强制就医"
        out["message"] = "检测到可能属于急症/危重症的信号（%s）。本工具不处理急症，请立即前往医院或拨打急救电话。" % "、".join(rf)
        out["action"] = "立即就医，不要依赖任何自助辨证"
        return _emit(out, as_json)

    matched = match_syndromes(text, db)
    if not matched:
        out["verdict"] = "信息不足"
        out["directions"] = []
        out["message"] = "未从描述中匹配到明确证素线索。请补充四诊信息后再分析。"
    else:
        directions = []
        for score, s in matched:
            directions.append({
                "name": s["name"],
                "domain": s["domain"],
                "hint": s["hint"],
                "matched_clues": score,
                "total_clues": len(s["clues"]),
            })
        out["verdict"] = "思路方向"
        out["directions"] = directions
        out["message"] = "以下为可能的辨证方向（按线索匹配度排序），仅供思路参考，非确诊："

    out["five_step"] = ["辨症（确认症状有无/真假/偏全）",
                        "辨证（八纲→病性→病位，定证名）",
                        "辨病（确定疾病诊断，中西对应）",
                        "辨人（性别/年龄/体质/习惯差异）",
                        "辨机（机制与传变趋势，先安未受邪之地）"]
    out["four_diagnosis"] = db.get("four_diagnosis_prompt", [])
    out["redline"] = "本工具为学习/思路引导，非诊疗、非确诊；最终诊断须由执业中医师四诊合参完成；急症立即就医。"
    out["action"] = "补充四诊信息后复诊思路，或直接咨询执业中医师"
    return _emit(out, as_json)


def _emit(out, as_json):
    if as_json:
        return json.dumps(out, ensure_ascii=False, indent=2)
    lines = []
    lines.append("🔍 扁鹊·辨证思维引导")
    lines.append("─" * 32)
    lines.append("· 输入：%s" % out["input"])
    if out.get("red_flag"):
        lines.append("⚠ 急症红线命中：%s" % "、".join(out["red_flag"]))
        lines.append(out["message"])
        lines.append("★ 动作：%s" % out["action"])
        return "\n".join(lines)
    lines.append("· 结论：%s" % out["verdict"])
    if out.get("directions"):
        lines.append(out["message"])
        for i, d in enumerate(out["directions"], 1):
            lines.append("  %d. %s（%s）线索 %d/%d — %s" % (i, d["name"], d["domain"], d["matched_clues"], d["total_clues"], d["hint"]))
    else:
        lines.append(out["message"])
    lines.append("─" * 32)
    lines.append("· 五步思维：")
    for s in out["five_step"]:
        lines.append("   %s" % s)
    lines.append("· 建议补充采集（四诊）：")
    for p in out["four_diagnosis"]:
        lines.append("   - %s" % p)
    lines.append("★ 红线：%s" % out["redline"])
    return "\n".join(lines)


if __name__ == "__main__":
    arg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if arg == "--json" and not sys.stdin.isatty():
        arg = sys.stdin.read()
    is_json = "--json" in sys.argv
    if is_json:
        arg = arg.replace("--json", "").strip()
    print(run(arg, as_json=is_json))
