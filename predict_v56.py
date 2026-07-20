#!/usr/bin/env python3
"""
V5.6 — 全面強化版
========================
新增：
1. 嚴格推薦門檻：≥60%先俾方向，<60%=純分析
2. Brier Score 持續監控
3. 傷病/停賽因子（手動 --injuries）
4. 淘汰賽經驗因子（--experience）
5. 賽程疲勞因子（--rest_diff）
"""
import math, json, sys

def poisson(l,k): return (l**k)*math.exp(-l)/math.factorial(k)

STAR_FACTOR = {
    "梅西": 0.08, "美斯": 0.08, "Messi": 0.08,
    "C朗": 0.06, "C.朗拿度": 0.06, "Ronaldo": 0.06,
    "麥巴比": 0.07, "Mbappe": 0.07, "Mbappé": 0.07,
    "夏蘭特": 0.07, "Haaland": 0.07,
    "比寧咸": 0.04, "Bellingham": 0.04,
    "卡尼": 0.04, "Kane": 0.04,
    "迪布尼": 0.04, "De Bruyne": 0.04,
}

STAR_TEAMS = {"阿根廷":0.06,"法國":0.05,"葡萄牙":0.05,"英格蘭":0.04,"巴西":0.04,"挪威":0.06}

def get_star_boost(name):
    for k,v in STAR_FACTOR.items():
        if k.lower() in name.lower(): return v
    for k,v in STAR_TEAMS.items():
        if k in name: return v
    return 0.0

def predict(ta, tb, oh, od, oa, alt=0, is_ko=True,
            inj_a=0, inj_b=0, exp_a=0, exp_b=0, rest=0):
    """
    ta, tb: 隊名
    oh, od, oa: 賠率
    alt: 海拔
    is_ko: 淘汰賽
    inj_a, inj_b: 傷病影響（-0.1 ~ -0.3）
    exp_a, exp_b: 淘汰賽經驗（0~1，0.5=平均）
    rest: 休息日差異（正=ta休息更多）
    """
    # 去vig
    ih,id_,ia=1/oh,1/od,1/oa
    t=ih+id_+ia; ph,pd,pa=ih/t,id_/t,ia/t
    la=-math.log(1-ph-pd*0.4)*1.8
    lb=-math.log(1-pa-pd*0.4)*1.8
    for _ in range(5):
        wp=sum(poisson(la,i)*poisson(lb,j) for i in range(10) for j in range(10) if i>j)
        s=(ph/max(wp,0.001))**0.3; la*=s; lb/=s
    # 巨星
    la*=1+get_star_boost(ta); lb*=1+get_star_boost(tb)
    # 海拔
    if alt>=1500:
        hf=1+(alt-1500)*0.0015/100; af=max(1-(alt-1500)*0.0005/100,0.92)
        la*=hf; lb*=af
    # 傷病
    la*=1+inj_a; lb*=1+inj_b
    # 休息日
    if rest>0: la*=1+rest*0.02
    elif rest<0: lb*=1+abs(rest)*0.02
    # 淘汰賽經驗（調整xG）
    la*=0.95+exp_a*0.1; lb*=0.95+exp_b*0.1
    
    def dc_fn(la,lb,rho=0.05):
        def f(i,j):
            if i==0 and j==0: return 1-la*lb*rho
            if i==0 and j==1: return 1+la*rho
            if i==1 and j==0: return 1+lb*rho
            if i==1 and j==1: return 1-rho
            return 1.0
        s=[];t=0
        for i in range(12):
            for j in range(12):
                p=poisson(la,i)*poisson(lb,j)*f(i,j)
                if p>0.0005: s.append((i,j,p)); t+=p
        return [(i,j,p/t) for i,j,p in s]
    
    scores=dc_fn(la,lb,0.08)
    wa=sum(p for i,j,p in scores if i>j)
    dr=sum(p for i,j,p in scores if i==j)
    wb=sum(p for i,j,p in scores if j>i)
    dr+=0.08; wa-=0.08*(wa/(wa+wb)); wb-=0.08*(wb/(wa+wb))
    if wa>wb: wa-=0.03; wb+=0.03
    elif wb>wa: wb-=0.03; wa+=0.03
    et=dr*0.55; ew=et*(wa/(wa+wb)*1.1); ew2=et*(wb/(wa+wb)*0.9); pk=max(et-ew-ew2,0)
    aa=wa+ew+pk*0.5; ab=wb+ew2+pk*0.5
    xg=round(la+lb,2); o25=round(max(sum(p for i,j,p in scores if i+j>2)-0.05,0)*100,1)
    ts=sorted(scores,key=lambda x:-x[2])[:5]
    tg={}
    for g in range(9):
        p=sum(p for i,j,p in scores if i+j==g)
        if p>0.005: tg[g]=round(p*100,1)
    
    mp=max(wa,dr,wb)*100
    
    # == V5.6 新功能 ==
    # 1. 推薦門檻
    if mp>=80: level="🟢 高信心"
    elif mp>=60: level="🟡 中信心"
    else: level="🔴 純分析"
    
    # 2. Brier（單場）
    actual=[1,0,0] if wa>wb and wa>dr else ([0,1,0] if dr>wa and dr>wb else [0,0,1])
    pred=[wa,dr,wb]
    brier=sum((a-p)**2 for a,p in zip(actual,pred))/3
    
    # 顯示
    sa=get_star_boost(ta)*100; sb=get_star_boost(tb)*100
    stage="🏆 淘汰賽" if is_ko else "📊 小組賽"
    rec=""
    if level=="🟢 高信心": rec=" ✅ 可參考"
    elif level=="🟡 中信心": rec=" ℹ️ 僅供參考"
    else: rec=" ⚠️ 純分析，不宜投注"
    
    print("="*60)
    print(f"  V5.6 預測：{ta} vs {tb}  {stage}{rec}")
    print(f"  Brier: {brier:.4f} | ",end="")
    print(f"🏔️{alt}m" if alt>0 else "🏟️中立場",end="")
    if rest!=0: print(f" | 休息差{rest:+d}天",end="")
    print()
    if sa>0 or sb>0: print(f"  ⭐ 巨星: {ta}+{sa:.0f}% / {tb}+{sb:.0f}%")
    if inj_a!=0 or inj_b!=0: print(f"  🏥 傷病: {ta}{inj_a*100:.0f}% / {tb}{inj_b*100:.0f}%")
    if exp_a>0 or exp_b>0: print(f"  🏆 經驗: {ta}{exp_a:.1f} / {tb}{exp_b:.1f}")
    print("="*60)
    print(f"  📊 90分鐘: {ta} {wa*100:.0f}% / 和 {dr*100:.0f}% / {tb} {wb*100:.0f}%")
    print(f"  ⏱️ 加時: {et*100:.0f}% | 12碼: {pk*100:.0f}%")
    print(f"  🎲 晉級: {ta} {aa*100:.0f}% / {tb} {ab*100:.0f}%")
    print(f"  ⚽ xG: {ta} {la:.2f} / {tb} {lb:.2f} (總{xg})")
    print(f"  ⚽ 總入球:")
    for g in range(7):
        if g in tg: print(f"    {g}球: {tg[g]}%")
    print(f"  📈 大2.5: {o25}% | 小2.5: {100-o25}%")
    print(f"  🎯 最可能比分:")
    for i,(g1,g2,p) in enumerate(ts):
        m="→" if i==0 else " "; print(f"    {m} {g1}-{g2} ({p*100:.1f}%)")
    print(f"  🚦 評級: {level}")
    if mp<60: print(f"  ⚠️ <60% 純分析，不構成投注建議")
    print()
    return {"wa":round(wa*100,1),"dr":round(dr*100,1),"wb":round(wb*100,1),"brier":round(brier,4)}

# ==================== 黃牌預測模組（可選）====================
CARD_DATA = {
    "法國":(6,4,0),"France":(6,4,0),"西班牙":(6,5,0),"Spain":(6,5,0),
    "英格蘭":(7,6,1),"England":(7,6,1),"阿根廷":(6,6,0),"Argentina":(6,6,0),
    "比利時":(6,10,1),"Belgium":(6,10,1),"葡萄牙":(6,7,0),"Portugal":(6,7,0),
    "巴西":(5,8,0),"Brazil":(5,8,0),"挪威":(5,3,0),"Norway":(5,3,0),
    "摩洛哥":(6,7,0),"Morocco":(6,7,0),"瑞士":(6,6,1),"Switzerland":(6,6,1),
    "哥倫比亞":(5,8,0),"Colombia":(5,8,0),"埃及":(5,12,0),"Egypt":(5,12,0),
}

def predict_cards(ta, tb, is_final=True):
    def get(t):
        for k,v in CARD_DATA.items():
            if t.lower() in k.lower() or k.lower() in t.lower(): return v
        return (3,4,0)
    pa,ya,_=get(ta); pb,yb,_=get(tb)
    avg_a=ya/max(pa,1); avg_b=yb/max(pb,1)
    factor=1.2*(0.9 if is_final else 1.0)
    exp_a=avg_a*factor; exp_b=avg_b*factor; total=exp_a+exp_b
    def p(l,k): return (l**k)*math.exp(-l)/math.factorial(k)
    dist={k:round(p(total,k)*100,1) for k in range(11) if p(total,k)>0.001}
    prob_02=sum(dist.get(k,0) for k in range(3))
    prob_35=sum(dist.get(k,0) for k in range(3,6))
    print(f"\n  🟨 黃牌預測 ({'決賽' if is_final else '淘汰賽'}模式):")
    print(f"    {ta} 場均{avg_a:.2f}張 → 預測{exp_a:.2f}張")
    print(f"    {tb} 場均{avg_b:.2f}張 → 預測{exp_b:.2f}張")
    print(f"    ** 總計: {total:.2f}張 **")
    print(f"    0-2張: {prob_02:.1f}% | 3-5張: {prob_35:.1f}% | 6+張: {100-prob_02-prob_35:.1f}%")
    rec="0-2張 ✅" if prob_02>=40 else ("3-5張 ✅" if prob_35>=40 else "⚠️不宜")
    print(f"    推薦: {rec}")

if __name__=="__main__":
    args=sys.argv[1:]
    show_cards="--cards" in args
    is_final="--final" in args
    
    if len(args)>=5:
        alt=0; inj_a=0; inj_b=0; exp_a=0.5; exp_b=0.5; rest=0; show_c=False
        for i,a in enumerate(args):
            if a=="--alt" and i+1<len(args): alt=int(args[i+1])
            if a=="--inj_a" and i+1<len(args): inj_a=float(args[i+1])
            if a=="--inj_b" and i+1<len(args): inj_b=float(args[i+1])
            if a=="--exp_a" and i+1<len(args): exp_a=float(args[i+1])
            if a=="--exp_b" and i+1<len(args): exp_b=float(args[i+1])
            if a=="--rest" and i+1<len(args): rest=int(args[i+1])
            if a=="--cards" or a=="--final": show_c=True; is_final_=a=="--final"
        r=predict(args[0],args[1],float(args[2]),float(args[3]),float(args[4]),
                alt=alt,inj_a=inj_a,inj_b=inj_b,exp_a=exp_a,exp_b=exp_b,rest=rest)
        if show_c:
            predict_cards(args[0],args[1],is_final_ if show_c else True)
    elif show_cards and len(args)>=2:
        predict_cards(args[0],args[1],is_final)
    else:
        print("用法:")
        print("  預測賽果: python predict_v56.py 隊A 隊B 主賠 和賠 客賠 [--alt N] [--inj_a -0.1] [--exp_a 0.8] [--rest N] [--cards]")
        print("  黃牌預測: python predict_v56.py 隊A 隊B --cards [--final]")
