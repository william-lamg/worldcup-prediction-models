"""
黃牌/紅牌預測 — 已整合入 V5.6 模型
=================================
用法：python card_model.py [隊A] [隊B] [--final]

數據源：ESPN Discipline Stats (2026 World Cup)
         https://www.espn.com/soccer/stats/_/league/FIFA.WORLD/view/discipline
"""
import json, math, sys

DISCIPLINE_DATA = {
    "法國": (6, 4, 0), "France": (6, 4, 0),
    "西班牙": (6, 5, 0), "Spain": (6, 5, 0),
    "英格蘭": (7, 6, 1), "England": (7, 6, 1),
    "阿根廷": (6, 6, 0), "Argentina": (6, 6, 0),
    "比利時": (6, 10, 1), "Belgium": (6, 10, 1),
    "葡萄牙": (6, 7, 0), "Portugal": (6, 7, 0),
    "巴西": (5, 8, 0), "Brazil": (5, 8, 0),
    "挪威": (5, 3, 0), "Norway": (5, 3, 0),
    "摩洛哥": (6, 7, 0), "Morocco": (6, 7, 0),
    "瑞士": (6, 6, 1), "Switzerland": (6, 6, 1),
    "哥倫比亞": (5, 8, 0), "Colombia": (5, 8, 0),
    "埃及": (5, 12, 0), "Egypt": (5, 12, 0),
    "美國": (5, 7, 1), "USA": (5, 7, 1),
    "荷蘭": (4, 3, 0), "Netherlands": (4, 3, 0),
    "德國": (4, 3, 0), "Germany": (4, 3, 0),
    "墨西哥": (5, 4, 1), "Mexico": (5, 4, 1),
    "塞內加爾": (4, 3, 0), "Senegal": (4, 3, 0),
}

KO_FACTOR = 1.2   # 淘汰賽 ×1.2
FINAL_FACTOR = 0.9  # 決賽 ×0.9（裁判尺度鬆）

def predict_cards(team_a, team_b, is_final=True):
    def get_stats(t):
        for k, v in DISCIPLINE_DATA.items():
            if t.lower() in k.lower() or k.lower() in t.lower():
                return v
        return (3, 4, 0)
    
    p_a, yc_a, rc_a = get_stats(team_a)
    p_b, yc_b, rc_b = get_stats(team_b)
    
    avg_a = yc_a / max(p_a, 1)
    avg_b = yc_b / max(p_b, 1)
    
    factor = KO_FACTOR * (FINAL_FACTOR if is_final else 1.0)
    
    exp_a = avg_a * factor
    exp_b = avg_b * factor
    total = exp_a + exp_b
    
    # 泊松
    def poisson(l, k):
        return (l**k) * math.exp(-l) / math.factorial(k)
    
    dist = {}
    for k in range(11):
        p = poisson(total, k)
        if p > 0.001:
            dist[k] = round(p * 100, 1)
    
    prob_0_2 = sum(dist.get(k, 0) for k in range(0, 3))
    prob_3_5 = sum(dist.get(k, 0) for k in range(3, 6))
    prob_6p = sum(dist.get(k, 0) for k in range(6, 11))
    red_p = round((rc_a + rc_b) / max(p_a + p_b, 1), 3)
    
    return {
        "avg_a": round(avg_a, 2), "avg_b": round(avg_b, 2),
        "exp_a": round(exp_a, 2), "exp_b": round(exp_b, 2),
        "total_exp": round(total, 2),
        "dist": dist,
        "prob_0_2": round(prob_0_2, 1),
        "prob_3_5": round(prob_3_5, 1),
        "prob_6p": round(prob_6p, 1),
        "red_prob": round(red_p * 100, 1),
    }

if __name__ == "__main__":
    args = sys.argv[1:]
    is_final = "--final" in args or len(args) < 2
    
    if len(args) >= 2:
        ta, tb = args[0], args[1]
    else:
        ta, tb = "法國", "西班牙"
    
    r = predict_cards(ta, tb, is_final)
    
    print("=" * 55)
    print(f"  🟨 黃牌預測：{ta} vs {tb}")
    if is_final:
        print(f"  🏆 決賽模式")
    print("=" * 55)
    print(f"  📊 場均黃牌: {ta} {r['avg_a']} / {tb} {r['avg_b']}")
    print(f"  🎯 預測: {ta} {r['exp_a']}張 + {tb} {r['exp_b']}張 = {r['total_exp']}張")
    print()
    print(f"  📈 黃牌分佈:")
    print(f"    0-2張: {r['prob_0_2']}% {'█'*int(r['prob_0_2']/2)}")
    print(f"    3-5張: {r['prob_3_5']}% {'█'*int(r['prob_3_5']/2)}")
    print(f"    6+張:  {r['prob_6p']}% {'█'*int(r['prob_6p']/2)}")
    print(f"  🟥 紅牌概率: {r['red_prob']}%")
    
    rec = "0-2張 ✅" if r['prob_0_2'] >= 40 else ("3-5張 ✅" if r['prob_3_5'] >= 40 else "⚠️ 高風險")
    print(f"  🎯 推薦: {rec}")
