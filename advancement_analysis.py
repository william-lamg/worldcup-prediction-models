"""
淘汰賽晉級概率估算
基於 V5 模型概率 + 淘汰賽晉級推導
"""
import json, math

# Round of 32 對陣（已賽 + 未賽）
# 格式：(隊A, 隊B, 預計A勝概率, 是否已完成)
round32 = [
    ("加拿大", "南非", 0.56, True),   # 已賽，加拿大贏
    ("巴西", "日本", 0.53, False),
    ("德國", "巴拉圭", 0.68, False),
    ("荷蘭", "摩洛哥", 0.49, False),
    ("象牙海岸", "挪威", 0.50, False),  # 估 ~50%
    ("法國", "瑞典", 0.65, False),
    ("墨西哥", "厄瓜多爾", 0.55, False),
    ("英格蘭", "剛果金", 0.70, False),
    ("比利時", "塞內加爾", 0.55, False),
    ("美國", "波黑", 0.60, False),
    ("葡萄牙", "克羅地亞", 0.58, False),
    ("西班牙", "奧地利", 0.72, False),
    ("瑞士", "阿爾及利亞", 0.52, False),
    ("阿根廷", "佛得角", 0.78, False),
    ("哥倫比亞", "加納", 0.55, False),
    ("澳洲", "埃及", 0.45, False),
]

# 16強對陣（已知）
round16 = [
    ("加拿大", "巴西/日本"),         # M73 勝者 vs M75 勝者
    ("德國/巴拉圭", "荷蘭/摩洛哥"),  # M76 勝者 vs M77 勝者
    ("象牙海岸/挪威", "法國/瑞典"),  # M78 勝者 vs M79 勝者
    ("墨西哥/厄瓜多爾", None),       # M80 勝者
    ("英格蘭/剛果金", None),         # M81 勝者
    ("比利時/塞內加爾", "美國/波黑"),# M82 vs M83
    ("葡萄牙/克羅地亞", "西班牙/奧地利"), # M84 vs M85
    ("瑞士/阿爾及利亞", None),       # M86 
    ("阿根廷/佛得角", None),         # M87
    ("哥倫比亞/加納", "澳洲/埃及"),  # M88 vs M89
]

def calc_advance(matches, probs):
    """計算晉級概率"""
    results = {}
    for team, prob in probs.items():
        # 16強概率 = win round32
        r16 = prob
    
    return results

# 計算所有隊嘅32強晉級概率
print("=" * 50)
print("  🏆 淘汰賽晉級概率估算")
print("=" * 50)

advance_probs = {}
for team_a, team_b, prob_a, done in round32:
    prob_b = 1 - prob_a
    if done:
        advance_probs[team_a] = prob_a
        advance_probs[team_b] = 0
        print(f"  {'✅' if prob_a > 0.5 else '❌'} {team_a} {prob_a*100:.0f}% vs {team_b} {prob_b*100:.0f}%")
    else:
        advance_probs[team_a] = prob_a
        advance_probs[team_b] = prob_b
        bar_a = "█" * int(prob_a * 20)
        bar_b = "█" * int(prob_b * 20)
        print(f"     {team_a:>8} {prob_a*100:.0f}% {bar_a:<20} {team_b:<8} {prob_b*100:.0f}% {bar_b}")

print()

# 估計16強晉級概率
print("=" * 50)
print("  🏆 16強晉級概率（Top 10）")
print("=" * 50)

sorted_teams = sorted(advance_probs.items(), key=lambda x: -x[1])
for team, prob in sorted_teams:
    bar = "█" * int(prob * 20)
    print(f"  {team:>10} {prob*100:.0f}% {bar}")

print()
print("=" * 50)
print("  🏆 最早確定晉級16強嘅球隊")
print("=" * 50)

# 已確定
confirmed = [t for t, p in sorted_teams if p >= 0.70 or (t == "加拿大" and p == 0.56)]
# 用已確定或接近確定嘅
high_prob = [t for t, p in sorted_teams if p >= 0.65]
for t in high_prob:
    print(f"  ✅ {t}")
