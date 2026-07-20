import math

def poisson(l,k):
    return (l**k)*math.exp(-l)/math.factorial(k)

def analyze(ta, tb, la, lb, pa, pd, pb):
    total = la + lb
    print(f'{"="*55}')
    print(f'  {ta} vs {tb}')
    print(f'{"="*55}')
    
    o25 = sum(poisson(la,i)*poisson(lb,j) for i in range(15) for j in range(15) if i+j>2)
    o35 = sum(poisson(la,i)*poisson(lb,j) for i in range(15) for j in range(15) if i+j>3)
    
    print(f'  勝平負: {ta} {pa*100:.0f}% / 和 {pd*100:.0f}% / {tb} {pb*100:.0f}%')
    print(f'  xG: {ta} {la:.2f} / {tb} {lb:.2f} | 預期總入球: {total:.2f}')
    
    # 大小球最佳選擇
    print(f'  總入球推薦:')
    print(f'    大 2.5: {o25*100:.0f}% | 小 2.5: {(1-o25)*100:.0f}%')
    print(f'    大 3.5: {o35*100:.0f}% | 小 3.5: {(1-o35)*100:.0f}%')
    if o25 >= 0.60:
        print(f'    -> 推薦大 2.5 球')
    elif o25 <= 0.40:
        print(f'    -> 推薦小 2.5 球')
    else:
        print(f'    -> 大小球五五波，不宜入手')
    
    scores_list = [(i,j, poisson(la,i)*poisson(lb,j)) for i in range(12) for j in range(12)]
    
    # 讓球分析（針對熱門隊）
    fav = ta if pa > pb else tb
    l_fav = la if pa > pb else lb
    l_und = lb if pa > pb else la
    
    print(f'  讓球分析 ({fav} 讓球):')
    for hcap in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        win = sum(p for i,j,p in scores_list if pa>pb and i-j > hcap-0.5 or pb>pa and j-i > hcap-0.5)
        lose = sum(p for i,j,p in scores_list if pa>pb and i-j < hcap-0.5 or pb>pa and j-i < hcap-0.5)
        push = 1 - win - lose
        label = f'{fav} -{hcap:.0f}' if hcap == int(hcap) else f'{fav} -{hcap:.1f}'
        if hcap <= 2.0:
            print(f'    {label}: 贏 {win*100:.0f}% / 走 {push*100:.0f}% / 輸 {lose*100:.0f}%')
    
    # 找到最佳讓球（贏面 55-80% 之間的最近整數）
    best = None
    for hcap in [x/2 for x in range(1,9)]:
        win_p = sum(p for i,j,p in scores_list if pa>pb and i-j > hcap-0.5 or pb>pa and j-i > hcap-0.5)
        if 0.55 <= win_p <= 0.82:
            if best is None or hcap > best[0]:
                best = (hcap, win_p)
    
    if best:
        label = f'{fav} -{best[0]:.0f}' if best[0] == int(best[0]) else f'{fav} -{best[0]:.1f}'
        print(f'  🏆 最佳讓球: {label}（贏面 {best[1]*100:.0f}%）')
    else:
        # 冇清晰讓球推薦，就推薦讓 0.5
        win_05 = sum(p for i,j,p in scores_list if pa>pb and i-j > -0.5 or pb>pa and j-i > -0.5)
        print(f'  🏆 最佳讓球: {fav} -0.5（贏面 {win_05*100:.0f}%，即勝平負）')
    
    # 最可能比分
    top_scores = sorted(scores_list, key=lambda x: -x[2])[:5]
    print(f'  最可能比分:')
    for i,(g1,g2,p) in enumerate(top_scores):
        print(f'    {ta[:3]} {g1}-{g2} {tb[:3]} ({p*100:.1f}%)')

analyze('西班牙', '沙特', 3.30, 0.70, 0.862, 0.093, 0.045)
analyze('比利時', '伊朗', 1.95, 0.70, 0.668, 0.208, 0.125)
analyze('烏拉圭', '佛得角', 2.50, 0.50, 0.812, 0.133, 0.055)
analyze('紐西蘭', '埃及', 0.65, 1.65, 0.142, 0.243, 0.615)
