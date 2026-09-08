#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华佗·主动问诊引擎（真实可执行逻辑，非文档）。

用法：
  python3 huatuo_engine.py "感冒怕冷鼻塞"           # 文本检索
  python3 huatuo_engine.py "血压高" --json          # JSON 输出
  python3 huatuo_engine.py "胸口剧痛喘不上气"        # 急症红标

逻辑：① 急症红标拦截 → ② 症状→病证归类 → ③ 从 resources/remedies.json 检索验方 →
      ④ 按安全分级（绿/黄）输出卡片 + 红线。
所有配方仅供养生参考，不替代执业医师。
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "resources", "remedies.json")

# 急症关键词：出现即强制就医，不给方（红线）
EMERGENCY = [
    "胸痛", "呼吸困难", "喘不上气", "大出血", "吐血", "咯血", "便血量大", "黑便",
    "中风", "心梗", "昏迷", "抽搐", "休克", "窒息", "骨折", "烧伤", "中毒",
    "过敏休克", "意识", "剧烈腹痛", "高热惊厥", "昏迷不醒", "呕血", "宫外孕",
]

# 症状/病证 → 检索关键词（口语化，覆盖用户怎么搜）
SYMPTOM_MAP = {
    "感冒": ["感冒", "受凉", "鼻塞", "流涕", "打喷嚏", "发烧", "发热恶寒"],
    "咳嗽": ["咳嗽", "咳痰", "咯痰", "久咳", "干咳", "痰多"],
    "失眠": ["失眠", "睡不着", "多梦", "易醒", "睡眠", "安神", "神经衰弱"],
    "血压": ["血压", "头晕目眩", "高血压", "头昏"],
    "胃": ["胃痛", "胃寒", "胃疼", "胃胀", "反酸", "胃溃疡", "十二指肠溃疡", "胃炎", "恶心", "呕吐", "嗳气"],
    "头痛": ["头痛", "偏头痛", "头昏", "头晕"],
    "鼻炎": ["鼻炎", "鼻窦炎", "鼻塞", "鼻痒", "喷嚏"],
    "腹泻": ["腹泻", "拉肚子", "泄泻", "肠炎", "下痢", "痢疾"],
    "便秘": ["便秘", "大便干", "排便"],
    "牙痛": ["牙痛", "牙疼", "牙周炎", "牙齿", "牙"],
    "关节": ["关节", "类风湿", "风湿", "腰痛", "腰疼", "骨刺", "骨质增生", "腰肌", "肩周炎"],
    "皮肤": ["皮肤", "湿疹", "瘙痒", "冻疮", "疮", "癣", "狐臭", "瘊子", "脚气", "脚臭", "皮炎"],
    "前列腺": ["前列腺"],
    "哮喘": ["哮喘", "喘", "气管炎", "支气管炎", "肺气肿", "支气管"],
    "肾": ["肾", "遗精", "遗尿", "腰酸", "肾虚"],
    "乳": ["乳房", "乳腺", "乳腺炎"],
    "儿科": ["小儿", "遗尿", "厌食", "蛲虫", "蛔", "百日咳", "儿童"],
    "产后": ["产后", "子宫", "恶露", "缺乳"],
    "痔": ["痔疮", "肛裂"],
    "眼": ["眼", "视力", "目赤", "眼疲劳", "眼花"],
    "糖尿病": ["糖尿病", "血糖"],
    "肝": ["肝", "脂肪肝"],
    "减肥": ["减肥", "肥胖", "苗条", "瘦"],
    "脑": ["脑血栓", "中风", "癫痫", "健脑", "益智", "健忘"],
    "咽": ["咽炎", "咽喉", "扁桃", "嗓子", "喉咙"],
    "口腔": ["口腔溃疡", "口疮", "口臭"],
    "感冒": ["防感冒", "呼吸道"],
}


def load_db():
    try:
        with open(DB, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def detect_emergency(q):
    return [k for k in EMERGENCY if k in q]


def classify(q):
    keys = []
    for k, vals in SYMPTOM_MAP.items():
        if k in q or any(v in q for v in vals):
            keys.extend(vals)
            keys.append(k)
    # 去重保序
    seen = set()
    return [x for x in keys if not (x in seen or seen.add(x))]


def retrieve(q, keys, db, top=8):
    if not keys:
        return []
    scored = []
    for r in db:
        blob = " ".join([r.get("category", ""), r.get("indication", ""), r.get("name", ""), r.get("effect", "")])
        score = sum(1 for kk in keys if kk in blob)
        if r.get("name", "") in q:
            score += 2
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:top]]


def grade(r):
    src = r.get("source", "")
    name = r.get("name", "")
    if "酒" in name or src == "药酒库":
        return "黄", "含酒精或药材，需辨证、孕妇及服药者慎用，务必遵医嘱"
    if r.get("type") == "tip":
        return "绿", "民间保健法/食疗思路，安全性较高，仍须结合体质"
    return "绿", "食疗/外治调理，老人小孩皆宜，症状不缓解请就医"


def format_card(r):
    g, note = grade(r)
    lines = []
    lines.append(f"【{r['name']}】  「{r['category']}」[{r['source']}]  安全等级：{g}")
    if r.get("ingredients"):
        lines.append(f"· 用料：{r['ingredients']}")
    if r.get("usage"):
        lines.append(f"· 制用法：{r['usage']}")
    if r.get("effect"):
        lines.append(f"· 功效：{r['effect']}")
    if r.get("indication"):
        lines.append(f"· 适应症：{r['indication']}")
    lines.append(f"· 注：{note}")
    return "\n".join(lines)


def run(q, as_json=False):
    db = load_db()
    if not db:
        return {"error": "remedies.json 未生成，请先运行 build_remedies_db.py"}
    emerg = detect_emergency(q)
    if emerg:
        out = {
            "level": "RED",
            "matched_emergency": emerg,
            "reply": "⚠️ 检测到可能涉及急症信号（%s）。华佗不敢替医做主——请立即就医或拨打急救，不要自行用药/偏方。" % "、".join(emerg),
        }
        return out if as_json else out["reply"]
    keys = classify(q)
    if not keys:
        return ({"level": "ASK", "reply": "请补充：① 哪里不舒服（部位）？② 寒热（怕冷/怕热）？③ 急缓（突发/反复）？④ 有无孕/慢病/过敏？以便华佗对症给方。"} if as_json else
                "请补充：① 哪里不舒服（部位）？② 寒热（怕冷/怕热）？③ 急缓（突发/反复）？④ 有无孕/慢病/ 过敏？以便华佗对症给方。")
    hits = retrieve(q, keys, db)
    if not hits:
        return ({"level": "NO_HIT", "reply": "暂无直接匹配的验方，请补充更多症状，或描述具体部位/寒热。"}
                if as_json else "暂无直接匹配的验方，请补充更多症状，或描述具体部位/寒热。")
    blocks = ["【华佗问诊】依据「%s」检索到 %d 条调理思路（仅供养生，非诊疗）：" % ("/".join(keys[:4]), len(hits)), ""]
    for r in hits:
        blocks.append(format_card(r))
        blocks.append("-")
    blocks.append("")
    blocks.append("★ 红线：以上为民间调理思路，复杂体质/孕妇/儿童/慢病/过敏体质请务必就医，不可自行长期服。")
    text = "\n".join(blocks)
    if as_json:
        return {"level": "GREEN", "count": len(hits), "recipes": hits, "text": text}
    return text


def main():
    # 退出码：0=成功 1=参数错 2=知识库缺失 3=运行异常（宿主可据此判断）
    as_json = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--json"]
    q = args[0] if args else ""
    if not q:
        print("【缺参数】用法: python3 huatuo_engine.py \"症状描述\" [--json]")
        print("【示例】python3 huatuo_engine.py \"感冒怕冷鼻塞\"")
        sys.exit(1)
    if not os.path.exists(DB):
        print("【缺知识库】resources/remedies.json 不存在，请先运行 scripts/build_remedies_db.py 生成 339 条验方库。")
        sys.exit(2)
    try:
        res = run(q, as_json)
    except Exception as e:
        print("【运行出错】引擎执行异常：%s（请检查 resources/remedies.json 是否为合法 JSON）" % e)
        sys.exit(3)
    print(res if isinstance(res, str) else json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
