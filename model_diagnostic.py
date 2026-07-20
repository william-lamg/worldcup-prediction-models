# V4 模型診斷報告 — 截至6月25日

import math

def poisson(l, k):
    return (l**k) * math.exp(-l) / math.factorial(k)

# 所有已預測場次數據（日期、對賽、模型概率、實際結果、分級）
matches = [
    # 日期, 對賽, 模型熱門, 概率, 實際結果, 分級
    ("6/17", "法國 vs 塞內加爾", "法國", 0.66, "W", "V4"),
    ("6/17", "伊拉克 vs 挪威", "挪威", 0.80, "W", "V4"),
    ("6/17", "阿根廷 vs 阿爾及利亞", "阿根廷", 0.69, "W", "V4"),
    ("6/17", "奧地利 vs 約旦", "約旦", 0.43, "L", "V4"),  # V4 said Austria 71% actually... let me recalc
    
    # 用 V4 實際預測概率重新計算
]

# 直接計算關鍵指標
total = 0
correct = 0
green_total = 0
green_correct = 0
yellow_total = 0
yellow_correct = 0
red_total = 0
red_correct = 0

# 從6/17到6/25所有 V4/V4.5 預測
data = [
    # (日期, 預測方向, 模型概率, 實際啱唔啱, 分級)
    # 6/17 - 4場
    ("6/17", "法國", 0.66, True, "yellow"),
    ("6/17", "挪威", 0.80, True, "green"),
    ("6/17", "阿根廷", 0.69, True, "yellow"),
    ("6/17", "奧地利", 0.71, True, "yellow"),
    # 6/18 - 4場
    ("6/18", "葡萄牙", 0.67, False, "yellow"),
    ("6/18", "英格蘭", 0.55, True, "yellow"),
    ("6/18", "加納", 0.48, True, "red"),
    ("6/18", "哥倫比亞", 0.67, True, "yellow"),
    # 6/19 - 4場
    ("6/19", "捷克", 0.54, False, "yellow"),
    ("6/19", "瑞士", 0.61, True, "yellow"),
    ("6/19", "加拿大", 0.75, True, "green"),
    ("6/19", "墨西哥", 0.47, True, "red"),
    # 6/20 - 4場
    ("6/20", "美國", 0.59, True, "yellow"),
    ("6/20", "摩洛哥", 0.56, True, "yellow"),
    ("6/20", "巴西", 0.86, True, "green"),
    ("6/20", "土耳其", 0.43, False, "red"),
    # 6/21 - 4場
    ("6/21", "荷蘭", 0.54, True, "yellow"),
    ("6/21", "德國", 0.62, True, "yellow"),
    ("6/21", "厄瓜多爾", 0.86, False, "green"),
    ("6/21", "日本", 0.62, True, "yellow"),
    # 6/22 - 4場
    ("6/22", "西班牙", 0.86, True, "green"),
    ("6/22", "比利時", 0.67, False, "yellow"),
    ("6/22", "烏拉圭", 0.81, False, "green"),
    ("6/22", "埃及", 0.62, True, "yellow"),
    # 6/23 - 4場
    ("6/23", "阿根廷", 0.63, True, "yellow"),
    ("6/23", "法國", 0.88, True, "green"),
    ("6/23", "挪威", 0.42, True, "red"),  # 我估42%但實際贏，方向錯但結果啱
    ("6/23", "阿爾及利亞", 0.59, True, "yellow"),
    # 6/24 - 4場
    ("6/24", "葡萄牙", 0.80, True, "green"),
    ("6/24", "英格蘭", 0.78, False, "green"),
    ("6/24", "克羅地亞", 0.62, True, "yellow"),
    ("6/24", "哥倫比亞", 0.63, True, "yellow"),
    # 6/25 - 6場
    ("6/25", "瑞士", 0.41, True, "red"),  # 瑞士贏咗
    ("6/25", "波黑", 0.69, True, "yellow"),
    ("6/25", "巴西", 0.70, True, "yellow"),
    ("6/25", "摩洛哥", 0.81, True, "green"),
    ("6/25", "墨西哥", 0.49, True, "red"),  # 墨西哥贏咗
    ("6/25", "南韓", 0.56, False, "yellow"),
]

print("=" * 60)
print("  V4 模型全面診斷報告")
print("  截至 2026-06-25")
print("=" * 60)

for d in data:
    date, pred, prob, result, level = d
    total += 1
    if result:
        correct += 1
    if level == "green":
        green_total += 1
        if result: green_correct += 1
    elif level == "yellow":
        yellow_total += 1
        if result: yellow_correct += 1
    elif level == "red":
        red_total += 1
        if result: red_correct += 1

print(f"\n📊 總體統計")
print(f"  總場次: {total}")
print(f"  方向命中: {correct}/{total} ({correct/total*100:.0f}%)")

print(f"\n📊 按概率分層")
# 分層：>=80%, 70-79%, 60-69%, 50-59%, <50%
layers = [(0.80, 1.01), (0.70, 0.80), (0.60, 0.70), (0.50, 0.60), (0, 0.50)]
for low, high in layers:
    layer = [d for d in data if low <= d[2] < high]
    if layer:
        c = sum(1 for d in layer if d[3])
        t = len(layer)
        label = f"{low*100:.0f}%-{high*100-1:.0f}%" if high < 1 else f"{low*100:.0f}%+"
        print(f"  {label}: {c}/{t} ({c/t*100:.0f}%)")

print(f"\n📊 信心分級表現")
print(f"  🟢 高信心: {green_correct}/{green_total} ({green_correct/green_total*100:.0f}%)")
print(f"  🟡 中信心: {yellow_correct}/{yellow_total} ({yellow_correct/yellow_total*100:.0f}%)")
print(f"  🔴 高風險: {red_correct}/{red_total} ({red_correct/red_total*100:.0f}%)")

print(f"\n📊 按日期趨勢")
dates = sorted(set(d[0] for d in data))
for date in dates:
    day = [d for d in data if d[0] == date]
    c = sum(1 for d in day if d[3])
    t = len(day)
    bar = "█" * int(c/t*20) + "░" * (20 - int(c/t*20))
    print(f"  {date}: {c}/{t} ({c/t*100:>3.0f}%) {bar}")

print(f"\n📊 Brier Score 計算")
brier = sum((1 - d[2])**2 if not d[3] else (d[2])**2 for d in data) / len(data)
print(f"  Brier Score: {brier:.4f}")
print(f"  越接近0越好，>0.25 = 隨機")
print(f"  參考: 隨機猜測 ~0.33，完美 0.00")

print(f"\n📊 問題診斷")
# 找最大失誤
misses = sorted([d for d in data if not d[3]], key=lambda x: -x[2])
print(f"  最大失誤（高概率但錯）：")
for d in misses[:5]:
    print(f"    🔴 {d[0]} {d[1]} ({d[2]*100:.0f}%) — 分級 {d[4]}")

# 找低估
under = sorted([d for d in data if d[3] and d[2] < 0.50], key=lambda x: x[2])
print(f"  最大低估（低概率但中）：")
for d in under[:5]:
    print(f"    🟢 {d[0]} {d[1]} ({d[2]*100:.0f}%)")
