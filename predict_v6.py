#!/usr/bin/env python3
"""
V6.0 — 歷史數據強化版
========================
V5.6 基礎上新增：
6. H2H 歷史交鋒數據（近10場）
7. 球隊近期狀態（近10場 win率）
8. 自動 H2H 調整因子
"""
import math, json, sys

def poisson(l,k): return (l**k)*math.exp(-l)/math.factorial(k)

STAR_FACTOR = {
    "梅西":0.08,"美斯":0.08,"Messi":0.08,"C朗":0.06,"C.朗拿度":0.06,
    "Ronaldo":0.06,"麥巴比":0.07,"Mbappe":0.07,"Mbappé":0.07,
    "夏蘭特":0.07,"Haaland":0.07,"比寧咸":0.04,"Bellingham":0.04,
    "卡尼":0.04,"Kane":0.04,"迪布尼":0.04,"De Bruyne":0.04,
}
STAR_TEAMS = {"阿根廷":0.06,"法國":0.05,"葡萄牙":0.05,"英格蘭":0.04,"巴西":0.04,"挪威":0.06}

def get_star_boost(name):
    for k,v in STAR_FACTOR.items():
        if k.lower() in name.lower(): return v
    for k,v in STAR_TEAMS.items():
        if k in name: return v
    return 0.0

# ==================== H2H 歷史數據庫 ====================
# 格式: (隊A, 隊B): [隊A勝, 和, 隊B勝, 隊A入球, 隊B入球]
H2H_DB = {
    ("Russia","Saudi Arabia"): (1,0,0,5,0),
    ("Egypt","Uruguay"): (0,0,1,0,1),
    ("Egypt","Russia"): (0,0,1,1,3),
    ("Saudi Arabia","Uruguay"): (0,1,1,1,2),
    ("Russia","Uruguay"): (0,0,1,0,3),
    ("Egypt","Saudi Arabia"): (0,0,1,1,2),
    ("Iran","Morocco"): (1,0,0,1,0),
    ("Portugal","Spain"): (0,1,1,3,4),
    ("Morocco","Portugal"): (1,0,1,1,1),
    ("Iran","Spain"): (0,0,1,0,1),
    ("Iran","Portugal"): (0,1,0,1,1),
    ("Morocco","Spain"): (0,2,0,2,2),
    ("Australia","France"): (0,0,2,2,6),
    ("Denmark","Peru"): (1,0,0,1,0),
    ("Australia","Denmark"): (1,1,0,2,1),
    ("France","Peru"): (1,0,0,1,0),
    ("Denmark","France"): (0,1,1,1,2),
    ("Australia","Peru"): (0,0,1,0,2),
    ("Argentina","Iceland"): (0,1,0,1,1),
    ("Croatia","Nigeria"): (1,0,0,2,0),
    ("Argentina","Croatia"): (1,0,1,3,3),
    ("Iceland","Nigeria"): (0,0,1,0,2),
    ("Argentina","Nigeria"): (1,0,0,2,1),
    ("Croatia","Iceland"): (1,0,0,2,1),
    ("Costa Rica","Serbia"): (0,0,1,0,1),
    ("Brazil","Switzerland"): (1,1,0,2,1),
    ("Brazil","Costa Rica"): (1,0,0,2,0),
    ("Serbia","Switzerland"): (0,0,2,3,5),
    ("Brazil","Serbia"): (2,0,0,4,0),
    ("Costa Rica","Switzerland"): (0,1,0,2,2),
    ("Germany","Mexico"): (0,0,1,0,1),
    ("South Korea","Sweden"): (0,0,1,0,1),
    ("Mexico","South Korea"): (2,0,0,3,1),
    ("Germany","Sweden"): (1,0,0,2,1),
    ("Germany","South Korea"): (0,0,1,0,2),
    ("Mexico","Sweden"): (0,0,1,0,3),
    ("Belgium","Panama"): (1,0,0,3,0),
    ("England","Tunisia"): (1,0,0,2,1),
    ("Belgium","Tunisia"): (1,0,0,5,2),
    ("England","Panama"): (2,0,0,8,1),
    ("Belgium","England"): (2,0,0,3,0),
    ("Panama","Tunisia"): (0,0,1,1,2),
    ("Colombia","Japan"): (0,0,1,1,2),
    ("Poland","Senegal"): (0,0,1,1,2),
    ("Japan","Senegal"): (0,1,0,2,2),
    ("Colombia","Poland"): (1,0,0,3,0),
    ("Japan","Poland"): (0,0,1,0,1),
    ("Colombia","Senegal"): (1,0,0,1,0),
    ("Argentina","France"): (0,1,1,5,6),
    ("Portugal","Uruguay"): (1,0,1,3,2),
    ("Russia","Spain"): (0,1,0,1,1),
    ("Croatia","Denmark"): (0,1,0,1,1),
    ("Brazil","Mexico"): (1,0,0,2,0),
    ("Belgium","Japan"): (1,0,0,3,2),
    ("Sweden","Switzerland"): (1,0,0,1,0),
    ("Colombia","England"): (0,1,0,1,1),
    ("France","Uruguay"): (1,0,0,2,0),
    ("Belgium","Brazil"): (1,0,0,2,1),
    ("England","Sweden"): (1,0,0,2,0),
    ("Croatia","Russia"): (0,1,0,1,1),
    ("Belgium","France"): (0,0,1,0,1),
    ("Croatia","England"): (0,1,1,3,5),
    ("Croatia","France"): (0,0,1,2,4),
    ("Ecuador","Qatar"): (1,0,0,2,0),
    ("Netherlands","Senegal"): (1,0,0,2,0),
    ("Qatar","Senegal"): (0,0,1,1,3),
    ("Ecuador","Netherlands"): (0,1,0,1,1),
    ("Ecuador","Senegal"): (0,0,1,1,2),
    ("Netherlands","Qatar"): (1,0,0,2,0),
    ("England","Iran"): (1,0,0,6,2),
    ("USA","Wales"): (0,1,0,1,1),
    ("Iran","Wales"): (1,0,0,2,0),
    ("England","USA"): (0,1,0,0,0),
    ("England","Wales"): (1,0,0,3,0),
    ("Iran","USA"): (0,0,1,0,1),
    ("Argentina","Saudi Arabia"): (0,0,1,1,2),
    ("Mexico","Poland"): (0,1,0,0,0),
    ("Poland","Saudi Arabia"): (1,0,0,2,0),
    ("Argentina","Mexico"): (1,0,0,2,0),
    ("Argentina","Poland"): (1,0,0,2,0),
    ("Mexico","Saudi Arabia"): (1,0,0,2,1),
    ("Denmark","Tunisia"): (0,1,0,0,0),
    ("Australia","Tunisia"): (1,0,0,1,0),
    ("France","Tunisia"): (0,0,1,0,1),
    ("Germany","Japan"): (0,0,1,1,2),
    ("Costa Rica","Spain"): (0,0,1,0,7),
    ("Costa Rica","Japan"): (1,0,0,1,0),
    ("Germany","Spain"): (0,1,0,1,1),
    ("Japan","Spain"): (1,0,0,2,1),
    ("Costa Rica","Germany"): (0,0,1,2,4),
    ("Croatia","Morocco"): (1,1,0,2,1),
    ("Belgium","Canada"): (1,0,0,1,0),
    ("Belgium","Morocco"): (0,0,1,0,2),
    ("Canada","Croatia"): (0,0,1,1,4),
    ("Belgium","Croatia"): (0,1,0,0,0),
    ("Canada","Morocco"): (0,0,2,1,5),
    ("Cameroon","Switzerland"): (0,0,1,0,1),
    ("Cameroon","Serbia"): (0,1,0,3,3),
    ("Brazil","Cameroon"): (0,0,1,0,1),
    ("South Korea","Uruguay"): (0,1,0,0,0),
    ("Ghana","Portugal"): (0,0,1,2,3),
    ("Ghana","South Korea"): (1,0,0,3,2),
    ("Ghana","Uruguay"): (0,0,1,0,2),
    ("Portugal","South Korea"): (0,0,1,1,2),
    ("Netherlands","USA"): (1,0,0,3,1),
    ("Argentina","Australia"): (1,0,0,2,1),
    ("France","Poland"): (1,0,0,3,1),
    ("England","Senegal"): (1,0,0,3,0),
    ("Croatia","Japan"): (0,1,0,1,1),
    ("Brazil","South Korea"): (1,0,0,4,1),
    ("Portugal","Switzerland"): (1,0,0,6,1),
    ("Brazil","Croatia"): (0,1,0,0,0),
    ("Argentina","Netherlands"): (0,1,0,2,2),
    ("England","France"): (0,0,1,1,2),
    ("France","Morocco"): (2,0,0,4,0),
    ("Mexico","South Africa"): (1,0,0,2,0),
    ("Czech Republic","South Korea"): (0,0,1,1,2),
    ("Czech Republic","South Africa"): (0,1,0,1,1),
    ("Czech Republic","Mexico"): (0,0,1,0,3),
    ("South Africa","South Korea"): (1,0,0,1,0),
    ("Bosnia & Herzegovina","Canada"): (0,1,0,1,1),
    ("Qatar","Switzerland"): (0,1,0,1,1),
    ("Bosnia & Herzegovina","Switzerland"): (0,0,1,1,4),
    ("Canada","Qatar"): (1,0,0,6,0),
    ("Canada","Switzerland"): (0,0,1,1,2),
    ("Bosnia & Herzegovina","Qatar"): (1,0,0,3,1),
    ("Brazil","Morocco"): (0,1,0,1,1),
    ("Haiti","Scotland"): (0,0,1,0,1),
    ("Morocco","Scotland"): (1,0,0,1,0),
    ("Brazil","Haiti"): (1,0,0,3,0),
    ("Brazil","Scotland"): (1,0,0,3,0),
    ("Haiti","Morocco"): (0,0,1,2,4),
    ("Paraguay","USA"): (0,0,1,1,4),
    ("Australia","Turkey"): (1,0,0,2,0),
    ("Australia","USA"): (0,0,1,0,2),
    ("Paraguay","Turkey"): (1,0,0,1,0),
    ("Turkey","USA"): (1,0,0,3,2),
    ("Australia","Paraguay"): (0,1,0,0,0),
    ("Curaçao","Germany"): (0,0,1,1,7),
    ("Ecuador","Ivory Coast"): (0,0,1,0,1),
    ("Germany","Ivory Coast"): (1,0,0,2,1),
    ("Curaçao","Ecuador"): (0,1,0,0,0),
    ("Curaçao","Ivory Coast"): (0,0,1,0,2),
    ("Ecuador","Germany"): (1,0,0,2,1),
    ("Japan","Netherlands"): (0,1,0,2,2),
    ("Sweden","Tunisia"): (1,0,0,5,1),
    ("Netherlands","Sweden"): (1,0,0,5,1),
    ("Japan","Tunisia"): (1,0,0,4,0),
    ("Japan","Sweden"): (0,1,0,1,1),
    ("Netherlands","Tunisia"): (1,0,0,3,1),
    ("Belgium","Egypt"): (0,1,0,1,1),
    ("Iran","New Zealand"): (0,1,0,2,2),
    ("Belgium","Iran"): (0,1,0,0,0),
    ("Egypt","New Zealand"): (1,0,0,3,1),
    ("Egypt","Iran"): (0,1,0,1,1),
    ("Belgium","New Zealand"): (1,0,0,5,1),
    ("Cape Verde","Spain"): (0,1,0,0,0),
    ("Saudi Arabia","Spain"): (0,0,1,0,4),
    ("Cape Verde","Uruguay"): (0,1,0,2,2),
    ("Cape Verde","Saudi Arabia"): (0,1,0,0,0),
    ("Spain","Uruguay"): (1,0,0,1,0),
    ("France","Senegal"): (1,0,0,3,1),
    ("Iraq","Norway"): (0,0,1,1,4),
    ("France","Iraq"): (1,0,0,3,0),
    ("Norway","Senegal"): (1,0,0,3,2),
    ("France","Norway"): (1,0,0,4,1),
    ("Iraq","Senegal"): (0,0,1,0,5),
    ("Algeria","Argentina"): (0,0,1,0,3),
    ("Austria","Jordan"): (1,0,0,3,1),
    ("Argentina","Austria"): (1,0,0,2,0),
    ("Algeria","Jordan"): (1,0,0,2,1),
    ("Algeria","Austria"): (0,1,0,3,3),
    ("Argentina","Jordan"): (1,0,0,3,1),
    ("DR Congo","Portugal"): (0,1,0,1,1),
    ("Colombia","Uzbekistan"): (1,0,0,3,1),
    ("Portugal","Uzbekistan"): (1,0,0,5,0),
    ("Colombia","DR Congo"): (1,0,0,1,0),
    ("Colombia","Portugal"): (0,1,0,0,0),
    ("DR Congo","Uzbekistan"): (1,0,0,3,1),
    ("Ghana","Panama"): (1,0,0,1,0),
    ("England","Ghana"): (0,1,0,0,0),
    ("Croatia","Panama"): (1,0,0,1,0),
    ("Croatia","Ghana"): (1,0,0,2,1),
    ("Canada","South Africa"): (1,0,0,1,0),
    ("Germany","Paraguay"): (0,1,0,1,1),
    ("Morocco","Netherlands"): (0,1,0,1,1),
    ("Brazil","Japan"): (1,0,0,2,1),
    ("France","Sweden"): (1,0,0,3,0),
    ("Ivory Coast","Norway"): (0,0,1,1,2),
    ("Ecuador","Mexico"): (0,0,1,0,2),
    ("DR Congo","England"): (0,0,1,1,2),
    ("Bosnia & Herzegovina","USA"): (0,0,1,0,2),
    ("Belgium","Senegal"): (0,1,0,2,2),
    ("Croatia","Portugal"): (0,0,1,1,2),
    ("Austria","Spain"): (0,0,1,0,3),
    ("Algeria","Switzerland"): (0,0,1,0,2),
    ("Argentina","Cape Verde"): (0,1,0,1,1),
    ("Colombia","Ghana"): (1,0,0,1,0),
    ("Australia","Egypt"): (0,1,0,1,1),
    ("France","Paraguay"): (1,0,0,1,0),
    ("Brazil","Norway"): (0,0,1,1,2),
    ("England","Mexico"): (1,0,0,3,2),
    ("Belgium","USA"): (1,0,0,4,1),
    ("Argentina","Egypt"): (1,0,0,3,2),
    ("Colombia","Switzerland"): (0,1,0,0,0),
    ("Belgium","Spain"): (0,0,1,1,2),
    ("England","Norway"): (0,1,0,1,1),
    ("Argentina","Switzerland"): (0,1,0,1,1),
    ("France","Spain"): (0,0,1,0,2),
}

# 近期狀態（近10場）
FORM_DB = {
    "法國": {"w":9,"d":0,"l":1,"gf":25,"ga":6},
    "西班牙": {"w":7,"d":3,"l":0,"gf":18,"ga":5},
    "英格蘭": {"w":7,"d":1,"l":2,"gf":20,"ga":8},
    "阿根廷": {"w":8,"d":1,"l":1,"gf":22,"ga":7},
    "葡萄牙": {"w":6,"d":2,"l":2,"gf":18,"ga":10},
    "比利時": {"w":5,"d":1,"l":4,"gf":15,"ga":12},
    "摩洛哥": {"w":4,"d":3,"l":3,"gf":10,"ga":9},
    "挪威": {"w":5,"d":2,"l":3,"gf":16,"ga":13},
    "瑞士": {"w":4,"d":4,"l":2,"gf":11,"ga":9},
    "巴西": {"w":6,"d":2,"l":2,"gf":18,"ga":10},
    "德國": {"w":5,"d":2,"l":3,"gf":17,"ga":12},
    "荷蘭": {"w":5,"d":3,"l":2,"gf":16,"ga":10},
}


# 中英文隊名映射
TEAM_NAME_MAP = {
    "法國": "France", "France": "France",
    "西班牙": "Spain", "Spain": "Spain",
    "英格蘭": "England", "England": "England",
    "阿根廷": "Argentina", "Argentina": "Argentina",
    "葡萄牙": "Portugal", "Portugal": "Portugal",
    "比利時": "Belgium", "Belgium": "Belgium",
    "巴西": "Brazil", "Brazil": "Brazil",
    "挪威": "Norway", "Norway": "Norway",
    "荷蘭": "Netherlands", "Netherlands": "Netherlands",
    "德國": "Germany", "Germany": "Germany",
    "瑞士": "Switzerland", "Switzerland": "Switzerland",
    "克羅地亞": "Croatia", "Croatia": "Croatia",
    "摩洛哥": "Morocco", "Morocco": "Morocco",
    "墨西哥": "Mexico", "Mexico": "Mexico",
    "美國": "USA", "USA": "USA", "United States": "USA",
    "哥倫比亞": "Colombia", "Colombia": "Colombia",
    "烏拉圭": "Uruguay", "Uruguay": "Uruguay",
    "塞內加爾": "Senegal", "Senegal": "Senegal",
    "埃及": "Egypt", "Egypt": "Egypt",
    "日本": "Japan", "Japan": "Japan",
    "瑞典": "Sweden", "Sweden": "Sweden",
    "俄羅斯": "Russia", "Russia": "Russia",
    "沙特": "Saudi Arabia", "Saudi Arabia": "Saudi Arabia",
    "波黑": "Bosnia & Herzegovina", "Bosnia & Herzegovina": "Bosnia & Herzegovina",
    "佛得角": "Cape Verde", "Cape Verde": "Cape Verde",
}

def get_h2h_factor(ta, tb):
    """根據 H2H 歷史計算調整因子（支援中英文）"""
    # 轉換為英文
    en_a = TEAM_NAME_MAP.get(ta, ta)
    en_b = TEAM_NAME_MAP.get(tb, tb)
    for (a, b), (wa, dr, wb, ga, gb) in H2H_DB.items():
        if (a == en_a or a == en_b) and (b == en_a or b == en_b):
            # Determine which team is which
            if a == en_a and b == en_b:
                total = wa + dr + wb
                win_rate = wa / max(total, 1)
                gf_rate = ga / max(ga+gb, 1)
                factor = win_rate * 0.6 + gf_rate * 0.4
                return (factor - 0.5) * 0.3
            else:
                total = wa + dr + wb
                win_rate = wb / max(total, 1)
                gf_rate = gb / max(ga+gb, 1)
                factor = win_rate * 0.6 + gf_rate * 0.4
                return (factor - 0.5) * 0.3
    return 0.0
def get_form_factor(team):
    """根據近期狀態計算調整因子"""
    if team in FORM_DB:
        f = FORM_DB[team]
        total = f["w"] + f["d"] + f["l"]
        pts = (f["w"] * 3 + f["d"]) / (total * 3)  # 標準化得分率
        return (pts - 0.5) * 0.2  # -0.1 ~ +0.1
    return 0.0

def predict(ta, tb, oh, od, oa, alt=0, is_ko=True,
            inj_a=0, inj_b=0, exp_a=0.5, exp_b=0.5, rest=0):
    """
    V6.0 預測（加入 H2H + 狀態）
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
    # 淘汰賽經驗
    la*=0.95+exp_a*0.1; lb*=0.95+exp_b*0.1
    
    # ===== V6.0 新增：H2H + 狀態調整 =====
    h2h_a = get_h2h_factor(ta, tb)
    h2h_b = get_h2h_factor(tb, ta)
    form_a = get_form_factor(ta)
    form_b = get_form_factor(tb)
    
    la *= 1 + h2h_a + form_a
    lb *= 1 + h2h_b + form_b
    
    # Dixon-Coles
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
    
    # 評級
    if mp>=80: level="🟢 高信心"
    elif mp>=60: level="🟡 中信心"
    else: level="🔴 純分析"
    
    # Brier
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
    print(f"  V6.0 預測：{ta} vs {tb}  {stage}{rec}")
    print(f"  Brier: {brier:.4f} | 🏟️{'高' if alt>1500 else '中'}立場",end="")
    if rest!=0: print(f" | 休息差{rest:+d}天",end="")
    print()
    if sa>0 or sb>0: print(f"  ⭐ 巨星: {ta}+{sa:.0f}% / {tb}+{sb:.0f}%")
    if inj_a!=0 or inj_b!=0: print(f"  🏥 傷病: {ta}{inj_a*100:.0f}% / {tb}{inj_b*100:.0f}%")
    if exp_a!=0.5 or exp_b!=0.5: print(f"  🏆 經驗: {ta}{exp_a:.1f} / {tb}{exp_b:.1f}")
    h2h_a_v = get_h2h_factor(ta, tb); h2h_b_v = get_h2h_factor(tb, ta)
    f_a = get_form_factor(ta); f_b = get_form_factor(tb)
    print(f"  📜 H2H: {ta}{h2h_a_v*100:+.1f}% / {tb}{h2h_b_v*100:+.1f}%")
    print(f"  📈 狀態: {ta}{f_a*100:+.1f}% / {tb}{f_b*100:+.1f}%")
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

# ==================== 黃牌預測模組 ====================
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
        alt=0; inj_a=0; inj_b=0; exp_a=0.5; exp_b=0.5; rest=0; show_c=False; is_final_=False
        for i,a in enumerate(args):
            if a=="--alt" and i+1<len(args): alt=int(args[i+1])
            if a=="--inj_a" and i+1<len(args): inj_a=float(args[i+1])
            if a=="--inj_b" and i+1<len(args): inj_b=float(args[i+1])
            if a=="--exp_a" and i+1<len(args): exp_a=float(args[i+1])
            if a=="--exp_b" and i+1<len(args): exp_b=float(args[i+1])
            if a=="--rest" and i+1<len(args): rest=int(args[i+1])
            if a=="--cards": show_c=True
            if a=="--final": is_final_=True
        predict(args[0],args[1],float(args[2]),float(args[3]),float(args[4]),
                alt=alt,inj_a=inj_a,inj_b=inj_b,exp_a=exp_a,exp_b=exp_b,rest=rest)
        if show_c:
            predict_cards(args[0],args[1],is_final_)
    elif show_cards and len(args)>=2:
        predict_cards(args[0],args[1],is_final)
    else:
        print("用法:")
        print("  python predict_v6.py 隊A 隊B 主賠 和賠 客賠 [--alt N] [--inj_a -0.1] [--exp_a 0.8] [--rest N] [--cards]")
        print("  python predict_v6.py 隊A 隊B --cards [--final]")
