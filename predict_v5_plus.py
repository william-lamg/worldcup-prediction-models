#!/usr/bin/env python3
"""
V5+ 強化預測 — 加時/12碼/總入球
==================================
基於 V5 引擎，增加：
1. 加時概率（淘汰賽）
2. 12碼大戰概率
3. 總入球詳細分佈（0球到6+球）
"""
import math, json, sys

def poisson(l, k):
    return (l**k) * math.exp(-l) / math.factorial(k)

def dixon_coles_correction(l_a, l_b, rho=0.05):
    def dc_factor(i, j):
        if i == 0 and j == 0: return 1 - l_a * l_b * rho
        elif i == 0 and j == 1: return 1 + l_a * rho
        elif i == 1 and j == 0: return 1 + l_b * rho
        elif i == 1 and j == 1: return 1 - rho
        else: return 1.0
    scores = []
    total = 0
    for i in range(12):
        for j in range(12):
            p_raw = poisson(l_a, i) * poisson(l_b, j)
            p_dc = p_raw * dc_factor(i, j)
            if p_dc > 0.0005:
                scores.append((i, j, p_dc))
                total += p_dc
    return [(i, j, p/total) for i, j, p in scores]

def de_vig(odds_h, odds_d, odds_a):
    imp_h, imp_d, imp_a = 1/odds_h, 1/odds_d, 1/odds_a
    total = imp_h + imp_d + imp_a
    return imp_h/total, imp_d/total, imp_a/total

def altitude_factor(alt_m):
    if alt_m < 1500: return 1.0, 1.0
    return 1.0 + (alt_m-1500)*0.003/100, max(1.0 - (alt_m-1500)*0.001/100, 0.85)

def predict_enhanced(team_a, team_b, odds_h, odds_d, odds_a,
                     is_knockout=True, altitude=0, rest_diff=0):
    # 1. 去vig
    p_h, p_d, p_a = de_vig(odds_h, odds_d, odds_a)

    # 2. 反推xG
    l_a = -math.log(1 - p_h - p_d*0.4) * 1.8
    l_b = -math.log(1 - p_a - p_d*0.4) * 1.8
    for _ in range(5):
        total_prob = sum(poisson(l_a,i)*poisson(l_b,j) for i in range(10) for j in range(10) if i>j)
        scale = (p_h / max(total_prob, 0.001)) ** 0.3
        l_a *= scale; l_b /= scale

    # 3. 海拔
    h_f, a_f = altitude_factor(altitude)
    l_a *= h_f; l_b *= a_f

    # 4. Dixon-Coles
    rho = 0.08 if is_knockout else 0.05
    scores = dixon_coles_correction(l_a, l_b, rho)

    # 5. 基本概率（90分鐘）
    win_a = sum(p for i,j,p in scores if i>j)
    draw = sum(p for i,j,p in scores if i==j)
    win_b = sum(p for i,j,p in scores if j>i)

    # 6. 淘汰賽和波調整
    if is_knockout:
        boost = 0.08
        draw += boost
        win_a -= boost * (win_a / (win_a+win_b))
        win_b -= boost * (win_b / (win_a+win_b))

    # 7. 加時+12碼概率
    # 假設和波後有~55%入加時（其餘即時12碼？實際係加時30分鐘）
    # 加時後仍和的概率 = 和波 * 加時和波率 (~35%)
    extra_time_prob = draw * 0.55  # 和波後進入加時
    # 加時後分勝負（假設加時勝率略傾向強隊）
    et_win_a = extra_time_prob * (win_a / (win_a+win_b) * 1.1)
    et_win_b = extra_time_prob * (win_b / (win_a+win_b) * 0.9)
    # 加時後仍和 → 12碼
    penalty_prob = extra_time_prob - et_win_a - et_win_b
    
    # 總晉級概率
    total_advance_a = win_a + et_win_a + penalty_prob * 0.5  # 12碼50/50
    total_advance_b = win_b + et_win_b + penalty_prob * 0.5

    # 8. 總入球分析
    total_goals = {}
    for g in range(9):
        prob = sum(p for i,j,p in scores if i+j == g)
        if prob > 0.005:
            total_goals[g] = round(prob*100, 1)
    
    # 大小球
    over15 = sum(p for i,j,p in scores if i+j >= 1)
    over25 = sum(p for i,j,p in scores if i+j > 2)
    over35 = sum(p for i,j,p in scores if i+j > 3)
    over45 = sum(p for i,j,p in scores if i+j > 4)
    
    # 最可能比分
    top_scores = sorted(scores, key=lambda x: -x[2])[:10]

    result = {
        "team_a": team_a, "team_b": team_b,
        "l_a": round(l_a,2), "l_b": round(l_b,2),
        "altitude": altitude,
        "is_knockout": is_knockout,

        # 90分鐘
        "win_a_90": round(win_a*100,1),
        "draw_90": round(draw*100,1),
        "win_b_90": round(win_b*100,1),
        "market_a": round(p_h*100,1),
        "market_d": round(p_d*100,1),
        "market_b": round(p_a*100,1),

        # 加時/12碼/晉級
        "extra_time_prob": round(extra_time_prob*100,1),
        "penalty_prob": round(penalty_prob*100,1),
        "advance_a": round(total_advance_a*100,1),
        "advance_b": round(total_advance_b*100,1),

        # 總入球
        "total_goals_dist": total_goals,
        "over15": round(over15*100,1),
        "over25": round(over25*100,1),
        "over35": round(over35*100,1),
        "over45": round(over45*100,1),
        "expected_goals": round(l_a + l_b, 2),
        "most_likely_total": max(total_goals, key=total_goals.get) if total_goals else "?",

        # 比分
        "top_scores": [(i,j,round(p*100,1)) for i,j,p in top_scores]
    }
    return result

def print_report(r):
    stage = "🏆 32強" if r["is_knockout"] else "📊 小組賽"
    print(f"\n{'='*60}")
    print(f"  V5+ 強化預測：{r['team_a']} vs {r['team_b']}  {stage}")
    if r["altitude"] > 0:
        print(f"  🏔️ 海拔: {r['altitude']}m")
    print(f"  ⚽ 期望入球: {r['team_a']} {r['l_a']} / {r['team_b']} {r['l_b']} (總計 {r['expected_goals']})")
    print(f"{'='*60}")

    # 90分鐘（勝平負）
    print(f"\n  📊 90分鐘結果:")
    print(f"    {r['team_a']}勝 {r['win_a_90']}% / 和 {r['draw_90']}% / {r['team_b']}勝 {r['win_b_90']}%")

    # 加時/12碼
    print(f"\n  ⏱️ 淘汰賽路徑:")
    print(f"    和波後入加時: {r['extra_time_prob']}%")
    print(f"    12碼大戰:     {r['penalty_prob']}%")
    print(f"    {r['team_a']}總晉級概率: {r['advance_a']}%")
    print(f"    {r['team_b']}總晉級概率: {r['advance_b']}%")
    if r["penalty_prob"] > 15:
        print(f"    ⚠️ 12碼風險高！")

    # 總入球
    print(f"\n  ⚽ 總入球分佈:")
    for g in range(7):
        if str(g) in r["total_goals_dist"]:
            bar = "█" * int(r["total_goals_dist"][str(g)] / 3)
            print(f"    {g:>2} 球: {r['total_goals_dist'][str(g)]:>5.1f}% {bar}")

    print(f"\n  📈 大小球:")
    print(f"    大1.5 {r['over15']}% | 大2.5 {r['over25']}% | 大3.5 {r['over35']}% | 大4.5 {r['over45']}%")
    print(f"    預期總入球: {r['expected_goals']} | 最可能總入球: {r['most_likely_total']}球")
    o25_rec = "大2.5" if r['over25'] >= 55 else ("小2.5" if r['over25'] <= 40 else "不宜")
    print(f"    推薦: {o25_rec}")

    # 比分
    print(f"\n  🎯 最可能比分（90分鐘）:")
    for i,(g1,g2,p) in enumerate(r["top_scores"][:8]):
        marker = "→" if i==0 else " "
        print(f"    {marker} {r['team_a'][:4]} {g1}-{g2} {r['team_b'][:4]} ({p}%)")

    # 信心
    maxp = max(r['win_a_90'], r['draw_90'], r['win_b_90'])
    if maxp >= 80: level = "🟢 高"
    elif maxp >= 60: level = "🟡 中"
    else: level = "🔴 高風險"
    print(f"\n  🚦 信心: {level}（最高 {maxp}%）")

def load_odds_from_file(path):
    """從JSON檔案載入賠率"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

if __name__ == "__main__":
    # 內置聽日賽程（7月4日 HKT）
    tomorrow_matches = [
        ("澳洲", "埃及", 2.20, 3.00, 3.30, 0),
        ("阿根廷", "佛得角", 1.30, 5.00, 9.00, 0),
        ("哥倫比亞", "加納", 1.75, 3.40, 4.50, 0),
    ]
    
    for team_a, team_b, oh, od, oa, alt in tomorrow_matches:
        r = predict_enhanced(team_a, team_b, oh, od, oa, is_knockout=True, altitude=alt)
        print_report(r)
        # JSON輸出
        print(f"\n{json.dumps({k:v for k,v in r.items() if k != 'top_scores'}, ensure_ascii=False, indent=2)}")
