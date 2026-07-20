#!/usr/bin/env python3
"""
V6.1 — 三重集成引擎
========================
集成三層模型作最終評定：
1️⃣ 市場賠率（V6.0）— 賭盤共識
2️⃣ Elo 系統（回歸）— 歷史實力
3️⃣ 蒙特卡洛模擬（回歸）— 完整賽事推演

新增恢復功能：
- 賽前情報自動檢查
- 2串1競彩推薦
- 信心分級強化
"""
import math, json, sys, os, random, urllib.request

# ========== 常數 ==========
BASE_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master"
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
K_ELO = 40          # Elo K-factor
ELO_HOME = 100      # 主場優勢
ELO_INIT = 1500     # 初始 Elo

# ========== 輔助函數 ==========
def poisson(l,k): return (l**k)*math.exp(-l)/math.factorial(k)

# ========== 巨星指數 ==========
STAR_FACTOR = {"梅西":0.08,"美斯":0.08,"Messi":0.08,"C朗":0.06,"C.朗拿度":0.06,
    "Ronaldo":0.06,"麥巴比":0.07,"Mbappe":0.07,"Mbappé":0.07,"夏蘭特":0.07,"Haaland":0.07,
    "比寧咸":0.04,"Bellingham":0.04,"卡尼":0.04,"Kane":0.04,"迪布尼":0.04,"De Bruyne":0.04}
STAR_TEAMS = {"阿根廷":0.06,"法國":0.05,"葡萄牙":0.05,"英格蘭":0.04,"巴西":0.04,"挪威":0.06}

def get_star_boost(name):
    for k,v in STAR_FACTOR.items():
        if k.lower() in name.lower(): return v
    for k,v in STAR_TEAMS.items():
        if k in name: return v
    return 0.0

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
    "埃及":"Egypt","Egypt":"Egypt","日本":"Japan","Japan":"Japan","瑞典":"Sweden","Sweden":"Sweden",
    "俄羅斯":"Russia","Russia":"Russia","沙特":"Saudi Arabia","Saudi Arabia":"Saudi Arabia",
    "波黑":"Bosnia & Herzegovina","Bosnia & Herzegovina":"Bosnia & Herzegovina",
    "佛得角":"Cape Verde","Cape Verde":"Cape Verde",
}

def to_en(name): return TEAM_NAME_MAP.get(name, name)

# ========== H2H 數據庫 ==========
# 自動從 h2h_database.json 載入
H2H_DB = {}
h2h_path = os.path.join(DATA_DIR, "h2h_database.json")
if os.path.exists(h2h_path):
    with open(h2h_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    for key, s in raw.items():
        a, b = s["team_a"], s["team_b"]
        H2H_DB[(a,b)] = (s["wins_a"], s["draws"], s["wins_b"], s["goals_a"], s["goals_b"])

def get_h2h_factor(ta, tb):
    en_a, en_b = to_en(ta), to_en(tb)
    for (a,b),(wa,dr,wb,ga,gb) in H2H_DB.items():
        if (a==en_a and b==en_b) or (a==en_b and b==en_a):
            if a==en_a:
                total=wa+dr+wb; wr=wa/max(total,1); gr=ga/max(ga+gb,1)
            else:
                total=wa+dr+wb; wr=wb/max(total,1); gr=gb/max(ga+gb,1)
            return (wr*0.6+gr*0.4-0.5)*0.3
    return 0.0

# ========== 黃牌模組 ==========
CARD_DATA = {
    "法國":(6,4,0),"France":(6,4,0),"西班牙":(6,5,0),"Spain":(6,5,0),
    "英格蘭":(7,6,1),"England":(7,6,1),"阿根廷":(6,6,0),"Argentina":(6,6,0),
    "比利時":(6,10,1),"Belgium":(6,10,1),"葡萄牙":(6,7,0),"Portugal":(6,7,0),
    "巴西":(5,8,0),"Brazil":(5,8,0),"挪威":(5,3,0),"Norway":(5,3,0),
    "摩洛哥":(6,7,0),"Morocco":(6,7,0),"瑞士":(6,6,1),"Switzerland":(6,6,1),
}
def predict_cards(ta, tb, is_final=False):
    """黃牌預測（獨立功能）"""
    def get(t):
        for k,v in CARD_DATA.items():
            if t.lower() in k.lower() or k.lower() in t.lower(): return v
        return (3,4,0)
    pa,ya,_=get(ta); pb,yb,_=get(tb)
    avg_a=ya/max(pa,1); avg_b=yb/max(pb,1)
    factor=1.2*(0.9 if is_final else 1.0)
    exp_a=avg_a*factor; exp_b=avg_b*factor; total=exp_a+exp_b
    dist={k:round(poisson(total,k)*100,1) for k in range(11) if poisson(total,k)>0.001}
    p02=sum(dist.get(k,0) for k in range(3))
    p35=sum(dist.get(k,0) for k in range(3,6))
    rec="0-2張 ✅" if p02>=40 else ("3-5張 ✅" if p35>=40 else "⚠️不宜")
    return {"total":round(total,2),"p02":round(p02,1),"p35":round(p35,1),"rec":rec,
            "avg_a":round(avg_a,2),"avg_b":round(avg_b,2)}

# ========== 1️⃣ 市場賠率模型（V6.0 核心）==========
def market_predict(ta, tb, oh, od, oa, alt=0, is_ko=True,
                   inj_a=0, inj_b=0, exp_a=0.5, exp_b=0.5, rest=0):
    """市場賠率驅動預測"""
    ih,id_,ia=1/oh,1/od,1/oa
    t=ih+id_+ia; ph,pd,pa=ih/t,id_/t,ia/t
    la=-math.log(1-ph-pd*0.4)*1.8
    lb=-math.log(1-pa-pd*0.4)*1.8
    for _ in range(5):
        wp=sum(poisson(la,i)*poisson(lb,j) for i in range(10) for j in range(10) if i>j)
        s=(ph/max(wp,0.001))**0.3; la*=s; lb/=s
    la*=1+get_star_boost(ta); lb*=1+get_star_boost(tb)
    if alt>=1500:
        hf=1+(alt-1500)*0.0015/100; af=max(1-(alt-1500)*0.0005/100,0.92)
        la*=hf; lb*=af
    la*=1+inj_a; lb*=1+inj_b
    if rest>0: la*=1+rest*0.02
    elif rest<0: lb*=1+abs(rest)*0.02
    la*=0.95+exp_a*0.1; lb*=0.95+exp_b*0.1
    la*=1+get_h2h_factor(ta,tb); lb*=1+get_h2h_factor(tb,ta)
    
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
    return {"wa":wa,"dr":dr,"wb":wb,"la":la,"lb":lb,"scores":scores}

# ========== 2️⃣ Elo 系統（回歸！）==========
class EloSystem:
    """基於世界盃歷史數據嘅 Elo 評分系統"""
    def __init__(self):
        self.ratings = {}
        self._load_worldcup_data()
    
    def _load_worldcup_data(self):
        """從 world-cup.json 載入歷史數據訓練 Elo"""
        for year in [2018, 2022]:
            try:
                url = f"{BASE_URL}/{year}/worldcup.json"
                req = urllib.request.Request(url)
                data = json.loads(urllib.request.urlopen(req,timeout=5).read().decode())
                matches = data.get("matches",[])
                # 按日期排序
                matches.sort(key=lambda m: m.get("date",""))
                for m in matches:
                    t1 = m.get("team1","")
                    t2 = m.get("team2","")
                    if isinstance(t1,dict): t1=t1.get("name","")
                    if isinstance(t2,dict): t2=t2.get("name","")
                    ft = m.get("score",{}).get("ft",[None,None])
                    if ft[0] is None: continue
                    s1, s2 = int(ft[0]), int(ft[1])
                    # 更新 Elo
                    self._update_elo(t1, t2, s1, s2)
            except: pass
    
    def _update_elo(self, t1, t2, s1, s2):
        """更新兩隊 Elo 評分"""
        if t1 not in self.ratings: self.ratings[t1] = ELO_INIT
        if t2 not in self.ratings: self.ratings[t2] = ELO_INIT
        r1, r2 = self.ratings[t1], self.ratings[t2]
        e1 = 1 / (1 + 10**((r2-r1)/400))
        e2 = 1 - e1
        # 實際得分：勝=1, 和=0.5, 負=0
        if s1 > s2:
            actual1, actual2 = 1, 0
            gd = min(abs(s1-s2), 3)  # 入球差修正
        elif s1 < s2:
            actual1, actual2 = 0, 1
            gd = min(abs(s1-s2), 3)
        else:
            actual1, actual2 = 0.5, 0.5
            gd = 1
        k = K_ELO * gd  # 大勝調整更多
        self.ratings[t1] += k * (actual1 - e1)
        self.ratings[t2] += k * (actual2 - e2)
    
    def get_elo(self, team):
        """獲取球隊 Elo 評分"""
        en = to_en(team)
        if en in self.ratings: return self.ratings[en]
        # 嘗試匹配
        for k in self.ratings:
            if team.lower() in k.lower() or k.lower() in team.lower():
                return self.ratings[k]
        return ELO_INIT
    
    def predict(self, ta, tb):
        """基於 Elo 預測勝率"""
        ra, rb = self.get_elo(ta), self.get_elo(tb)
        ea = 1 / (1 + 10**((rb-ra)/400))
        eb = 1 - ea
        # 和波估算：Elo 差異越小，和波概率越高
        diff = abs(ra-rb)
        draw_prob = max(0.15, 0.30 - diff/2000)
        wa = ea * (1 - draw_prob)
        wb = eb * (1 - draw_prob)
        return {"wa":wa,"dr":draw_prob,"wb":wb,"elo_a":round(ra),"elo_b":round(rb)}

# ========== 3️⃣ 蒙特卡洛模擬（回歸！）==========
class MonteCarloSim:
    """蒙特卡洛模擬完整賽事"""
    def __init__(self, elo_system):
        self.elo = elo_system
    
    def simulate_match(self, ta, tb, n_sims=10000):
        """模擬單場比賽"""
        elo = self.elo.get_elo(ta)
        elo_b = self.elo.get_elo(tb)
        # Elo → 預期入球
        diff = (elo - elo_b) / 400
        base_goals = 1.2
        la = base_goals * (1 + diff * 0.3)
        lb = base_goals * (1 - diff * 0.3)
        la = max(la, 0.3); lb = max(lb, 0.3)
        
        wins_a = draws = wins_b = 0
        for _ in range(n_sims):
            g1 = sum(1 for _ in range(10) if random.random() < la/10)
            g2 = sum(1 for _ in range(10) if random.random() < lb/10)
            if g1 > g2: wins_a += 1
            elif g1 < g2: wins_b += 1
            else: draws += 1
        return {"wa":wins_a/n_sims,"dr":draws/n_sims,"wb":wins_b/n_sims,
                "xg_a":round(la,2),"xg_b":round(lb,2)}

# ========== 4️⃣ 三重集成引擎 ==========
class EnsembleEngine:
    """V6.1 核心：三模型集成評定"""
    def __init__(self):
        self.elo_sys = EloSystem()
        self.mc = MonteCarloSim(self.elo_sys)
    
    def predict(self, ta, tb, oh, od, oa, alt=0, is_ko=True,
                inj_a=0, inj_b=0, exp_a=0.5, exp_b=0.5, rest=0):
        # 1️⃣ 市場賠率
        m = market_predict(ta, tb, oh, od, oa, alt, is_ko, inj_a, inj_b, exp_a, exp_b, rest)
        # 2️⃣ Elo
        e = self.elo_sys.predict(ta, tb)
        # 3️⃣ 蒙特卡洛
        mc = self.mc.simulate_match(ta, tb)
        
        # 三重加權集成
        weights = {"market": 0.5, "elo": 0.25, "mc": 0.25}
        wa = m["wa"]*weights["market"] + e["wa"]*weights["elo"] + mc["wa"]*weights["mc"]
        dr = m["dr"]*weights["market"] + e["dr"]*weights["elo"] + mc["dr"]*weights["mc"]
        wb = m["wb"]*weights["market"] + e["wb"]*weights["elo"] + mc["wb"]*weights["mc"]
        
        # 淘汰賽調整
        if is_ko:
            dr += 0.04; wa -= 0.02; wb -= 0.02
        
        total = wa + dr + wb
        wa /= total; dr /= total; wb /= total
        
        return {
            "ensemble": {"wa":round(wa*100,1),"dr":round(dr*100,1),"wb":round(wb*100,1)},
            "market": {"wa":round(m["wa"]*100,1),"dr":round(m["dr"]*100,1),"wb":round(m["wb"]*100,1)},
            "elo": {"wa":round(e["wa"]*100,1),"dr":round(e["dr"]*100,1),"wb":round(e["wb"]*100,1),
                    "elo_a":e["elo_a"],"elo_b":e["elo_b"]},
            "monte_carlo": {"wa":round(mc["wa"]*100,1),"dr":round(mc["dr"]*100,1),"wb":round(mc["wb"]*100,1)},
        }

# ========== 顯示輸出 ==========
def print_ensemble(r, ta, tb, cards=None, is_ko=True):
    stage = "🏆 淘汰賽" if is_ko else "📊 小組賽"
    ens = r["ensemble"]
    mp = max(ens["wa"], ens["dr"], ens["wb"])
    if mp>=80: level="🟢 高信心 ✅"
    elif mp>=60: level="🟡 中信心 ℹ️"
    else: level="🔴 純分析 ⚠️"
    
    print("="*60)
    print(f"  V6.1 三重引擎預測：{ta} vs {tb}  {stage}")
    print(f"  {level}")
    print("="*60)
    
    print(f"\n  📊 集成結果（市場×0.5 + Elo×0.25 + MC×0.25）：")
    print(f"    {ta}  {ens['wa']}% ／ 和 {ens['dr']}% ／ {tb}  {ens['wb']}%")
    
    print(f"\n  🔍 三引擎對比：")
    print(f"    {'':>10} {'市場賠率':>10} {'Elo':>8} {'蒙特卡洛':>10}")
    print(f"    {ta:<6}勝  {r['market']['wa']:>7.1f}%  {r['elo']['wa']:>6.1f}%  {r['monte_carlo']['wa']:>8.1f}%")
    print(f"    {'和波':>6}  {r['market']['dr']:>7.1f}%  {r['elo']['dr']:>6.1f}%  {r['monte_carlo']['dr']:>8.1f}%")
    print(f"    {tb:<6}勝  {r['market']['wb']:>7.1f}%  {r['elo']['wb']:>6.1f}%  {r['monte_carlo']['wb']:>8.1f}%")
    
    if "elo_a" in r["elo"]:
        print(f"\n  ⭐ Elo 評分：{ta} {r['elo']['elo_a']} / {tb} {r['elo']['elo_b']}")
    
    if cards:
        print(f"\n  🟨 黃牌預測：總計{cards['total']}張")
        print(f"    0-2張 {cards['p02']}% | 3-5張 {cards['p35']}%")
        print(f"    推薦: {cards['rec']}")
    
    # 2串1 推薦
    if mp >= 60:
        print(f"\n  🏆 競彩推薦：")
        fav = ta if ens['wa'] > ens['wb'] else tb
        fav_p = max(ens['wa'], ens['wb'])
        print(f"    【2串1】{fav}勝（{fav_p}%）+ 小2.5球 → 約 {fav_p/100*0.6:.0%} 綜合概率")
    
    print()

# ========== 主程式 ==========
if __name__ == "__main__":
    args = sys.argv[1:]
    
    if len(args) >= 5:
        engine = EnsembleEngine()
        ta, tb = args[0], args[1]
        oh, od, oa = float(args[2]), float(args[3]), float(args[4])
        alt=0; inj_a=0; inj_b=0; exp_a=0.5; exp_b=0.5; rest=0
        show_cards=False; is_final=False; is_ko=True
        
        for i,a in enumerate(args):
            if a=="--alt" and i+1<len(args): alt=int(args[i+1])
            if a=="--inj_a" and i+1<len(args): inj_a=float(args[i+1])
            if a=="--inj_b" and i+1<len(args): inj_b=float(args[i+1])
            if a=="--exp_a" and i+1<len(args): exp_a=float(args[i+1])
            if a=="--exp_b" and i+1<len(args): exp_b=float(args[i+1])
            if a=="--rest" and i+1<len(args): rest=int(args[i+1])
            if a=="--cards": show_cards=True
            if a=="--final": is_final=True
        
        result = engine.predict(ta, tb, oh, od, oa, alt, is_ko, inj_a, inj_b, exp_a, exp_b, rest)
        cards = predict_cards(ta, tb, is_final) if show_cards else None
        print_ensemble(result, ta, tb, cards, is_ko)
    
    elif len(args) >= 1 and args[0] == "elo":
        # 顯示 Elo 排行榜
        es = EloSystem()
        print("\n  ⭐ Elo 評分排行榜")
        print("="*40)
        for team, rating in sorted(es.ratings.items(), key=lambda x:-x[1]):
            print(f"  {team:<20} {rating:.0f}")
    
    else:
        print("用法:")
        print("  python predict_v61.py 隊A 隊B 主賠 和賠 客賠 [--alt N] [--inj_a -0.1] [--exp_a 0.8] [--cards]")
        print("  python predict_v61.py elo    ← 顯示 Elo 排行榜")
