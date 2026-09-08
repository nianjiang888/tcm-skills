#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_roadmap.py —— 生成《中医自学路线图》A4 HTML 交付物。

用法:
  python build_roadmap.py --background zero   --clinical no  --goal entry  --name 张三 --out roadmap.html
  python build_roadmap.py --background clinical --clinical yes --goal clinic --name 李四 --out roadmap.html

参数:
  --background  起点背景: zero(零基础/古文弱) | classical(有古文底子) | clinical(有临床体验)
  --clinical    是否已有临床: yes | no
  --goal        目标方向:   entry(入门启蒙) | classic(经典溯源) | clinic(临床提高) | exam(应试) | interest(兴趣养生)
  --name        学习者名字(用于报告抬头)
  --out         输出 HTML 路径
"""
import argparse
from datetime import date

# ───────────────────────────────────────────────────────────
# 六阶课程数据（与 learning-progression.md 同步）
# ───────────────────────────────────────────────────────────
STAGES = [
    {
        "no": 1, "title": "启蒙筑基", "months": "1–2 个月",
        "task": "建立中医世界观 + 中药方剂入门",
        "exit": "读懂四小经典白文、能背常用汤头",
        "learn": "阴阳五行、脏腑气血津液、病因病机；药性寒热温凉五味归经；君臣佐使方歌。",
        "depth": "口述五脏六腑表里关系；说清 50 味常用药功效；背出 30 首基础方组成主治。",
        "self_test": [
            "默写心与小肠、肺与大肠的表里关系各自主什么。",
            "说出麻黄汤、桂枝汤、六味地黄丸的组成与主治区别。",
            "十八反'半蒌贝蔹及攻乌'指哪几味反乌头？",
        ],
        "books": "《医学三字经》→《药性赋》→《汤头歌诀》→《濒湖脉学》",
        "next": "观念清、药方可配对，才能进治则与经典，否则读《内经》如天书。",
    },
    {
        "no": 2, "title": "治学方法与治则", "months": "约 1 个月",
        "task": "五勤读书法 + 治则八条 + 知常达变",
        "exit": "能区分治则与治法、说清标本缓急",
        "learn": "五勤(读思问写习)、由约而博由浅入深；治则八条；医门八法总览。",
        "depth": "解释'治病求本'本在何处；列举八法各 1–2 代表方；区分治则与治法。",
        "self_test": [
            "标症紧急(如大出血)而本虚不显，先治标还是治本？为什么？",
            "同是头痛，为何有人疏散风寒、有人平肝潜阳？体现哪条治则？",
        ],
        "books": "《医学心悟》(程钟龄) + 《自学中医阶梯(一)》治则浅说/治法漫谈",
        "next": "治则是方向盘，经典是地图；有方向感再读经典不迷路。",
    },
    {
        "no": 3, "title": "经典溯源", "months": "6–12 个月(核心)",
        "task": "内经→伤寒→金匮→本草→温病，抓特色不逐字啃",
        "exit": "懂六经提纲、背 50 味本草上品功效",
        "learn": "每部先读白话浅解再读白文做卡片；伤寒重六经、金匮重脏腑杂病、温病重卫气营血。",
        "depth": "背六经提纲；伤寒条文能读能解；本草上品 50 味信手拈来。",
        "self_test": [
            "'太阳之为病，脉浮，头项强痛而恶寒'属哪一经？主方思路？",
            "温病卫气营血与伤寒六经分别解决哪类病证？关系如何？",
        ],
        "books": "《内经知要浅解》→《伤寒论》+《伤寒来苏集》→《金匮要略新解》→《神农本草经读》→《温病条辨》",
        "next": "经典给'理法'，下一阶补辨证实操框架。",
    },
    {
        "no": 4, "title": "临床思维与辨证", "months": "3–6 个月",
        "task": "四诊 + 八纲 + 脏腑/六经辨证",
        "exit": "拿到症状能列证型清单、不再见症不对证",
        "learn": "望闻问切(十问、基本脉象)；八纲、脏腑辨证、六经、卫气营血辨证。",
        "depth": "发热恶寒头痛能列风寒/风热/少阳并说鉴别；浮数沉迟脉义清楚。",
        "self_test": [
            "发热、恶寒轻、咽痛、舌尖红、脉浮数——八纲何证？六经何经？",
            "失眠心脾两虚与肝郁化火在问诊舌脉上如何区分？",
        ],
        "books": "《中医诊断学》教材 + 第三阶经典辨证条文对照",
        "next": "辨证框架立住，才能进具体病种专题深入。",
    },
    {
        "no": 5, "title": "常见病专题", "months": "长期(分科深入)",
        "task": "外感/内科/妇科/儿科/皮外五官科常见病辨证",
        "exit": "每病掌握 2–4 基本证型与通治方，知兼夹变证",
        "learn": "每病先掌握'常'(基本证型通治方)，再学'变'(兼夹变证)；严禁照搬自服。",
        "depth": "感冒风寒/风热三点鉴别；虚人反复感冒治法异于单纯解表。",
        "self_test": [
            "风寒与风热感冒在主症、舌脉、用药方向上三点区别？",
            "虚人反复感冒，治法与单纯解表有何不同？",
        ],
        "books": "《自学中医阶梯(二)》+ 《方剂学》《中医内科学》教材",
        "next": "专题是'点'，跟师临证才能连成'线'与'面'。",
    },
    {
        "no": 6, "title": "跟师与临证", "months": "终身",
        "task": "抄方、医案、各家学说(伤寒/温病/金元四大家)",
        "exit": "把前 5 阶在真实病案中串成自己的辨证习惯",
        "learn": "脉诊腹诊剂量拿捏变证决断非口传心授难精；远离'神医包治'误导。",
        "depth": "能跟诊记录并复盘老师辨证用药思路；熟读 2–3 家医案。",
        "self_test": [
            "选一位本地明师，列出其学术特点与你的跟诊计划。",
            "用前 5 阶知识复盘一则自己或家人真实病案(仅学习，不自治)。",
        ],
        "books": "名医医案集 + 师承跟诊 + 正规中医培训",
        "next": "学无止境；自学到一定程度必须跟师，纸上谈兵有限。",
    },
]

EIGHT_METHODS = [
    ("汗", "解表发汗", "麻黄汤/桂枝汤/银翘散", "表已入里或阴虚禁汗"),
    ("吐", "涌吐上出", "瓜蒂散/盐汤探吐", "体虚孕妇失血禁用"),
    ("下", "攻里通腑", "大承气汤/十枣汤", "阳虚燥结老人慎用"),
    ("和", "和解枢机", "小柴胡汤/逍遥散", "纯表纯里不用和"),
    ("温", "温里回阳", "理中丸/四逆汤", "真热假寒误用危"),
    ("清", "清热泻火", "白虎汤/黄连解毒", "真寒假热误清败"),
    ("消", "消散渐积", "保和丸/二陈汤", "正虚积甚消补兼施"),
    ("补", "补益虚损", "四君/四物/六味", "无虚而补闭门留寇"),
]

REFER_CARDS = [
    ("感冒", "风寒(荆防败毒散) / 风热(银翘散) / 暑湿(新加香薷饮) / 虚人(参苏饮)"),
    ("咳嗽", "外感止嗽散·桑菊饮；内伤本在脾(二陈+三子)·痰热清金·阴虚沙参麦冬"),
    ("胃痛", "寒邪良附丸·食滞保和丸·肝气柴胡疏肝·虚寒黄芪建中"),
    ("眩晕", "肝阳天麻钩藤·痰浊半夏白术天麻·气血虚归脾·肾亏左归"),
    ("水肿", "腰以上发汗(越婢加术)·腰以下利小便(实脾/真武)"),
    ("哮喘", "发作宣肺(射干麻黄/定喘)·缓解补肾纳气(肾气丸)"),
]


def start_advice(background, clinical, goal):
    if background == "classical":
        return "建议起点：第 3 阶(经典溯源)，可略过第 1 阶启蒙，但第 2 阶治则务必补；古文底子让你直读白文更顺。"
    if background == "clinical":
        return "建议起点：第 4–5 阶(临床思维/常见病专题)，以治疗学为纲回补经典短板(伤寒/金匮择要)；" + (
            "已有临床体验，重点在'知常达变'。" if clinical == "yes" else "")
    # zero / 默认
    base = "建议起点：第 1 阶(启蒙筑基)，由浅入深、由约而博，切勿硬啃《内经》。"
    if goal == "interest":
        base += " 兴趣养生向：可把第 5 阶'治未病'与养生作为重点，不强制通关经典。"
    if goal == "exam":
        base += " 应试向：以统编教材章节对照六阶，经典重条文背诵与方证对应。"
    return base


def render_html(name, background, clinical, goal):
    adv = start_advice(background, clinical, goal)
    overview = "".join(
        f"<tr><td>{s['no']}</td><td><b>{s['title']}</b></td><td>{s['task']}</td>"
        f"<td>{s['months']}</td><td>{s['exit']}</td></tr>" for s in STAGES)

    detail = ""
    for s in STAGES:
        tests = "".join(f"<li>☐ {t}</li>" for t in s["self_test"])
        detail += f"""
        <div class="stage">
          <h3>第 {s['no']} 阶 · {s['title']} <span class="tag">{s['months']}</span></h3>
          <table class="kv">
            <tr><th>本阶任务</th><td>{s['task']}</td></tr>
            <tr><th>学什么</th><td>{s['learn']}</td></tr>
            <tr><th>学多深(掌握标准)</th><td>{s['depth']}</td></tr>
            <tr><th>核心书目(顺序)</th><td>{s['books']}</td></tr>
            <tr><th>完成标志</th><td>{s['exit']}</td></tr>
            <tr><th>下一阶衔接</th><td>{s['next']}</td></tr>
          </table>
          <p class="st-title">自测题(做完打勾，回来复盘)：</p>
          <ul class="tests">{tests}</ul>
        </div>"""

    methods = "".join(
        f"<tr><td><b>{m[0]}</b></td><td>{m[1]}</td><td>{m[2]}</td><td class='warn'>{m[3]}</td></tr>"
        for m in EIGHT_METHODS)

    refs = "".join(
        f"<tr><td><b>{r[0]}</b></td><td>{r[1]}</td></tr>" for r in REFER_CARDS)

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>中医自学路线图 · {name}</title>
<style>
  @page {{ size: A4; margin: 16mm 14mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "SimSun","Songti SC","Noto Serif CJK SC",serif; color:#1a1a1a;
         font-size: 11pt; line-height: 1.55; margin:0; }}
  h1 {{ text-align:center; font-size:20pt; margin:0 0 2mm; }}
  .sub {{ text-align:center; color:#666; font-size:10pt; margin-bottom:6mm; }}
  h3 {{ font-size:13pt; border-left:4px solid #9e2a2b; padding-left:6px; margin:6mm 0 2mm; }}
  .tag {{ font-size:9pt; color:#fff; background:#9e2a2b; padding:1px 6px; border-radius:3px; margin-left:6px; }}
  table {{ width:100%; border-collapse:collapse; margin:2mm 0; font-size:10pt; }}
  th,td {{ border:1px solid #bbb; padding:3px 6px; vertical-align:top; text-align:left; }}
  th {{ background:#f3ece7; width:22%; font-weight:bold; }}
  .kv th {{ width:20%; }}
  .warn {{ color:#9e2a2b; }}
  .stage {{ border:1px solid #ddd; border-radius:4px; padding:0 4mm 3mm; margin-bottom:3mm; page-break-inside:avoid; }}
  .st-title {{ font-weight:bold; margin:2mm 0 1mm; }}
  .tests li {{ margin:1mm 0; }}
  .advice {{ background:#f3ece7; border:1px solid #d9c4b8; border-radius:4px; padding:3mm; margin:3mm 0; }}
  .footer {{ margin-top:6mm; font-size:9pt; color:#888; border-top:1px solid #ccc; padding-top:2mm; }}
</style></head><body>
  <h1>中医自学路线图</h1>
  <div class="sub">学习者：{name} ｜ 生成日期：{date.today().isoformat()} ｜ 源：自学中医阶梯(一)(二)</div>

  <div class="advice">
    <b>★ 你的起点建议：</b><br>{adv}<br><br>
    <b>怎么用这份图：</b>分步陪学——每次只攻一阶，自测打勾后回来复盘再进下一阶；
    想看全貌就保留此图。内容源自经典辅导读物，仅供学习参考。
  </div>

  <h3>六阶总览</h3>
  <table>
    <tr><th style="width:6%">阶</th><th style="width:16%">主题</th><th>核心任务</th><th style="width:14%">时长</th><th style="width:22%">出口标志</th></tr>
    {overview}
  </table>

  <h3>逐阶详述（带 checkpoint）</h3>
  {detail}

  <h3>医门八法速记卡</h3>
  <table>
    <tr><th style="width:8%">法</th><th style="width:20%">含义</th><th style="width:34%">代表方</th><th>误用警示</th></tr>
    {methods}
  </table>

  <h3>常备辨证速查卡（收藏备查）</h3>
  <table>
    <tr><th style="width:16%">病证</th><th>证型 → 治法/代表方</th></tr>
    {refs}
  </table>

  <div class="footer">
    免责声明：本路线图为中医自学辅导与教育参考，<b>不是诊疗工具，不替代执业医师</b>。
    古籍方剂严禁自行服用；身体不适、急症、孕产妇及慢性病患者务必就医。内容摘自《自学中医阶梯（一）（二）》及公认善本导读，供学习交流。
  </div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="生成中医自学路线图 A4 HTML")
    ap.add_argument("--background", default="zero", choices=["zero", "classical", "clinical"])
    ap.add_argument("--clinical", default="no", choices=["yes", "no"])
    ap.add_argument("--goal", default="entry", choices=["entry", "classic", "clinic", "exam", "interest"])
    ap.add_argument("--name", default="学习者")
    ap.add_argument("--out", default="roadmap.html")
    a = ap.parse_args()
    html = render_html(a.name, a.background, a.clinical, a.goal)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成: {a.out} ({len(html.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
