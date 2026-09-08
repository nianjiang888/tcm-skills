#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 4 个民间包的真实卡片（百酒/百粥/百汤/百姓）抽取结构化验方，生成 resources/remedies.json。
仅做本地可逆操作，无任何外部依赖。
"""

import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SOURCES = [
    ("药酒库", os.path.join(BASE, "tcm-baijiu-1.0.0", "baijiu-cards.md")),
    ("粥疗库", os.path.join(BASE, "tcm-baizhou-1.0.0", "baizhou-cards.md")),
    ("汤疗库", os.path.join(BASE, "tcm-baitang-1.0.0", "baitang-cards.md")),
    ("民间综合库", os.path.join(BASE, "tcm-baixing-1.0.0", "baixing-cards.md")),
]

FIELD_MAP = [
    (r"用料", "ingredients"),
    (r"用料与方法|用法", "usage"),
    (r"制用法", "usage"),
    (r"方法", "usage"),
    (r"功效", "effect"),
    (r"适应症|适应证", "indication"),
]


def clean_text(t):
    # 去掉 LaTeX 噪声
    t = re.sub(r"\\text\{(.*?)\}", r"\1", t)
    t = re.sub(r"\$\$?.*?\$?\$", "", t)
    return t.strip()


def parse_file(source_label, path):
    if not os.path.exists(path):
        print("missing", path)
        return []
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    entries = []
    current_cat = "未归类"
    cur = None
    field_lines = {}

    def flush():
        nonlocal cur
        if cur and (cur.get("ingredients") or cur.get("usage") or cur.get("effect") or cur.get("indication")):
            entries.append(cur)

    for raw in lines:
        line = raw.strip()
        if line.startswith("## "):
            flush()
            cur = None
            m = re.match(r"##\s*◆\s*(.+)", line)
            if m:
                current_cat = clean_text(m.group(1))
            else:
                current_cat = clean_text(line.lstrip("# ").strip())
            continue
        if line.startswith("### "):
            flush()
            cur = {
                "name": clean_text(line[3:].strip()),
                "category": current_cat,
                "source": source_label,
                "type": "recipe",
                "ingredients": "",
                "usage": "",
                "effect": "",
                "indication": "",
            }
            continue
        if cur is not None:
            m = re.match(r"-\s*\*\*(.+?)\*\*[：:]\s*(.*)", line)
            if m:
                key = m.group(1)
                val = clean_text(m.group(2))
                target = None
                for pat, fld in FIELD_MAP:
                    if re.search(pat, key):
                        target = fld
                        break
                if target:
                    cur[target] = (cur[target] + " " + val).strip() if cur[target] else val
                continue
        # 平铺条目（百姓索引中的 `- 标题` 形式，无结构化字段）
        m2 = re.match(r"-\s+(?![\*\d])(.+)$", line)
        if m2 and not line.startswith("- **") and cur is None:
            txt = clean_text(m2.group(1))
            if txt:
                entries.append({
                    "name": txt,
                    "category": current_cat,
                    "source": source_label,
                    "type": "tip",
                    "ingredients": "",
                    "usage": "（详见原书《百姓治百病》对应条目，本章为索引）",
                    "effect": "",
                    "indication": txt,
                })
    flush()
    return entries


def main():
    all_entries = []
    for label, path in SOURCES:
        all_entries.extend(parse_file(label, path))
    # 去重（同名同出处）
    seen = set()
    dedup = []
    for e in all_entries:
        k = (e["name"], e["source"], e["category"])
        if k in seen:
            continue
        seen.add(k)
        dedup.append(e)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources", "remedies.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dedup, f, ensure_ascii=False, indent=2)
    print("total entries:", len(dedup))
    by_src = {}
    for e in dedup:
        by_src[e["source"]] = by_src.get(e["source"], 0) + 1
    print("by source:", by_src)
    by_cat = {}
    for e in dedup:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
    tops = sorted(by_cat.items(), key=lambda x: -x[1])[:30]
    print("top categories:", tops)


if __name__ == "__main__":
    main()
