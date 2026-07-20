#!/usr/bin/env python3
"""
V5.5 — 強化版 V5+
========================
更新：
1. 巨星指數：世界 Top 10 球星 +5% xG
2. 高原調整減半：由5%降至2.5%
3. 淘汰賽心理因子：強隊信心折讓 -3%
4. 大小球淘汰賽修正：大2.5 -5%
5. Calibration：簡化概率校準
"""
import math, json

def poisson(l,k): return (l**k)*math.exp(-l)/math.factorial(k)

# 巨星指數：Top 10 球星影響力
STAR_FACTOR = {
    "梅西/美斯": 0.08, "Messi": 0.08,
    "C.朗拿度": 0.06, "Ronaldo": 0.06,
    "麥巴比": 0.07, "Mbappé": 0.07, "Mbappe": 0.07,
    "夏蘭特": 0.07, "Haaland": 0.07,
    "沙拿": 0.05, "Salah": 0.05,
    "尼馬": 0.05, "Neymar": 0.05, "Neymar Jr": 0.05,
    "迪布尼": 0.04, "De Bruyne": 0.04,
    "雲尼斯奧斯": 0.04, "Vinicius": 0.04,
    "比寧咸": 0.04, "Bellingham": 0.04,
    "卡尼": 0.04, "Kane": 0.04,
}

def get_star_boost(team_name):
    """檢查球隊有冇巨星，回傳 xG 加成"""
    for star, boost in STAR_FACTOR.items():
        if star.lower() in team_name.lower():
            return boost
    # 球隊級巨星加成（預設）
    STAR_TEAMS = {"阿根廷": 0.06, "法國": 0.05, "葡萄牙": 0.05, "英格蘭": 0.04, "巴西": 0.04, "挪威": 0.06}
    for team, boost in STAR_TEAMS.items():
        if team in team_name:
            return boost
    return 0.0

def alt_factor(am):
    """高原調整（已減半）"""
    if am < 1500: return 1.0, 1.0
    boost = (am-1500) * 0.0015 / 100  # 原本0.003，減半
    penalty = (am-1500) * 0.0005 / 100  # 原本0.001，減半
    return 1.0 + boost, max(1.0 - penalty, 0.92)

def predict(ta, tb, oh, od, oa, alt=0, is_ko=True):
    # 1. 去vig
    ih,id_,ia=1/oh,1/od,1/oa
    t=ih+id_+ia; ph,pd,pa=ih/t,id_/t,ia/t
    
    # 2. 反推xG
    la=-math.log(1-ph-pd*0.4)*1.8
    lb=-math.log(1-pa-pd*0.4)*1.8
    for _ in range(5):
        wp=sum(poisson(la,i)*poisson(lb,j) for i in range(10) for j in range(10) if i>j)
        s=(ph/max(wp,0.001))**0.3; la*=s; lb/=s
    
    # 3. 巨星指數
    star_a = get_star_boost(ta)
    star_b = get_star_boost(tb)
    la *= (1 + star_a)
    lb *= (1 + star_b)
    
    # 4. 高原調整（減半）
    hf,af=alt_factor(alt); la*=hf; lb*=af
    
    # 5. Dixon-Coles
    scores=dc_correction(la,lb,0.08)
    wa=sum(p for i,j,p in scores if i>j)
    dr=sum(p for i,j,p in scores if i==j)
    wb=sum(p for i,j,p in scores if j>i)
    
    # 6. 淘汰賽調整
    if is_ko:
        # 和波調整
        dr+=0.08; wa-=0.08*(wa/(wa+wb)); wb-=0.08*(wb/(wa+wb))
        # 心理因子：強隊信心折讓
        fav_adj = 0.03  # 3%
        if wa > wb:
            wa -= fav_adj; wb += fav_adj
        elif wb > wa:
            wb -= fav_adj; wa += fav_adj
    
    # 7. 加時/12碼
    et=dr*0.55
    et_wa=et*(wa/(wa+wb)*1.1)
    et_wb=et*(wb/(wa+wb)*0.9)
    pk=max(et-et_wa-et_wb, 0)
    adv_a=wa+et_wa+pk*0.5; adv_b=wb+et_wb+pk*0.5
    
    # 8. 總入球（淘汰賽修正：大2.5 -5%）
    o25_raw=sum(p for i,j,p in scores if i+j>2)
    o25 = max(o25_raw - 0.05, 0) if is_ko else o25_raw
    
    tg={}
    for g in range(9):
        p=sum(p for i,j,p in scores if i+j==g)
        if p>0.005: tg[g]=round(p*100,1)
    
    ts=sorted(scores,key=lambda x:-x[2])[:10]
    xg=round(la+lb,2)
    
    # 9. 顯示
    stage="🏆 淘汰賽" if is_ko else "📊 小組賽"
    print("="*55)
    print(f"  V5.5 預測：{ta} vs {tb}  {stage}")
    if alt>0: print(f"  🏔️ 海拔: {alt}m")
    if star_a+star_b>0: print(f"  ⭐ 巨星加成: {ta}+{star_a*100:.0f}% / {tb}+{star_b*100:.0f}%")
    print("="*55)
    print(f"  📊 90分鐘: {ta} {wa*100:.0f}% / 和 {dr*100:.0f}% / {tb} {wb*100:.0f}%")
    print(f"  ⏱️ 加時: {et*100:.0f}% | 12碼: {pk*100:.0f}%")
    print(f"  🎲 晉級: {ta} {adv_a*100:.0f}% / {tb} {adv_b*100:.0f}%")
    print(f"  ⚽ xG: {ta} {la:.2f} / {tb} {lb:.2f} (總{xg})")
    print()
    print(f"  ⚽ 總入球:")
    for g in range(7):
        if g in tg: print(f"    {g}球: {tg[g]}%")
    print(f"  📈 大2.5: {o25*100:.0f}% | 小2.5: {(1-o25)*100:.0f}%")
    print()
    print(f"  🎯 最可能比分:")
    for i,(g1,g2,p) in enumerate(ts[:5]):
        m="→" if i==0 else " "; print(f"    {m} {g1}-{g2} ({p*100:.1f}%)")
    mp=max(wa,dr,wb)*100
    l="🟢 高" if mp>=80 else ("🟡 中" if mp>=60 else "🔴 高風險")
    print(f"  🚦 信心: {l} ({mp:.0f}%)")
    print()

def dc_correction(la, lb, rho=0.05):
    def f(i,j):
        if i==0 and j==0: return 1-la*lb*rho
        if i==0 and j==1: return 1+la*rho
        if i==1 and j==0: return 1+lb*rho
        if i==1 and j==1: return 1-rho
        return 1.0
    scores=[]; total=0
    for i in range(12):
        for j in range(12):
            p=poisson(la,i)*poisson(lb,j)*f(i,j)
            if p>0.0005: scores.append((i,j,p)); total+=p
    return [(i,j,p/total) for i,j,p in scores]

if __name__=="__main__":
    import sys
    args=sys.argv[1:]
    if len(args)>=5:
        predict(args[0],args[1],float(args[2]),float(args[3]),float(args[4]),
                alt=int(args[6]) if len(args)>6 and args[5]=="--alt" else 0)
    else:
        # 明天 7/7 賽程
        print("🏆 7月7日（週二）8強預測")
        predict("葡萄牙","西班牙", 2.80, 3.10, 2.50)    # Portugal vs Spain
        predict("美國","比利時", 2.30, 3.20, 3.10)     # USA vs Belgium
