#!/usr/bin/env python3
"""
worldcup_data.py — 世界盃歷史數據獲取工具
=========================================
從 openfootball/world-cup.json（免費，無需 API Key）獲取數據
自動更新 V6.0 嘅 H2H 數據庫

數據源：https://github.com/openfootball/world-cup.json
許可：Public Domain

用法：
  python worldcup_data.py fetch          ← 下載最新世界盃數據
  python worldcup_data.py h2h 法國 西班牙 ← 查 H2H 記錄
  python worldcup_data.py update         ← 更新 V6.0 數據庫
"""
import json, urllib.request, os, sys

BASE_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master"
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(DATA_DIR, ".worldcup_cache")
H2H_FILE = os.path.join(DATA_DIR, "h2h_database.json")

# 世界盃年份（可擴展）
WORLD_CUPS = [2018, 2022, 2026]

def fetch_json(year, filename="worldcup.json"):
    """從 GitHub 下載 JSON 數據"""
    url = f"{BASE_URL}/{year}/{filename}"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        matches = data.get("matches", []) or data.get("rounds", [])
        if isinstance(matches, list):
            print(f"  ✅ {year}/{filename} — {len(matches)} matches")
        else:
            # 可能是 rounds 格式
            all_m = []
            for r in matches:
                all_m.extend(r.get("matches", []))
            print(f"  ✅ {year}/{filename} — {len(all_m)} matches (rounds)" if all_m else f"  ✅ {year}/{filename}")
            return data
        return data
    except Exception as e:
        print(f"  ❌ {year}/{filename} — {e}")
        return None

def extract_h2h(data, team_a, team_b):
    """從世界盃數據中提取兩隊交鋒記錄"""
    results = []
    all_items = data.get("matches", []) or data.get("rounds", [])
    matches = []
    if all_items and isinstance(all_items[0], dict) and "matches" in all_items[0]:
        for r in all_items:
            matches.extend(r.get("matches", []))
    elif isinstance(all_items, list):
        matches = all_items
    
    for match in matches:
            t1 = match.get("team1", "")
            t2 = match.get("team2", "")
            if isinstance(t1, dict): t1 = t1.get("name", "")
            if isinstance(t2, dict): t2 = t2.get("name", "")
            score = match.get("score", {})
            
            # 檢查是否匹配（支援中英文隊名）
            def match_name(name, target):
                return (target.lower() in name.lower() or 
                       name.lower() in target.lower())
            
            if (match_name(t1, team_a) and match_name(t2, team_b)) or \
               (match_name(t1, team_b) and match_name(t2, team_a)):
                
                ft = score.get("ft", [None, None])
                if ft[0] is not None and ft[1] is not None:
                    home = t1
                    away = t2
                    home_score = int(ft[0])
                    away_score = int(ft[1])
                    
                    # 判斷結果
                    if home_score > away_score:
                        winner = home
                    elif home_score < away_score:
                        winner = away
                    else:
                        winner = "draw"
                    
                    results.append({
                        "date": match.get("date", ""),
                        "round": round_data.get("name", ""),
                        "home": home,
                        "away": away,
                        "score": f"{home_score}-{away_score}",
                        "winner": winner,
                        "home_score": home_score,
                        "away_score": away_score,
                    })
    return results

def build_h2h_database():
    """從所有世界盃數據建立 H2H 數據庫"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    all_matches = []
    for year in WORLD_CUPS:
        data = fetch_json(year)
        if data:
            all_items = data.get("matches", []) or data.get("rounds", [])
            items = []
            if all_items and isinstance(all_items[0], dict) and "matches" in all_items[0]:
                for r in all_items:
                    items.extend(r.get("matches", []))
            elif isinstance(all_items, list):
                items = all_items
            
            for match in items:
                    score = match.get("score", {}).get("ft", [None, None])
                    if score[0] is not None:
                        t1 = match["team1"]
                        t2 = match["team2"]
                        if isinstance(t1, dict): t1 = t1.get("name", "")
                        if isinstance(t2, dict): t2 = t2.get("name", "")
                        all_matches.append({
                            "year": year,
                            "round": match.get("round", ""),
                            "date": match.get("date", ""),
                            "team1": t1,
                            "team2": t2,
                            "score1": int(score[0]),
                            "score2": int(score[1]),
                        })
    
    print(f"\n📊 共收集 {len(all_matches)} 場世界盃比賽")
    
    # 建立 H2H 統計
    h2h = {}
    for m in all_matches:
        pair = tuple(sorted([m["team1"], m["team2"]]))
        if pair not in h2h:
            h2h[pair] = {"wins_a": 0, "wins_b": 0, "draws": 0, 
                         "goals_a": 0, "goals_b": 0, "matches": []}
        
        entry = h2h[pair]
        if m["team1"] == pair[0]:
            entry["goals_a"] += m["score1"]
            entry["goals_b"] += m["score2"]
            if m["score1"] > m["score2"]:
                entry["wins_a"] += 1
            elif m["score1"] < m["score2"]:
                entry["wins_b"] += 1
            else:
                entry["draws"] += 1
        else:
            entry["goals_a"] += m["score2"]
            entry["goals_b"] += m["score1"]
            if m["score2"] > m["score1"]:
                entry["wins_a"] += 1
            elif m["score2"] < m["score1"]:
                entry["wins_b"] += 1
            else:
                entry["draws"] += 1
        
        entry["matches"].append(m)
    
    # 保存到檔案
    output = {}
    for (a, b), stats in h2h.items():
        key = f"{a} vs {b}"
        output[key] = {
            "team_a": a, "team_b": b,
            "wins_a": stats["wins_a"],
            "draws": stats["draws"],
            "wins_b": stats["wins_b"],
            "goals_a": stats["goals_a"],
            "goals_b": stats["goals_b"],
            "total": stats["wins_a"] + stats["draws"] + stats["wins_b"],
            "matches": [f"{m['team1']} {m['score1']}-{m['score2']} {m['team2']} ({m['date']})" 
                       for m in stats["matches"][-10:]]  # 最近10場
        }
    
    with open(H2H_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"💾 已保存到 {H2H_FILE}")
    print(f"📁 共 {len(output)} 對 H2H 組合")
    return output

def query_h2h(team_a, team_b):
    """查詢兩隊 H2H 記錄"""
    if not os.path.exists(H2H_FILE):
        print("⚠️ 未找到 H2H 數據庫，請先執行：python worldcup_data.py fetch")
        return
    
    with open(H2H_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 匹配
    for key, stats in data.items():
        ta, tb = stats["team_a"], stats["team_b"]
        if (team_a.lower() in ta.lower() or ta.lower() in team_a.lower()) and \
           (team_b.lower() in tb.lower() or tb.lower() in team_b.lower()):
            print(f"\n📜 H2H：{ta} vs {tb}（世界盃歷史）")
            print(f"   共 {stats['total']} 場")
            print(f"   {ta} {stats['wins_a']} 勝 / 和 {stats['draws']} / {tb} {stats['wins_b']} 勝")
            print(f"   入球: {ta} {stats['goals_a']} - {tb} {stats['goals_b']}")
            print(f"\n   最近對賽:")
            for m in stats["matches"]:
                print(f"   · {m}")
            return
    
    print(f"⚠️ 未找到 {team_a} vs {team_b} 的世界盃 H2H 記錄")

def generate_v60_h2h_code():
    """生成 V6.0 H2H 數據庫代碼"""
    if not os.path.exists(H2H_FILE):
        print("⚠️ 請先執行：python worldcup_data.py fetch")
        return
    
    with open(H2H_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 生成 Python 代碼
    lines = ["# 自動生成：worldcup_data.py\n# 數據源：openfootball/world-cup.json\nH2H_DB = {\n"]
    for key, stats in data.items():
        ta, tb = stats["team_a"], stats["team_b"]
        wa = stats["wins_a"]
        dr = stats["draws"]
        wb = stats["wins_b"]
        ga = stats["goals_a"]
        gb = stats["goals_b"]
        lines.append(f'    ("{ta}","{tb}"): ({wa},{dr},{wb},{ga},{gb}),\n')
        lines.append(f'    ("{tb}","{ta}"): ({wb},{dr},{wa},{gb},{ga}),\n')
    lines.append("}\n")
    
    code = "".join(lines)
    print(code)
    return code

if __name__ == "__main__":
    args = sys.argv[1:]
    
    if len(args) >= 1 and args[0] == "fetch":
        print("🌍 下載世界盃歷史數據...")
        build_h2h_database()
    
    elif len(args) >= 1 and args[0] == "h2h" and len(args) >= 3:
        query_h2h(args[1], args[2])
    
    elif len(args) >= 1 and args[0] == "update":
        build_h2h_database()
        print("\n🔧 生成 H2H 代碼...")
        generate_v60_h2h_code()
        print("\n💡 將上面嘅 H2H_DB 代碼複製到 predict_v6.py")
    
    else:
        print("用法:")
        print("  python worldcup_data.py fetch          ← 下載世界盃數據")
        print("  python worldcup_data.py h2h 法國 西班牙  ← 查 H2H")
        print("  python worldcup_data.py update         ← 更新 V6.0 數據庫")
