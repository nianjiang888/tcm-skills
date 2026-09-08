#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate A4 printable 华佗养生速查手册 (HTML -> print to PDF)."""
import argparse
import html
import os

CARDS = [
    ("风寒感冒", [
        ("葱豉酒", "生大葱30克，淡豆豉15克，黄酒50毫升",
         "豆豉加水煮10分钟，放大葱煎沸5分钟，加黄酒出锅，趁热服下。",
         "发汗解表，祛寒和胃", "风寒感冒，发热头痛，恶心呕吐"),
        ("雪里蕻豆腐粥", "新鲜雪里蕻100克，嫩豆腐60克，生姜5克，连须葱白2根，大米100克",
         "大米煮粥，五成熟加雪里蕻、豆腐、姜丝、葱白，再煮至熟。每日1次，3-5天。",
         "宣肺豁痰、温中散寒、发汗解表", "风寒感冒，发热畏寒头痛"),
        ("雪菜豆腐汤", "新鲜雪里蕻100克，嫩豆腐100克，姜丝10克，葱白30克，精盐味精适量",
         "同料煮汤，熟后调味。每日1-2次，5-7天。",
         "宣肺豁痰、温中利水、发汗解表", "风寒感冒，发热恶寒、鼻塞流清涕"),
    ]),
    ("风热感冒", [
        ("薄荷汤", "新鲜薄荷30克，冰糖20克",
         "薄荷、冰糖加水烧开再煮2-3分钟。每日2次，5-7天。",
         "疏散风热、清咽利喉", "风热感冒，咽喉肿痛、痰涕黄稠"),
        ("桑叶菊花汤", "桑叶10克，菊花30克，白糖适量",
         "煮沸后文火3-5分钟，调白糖饮服。每日2次，5-7天。",
         "疏风清热、平肝明目", "风热感冒、目赤肿痛"),
    ]),
    ("咳嗽", [
        ("雪梨酒", "雪梨500克，白酒1000毫升",
         "雪梨去皮核切块，浸入酒内密封7日。每取适量，每日2-3次。",
         "清热化痰，生津润燥", "咳嗽、烦渴、痰热、便秘"),
        ("桑白皮酒", "桑白皮100克，米酒500毫升",
         "桑白皮粗末浸酒密封7日。每服15-20毫升，每日3次。",
         "泻肺行水，清肺止咳", "肺热咳喘，痰黄而稠"),
        ("鸭蛋银耳粥", "鸭蛋1只，银耳30克，大米100克，米醋5ml，白糖30克",
         "银耳泡发，大米煮粥，八成熟加银耳，熟后打蛋调匀加醋糖。每日2次。",
         "润肺生津、清热止咳", "肺阴虚咳嗽，咽干痰少"),
    ]),
    ("失眠", [
        ("茯苓粥", "茯苓粉与大米同煮为粥",
         "日常早餐食用。", "宁心安神", "失眠、心神不宁"),
    ]),
    ("头痛", [
        ("蔓荆子酒", "蔓荆子200克，白酒500毫升",
         "制粗末浸酒密封7日去渣。每服10-15毫升，每日3次。",
         "疏散风热、清利头目", "风热头昏头痛、偏头痛"),
    ]),
    ("血压偏高", [
        ("橘皮降血压", "橘皮（陈皮）泡水代茶饮",
         "日常代茶。", "理气化痰、辅助降压", "血压偏高、痰多胸闷"),
        ("绿豆汤", "绿豆30-50克，冰糖适量",
         "煮烂加冰糖，日常饮用。", "祛热解暑、降压明目", "暑热、高血压"),
    ]),
    ("脾胃虚寒", [
        ("生姜萝卜粥", "生姜15克，白萝卜100克，大米100克，红糖50克",
         "大米煮粥，八成熟加萝卜、姜丝、红糖再煮。每日1-2次。",
         "温中散寒", "胃寒、风寒兼胃不适"),
        ("葱姜汤", "连根须大葱50克，生姜6克，精盐味精适量",
         "葱末姜丝加水煮沸15分钟，调味趁热服。每日2次。",
         "温中散寒、和胃止呕", "胃脘冷痛、恶心呕吐"),
    ]),
    ("牙痛", [
        ("生姜片止牙痛", "生姜切片", "咬在痛处或外敷。", "温中散寒止痛", "牙痛（寒性）"),
    ]),
    ("鼻炎", [
        ("丝瓜藤粥", "鲜丝瓜藤50克，大米60克，蜂蜜30克",
         "丝瓜藤煎煮30分钟去渣，加大米煮粥，熟后调蜂蜜。每日2次，3-5天。",
         "通筋活络、去痰镇咳", "鼻炎、咳嗽有浓痰"),
    ]),
]


def build(name: str, use: str, out: str) -> str:
    esc = html.escape
    parts = []
    parts.append(f"<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>")
    parts.append("<title>华佗养生速查手册</title>")
    parts.append("<style>body{font-family:'Songti SC',serif;max-width:820px;margin:24px auto;padding:0 16px;color:#222}"
                 "h1{text-align:center;border-bottom:3px solid #b00;padding-bottom:8px}"
                 ".meta{color:#666;font-size:13px;text-align:center;margin-bottom:18px}"
                 ".cat{margin-top:22px}h2{color:#b00;border-left:6px solid #b00;padding-left:10px}"
                 ".card{border:1px solid #ddd;border-radius:8px;padding:10px 14px;margin:8px 0;background:#fffdf7}"
                 ".name{font-weight:700;color:#333}.tag{color:#888;font-size:12px}"
                 "ul{margin:4px 0 0 18px;padding:0}.warn{color:#b00;font-size:12px;margin-top:14px}"
                 "@media print{body{max-width:none}}</style></head><body>")
    parts.append(f"<h1>华佗养生速查手册</h1>")
    parts.append(f"<div class='meta'>姓名：{esc(name)}　用途：{esc(use)}　|　仅供养生参考，非诊疗，务必遵医嘱</div>")
    for cat, items in CARDS:
        parts.append(f"<div class='cat'><h2>{esc(cat)}</h2>")
        for n, use0, how, eff, ind in items:
            parts.append(f"<div class='card'><div class='name'>{esc(n)}</div>"
                         f"<ul>"
                         f"<li>用料：{esc(use0)}</li>"
                         f"<li>制用法：{esc(how)}</li>"
                         f"<li>功效：{esc(eff)}</li>"
                         f"<li>适应症：{esc(ind)}</li>"
                         f"</ul></div>")
        parts.append("</div>")
    parts.append("<p class='warn'>⚠ 急症（胸痛/呼吸困难/大出血/意识改变）立即就医；孕妇、儿童、慢病、过敏体质请遵医嘱。本手册非诊疗、非处方。</p>")
    parts.append("</body></html>")
    text = "".join(parts)
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    return out


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--name", default="使用者")
    a.add_argument("--use", default="日常养生")
    a.add_argument("--out", default="huatuo_handbook.html")
    args = a.parse_args()
    out = build(args.name, args.use, args.out)
    print("生成完成:", os.path.abspath(out))
