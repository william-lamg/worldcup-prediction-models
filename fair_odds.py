import math

def poisson(l, k):
    return (l**k) * math.exp(-l) / math.factorial(k)

def fair_odds(prob):
    if prob < 0.001:
        return 999
    return round(1 / prob * 0.95, 2)

matches = [
    ('西班牙 vs 沙特', 3.30, 0.70, '西班牙', '沙特'),
    ('比利時 vs 伊朗', 1.95, 0.70, '比利時', '伊朗'),
    ('烏拉圭 vs 佛得角', 2.50, 0.50, '烏拉圭', '佛得角'),
    ('紐西蘭 vs 埃及', 0.65, 1.65, '紐西蘭', '埃及'),
]

for name, la, lb, ha, aa in matches:
    scores = []
    for i in range(8):
        for j in range(8):
            p = poisson(la, i) * poisson(lb, j)
            if p > 0.002:
                scores.append((i, j, p))
    scores.sort(key=lambda x: -x[2])
    
    print("=" * 55)
    print(f"  {name} — 公平賠率（含5%抽水）")
    print("=" * 55)
    print(f"  {'比分':>8} {'模型概率':>8} {'公平賠率':>10}")
    print(f"  {'-'*30}")
    
    for i, j, p in scores[:12]:
        winner = ha if i > j else (aa if j > i else '和')
        label = f"{ha[:2]}{i}-{j}{aa[:2]}"
        odds = fair_odds(p)
        print(f"  {label:>10} {p*100:>6.1f}% {odds:>8.2f}")
    
    print()
    print(f"  --- 總進球數 ---")
    for g in range(0, 7):
        prob = sum(poisson(la, i)*poisson(lb, j) for i in range(8) for j in range(8) if i+j == g)
        if prob > 0.01:
            odds = fair_odds(prob)
            print(f"  總進球 {g}: {prob*100:.1f}% -> 公平賠率 {odds:.2f}")
    print()
