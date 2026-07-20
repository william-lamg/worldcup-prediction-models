#!/usr/bin/env python3
"""
V7.0 — 戰後重建版
===================
基於 V6.1 完整覆盤的 5 大改進：
1. 決賽/壓力調整：防守型球隊 +8% 優勢
2. 防守體系因子：失球率極低球隊自動加成
3. 季軍戰獨立模型：開放比賽 → 大球傾向
4. Elo 回溯至 2010 世界盃
5. 獨立於市場賠率嘅判斷權重

數據源：openfootball/world-cup.json（Public Domain）
"""
import math, json, sys, os, random, urllib.request

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master"
H2H_PATH = os.path.join(DATA_DIR, "h2h_database.json")
ELO_INIT = 1500
K_ELO = 32

def poisson(l,k): return (l**k)*math.exp(-l)/math.factorial(k)

# ========== 隊名映射 ==========
TEAM_NAME_MAP = {
    "法國":"France","France":"France","西班牙":"Spain","Spain":"Spain",
    "英格蘭":"England","England":"England","阿根廷":"Argentina","Argentina":"Argentina",
    "葡萄牙":"Portugal","Portugal":"Portugal","比利時":"Belgium","Belgium":"Belgium",
    "巴西":"Brazil","Brazil":"Brazil","挪威":"Norway","Norway":"Norway",
    "荷蘭":"Netherlands","Netherlands":"Netherlands","德國":"Germany","Germany":"Germany",
    "瑞士":"Switzerland","Switzerland":"Switzerland","克羅地亞":"Croatia","Croatia":"Croatia",
    "摩洛哥":"Morocco","Morocco":"Morocco","墨西哥":"Mexico","Mexico":"Mexico",
    "美國":"USA","USA":"USA","United States":"USA","哥倫比亞":"Colombia","Colombia":"Colombia",
    "烏拉圭":"Uruguay","Uruguay":"Uruguay","塞內加爾":"Senegal","Senegal":"Senegal",
    "埃及":"Egypt","Egypt":"Egypt","日本":"Japan","Japan":"Japan",
    "瑞典":"Sweden","Sweden":"Sweden","丹麥":"Denmark","Denmark":"Denmark",
}
def to_en(name): return TEAM_NAME_MAP.get(name, name)

# ========== 巨星指數 ==========
STAR = {"梅西":0.08,"美斯":0.08,"C朗":0.06,"C.朗拿度":0.06,"麥巴比":0.07,"Mbappe":0.07,
        "Haaland":0.07}
STAR_TEAM = {"阿根廷":0.06,"法國":0.05,"葡萄牙":0.05,"英格蘭":0.04,"巴西":0.04,"挪威":0.06}
def star(team):
    for k,v in STAR.items():
        if k.lower() in team.lower(): return v
    for k,v in STAR_TEAM.items():
        if k in team: return v
    return 0.0

# ========== H2H 加載 ==========
H2H = {}
if os.path.exists(H2H_PATH):
    with open(H2H_PATH,"r",encoding="utf-8") as f:
        for k,s in json.load(f).items():
            H2H[(s["team_a"],s["team_b"])] = (s["wins_a"],s["draws"],s["wins_b"],s["goals_a"],s["goals_b"])

def h2h_factor(ta,tb):
    ea,eb=to_en(ta),to_en(tb)
    for (a,b),(wa,dr,wb,ga,gb) in H2H.items():
        if (a==ea and b==eb) or (a==eb and b==ea):
            if a==ea: wr=wa/max(wa+dr+wb,1); gr=ga/max(ga+gb,1)
            else: wr=wb/max(wa+dr+wb,1); gr=gb/max(ga+gb,1)
            return (wr*0.6+gr*0.4-0.5)*0.3
    return 0.0

# ========== 🆕 V7.0: Elo 回溯至 2010 ==========
class EloV7:
    def __init__(self):
        self.r = {}
        for y in [2010,2014,2018,2022]:
            self._load(y)
    
    def _load(self,year):
        try:
            url = f"{BASE_URL}/{year}/worldcup.json"
            data = json.loads(urllib.request.urlopen(
                urllib.request.Request(url),timeout=5).read().decode())
            matches = data.get("matches",[])
            matches.sort(key=lambda m: m.get("date",""))
            for m in matches:
                t1=m.get("team1",""); t2=m.get("team2","")
                if isinstance(t1,dict): t1=t1.get("name","")
                if isinstance(t2,dict): t2=t2.get("name","")
                ft=m.get("score",{}).get("ft",[None,None])
                if ft[0] is None: continue
                s1,s2=int(ft[0]),int(ft[1])
                if t1 not in self.r: self.r[t1]=ELO_INIT
                if t2 not in self.r: self.r[t2]=ELO_INIT
                r1,r2=self.r[t1],self.r[t2]
                e1=1/(1+10**((r2-r1)/400)); e2=1-e1
                a1,a2 = (1,0) if s1>s2 else ((0,1) if s1<s2 else (0.5,0.5))
                gd=min(abs(s1-s2),3) if s1!=s2 else 1
                k=K_ELO*gd
                self.r[t1]+=k*(a1-e1)
                self.r[t2]+=k*(a2-e2)
        except: pass
    
    def get(self,team):
        en=to_en(team)
        if en in self.r: return self.r[en]
        for k in self.r:
            if team.lower() in k.lower() or k.lower() in team.lower():
                return self.r[k]
        return ELO_INIT
    
    def predict(self,ta,tb):
        ra,rb=self.get(ta),self.get(tb)
        ea=1/(1+10**((rb-ra)/400)); eb=1-ea
        diff=abs(ra-rb)
        dp=max(0.15,0.30-diff/2000)
        return {"wa":ea*(1-dp),"dr":dp,"wb":eb*(1-dp),"elo_a":round(ra),"elo_b":round(rb)}
    
    def ranking(self):
        return sorted(self.r.items(),key=lambda x:-x[1])

# ========== 蒙特卡洛 ==========
class MonteCarloV7:
    def __init__(self,elo): self.elo=elo
    def sim(self,ta,tb,n=10000):
        ra,rb=self.elo.get(ta),self.elo.get(tb)
        diff=(ra-rb)/400
        la=max(1.2*(1+diff*0.3),0.3); lb=max(1.2*(1-diff*0.3),0.3)
        w=d=0
        for _ in range(n):
            g1=sum(1 for _ in range(10) if random.random()<la/10)
            g2=sum(1 for _ in range(10) if random.random()<lb/10)
            if g1>g2: w+=1
            elif g1<g2: pass
            else: d+=1
        return {"wa":w/n,"dr":d/n,"wb":1-(w+d)/n,"xg_a":round(la,2),"xg_b":round(lb,2)}

# ========== 🆕 V7.0: 防守體系因子 ==========
DEFENSIVE_TEAMS = {
    "西班牙": 0.07, "Spain": 0.07,  # 7場僅失1球
    "摩洛哥": 0.04, "Morocco": 0.04,
    "克羅地亞": 0.03, "Croatia": 0.03,
    "瑞士": 0.03, "Switzerland": 0.03,
}

def defensive_factor(team):
    for k,v in DEFENSIVE_TEAMS.items():
        if team.lower() in k.lower() or k.lower() in team.lower():
            return v
    return 0.0

# ========== 🆕 V7.0: 決賽壓力調整 ==========
def pressure_adjustment(is_final, is_third_place=False):
    """
    決賽：防守型球隊 +8% xG 優勢（壓力下防守更穩定）
    季軍戰：雙方 +15% xG（開放式大球賽）
    """
    if is_third_place:
        return 0.15, 0.15  # 雙方進攻加成
    elif is_final:
        return 0.0, 0.0    # 防守加成在外層處理
    return 0.0, 0.0

# ========== 市場賠率引擎（V7 增強版）==========
def market_v7(ta,tb,oh,od,oa,alt,is_ko,inj_a,inj_b,exp_a,exp_b,rest,
              is_final=False, is_third=False):
    ih,id_,ia=1/oh,1/od,1/oa
    t=ih+id_+ia; ph,pd,pa=ih/t,id_/t,ia/t
    la=-math.log(1-ph-pd*0.4)*1.8
    lb=-math.log(1-pa-pd*0.4)*1.8
    for _ in range(5):
        wp=sum(poisson(la,i)*poisson(lb,j) for i in range(10) for j in range(10) if i>j)
        s=(ph/max(wp,0.001))**0.3; la*=s; lb/=s
    
    # 巨星
    la*=1+star(ta); lb*=1+star(tb)
    # 海拔
    if alt>=1500:
        la*=1+(alt-1500)*0.0015/100; lb*=max(1-(alt-1500)*0.0005/100,0.92)
    # 傷病
    la*=1+inj_a; lb*=1+inj_b
    # 休息
    if rest>0: la*=1+rest*0.02
    elif rest<0: lb*=1+abs(rest)*0.02
    # 經驗
    la*=0.95+exp_a*0.1; lb*=0.95+exp_b*0.1
    # H2H
    la*=1+h2h_factor(ta,tb); lb*=1+h2h_factor(tb,ta)
    
    # 🆕 V7: 防守體系
    la*=1+defensive_factor(ta); lb*=1+defensive_factor(tb)
    
    # 🆕 V7: 決賽壓力
    if is_final:
        def_a = defensive_factor(ta)
        def_b = defensive_factor(tb)
        if def_a > def_b:
            la *= 1 + 0.08  # 防守更強一方在決賽中獲得優勢
        elif def_b > def_a:
            lb *= 1 + 0.08
    
    # 🆕 V7: 季軍戰開放模式
    if is_third:
        boost = 0.15
        la *= 1 + boost
        lb *= 1 + boost
    
    def dc(la,lb,rho=0.05):
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
    
    scores=dc(la,lb,0.08)
    wa=sum(p for i,j,p in scores if i>j)
    dr=sum(p for i,j,p in scores if i==j)
    wb=sum(p for i,j,p in scores if j>i)
    dr+=0.08; wa-=0.08*(wa/(wa+wb)); wb-=0.08*(wb/(wa+wb))
    if wa>wb: wa-=0.03; wb+=0.03
    elif wb>wa: wb-=0.03; wa+=0.03
    return {"wa":wa,"dr":dr,"wb":wb,"la":la,"lb":lb}

# ========== 🆕 V7.0 集成引擎 ==========
class EngineV7:
    def __init__(self):
        self.elo = EloV7()
        self.mc = MonteCarloV7(self.elo)
    
    def predict(self,ta,tb,oh,od,oa,alt=0,is_ko=True,
                inj_a=0,inj_b=0,exp_a=0.5,exp_b=0.5,rest=0,
                is_final=False,is_third=False):
        
        m = market_v7(ta,tb,oh,od,oa,alt,is_ko,inj_a,inj_b,exp_a,exp_b,rest,
                       is_final,is_third)
        e = self.elo.predict(ta,tb)
        mc = self.mc.sim(ta,tb)
        
        # 🆕 V7: 獨立權重（市場賠率降權）
        if is_final or is_third:
            w = {"market":0.35,"elo":0.35,"mc":0.30}  # 減少市場依賴
        else:
            w = {"market":0.50,"elo":0.25,"mc":0.25}
        
        wa = m["wa"]*w["market"]+e["wa"]*w["elo"]+mc["wa"]*w["mc"]
        dr = m["dr"]*w["market"]+e["dr"]*w["elo"]+mc["dr"]*w["mc"]
        wb = m["wb"]*w["market"]+e["wb"]*w["elo"]+mc["wb"]*w["mc"]
        
        if is_ko:
            dr+=0.04; wa-=0.02; wb-=0.02
        
        t=wa+dr+wb; wa/=t; dr/=t; wb/=t
        
        return {
            "ensemble":{"wa":round(wa*100,1),"dr":round(dr*100,1),"wb":round(wb*100,1)},
            "market":{"wa":round(m["wa"]*100,1),"dr":round(m["dr"]*100,1),"wb":round(m["wb"]*100,1)},
            "elo":{"wa":round(e["wa"]*100,1),"dr":round(e["dr"]*100,1),"wb":round(e["wb"]*100,1),
                    "elo_a":e["elo_a"],"elo_b":e["elo_b"]},
            "mc":{"wa":round(mc["wa"]*100,1),"dr":round(mc["dr"]*100,1),"wb":round(mc["wb"]*100,1)},
        }

# ========== 顯示 ==========
def print_v7(r,ta,tb,is_final=False,is_third=False):
    stage = "🏆 決賽" if is_final else ("🥉 季軍戰" if is_third else "🏆 淘汰賽")
    ens = r["ensemble"]
    mp = max(ens["wa"],ens["dr"],ens["wb"])
    level = "🟢 高信心 ✅" if mp>=80 else ("🟡 中信心 ℹ️" if mp>=60 else "🔴 純分析")
    
    print("="*60)
    print(f"  V7.0 預測：{ta} vs {tb}  {stage}")
    print(f"  {level} | 市場權重："+("35%" if is_final or is_third else "50%"))
    print("="*60)
    
    print(f"\n  📊 集成：{ta} {ens['wa']}% ／ 和 {ens['dr']}% ／ {tb} {ens['wb']}%")
    
    print(f"\n  🔍 三引擎：")
    print(f"    {'':10} {'市場':>8} {'Elo':>8} {'MC':>8}")
    print(f"    {ta:<6}勝 {r['market']['wa']:>6.1f}% {r['elo']['wa']:>6.1f}% {r['mc']['wa']:>6.1f}%")
    print(f"    {'和波':>6} {r['market']['dr']:>6.1f}% {r['elo']['dr']:>6.1f}% {r['mc']['dr']:>6.1f}%")
    print(f"    {tb:<6}勝 {r['market']['wb']:>6.1f}% {r['elo']['wb']:>6.1f}% {r['mc']['wb']:>6.1f}%")
    
    if "elo_a" in r["elo"]:
        print(f"\n  ⭐ Elo：{ta} {r['elo']['elo_a']} / {tb} {r['elo']['elo_b']}")
    
    # V7 特色標記
    if is_final:
        print(f"  🛡️ 決賽模式：防守體系加成 + 市場權重降為 35%")
    if is_third:
        print(f"  ⚡ 季軍戰模式：開放進攻 + 市場權重降為 35%")
    print()

if __name__=="__main__":
    args=sys.argv[1:]
    if len(args)>=5:
        engine=EngineV7()
        ta,tb=args[0],args[1]
        oh,od,oa=float(args[2]),float(args[3]),float(args[4])
        alt=0; inj_a=0; inj_b=0; exp_a=0.5; exp_b=0.5; rest=0
        is_final=False; is_third=False
        for i,a in enumerate(args):
            if a=="--alt" and i+1<len(args): alt=int(args[i+1])
            if a=="--inj_a" and i+1<len(args): inj_a=float(args[i+1])
            if a=="--inj_b" and i+1<len(args): inj_b=float(args[i+1])
            if a=="--exp_a" and i+1<len(args): exp_a=float(args[i+1])
            if a=="--exp_b" and i+1<len(args): exp_b=float(args[i+1])
            if a=="--rest" and i+1<len(args): rest=int(args[i+1])
            if a=="--final": is_final=True
            if a=="--third": is_third=True
        r=engine.predict(ta,tb,oh,od,oa,alt,True,inj_a,inj_b,exp_a,exp_b,rest,
                         is_final,is_third)
        print_v7(r,ta,tb,is_final,is_third)
    else:
        print("V7.0 用法:")
        print("  python predict_v7.py 隊A 隊B 主賠 和賠 客賠 [--final] [--third] [--inj_a -0.1] [--exp_a 0.8]")
        print("  python predict_v7.py elo    ← Elo 排行榜")
        print("\n🆕 V7.0 新功能：")
        print("  --final  決賽壓力模式（防守加成+降市場權重）")
        print("  --third  季軍戰開放模式（進攻加成+降市場權重）")
        print("  Elo 數據回溯至 2010 世界盃")
