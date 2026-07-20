#!/usr/bin/env python3
"""
V4 世界盃預測系統
=================
核心哲學：市場賠率係最準嘅信號，唔靠 Elo

流程：
  ① 輸入市場賠率（手動或 WebSearch）
  ② 反推期望入球（從賠率倒推 xG）
  ③ 泊松分佈生成比分概率
  ④ 輸出勝平負 + 最可能比分

無 Elo、無洲份偏誤、純粹市場驅動
"""

import math
import sys
import json
import subprocess
import re

# ========== 核心函數 ==========

def vig_free_probs(odds_h, odds_d, odds_a):
    """將賠率轉為無抽水概率"""
    raw_h = 1.0 / odds_h
    raw_d = 1.0 / odds_d
    raw_a = 1.0 / odds_a
    total = raw_h + raw_d + raw_a
    vig = total - 1.0
    return {
        'home': round(raw_h / total * 100, 1),
        'draw': round(raw_d / total * 100, 1),
        'away': round(raw_a / total * 100, 1),
        'vig': round(vig * 100, 1)
    }


def probs_to_xg(home_prob, draw_prob, away_prob):
    """
    從勝平負概率倒推期望入球
    使用簡化版：利用泊松分布嘅特性，
    勝率 ≈ P(λ_h > λ_a)，和率 ≈ P(λ_h = λ_a)
    """
    # 從勝率和率倒推 λ
    # 用迭代逼近
    best = None
    best_err = 999
    
    for lh in [i * 0.05 for i in range(1, 80)]:  # 0.05 ~ 4.0
        for la in [i * 0.05 for i in range(1, 80)]:
            # 計算泊松概率
            p_h, p_d, p_a = 0, 0, 0
            for i in range(12):
                for j in range(12):
                    prob = poisson(lh, i) * poisson(la, j)
                    if i > j: p_h += prob
                    elif i == j: p_d += prob
                    else: p_a += prob
            
            err = (p_h - home_prob/100)**2 + (p_d - draw_prob/100)**2 + (p_a - away_prob/100)**2
            if err < best_err:
                best_err = err
                best = (lh, la, p_h, p_d, p_a)
    
    return best  # (λ_home, λ_away, calc_h, calc_d, calc_a)


def poisson(lmbda, k):
    """泊松分佈 P(X=k)"""
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


def score_distribution(lmbda_h, lmbda_a, top_n=5):
    """從 λ 生成比分概率分布"""
    scores = []
    for i in range(10):
        for j in range(10):
            p = poisson(lmbda_h, i) * poisson(lmbda_a, j)
            if p > 0.001:  # 只保留 >0.1%
                scores.append(((i, j), p * 100))
    
    scores.sort(key=lambda x: -x[1])
    return scores[:top_n]


def probs_from_xg(lmbda_h, lmbda_a):
    """從 λ 計算勝平負概率"""
    p_h, p_d, p_a = 0, 0, 0
    for i in range(12):
        for j in range(12):
            prob = poisson(lmbda_h, i) * poisson(lmbda_a, j)
            if i > j: p_h += prob
            elif i == j: p_d += prob
            else: p_a += prob
    return p_h, p_d, p_a


def get_v3_prediction(team_a_en, team_b_en):
    """從 V3 引擎獲取參考預測（只用比分分佈），需傳英文隊名"""
    engine = "wcpredict.py"
    py = "python3"
    
    try:
        r = subprocess.run([py, '-X', 'utf8', engine, 'match', team_a_en, team_b_en],
                          capture_output=True, timeout=30)
        out = r.stdout.decode('utf-8', errors='replace')
        if not out.strip():
            return None
        
        # 解析勝平負 — 更靈活嘅 regex
        pm = re.search(r'胜平负:\s+(.+?)胜\s+(\d+)%\s+平\s+(\d+)%\s+(.+?)胜\s+(\d+)%', out)
        # 解析比分
        sm = re.findall(r'([\d]+-[\d]+)\s+\(([\d.]+)%\)', out)
        
        if pm:
            return {
                'probs': {
                    'home': float(pm.group(2)),
                    'draw': float(pm.group(3)),
                    'away': float(pm.group(5))
                },
                'scores': [(s, float(p)) for s, p in sm[:5]]
            }
    except Exception as e:
        pass
    return None


def predict_from_odds(team_a, team_b, odds_h, odds_d, odds_a):
    """從市場賠率做完整預測（V4 核心）"""
    print(f"\n{'='*55}")
    print(f"  V4 預測：{team_a} vs {team_b}")
    print(f"{'='*55}")
    
    # 1. 去抽水
    vf = vig_free_probs(odds_h, odds_d, odds_a)
    print(f"\n  💰 市場賠率:")
    print(f"     {team_a}勝 {odds_h} | 和 {odds_d} | {team_b}勝 {odds_a}")
    print(f"     抽水率: {vf['vig']}%")
    print(f"     無抽水概率: {team_a} {vf['home']}% / 和 {vf['draw']}% / {team_b} {vf['away']}%")
    
    # 2. 反推期望入球
    xg_result = probs_to_xg(vf['home'], vf['draw'], vf['away'])
    if xg_result:
        lh, la, ch, cd, ca = xg_result
        print(f"\n  📊 反推期望入球 λ:")
        print(f"     {team_a}: {lh:.2f} 球")
        print(f"     {team_b}: {la:.2f} 球")
        print(f"     擬合誤差: {( (ch-vf['home']/100)**2 + (cd-vf['draw']/100)**2 + (ca-vf['away']/100)**2 )**0.5*100:.1f}%")
        
        # 3. 生成比分分佈
        scores = score_distribution(lh, la, 6)
        print(f"\n  🎯 最可能比分:")
        for i, ((h, a), p) in enumerate(scores):
            marker = '→' if i == 0 else ' '
            print(f"     {marker} {team_a} {h}-{a} {team_b} ({p:.1f}%)")
        
        # 4. 大小球概率
        over25 = 0
        for i in range(10):
            for j in range(10):
                if i + j > 2:
                    over25 += poisson(lh, i) * poisson(la, j)
        print(f"\n  📈 大小球:")
        print(f"     大 2.5: {over25*100:.1f}%")
        print(f"     小 2.5: {(1-over25)*100:.1f}%")
        
        return {
            'odds': {'h': odds_h, 'd': odds_d, 'a': odds_a},
            'vig_free': vf,
            'xg': (lh, la),
            'scores': scores,
            'over25': over25
        }
    else:
        print("  ❌ 無法反推期望入球")
        return None


def predict_no_odds(team_a, team_b, team_a_en=None, team_b_en=None):
    """冇賠率時：用 V3 + 校正層做參考（需英文隊名）"""
    en_a = team_a_en or team_a
    en_b = team_b_en or team_b
    v3 = get_v3_prediction(en_a, en_b)
    if not v3:
        print(f"  ❌ 無法獲取 V3 預測，試下提供英文隊名")
        print(f"     例如：python predict_v4.py match Iran 'New Zealand'")
        return
    
    print(f"\n{'='*55}")
    print(f"  ⚠️ V3 參考預測（冇市場賠率）: {team_a} vs {team_b}")
    print(f"{'='*55}")
    print(f"\n  📊 V3 概率:")
    p = v3['probs']
    print(f"     {team_a}勝 {p['home']}% / 和 {p['draw']}% / {team_b}勝 {p['away']}%")
    print(f"\n  🎯 最可能比分:")
    for i, (s, pp) in enumerate(v3['scores'][:5]):
        marker = '→' if i == 0 else ' '
        print(f"     {marker} {s} ({pp}%)")
    print(f"\n  ⚠️ 建議搭配市場賠率使用")
    return v3


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--help":
        print("""V4 預測系統用法:

  1) 有賠率（推薦）：
     python predict_v4.py odds "主隊" "客隊" 主勝賠率 和賠率 客勝賠率
     
     例子：python predict_v4.py odds "西班牙" "佛得角" 1.05 12.00 30.00

  2) 冇賠率（V3 參考）：
     python predict_v4.py match "主隊" "客隊"
     
     例子：python predict_v4.py match "西班牙" "佛得角"
""")
    elif len(sys.argv) >= 3 and sys.argv[1] == "match":
        team_a = sys.argv[2]
        team_b = sys.argv[3]
        team_a_en = sys.argv[4] if len(sys.argv) >= 5 else None
        team_b_en = sys.argv[5] if len(sys.argv) >= 6 else None
        predict_no_odds(team_a, team_b, team_a_en, team_b_en)
    elif len(sys.argv) >= 7 and sys.argv[1] == "odds":
        predict_from_odds(sys.argv[2], sys.argv[3],
                         float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]))
    else:
        print("用法：python predict_v4.py --help")
