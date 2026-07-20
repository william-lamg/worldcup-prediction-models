#!/usr/bin/env python3
"""
中國體育彩票競彩賠率即時查詢工具
==================================
從 17500.cn 獲取實時競彩賠率

用法：
  python jingcai_odds.py           → 列出今日所有競彩賽事
  python jingcai_odds.py "西班牙"   → 搜索指定球隊
"""

import requests
import re
import sys
import json
from datetime import datetime

HKT = 8  # UTC+8

# 球隊中英對照（用於顯示）
TEAM_NAMES = {
    "西班牙": "Spain", "沙特": "Saudi Arabia", "沙特阿拉伯": "Saudi Arabia",
    "比利時": "Belgium", "伊朗": "Iran",
    "烏拉圭": "Uruguay", "佛得角": "Cape Verde", "乌拉圭": "Uruguay",
    "紐西蘭": "New Zealand", "新西兰": "New Zealand", "埃及": "Egypt",
    "荷蘭": "Netherlands", "瑞典": "Sweden", "荷兰": "Netherlands",
    "德國": "Germany", "科特迪瓦": "Ivory Coast", "德国": "Germany",
    "厄瓜多尔": "Ecuador", "庫拉索": "Curaçao", "厄瓜多爾": "Ecuador",
    "突尼斯": "Tunisia", "突尼西亞": "Tunisia", "日本": "Japan",
    "美國": "USA", "澳洲": "Australia", "美国": "USA", "澳大利亚": "Australia",
    "蘇格蘭": "Scotland", "摩洛哥": "Morocco", "苏格兰": "Scotland",
    "巴西": "Brazil", "海地": "Haiti",
    "土耳其": "Turkey", "巴拉圭": "Paraguay",
    "捷克": "Czech Republic", "南非": "South Africa",
    "瑞士": "Switzerland", "波黑": "Bosnia",
    "加拿大": "Canada", "卡塔爾": "Qatar",
    "墨西哥": "Mexico", "南韓": "South Korea", "韩国": "South Korea",
    "葡萄牙": "Portugal", "刚果": "DR Congo",
    "英格蘭": "England", "克羅地亞": "Croatia", "英格兰": "England",
    "加納": "Ghana", "巴拿馬": "Panama", "加纳": "Ghana",
    "烏兹別克": "Uzbekistan", "哥倫比亞": "Colombia", "乌兹别克": "Uzbekistan",
    "阿根廷": "Argentina", "阿爾及利亞": "Algeria",
    "法國": "France", "塞內加爾": "Senegal",
    "伊拉克": "Iraq", "挪威": "Norway",
    "奧地利": "Austria", "約旦": "Jordan", "奥地利": "Austria",
    "塞内加尔": "Senegal", "阿尔及利亚": "Algeria",
}


def fetch_jingcai_odds():
    """從 17500.cn 獲取競彩賠率"""
    url = "https://6.17500.cn/?lottery=more&lotteryId=s_fb"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = "utf-8"
        html = r.text
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        return []
    
    # 解析賽事
    matches = []
    
    # 匹配所有賽事區塊
    # 找出所有 "世界杯" + 編號 + 球隊 + 賠率 的區塊
    blocks = re.findall(
        r'世界杯.*?周日(\d+).*?<a[^>]*>(\S+)</a>.*?(\d+:\d+).*?<a[^>]*>(\S+)</a>.*?'
        r'已开售.*?'
        r'<a[^>]*bonus[^>]*>.*?(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+).*?</a>.*?'
        r'<a[^>]*bonus[^>]*>.*?[+-]?(\d+).*?(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)',
        html, re.DOTALL
    )
    
    # 更簡單的方法：先按 "世界杯" 分割
    sections = html.split("世界杯")
    
    for sec in sections:
        # 提取場次編號
        num_m = re.search(r'周日(\d+)', sec)
        if not num_m:
            continue
        match_num = num_m.group(1)
        
        # 提取主隊、時間、客隊
        tm_m = re.search(r'<a[^>]*class="[^"]*"[^>]*>([^<]+)</a>\s*<br>\s*(\d+:\d+)', sec)
        if not tm_m:
            # 另一種格式
            tm_m = re.search(r'<a[^>]*>([^<]+)</a>.*?(\d+:\d+)', sec)
        
        # 嘗試多種方式提取
        lines = sec.split('<br>')
        
        home_team = ""
        match_time = ""
        away_team = ""
        
        for i, line in enumerate(lines):
            # 找主隊
            am = re.search(r'<a[^>]*>([^<]+)</a>', line)
            if am and not home_team:
                home_team = am.group(1).strip()
            # 找時間
            tm = re.search(r'(\d+:\d+)', line)
            if tm and not match_time:
                match_time = tm.group(1)
        
        # 找客隊
        all_links = re.findall(r'<a[^>]*>([^<]+)</a>', sec)
        if len(all_links) >= 2:
            home_team = all_links[0].strip()
            away_team = all_links[-1].strip()
        
        if not home_team or not away_team:
            continue
        
        # 提取賠率
        # 勝平負
        spf_m = re.search(r'<a[^>]*bonus-\d+-101[^>]*>.*?(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)', sec, re.DOTALL)
        
        # 讓球
        rq_m = re.search(r'<a[^>]*bonus-\d+-101[^>]*>.*?(---)?.*?([+-]?\d+).*?(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)', sec, re.DOTALL)
        
        spf_odds = None
        rq_info = None
        
        if spf_m:
            spf_odds = (float(spf_m.group(1)), float(spf_m.group(2)), float(spf_m.group(3)))
        
        if rq_m and len(rq_m.groups()) >= 5:
            try:
                hcap = int(rq_m.group(2))
                rq_info = (hcap, float(rq_m.group(3)), float(rq_m.group(4)), float(rq_m.group(5)))
            except:
                pass
        
        matches.append({
            "num": match_num,
            "home": home_team,
            "away": away_team,
            "time": match_time,
            "spf": spf_odds,
            "rq": rq_info,
        })
    
    return matches


def format_output(matches, search=None):
    """格式化輸出"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M")
    
    print(f"\n{'='*55}")
    print(f"  🇨🇳 中國體彩競彩實時賠率")
    print(f"  更新時間: {date_str} HKT")
    print(f"  數據源: 17500.cn")
    print(f"{'='*55}")
    
    filtered = matches
    if search:
        filtered = [m for m in matches if search.lower() in m['home'].lower() or search.lower() in m['away'].lower()]
    
    if not filtered:
        print(f"\n  ❌ 冇搵到{'「' + search + '」' if search else ''}相關賽事")
        return
    
    for m in filtered:
        en_home = TEAM_NAMES.get(m['home'], m['home'])
        en_away = TEAM_NAMES.get(m['away'], m['away'])
        
        print(f"\n  {'─'*50}")
        print(f"  周日{m['num']}  {m['home']}({en_home}) vs {m['away']}({en_away})")
        print(f"  開賽: {m['time']}")
        
        if m['spf']:
            h, d, a = m['spf']
            print(f"  🏆 勝平負: {m['home']}勝 {h:.2f} / 和 {d:.2f} / {m['away']}勝 {a:.2f}")
            # 計算隱含概率
            total = 1/h + 1/d + 1/a
            print(f"     隱含概率: {m['home']} {1/h/total*100:.0f}% / 和 {1/d/total*100:.0f}% / {m['away']} {1/a/total*100:.0f}%")
            print(f"     抽水率: {(total-1)*100:.1f}%")
        
        if m['rq']:
            hcap, h_w, h_d, h_a = m['rq']
            hcap_str = f"{hcap:+d}" if hcap > 0 else str(hcap)
            label = f"讓球 ({hcap_str})"
            if hcap >= 0:
                print(f"  🏳️ {label}: {m['home']}(讓) {h_w:.2f} / 和 {h_d:.2f} / {m['away']}(受讓) {h_a:.2f}")
            else:
                print(f"  🏳️ {label}: {m['home']}(受讓) {h_w:.2f} / 和 {h_d:.2f} / {m['away']}(讓) {h_a:.2f}")
        else:
            print(f"  🏳️ 讓球: 未開")


if __name__ == "__main__":
    matches = fetch_jingcai_odds()
    search = sys.argv[1] if len(sys.argv) > 1 else None
    format_output(matches, search)
    
    if not search and matches:
        # 顯示所有
        print(f"\n{'='*55}")
        print(f"  共 {len(matches)} 場賽事 | 用 'python jingcai_odds.py 球隊名' 搜索")
