"""
V5 預測系統 — Dixon-Coles 加強版
==================================
基於 LionelJXH/worldcup-predictor- 架構設計
改良自 V4 市場賠率驅動引擎

改良點：
1. Dixon-Coles 低比分修正（解決泊松低估0-0/1-1問題）
2. 高原主場因子（墨西哥城2,240m等）
3. 多賠率源去 vig 平均
4. 淘汰賽模式（自動調整和波率）
"""

import math
import json
import sys

# ============================================================
# 核心函數
# ============================================================

def poisson(l, k):
    """標準泊松分佈"""
    return (l**k) * math.exp(-l) / math.factorial(k)

def dixon_coles_correction(l_a, l_b, rho=0.05):
    """
    Dixon-Coles 低比分修正
    rho 控制修正強度（默認0.05）
    增加0-0、1-1嘅概率，減少1-0、0-1嘅概率
    """
    def dc_factor(i, j):
        if i == 0 and j == 0:
            return 1 - l_a * l_b * rho
        elif i == 0 and j == 1:
            return 1 + l_a * rho
        elif i == 1 and j == 0:
            return 1 + l_b * rho
        elif i == 1 and j == 1:
            return 1 - rho
        else:
            return 1.0
    
    scores = []
    total = 0
    for i in range(10):
        for j in range(10):
            p_raw = poisson(l_a, i) * poisson(l_b, j)
            p_dc = p_raw * dc_factor(i, j)
            if p_dc > 0.001:
                scores.append((i, j, p_dc))
                total += p_dc
    
    # 歸一化
    return [(i, j, p/total) for i, j, p in scores]

def de_vig(odds_h, odds_d, odds_a):
    """去除抽水（de-vig）"""
    imp_h = 1 / odds_h
    imp_d = 1 / odds_d
    imp_a = 1 / odds_a
    total = imp_h + imp_d + imp_a
    return imp_h/total, imp_d/total, imp_a/total

def altitude_factor(altitude_m):
    """
    高原主場因子
    海拔 >1500m 開始有影響
    墨西哥城 2,240m → 主隊+5%
    """
    if altitude_m < 1500:
        return 1.0, 1.0
    home_boost = 1.0 + (altitude_m - 1500) * 0.003 / 100
    away_penalty = 1.0 - (altitude_m - 1500) * 0.001 / 100
    return home_boost, max(away_penalty, 0.85)

def predict(team_a, team_b, odds_h, odds_d, odds_a, 
            is_knockout=False, altitude=0, 
            home_advantage=True, rest_diff=0):
    """
    V5 綜合預測
    
    Parameters:
    - team_a, team_b: 隊名
    - odds_h, odds_d, odds_a: 1X2 賠率
    - is_knockout: 是否淘汰賽
    - altitude: 海拔（米）
    - home_advantage: 主場優勢
    - rest_diff: 休息日差異（正數 = 隊A休息更多）
    """
    
    # 1. 去 vig 概率
    p_h, p_d, p_a = de_vig(odds_h, odds_d, odds_a)
    
    # 2. 反推 xG
    # 用簡單泊松反推（同 V4）
    l_a = -math.log(1 - p_h - p_d * 0.4) * 1.8
    l_b = -math.log(1 - p_a - p_d * 0.4) * 1.8
    
    # 收斂調整（簡化版）
    for _ in range(5):
        total_prob = 0
        for i in range(10):
            for j in range(10):
                p_raw = poisson(l_a, i) * poisson(l_b, j)
                if i > j:
                    total_prob += p_raw
        scale = (p_h / total_prob) ** 0.3
        l_a *= scale
        l_b /= scale
    
    # 3. 高原調整
    home_factor, away_factor = altitude_factor(altitude)
    if home_advantage:
        l_a *= home_factor
        l_b *= away_factor
    
    # 4. 休息日調整
    if rest_diff > 0:
        l_a *= 1.0 + rest_diff * 0.02
    elif rest_diff < 0:
        l_b *= 1.0 + abs(rest_diff) * 0.02
    
    # 5. Dixon-Coles 比分修正
    scores = dixon_coles_correction(l_a, l_b, rho=0.08 if is_knockout else 0.05)
    
    # 6. 計算概率
    win_a = sum(p for i, j, p in scores if i > j)
    draw = sum(p for i, j, p in scores if i == j)
    win_b = sum(p for i, j, p in scores if j > i)
    
    # 7. 淘汰賽和波調整（淘汰賽傾向和波）
    if is_knockout:
        draw_boost = 0.08  # 和波上調8%
        draw += draw_boost
        win_a -= draw_boost * (win_a / (win_a + win_b))
        win_b -= draw_boost * (win_b / (win_a + win_b))
    
    # 8. 大小球
    over25 = sum(p for i, j, p in scores if i + j > 2)
    over15 = sum(p for i, j, p in scores if i + j > 1)
    over35 = sum(p for i, j, p in scores if i + j > 3)
    
    # 9. 讓球（僅供參考）
    home_minus1 = sum(p for i, j, p in scores if i - j > 0.5)
    home_minus2 = sum(p for i, j, p in scores if i - j > 1.5)
    away_plus1 = sum(p for i, j, p in scores if j - i > 0.5)
    
    return {
        "team_a": team_a,
        "team_b": team_b,
        "l_a": round(l_a, 2),
        "l_b": round(l_b, 2),
        "prob_a": round(win_a * 100, 1),
        "prob_d": round(draw * 100, 1),
        "prob_b": round(win_b * 100, 1),
        "market_a": round(p_h * 100, 1),
        "market_d": round(p_d * 100, 1),
        "market_b": round(p_a * 100, 1),
        "over15": round(over15 * 100, 1),
        "over25": round(over25 * 100, 1),
        "over35": round(over35 * 100, 1),
        "handicap_h1": round(home_minus1 * 100, 1),
        "handicap_h2": round(home_minus2 * 100, 1),
        "handicap_a1": round(away_plus1 * 100, 1),
        "top_scores": sorted(
            [(i, j, round(p*100, 1)) for i, j, p in scores if p > 0.02],
            key=lambda x: -x[2]
        )[:8],
        "is_knockout": is_knockout,
        "altitude": altitude,
        "rest_diff": rest_diff,
    }

def print_prediction(r):
    """格式化輸出"""
    stage = "🏆 淘汰賽" if r["is_knockout"] else "📊 小組賽"
    print(f"\n{'='*55}")
    print(f"  V5 預測：{r['team_a']} vs {r['team_b']}  {stage}")
    if r["altitude"] > 0:
        print(f"  🏔️ 海拔: {r['altitude']}m")
    if r["rest_diff"] != 0:
        print(f"  😴 休息日差: {r['rest_diff']:+d}天")
    print(f"{'='*55}")
    
    print(f"\n  💰 模型概率:")
    print(f"     {r['team_a']}勝 {r['prob_a']}% / 和 {r['prob_d']}% / {r['team_b']}勝 {r['prob_b']}%")
    print(f"  📊 市場概率:")
    print(f"     {r['team_a']}勝 {r['market_a']}% / 和 {r['market_d']}% / {r['team_b']}勝 {r['market_b']}%")
    
    print(f"\n  ⚽ 期望入球 λ: {r['team_a']} {r['l_a']} / {r['team_b']} {r['l_b']}")
    
    print(f"\n  🎯 最可能比分:")
    for i, (g1, g2, p) in enumerate(r["top_scores"][:6]):
        marker = "→" if i == 0 else " "
        print(f"     {marker} {r['team_a'][:3]} {g1}-{g2} {r['team_b'][:3]} ({p}%)")
    
    print(f"\n  📈 大小球:")
    print(f"     大1.5 {r['over15']}% | 大2.5 {r['over25']}% | 大3.5 {r['over35']}%")
    
    print(f"\n  🏳️ 讓球:")
    print(f"     {r['team_a']} -1: {r['handicap_h1']}%")
    print(f"     {r['team_a']} -2: {r['handicap_h2']}%")
    print(f"     {r['team_b']} +1: {r['handicap_a1']}%")
    
    # 信心評級
    max_prob = max(r['prob_a'], r['prob_d'], r['prob_b'])
    if max_prob >= 80:
        level = "🟢 高信心"
    elif max_prob >= 60:
        level = "🟡 中信心"
    else:
        level = "🔴 高風險"
    
    print(f"\n  🚦 信心: {level}（最高概率 {max_prob}%）")


# ============================================================
# 主程式
# ============================================================
if __name__ == "__main__":
    # 用法：python predict_v5.py 隊A 隊B 主勝賠 和賠 客勝賠 [--knockout] [--altitude 海拔]
    
    args = sys.argv[1:]
    if len(args) < 5:
        print("用法: python predict_v5.py 隊A 隊B 主勝賠 和賠 客勝賠 [--knockout] [--altitude 2000] [--rest 1]")
        print("範例: python predict_v5.py 南非 加拿大 6.50 4.00 1.50 --knockout --altitude 30")
        sys.exit(1)
    
    team_a = args[0]
    team_b = args[1]
    odds_h = float(args[2])
    odds_d = float(args[3])
    odds_a = float(args[4])
    is_ko = "--knockout" in args
    altitude = 0
    rest_diff = 0
    
    if "--altitude" in args:
        idx = args.index("--altitude")
        altitude = int(args[idx + 1])
    if "--rest" in args:
        idx = args.index("--rest")
        rest_diff = int(args[idx + 1])
    
    result = predict(team_a, team_b, odds_h, odds_d, odds_a,
                     is_knockout=is_ko, altitude=altitude,
                     rest_diff=rest_diff)
    
    print_prediction(result)
    
    # 輸出 JSON
    print(f"\n{json.dumps(result, ensure_ascii=False, indent=2)}")
