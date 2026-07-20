import math

def poisson(l,k): return (l**k)*math.exp(-l)/math.factorial(k)

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

def alt_factor(am):
    if am<1500: return 1.0,1.0
    return 1.0+(am-1500)*0.003/100, max(1.0-(am-1500)*0.001/100,0.85)

def predict(ta,tb,oh,od,oa,alt=0):
    ih,id_,ia=1/oh,1/od,1/oa
    t=ih+id_+ia; ph,pd,pa=ih/t,id_/t,ia/t
    la=-math.log(1-ph-pd*0.4)*1.8
    lb=-math.log(1-pa-pd*0.4)*1.8
    for _ in range(5):
        wp=sum(poisson(la,i)*poisson(lb,j) for i in range(10) for j in range(10) if i>j)
        s=(ph/max(wp,0.001))**0.3; la*=s; lb/=s
    hf,af=alt_factor(alt); la*=hf; lb*=af
    scores=dc_correction(la,lb,0.08)
    wa=sum(p for i,j,p in scores if i>j)
    dr=sum(p for i,j,p in scores if i==j)
    wb=sum(p for i,j,p in scores if j>i)
    dr+=0.08; wa-=0.08*(wa/(wa+wb)); wb-=0.08*(wb/(wa+wb))
    et=dr*0.55
    et_wa=et*(wa/(wa+wb)*1.1)
    et_wb=et*(wb/(wa+wb)*0.9)
    pk=et-et_wa-et_wb
    adv_a=wa+et_wa+pk*0.5; adv_b=wb+et_wb+pk*0.5
    tg={}
    for g in range(9):
        p=sum(p for i,j,p in scores if i+j==g)
        if p>0.005: tg[g]=round(p*100,1)
    o25=sum(p for i,j,p in scores if i+j>2)
    o35=sum(p for i,j,p in scores if i+j>3)
    ts=sorted(scores,key=lambda x:-x[2])[:8]
    xg=round(la+lb,2)
    
    print("="*55)
    print(f"  V5+ 預測：{ta} vs {tb}  🏆 16強")
    if alt>0: print(f"  🏔️ 海拔: {alt}m")
    print("="*55)
    print(f"  📊 90分鐘: {ta} {wa*100:.0f}% / 和 {dr*100:.0f}% / {tb} {wb*100:.0f}%")
    print(f"  ⏱️ 加時: {et*100:.0f}% | 12碼: {max(pk,0)*100:.0f}%")
    print(f"  🎲 晉級: {ta} {adv_a*100:.0f}% / {tb} {adv_b*100:.0f}%")
    print(f"  ⚽ xG: {ta} {la:.2f} / {tb} {lb:.2f} (總{xg})")
    print()
    print(f"  ⚽ 總入球:")
    for g in range(7):
        if g in tg: print(f"    {g}球: {tg[g]}%")
    print(f"  📈 大2.5: {o25*100:.0f}% | 大3.5: {o35*100:.0f}%")
    print()
    print(f"  🎯 最可能比分:")
    for i,(g1,g2,p) in enumerate(ts[:5]):
        m="→" if i==0 else " "; print(f"    {m} {g1}-{g2} ({p*100:.1f}%)")
    mp=max(wa,dr,wb)*100
    l="🟢 高" if mp>=80 else ("🟡 中" if mp>=60 else "🔴 高風險")
    print(f"  🚦 信心: {l} ({mp:.0f}%)")
    print()

# Brazil vs Norway - Brazil strong favorite ~1.30/5.00/9.00
predict("巴西","挪威",1.30,5.00,9.00)
# Mexico vs England at Mexico City (2240m altitude)
predict("墨西哥","英格蘭",2.20,3.20,3.30,alt=2240)
