#!/usr/bin/env python3
"""
世界盃預測校正層 — 修正 V3 模型的 Confederation Bias

用法：python predict_corrected.py match "TeamA" "TeamB"
"""

import subprocess, re, sys, os

ENGINE = os.path.expanduser("~/.workbuddy/skills/world-cup-predict/wcpredict.py")
PYTHON = "python3"

CONFEDERATIONS = {
    "Spain":"UEFA","Germany":"UEFA","France":"UEFA","England":"UEFA",
    "Portugal":"UEFA","Netherlands":"UEFA","Belgium":"UEFA","Croatia":"UEFA",
    "Switzerland":"UEFA","Sweden":"UEFA","Denmark":"UEFA","Austria":"UEFA",
    "Norway":"UEFA","Scotland":"UEFA","Turkey":"UEFA","Czech Republic":"UEFA",
    "Italy":"UEFA","Poland":"UEFA","Ukraine":"UEFA",
    "Argentina":"CONMEBOL","Brazil":"CONMEBOL","Uruguay":"CONMEBOL",
    "Colombia":"CONMEBOL","Ecuador":"CONMEBOL","Paraguay":"CONMEBOL",
    "Japan":"AFC","South Korea":"AFC","Australia":"AFC","Iran":"AFC",
    "Saudi Arabia":"AFC","Qatar":"AFC","Iraq":"AFC","Uzbekistan":"AFC","Jordan":"AFC",
    "Morocco":"CAF","Senegal":"CAF","Egypt":"CAF","Ivory Coast":"CAF",
    "Algeria":"CAF","Tunisia":"CAF","Ghana":"CAF","South Africa":"CAF",
    "Cape Verde":"CAF","Congo":"CAF",
    "Mexico":"CONCACAF","United States":"CONCACAF","Canada":"CONCACAF",
    "Panama":"CONCACAF","Haiti":"CONCACAF","Curaçao":"CONCACAF",
    "New Zealand":"OFC",
}

def get_conf(team):
    for name, conf in CONFEDERATIONS.items():
        if name.lower() in team.lower() or team.lower() in name.lower():
            return conf, name
    return None, team

def run_match(team_a, team_b):
    r = subprocess.run([PYTHON, '-X', 'utf8', ENGINE, 'match', team_a, team_b],
                       capture_output=True, timeout=30)
    out = r.stdout.decode('utf-8', errors='replace')
    
    # Parse
    elo_m = re.search(r'Elo (\d+)\)[^)]*?(\d+)\)', out)
    xg_m = re.search(r'λ:\s*([\d.]+)\s*[—\-]\s*([\d.]+)', out)
    prob_m = re.search(r'胜平负:\s+(\S+)\s+(\d+)%\s+平\s+(\d+)%\s+(\S+)\s+(\d+)%', out)
    sc_m = re.findall(r'([\d]+-[\d]+)\s+\(([\d.]+)%\)', out)
    
    elo_a = elo_m.group(1) if elo_m else "?"
    elo_b = elo_m.group(2) if elo_m else "?"
    xg_a = xg_m.group(1) if xg_m else "?"
    xg_b = xg_m.group(2) if xg_m else "?"
    
    if prob_m:
        a_pct = float(prob_m.group(2)) / 100
        d_pct = float(prob_m.group(3)) / 100
        b_pct = float(prob_m.group(5)) / 100
    else:
        print(out)
        return
    
    # 校正
    conf_a, _ = get_conf(team_a)
    conf_b, _ = get_conf(team_b)
    
    corr = {
        ("UEFA","CAF"): (0.08,-0.08), ("CAF","UEFA"): (-0.08,0.08),
        ("UEFA","AFC"): (0.06,-0.06), ("AFC","UEFA"): (-0.06,0.06),
        ("UEFA","CONCACAF"): (0.05,-0.05), ("CONCACAF","UEFA"): (-0.05,0.05),
        ("CONMEBOL","CAF"): (0.04,-0.04), ("CAF","CONMEBOL"): (-0.04,0.04),
        ("CONMEBOL","AFC"): (0.03,-0.03), ("AFC","CONMEBOL"): (-0.03,0.03),
    }
    
    pair = (conf_a, conf_b)
    corr_a, corr_b = corr.get(pair, (0, 0))
    
    new_a = a_pct + corr_a
    new_b = b_pct + corr_b
    total = new_a + d_pct + new_b
    new_a /= total; new_d = d_pct / total; new_b /= total
    
    # Output
    print(f"\n{'='*55}")
    print(f"  {team_a} vs {team_b}")
    print(f"{'='*55}")
    print(f"  Elo: {team_a} {elo_a} vs {team_b} {elo_b}")
    print(f"  xG:  {xg_a} / {xg_b}")
    print(f"  合: {conf_a} vs {conf_b}")
    print()
    print(f"  📊 原始模型:")
    print(f"     {team_a}勝 {a_pct*100:.0f}% / 和 {d_pct*100:.0f}% / {team_b}勝 {b_pct*100:.0f}%")
    
    if abs(corr_a) > 0:
        print(f"  🔧 洲份校正 ({' +' if corr_a>0 else ' '}{corr_a*100:.0f}% / {corr_b*100:+.0f}%):")
    
    print(f"  ✅ 校正後:")
    print(f"     {team_a}勝 {new_a*100:.0f}% / 和 {new_d*100:.0f}% / {team_b}勝 {new_b*100:.0f}%")
    
    if abs(new_a - a_pct) > 0.05:
        print(f"     ⚠️ 校正幅度 >5%，建議以市場賠率為最終判斷")
    
    print(f"\n  🎯 最可能比分:")
    for i, (s, p) in enumerate(sc_m[:5]):
        print(f"    {'→' if i==0 else ' '} {s} ({p}%)")
    
    print(f"\n  💡 方向: {team_a if new_a>new_b else team_b}勝 ({max(new_a,new_b)*100:.0f}%)")
    
    print()

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "match":
        run_match(sys.argv[2], sys.argv[3])
    else:
        subprocess.run([PYTHON, '-X', 'utf8', ENGINE] + sys.argv[1:])
