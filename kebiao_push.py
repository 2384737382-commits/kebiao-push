# -*- coding: utf-8 -*-
"""
每日课表微信推送（PushPlus 一对多推送）
本地运行或 GitHub Actions 云端运行均可。
"""

import os
import json
import datetime
import urllib.request

# ================== 配置区 ==================
# 云端（GitHub Actions）通过 Secret 注入；本地运行请设置环境变量 PUSHPLUS_TOKEN
PUSHPLUS_TOKEN = os.environ["PUSHPLUS_TOKEN"]
TOPIC = "feiya01"   # PushPlus 一对多群组编码

# 本学期第 1 周的周一（由第10周周一=2026-11-16 推算）
SEMESTER_START = datetime.date(2026, 9, 14)

# 节次 -> 时间（按校园课程表 App 显示）
PERIOD_TIME = {
    1: "08:10-08:55",  2: "09:00-09:45",  3: "10:00-10:45",  4: "10:50-11:35",
    5: "11:40-12:25",  6: "13:30-14:15",  7: "14:20-15:05",  8: "15:15-16:00",
    9: "16:05-16:50", 10: "18:30-19:15", 11: "19:20-20:05", 12: "20:10-20:55",
    13: "21:00-21:45", 14: "21:50-22:35",
}

WEEKDAY_NAME = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# ================== 课表数据 ==================
def _weeks(spec):
    """'10-12,14' -> [10,11,12,14]"""
    result = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            result.extend(range(int(a), int(b) + 1))
        else:
            result.append(int(part))
    return result

COURSES = [
    # 周一
    (0, 1, 2,  "数据结构与算法★", "3-N204", "10-16"),
    (0, 3, 5,  "普通物理A2★", "2-S243", "10-16"),
    (0, 6, 7,  "数据结构与算法★", "2-N219", "10-16"),
    (0, 10, 11, "军事理论★", "2-S143", "10-16"),
    # 周二
    (1, 1, 2,  "高级英语(四级班)★", "2-S150", "10-16"),
    (1, 3, 5,  "数据库原理与应用A★", "3-N104", "10-16"),
    (1, 6, 7,  "[自修]C程序设计★", "2-S407", "10-16"),
    (1, 10, 11, "社会学与生活★", "2-N224", "10-16"),
    # 周三（形势与政策只在第10~12周）
    (2, 1, 2,  "形势与政策★", "2-S223", "10-12"),
    (2, 3, 5,  "数字电子技术★", "2-N106", "10-16"),
    # 周四
    (3, 3, 5,  "概率论与数理统计A★", "3-N210", "10-16"),
    (3, 6, 7,  "人工智能导论★", "2-N230", "10-16"),
    # 周五
    (4, 3, 5,  "毛泽东思想和中国特色社会主义理论体系概论★", "2-S143", "10-16"),
    (4, 6, 7,  "羽毛球(中级)★(自备球拍)", "体育馆三楼羽毛球房", "10-16"),
]


def current_week(today):
    return max(1, (today - SEMESTER_START).days // 7 + 1)


def _period_label(s, e):
    """节次文字，如 第1-2节"""
    return f"第{s}节" if s == e else f"第{s}-{e}节"


def _time_label(s, e):
    """时间段文字，如 08:10-09:45"""
    return PERIOD_TIME[s] if s == e else \
        f"{PERIOD_TIME[s].split('-')[0]}-{PERIOD_TIME[e].split('-')[1]}"


def _day_emoji(s):
    """按时段配个可爱的 emoji"""
    if s <= 5:
        return "🌅"
    if s <= 9:
        return "☀️"
    return "🌙"


CUTE_NO_CLASS = [
    "今天没有课，好好休息呀～ 🎀",
    "今天无课！去玩吧～ 🧸✨",
    "空空的一天，适合摸鱼和奶茶 🧋",
]


def build_day_html(target_date, label="今天"):
    wd = target_date.weekday()
    wk = current_week(target_date)
    day_courses = [c for c in COURSES if c[0] == wd and wk in _weeks(c[5])]

    lines = [
        # 居中、加粗、放大的标题
        '<div style="text-align:center;margin:6px 0 2px 0;">',
        f'<span style="font-size:22px;font-weight:bold;color:#e91e63;">🌸 {target_date.month}月{target_date.day}日 {WEEKDAY_NAME[wd]} 🌸</span><br>',
        f'<span style="font-size:14px;color:#999;">{label} · 第{wk}周 · {"共%d节课" % len(day_courses) if day_courses else "无课"}</span>',
        '</div>',
        '<hr style="border:none;border-top:2px dashed #f8bbd0;margin:8px 0;">',
    ]

    if not day_courses:
        import random
        lines.append(f'<p style="text-align:center;font-size:15px;color:#666;">{random.choice(CUTE_NO_CLASS)}</p>')
    else:
        lines.append(
            '<table style="width:100%;border-collapse:collapse;font-size:14px;">'
            '<tr style="background:#fce4ec;">'
            '<th style="padding:6px;border:1px solid #f8bbd0;">节次</th>'
            '<th style="padding:6px;border:1px solid #f8bbd0;">时间</th>'
            '<th style="padding:6px;border:1px solid #f8bbd0;">课程</th>'
            '<th style="padding:6px;border:1px solid #f8bbd0;">教室</th>'
            '</tr>'
        )
        for i, (_, s, e, name, room, _w) in enumerate(sorted(day_courses, key=lambda x: x[1])):
            bg = "#fff" if i % 2 == 0 else "#fff7fb"
            lines.append(
                f'<tr style="background:{bg};">'
                f'<td style="padding:6px;border:1px solid #f8bbd0;text-align:center;color:#ad1457;font-weight:bold;white-space:nowrap;">{_day_emoji(s)} {_period_label(s, e)}</td>'
                f'<td style="padding:6px;border:1px solid #f8bbd0;text-align:center;white-space:nowrap;">{_time_label(s, e)}</td>'
                f'<td style="padding:6px;border:1px solid #f8bbd0;">{name}</td>'
                f'<td style="padding:6px;border:1px solid #f8bbd0;text-align:center;color:#1565c0;white-space:nowrap;">📍{room}</td>'
                f'</tr>'
            )
        lines.append("</table>")
        lines.append('<p style="text-align:center;font-size:12px;color:#bbb;margin-top:6px;">—— 今天也要加油鸭 🐤 ——</p>')
    return "\n".join(lines)


def push(title, html):
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": html,
        "template": "html",
        "topic": TOPIC,
    }
    req = urllib.request.Request(
        "https://www.pushplus.plus/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(title, "->", resp.read().decode("utf-8"))


def main():
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    push(f"🌸 {WEEKDAY_NAME[today.weekday()]}课表 · {today.month}月{today.day}日", build_day_html(today, "今天"))
    push(f"🌸 明天 {WEEKDAY_NAME[tomorrow.weekday()]}课表 · {tomorrow.month}月{tomorrow.day}日", build_day_html(tomorrow, "明天"))
    print("推送完成")


if __name__ == "__main__":
    main()
