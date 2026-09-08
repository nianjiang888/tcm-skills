#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中医学问答索引手册 生成器
依据杨医亚《中医学问答》（上/下册，14 部分）结构，生成 A4 HTML，
可浏览器打开后「打印 → 另存 PDF」，作为个人随身检索字典。

用法:
  python build_qa_guide.py --name 张三 --level 入门 --focus 全科 --out guide.html
参数:
  --name   学习者姓名（写入封面）
  --level  入门 / 备考 / 临床  （影响“掌握标准”措辞）
  --focus  全科 / 总论 / 内科 / 妇科 / 儿科 / 针灸 ... （影响勾选重点）
  --out    输出 HTML 路径
"""
import argparse
import html
import datetime

# 14 部分导览（主题 / 代表方向 / 重点标记）
PARTS = [
    ("第一部分", "总论", "阴阳五行·藏象·气血津液·经络·病因病机", "地基"),
    ("第二部分", "内经", "《黄帝内经》要旨·阴阳应象·脏气法时", ""),
    ("第三部分", "伤寒", "六经辨证·太阳病·传变·经方运用", ""),
    ("第四部分", "金匮", "脏腑辨证·杂病论治·《金匮要略》方", ""),
    ("第五部分", "温病", "卫气营血·三焦辨证·温热类温病", ""),
    ("第六部分", "中药", "四气五味·升降浮沉·归经·配伍", "方药"),
    ("第七部分", "方剂", "君臣佐使·经方方义·类方鉴别", "方药"),
    ("第八部分", "内科", "感冒·咳嗽·胃脘痛·泄泻·水肿·黄疸…", "最常用"),
    ("第九部分", "妇科", "月经·带下·胎产·产后·杂病", ""),
    ("第十部分", "儿科", "生理病理特点·惊·疳·麻痘", ""),
    ("第十一部分", "外科", "痈疽·疔疮·瘰疬·流注", ""),
    ("第十二部分", "伤科(按摩)", "骨折·脱位·伤筋·手法", ""),
    ("第十三部分", "五官科", "眼科·耳鼻喉·口齿病证", ""),
    ("第十四部分", "针灸", "经络腧穴·刺灸法·配穴·治则", ""),
]

# 高频问答入口（与 qa-cards.md 对应）
QA_ENTRY = [
    ("基础", "怎样理解“左肾右命门”？命门火的功能是什么？", "A-1"),
    ("基础", "肾的主要功能？怎样理解“肾藏精”？", "A-2"),
    ("基础", "为什么称“脾胃为后天之本”？", "A-3"),
    ("基础", "怎样区别“内风”与“外风”？", "A-4"),
    ("基础", "痰饮怎样形成？致病特点？", "A-5"),
    ("基础", "何谓瘀血？成因与临床特点？", "A-6"),
    ("经典", "《伤寒论》六经辨证的实质？", "B-1"),
    ("经典", "温病“卫气营血”与“三焦”的关系？", "B-2"),
    ("经典", "《金匮要略》的辨证特点？", "B-3"),
    ("方药", "中药“四气五味”指什么？", "C-1"),
    ("方药", "方剂“君臣佐使”是什么？", "C-2"),
    ("方药", "怎样理解“经方”与“时方”？", "C-3"),
    ("内科", "风寒感冒与风热感冒治疗区别？", "D-1"),
    ("内科", "外感咳嗽与内伤咳嗽如何辨别？", "D-2"),
    ("内科", "实喘与虚喘如何鉴别？", "D-3"),
    ("内科", "泄泻常见证候与治要？", "D-4"),
    ("妇科", "妇科“经带胎产”四大纲？", "D-5"),
    ("儿科", "儿科“稚阴稚阳”“易虚易实”？", "D-6"),
]

LEVEL_TEXT = {
    "入门": "以“能讲清概念、不混淆”为掌握标准，重总论与内科基础。",
    "备考": "以“能答题、能辨析异同”为掌握标准，重经典与鉴别点。",
    "临床": "以“能联想证—方、能判断落点”为掌握标准，重内科与各科检索。",
}

FOCUS_HINT = {
    "全科": "14 部分全勾，按六阶顺序推进。",
    "总论": "重点勾第一部分，配合第六七部分打底。",
    "内科": "重点勾第八部分，配总论与方药。",
    "妇科": "重点勾第九部分，配总论与方剂。",
    "儿科": "重点勾第十部分，配总论。",
    "针灸": "重点勾第十四部分，配经络（总论）。",
}


def render_html(name, level, focus, date_str):
    lvl = LEVEL_TEXT.get(level, LEVEL_TEXT["入门"])
    fhint = FOCUS_HINT.get(focus, FOCUS_HINT["全科"])
    parts_rows = "".join(
        f"<tr><td><b>{pid}</b></td><td>{topic}</td><td>{detail}</td>"
        f"<td>{'★' if tag else ''}{tag}</td>"
        f"<td class='box'>☐</td></tr>"
        for pid, topic, detail, tag in PARTS
    )
    qa_rows = "".join(
        f"<tr><td>{cat}</td><td>{html.escape(q)}</td><td><code>{ref}</code></td>"
        f"<td class='box'>☐</td></tr>"
        for cat, q, ref in QA_ENTRY
    )
    return f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>中医学问答索引手册</title>
<style>
@page {{ size: A4; margin: 16mm 14mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: "SimSun","Songti SC",serif; color:#1a1a1a; font-size:12px; line-height:1.5; }}
h1 {{ text-align:center; font-size:22px; margin:0 0 4px; }}
.sub {{ text-align:center; color:#666; margin:0 0 14px; font-size:12px; }}
.meta {{ display:flex; justify-content:space-between; border:1px solid #999; padding:6px 10px; margin-bottom:12px; font-size:12px; }}
h2 {{ font-size:15px; border-left:4px solid #b03a2e; padding-left:8px; margin:16px 0 6px; }}
table {{ width:100%; border-collapse:collapse; margin-bottom:8px; }}
th,td {{ border:1px solid #bbb; padding:4px 6px; vertical-align:top; }}
th {{ background:#f3ece2; text-align:left; }}
.box {{ width:34px; text-align:center; font-size:16px; }}
code {{ color:#b03a2e; font-family:monospace; }}
.note {{ background:#faf6ef; border:1px dashed #c8a; padding:8px 10px; font-size:11.5px; }}
.footer {{ margin-top:14px; font-size:10.5px; color:#888; border-top:1px solid #ccc; padding-top:6px; }}
</style></head><body>
<h1>中医学问答索引手册</h1>
<p class="sub">基于杨医亚《中医学问答》（上/下册 · 14 部分）整理</p>
<div class="meta"><span>学习者：{html.escape(name)}</span><span>层次：{html.escape(level)}</span><span>生成：{date_str}</span></div>

<h2>一、如何使用本手册</h2>
<p>这是你的<b>随身中医问答字典</b>：脑子里冒出一个具体问题 → 看「十四部分导览」判断它落在哪一格 →
翻原书该部分查完整问答。本手册只给索引与高频入口，不替代原书千余问。</p>
<p class="note"><b>掌握标准（{html.escape(level)}）</b>：{html.escape(lvl)}<br>
<b>本次重点（{html.escape(focus)}）</b>：{html.escape(fhint)}</p>

<h2>二、十四部分导览（勾选你已掌握的部分）</h2>
<table>
<tr><th>部分</th><th>主题</th><th>代表问题方向</th><th>重点</th><th>已掌握</th></tr>
{parts_rows}
</table>

<h2>三、高频问答入口（勾选你已能吃透的卡片）</h2>
<table>
<tr><th>类别</th><th>问题</th><th>速查卡</th><th>已掌握</th></tr>
{qa_rows}
</table>

<h2>四、六阶分步陪学路线</h2>
<table>
<tr><th>阶</th><th>内容</th><th>对应部分</th></tr>
<tr><td>1 总论筑基</td><td>阴阳五行·藏象·气血津液·经络·病因病机</td><td>第一部分</td></tr>
<tr><td>2 经典四门</td><td>内经·伤寒·金匮·温病</td><td>第二~五部分</td></tr>
<tr><td>3 方药基础</td><td>中药·方剂</td><td>第六~七部分</td></tr>
<tr><td>4 内科精读</td><td>内科常见病辨证</td><td>第八部分</td></tr>
<tr><td>5 妇儿外五官伤科</td><td>按方向选学</td><td>第九~十三部分</td></tr>
<tr><td>6 针灸与综合运用</td><td>针灸 + 跨科检索能力</td><td>第十四部分</td></tr>
</table>

<div class="footer">教育参考，非诊疗工具。古籍方剂严禁自服，身体不适请就医。详见 disclaimer.md。</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="学习者")
    ap.add_argument("--level", default="入门", choices=["入门", "备考", "临床"])
    ap.add_argument("--focus", default="全科")
    ap.add_argument("--out", default="qa-guide.html")
    a = ap.parse_args()
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    out = render_html(a.name, a.level, a.focus, date_str)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"已生成: {a.out} ({len(out.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
