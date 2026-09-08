#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中医证候检索手册 生成器
========================
根据用户的「专长领域 / 学习层次 / 姓名」生成 A4 HTML 检索手册，可浏览器打印存 PDF。

用法：
  python build_syndrome_manual.py --focus 内科 --level 入门 --name 示例医学生 --out manual.html
  python build_syndrome_manual.py --focus 外感温病 --level 临床 --name 王大夫 --out /tmp/m.html

参数：
  --focus  专长领域: 全科 | 内科 | 妇科 | 儿科 | 外感温病  (默认 全科)
  --level  学习层次: 入门 | 进阶 | 临床                (默认 入门)
  --name   使用者姓名                               (默认 中医学习者)
  --out    输出 html 路径                           (默认 syndrome-manual.html)
"""
import argparse
import html
import datetime

# ---- 12 门索引（源自《中医证候学》以病因为纲）----
DOORS = [
    ("L01", "风证门", "风邪", "卫气失宣、清阳郁遏、营卫失调"),
    ("L02", "寒证门", "寒邪", "卫阳失宣、清阳虚郁、阳气虚郁"),
    ("L03", "暑证门", "暑邪", "暑伤津气、暑湿困脾"),
    ("L04", "湿证门", "湿邪", "清阳不化、气液郁蒸、脾气虚湿困"),
    ("L05", "燥证门", "燥邪", "清燥失润、津伤"),
    ("L06", "火(阳)证门", "火/热邪", "清气郁蒸、气血郁蒸、虚阳浮越"),
    ("L07", "气证门", "气机失调", "气郁、气滞、气逆、气虚"),
    ("L08", "痰证门", "痰浊", "痰热、风痰、痰湿"),
    ("L09", "饮证门", "饮停", "饮停胸胁、饮溢肢体"),
    ("L10", "瘀(血)证门", "瘀血", "气血郁滞、血瘀阻络、血脱"),
    ("L11", "食证门", "食滞", "食滞、虫滞"),
    ("L12", "虚证门", "正气虚", "气血阴阳虚、阳虚失固/失摄/虚脱"),
]

# ---- 专长领域 → 推荐检索范围 ----
FOCUS_MAP = {
    "全科": "12 门全览 + 脏腑各论 心/肝/脾/肺/肾/胃",
    "内科": "脏腑各论为主：心、肝、脾、肺、肾、胃病证类 + 虚证门",
    "妇科": "肝、肾、脾病证类 + 气血虚/瘀 + 冲任相关兼病",
    "儿科": "肺卫、脾胃、惊风(肝风) + 食滞门 + 气虚卫外",
    "外感温病": "风/寒/暑/湿/燥/火 六门 + 六经/卫气营血/三焦体系",
}

# ---- 六阶学习路线（与 learning-progression.md 对应）----
STAGES = [
    ("第1阶 总论筑基", "证/候/方症三级体系；12门45类框架；主副宾症", "能默写12门、看懂 L0x-Zxx-Hxxx 编码"),
    ("第2阶 病因证候", "12门逐门击破，每门2-3代表候", "每门能举1证+1方+1鉴别"),
    ("第3阶 病机基础", "气血津液、脏腑、经络；虚证门细化", "能把症状定到 门→类"),
    ("第4阶 外感体系", "六经 / 卫气营血 / 三焦，与六淫衔接", "能判外感层次、预判传变"),
    ("第5阶 脏腑各论", "45类281证，精读心肝肾脾胃肺", "每系统背3证3方+鉴别"),
    ("第6阶 综合临床", "复合证候、传变截断、方症对应、医案", "能写 门→类→证→候→方症 链条"),
]

LEVEL_HINT = {
    "入门": "重点放在第1–2阶与速查卡，先建立「门→类」直觉。",
    "进阶": "推进第3–4阶，打通病机与外感体系，开始合参兼病。",
    "临床": "直攻第5–6阶，用原书1870候与医案训练检索与截断眼光。",
}


def render_html(name, focus, level, out):
    f = FOCUS_MAP.get(focus, FOCUS_MAP["全科"])
    lvl = LEVEL_HINT.get(level, LEVEL_HINT["入门"])
    today = datetime.date.today().isoformat()

    door_rows = "".join(
        f"<tr><td><b>{code}</b></td><td>{dname}</td><td>{cause}</td><td>{rep}</td></tr>"
        for code, dname, cause, rep in DOORS
    )
    stage_rows = "".join(
        f"<tr><td><b>{s[0]}</b></td><td>{s[1]}</td><td>{s[2]}</td></tr>"
        for s in STAGES
    )
    checklist = "".join(
        f"<p>☐ {s[0]} —— {s[1]}</p>" for s in STAGES
    )

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>中医证候检索手册 · {html.escape(name)}</title>
<style>
@page {{ size: A4; margin: 16mm 14mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: "SimSun","Songti SC",serif; color:#1a1a1a; font-size:12.5px; line-height:1.7; }}
h1 {{ font-size:22px; text-align:center; margin:0 0 2px; }}
.sub {{ text-align:center; color:#666; font-size:12px; margin-bottom:14px; }}
h2 {{ font-size:15px; border-left:5px solid #8a1f1f; padding-left:8px; margin:18px 0 8px; color:#8a1f1f; }}
table {{ width:100%; border-collapse:collapse; margin:6px 0 10px; }}
th,td {{ border:1px solid #bbb; padding:5px 7px; vertical-align:top; }}
th {{ background:#f3ece6; font-weight:bold; }}
.note {{ background:#faf6f0; border:1px dashed #c9a; padding:8px 10px; font-size:12px; }}
.tag {{ display:inline-block; background:#8a1f1f; color:#fff; padding:2px 8px; border-radius:3px; font-size:11px; }}
.foot {{ margin-top:18px; font-size:10.5px; color:#888; border-top:1px solid #ddd; padding-top:6px; }}
</style></head>
<body>
<h1>中医证候检索手册</h1>
<div class="sub">基于《中医证候学》（李洪成等·中国医药科技出版社 2007）· 证—候—方症 三级体系</div>
<p style="text-align:center"><span class="tag">使用者 {html.escape(name)}</span>
<span class="tag">专长 {html.escape(focus)}</span>
<span class="tag">层次 {html.escape(level)}</span>
<span class="tag">生成 {today}</span></p>

<h2>一、本手册用法（先读）</h2>
<div class="note">
辨证三步：<b>先定「门」（病因）→ 再定「类」（脏腑）→ 落到「候/证」与「方症」</b>。<br>
检索范围（{html.escape(focus)}）：{html.escape(f)}<br>
层次建议：{html.escape(lvl)}<br>
提示：「候」是动态复合病机（含主症/副症/宾症），「证」是静态标志（病位+病因）。完整 1870 候请以原书为准。
</div>

<h2>二、12 门索引（以病因为纲）</h2>
<table>
<tr><th>编码</th><th>门</th><th>核心病因</th><th>代表证候方向</th></tr>
{door_rows}
</table>

<h2>三、六阶学习路线</h2>
<table>
<tr><th>阶段</th><th>内容</th><th>完成标准</th></tr>
{stage_rows}
</table>

<h2>四、我的学习进度自查</h2>
{checklist}

<h2>五、辨证入口速记</h2>
<div class="note">
• 外感先判层次：表→里、卫→气→营→血。<br>
• 内伤先定脏腑：心/肝/脾/肺/肾/胃，再看兼病（如肝郁脾虚、脾肾阳虚）。<br>
• 虚实证候：实（脉有力、拒按、急）→ 攻；虚（脉虚、喜按、久病）→ 补；虚实夹杂→ 标本缓急。<br>
• 见「反客为主」的宾症，往往是辨证关键，勿漏。
</div>

<div class="foot">
本手册为自学参考，非诊疗工具。古籍方剂严禁自服，身体不适请就医并在执业医师指导下用药。
生成自 tcm-syndrome-lookup 技能 · 内容结构化自《中医证候学》。
</div>
</body></html>"""
    with open(out, "w", encoding="utf-8") as fp:
        fp.write(doc)
    return out


def main():
    ap = argparse.ArgumentParser(description="生成《中医证候检索手册》A4 HTML")
    ap.add_argument("--focus", default="全科", choices=list(FOCUS_MAP.keys()))
    ap.add_argument("--level", default="入门", choices=list(LEVEL_HINT.keys()))
    ap.add_argument("--name", default="中医学习者")
    ap.add_argument("--out", default="syndrome-manual.html")
    args = ap.parse_args()
    o = render_html(args.name, args.focus, args.level, args.out)
    import os
    print(f"已生成: {os.path.abspath(o)} ({os.path.getsize(o)} bytes)")


if __name__ == "__main__":
    main()
