# 🏆 世界盃預測模型 V1 → V7.0 完整進化

> 2026 美加墨世界盃全程實戰覆盤 | 52 場比賽 | 12 個版本迭代

從初始泊松到三重集成引擎，48 日嘅模型進化之路。

---

## 📦 版本一覽（點擊跳轉）

| 版本 | 狀態 | 下載 | 核心 | 日期 |
|:---|:---:|:---|:---|---:|
| [V1](#v1--初始泊松模型) | ❌ 廢棄 | `predict_v1.py`（未保留） | Elo + 泊松 | 賽前 |
| [V2](#v2--改進泊松) | ❌ 廢棄 | `predict_v2.py`（未保留） | 改進泊松 | 賽前 |
| [V3](#v3--world-cup-predict-引擎) | ❌ 廢棄 | 外部引擎 | Elo + Dixon-Coles + MC | 6/12 |
| [V3.5](#v35--校正層) | ❌ 廢棄 | 未保留 | 洲份校正 | 6/15 |
| [V4](#v4--市場賠率引擎) | ✅ 可使用 | `predict_v4.py` | 市場賠率 + 泊松 | 6/15 |
| [V4.5](#v45--競彩整合版) | ✅ 可使用 | — | V4 + 競彩賠率 | 6/21 |
| [V5](#v5--dixon-coles--淘汰賽) | ✅ 可使用 | `predict_v5.py` | Dixon-Coles + 淘汰賽 | 6/28 |
| [V5+](#v5--強化版) | ✅ 可使用 | `predict_v5_plus.py` | 加時/12碼 | 7/3 |
| [V5.5](#v55--強化版-1) | ✅ 可使用 | `predict_v55.py` | 巨星/高原/心理 | 7/6 |
| [V5.6](#v56--強化版-1) | ✅ 可使用 | `predict_v56.py` | 紅黃牌/傷病/Brier | 7/12 |
| [V6.0](#v60--h2h-歷史版) | ✅ 可使用 | `predict_v6.py`（本地） | H2H 歷史數據 | 7/15 |
| [V6.1](#v61--三重集成引擎) | ✅ 可使用 | `predict_v61.py` | Elo+MC+市場三重 | 7/15 |
| [V7.0](#v70--戰後重建版) | ✅ **最新** | `predict_v7.py` | 防守體系/決賽模式 | 7/20 |

---

## 模型版本演進

### V1 — 初始泊松模型（已廢棄，未保留）
- **日期**: 世界盃開賽前
- **核心**: Elo + 自寫泊松分佈
- **問題**: 方向命中率 ~50%
- **下載**: 未保留

### V2 — 改進泊松（已廢棄，未保留）
- **核心**: 改進泊松參數
- **問題**: 依然 ~50%
- **下載**: 未保留

### V3 — world-cup-predict 引擎（已廢棄）
- **日期**: 6月12日
- **核心**: GitHub 開源引擎 Elo + Dixon-Coles + 蒙特卡洛
- **來源**: https://github.com/ML-KevinHe/world-cup-predict
- **問題**: Confederation Bias（洲份偏誤）
- **下載**: 外部引擎

### V3.5 — 校正層（已廢棄）
- **日期**: 6月15日
- **核心**: 自動識別洲份對戰組合，校正歐洲/非洲偏差
- **問題**: 治標唔治本
- **下載**: 未保留

### V4 — 市場賠率引擎（✅ 可使用）
- **日期**: 6月15日
- **核心**: 直接用 Bet365 賠率反推概率，泊松分佈生成比分
- **優點**: 冇洲份偏誤，28場方向命中率~75%
- **用法**: `python predict_v4.py odds "阿根廷" "法國" 2.50 3.20 2.80`
- **檔案**: `predict_v4.py`
- **下載**: `curl -O https://raw.githubusercontent.com/william-lamg/worldcup-prediction-models/main/predict_v4.py`

### V4.5 — 競彩整合版（✅ 可使用）
- **日期**: 6月21日
- **核心**: V4 + 競彩即時賠率 + 價值判斷
- **信心分級**: 🟢 ≥80% / 🟡 50-79% / 🔴 <50%

### V5 — Dixon-Coles + 淘汰賽調整（✅ 可使用）
- **日期**: 6月28日
- **核心**: 市場賠率 → Dixon-Coles 低比分修正 → 淘汰賽和波調整
- **新增**: 高原主場因子（--altitude）、淘汰賽模式（--knockout）
- **來源**: Dixon-Coles (1997) 低比分修正模型
- **用法**: `python predict_v5.py "巴西" "日本" 1.65 3.60 5.00 --knockout`
- **檔案**: `predict_v5.py`
- **下載**: `curl -O https://raw.githubusercontent.com/william-lamg/worldcup-prediction-models/main/predict_v5.py`

### V5+ — 強化版（✅ 可使用）
- **日期**: 7月3日
- **核心**: V5 + 加時/12碼概率 + 總入球分佈
- **新增**: 淘汰賽完整路徑分析（90分鐘→加時→12碼）
- **用法**: `python predict_v5_plus.py 巴西 日本 1.65 3.60 5.00`
- **檔案**: `predict_v5_plus.py`
- **下載**: `curl -O https://raw.githubusercontent.com/william-lamg/worldcup-prediction-models/main/predict_v5_plus.py`

### V5.5 — 強化版（✅ 可使用）
- **日期**: 7月6日
- **核心**: V5+ 全面強化
- **新增**:
  - ⭐ 巨星指數（Top 10 球星球隊 +5-8%）
  - 🏔️ 高原調整減半（5% → 2.5%）
  - 🧠 心理因子（強隊信心折讓 -3%）
  - ⚽ 淘汰賽大小球修正（大2.5 -5%）
- **用法**: `python predict_v55.py "葡萄牙" "西班牙" 2.80 3.10 2.50`
- **檔案**: `predict_v55.py`
- **下載**: `curl -O https://raw.githubusercontent.com/william-lamg/worldcup-prediction-models/main/predict_v55.py`

### V5.6 — 強化版（✅ 可使用）
- **日期**: 7月12日
- **核心**: V5.5 + 紅黃牌預測 + 嚴格推薦門檻
- **新增**:
  - 🟨 紅黃牌預測模組（--cards）
  - 🏥 傷病因子（--inj_a/b）
  - 🏆 經驗因子（--exp_a/b）
  - 😴 疲勞因子（--rest）
  - 📊 Brier Score 監控
  - 🔴 ≥60%嚴格推薦門檻
- **用法**: `python predict_v56.py "法國" "西班牙" 2.10 3.20 3.40 --cards`
- **檔案**: `predict_v56.py`
- **下載**: `curl -O https://raw.githubusercontent.com/william-lamg/worldcup-prediction-models/main/predict_v56.py`

### V6.0 — H2H 歷史版（✅ 可使用，本地）
- **日期**: 7月15日
- **核心**: V5.6 + 世界盃歷史交鋒數據
- **新增**:
  - 📜 H2H 歷史數據（2018/2022/2026共229場）
  - 📈 近期狀態因子（近10場戰績）
  - 🌐 中英文隊名自動映射
  - 🔄 自動 H2H 調整因子
- **用法**: `python predict_v6.py "法國" "西班牙" 2.10 3.20 3.40`
- **檔案**: `predict_v6.py`（本地，未上傳）

### V6.1 — 三重集成引擎（✅ 可使用）
- **日期**: 7月15-16日
- **核心**: 市場賠率 + Elo + 蒙特卡洛 三重集成
- **新增**:
  - ✅ Elo 系統回歸（V3 功能恢復）
  - ✅ 蒙特卡洛模擬回歸（V3 功能恢復）
  - 🔍 三引擎對比輸出
  - 🏆 2串1競彩推薦恢復
  - ⭐ Elo 排行榜（`python predict_v61.py elo`）
- **用法**: `python predict_v61.py "英格蘭" "阿根廷" 2.30 3.20 3.10 --cards --final`
- **檔案**: `predict_v61.py`
- **下載**: `curl -O https://raw.githubusercontent.com/william-lamg/worldcup-prediction-models/main/predict_v61.py`

### V6.1.1 — 賽前情報恢復
- **日期**: 7月15日
- **核心**: V6.1 + 賽前情報自動檢查
- **新增**:
  - ✅ 賽前情報檢查恢復（傷病/停賽/陣容）
  - 🏥 更精細傷病情況注入（WebSearch → --inj）
- **更新**: Automation prompt

### V7.0 — 戰後重建版（🆕 最新，✅ 推薦使用）
- **日期**: 7月20日
- **核心**: 基於52場完整覆盤嘅5大改進
- **改進**:
  - 🏆 決賽壓力模式（`--final`）：防守型球隊 +8%，市場權重降為35%
  - 🥉 季軍戰開放模式（`--third`）：雙方 +15% xG（開放比賽）
  - 🛡️ 防守體系因子（西班牙7場失1球自動加成）
  - 📊 Elo 回溯至2010世界盃（4屆數據）
  - ⚖️ 獨立權重：決賽/季軍戰市場權重由50%降至35%
- **用法**:
  ```bash
  # 決賽預測
  python predict_v7.py "西班牙" "阿根廷" 2.80 3.10 2.50 --final --exp_a 0.85 --exp_b 0.95
  
  # 季軍戰預測
  python predict_v7.py "英格蘭" "法國" 3.50 3.40 2.00 --third
  
  # 普通淘汰賽
  python predict_v7.py "隊A" "隊B" 主賠 和賠 客賠
  ```
- **檔案**: `predict_v7.py`
- **下載**: `curl -O https://raw.githubusercontent.com/william-lamg/worldcup-prediction-models/main/predict_v7.py`

## 效能統計

| 版本 | 場次 | 方向命中率 | 備註 |
|:---|:---:|:---:|:---|
| V1/V2 | ~5 | ~50% | 廢棄 |
| V3 | ~8 | ~50% | 洲份偏誤 |
| V4 | 28 | ~75% | 市場賠率新版 |
| V5 | 10 | 90% | 淘汰賽 |
| V5+ | 17 | 82% | 強化版 |
| V5.5 | ~15 | ~60% | 8強後下滑 |
| V5.6 | 3 | 50% | 4強後失準 |
| V6.0 | 1 | — | H2H 數據版 |
| V6.1 | 2 | 0% | 決賽全錯 |
| V6.1.1 | 3 | 0% | 決賽+季軍戰全錯 |
| **V7.0** 🆕 | — | — | **戰後重建** |

## 引用來源

### 學術論文
- **Dixon, M.J. & Coles, S.G. (1997)**. *Modelling Association Football Scores and Inefficiencies in the Football Betting Market.* Journal of the Royal Statistical Society: Series C, 46(2), 265-280.
  - 雙變量泊松分佈（Bivariate Poisson）低比分修正模型嘅原始論文
  - V5/V5+/V5.5 嘅 Dixon-Coles 修正 Rho 參數基於此論文

### 開源項目
- **ML-KevinHe/world-cup-predict** — https://github.com/ML-KevinHe/world-cup-predict
  - V3 引擎基礎，Elo + Dixon-Coles + Monte Carlo
  - 已廢棄，因洲份偏誤（Confederation Bias）
- **Hicruben/world-cup-2026-prediction-model** — https://github.com/Hicruben/world-cup-2026-prediction-model
  - Elo → Dixon-Coles → 50,000次蒙特卡羅模擬
  - RPS 0.175，65%準確率（72場中47場）
  - V5 淘汰賽模擬參考來源
- **LionelJXH/worldcup-predictor-** — https://github.com/LionelJXH/worldcup-predictor-
  - 市場賠率引導集成模型（Market-anchored ensemble）
  - 環境因子調整（海拔/天氣/休息日/傷病）
  - V5 高原調整同上下文因子參考來源
- **martj42/international_results** — https://github.com/martj42/international_results
  - 國際足球比賽歷史數據（公開 CSV），用於 Elo 校準

## 數據來源

| 數據 | 來源 | 是否需要API |
|:---|---|:---:|
| 國際賠率（Bet365/betfair/SkyBet） | WebSearch 實時搜索 | ❌ 免費 |
| 競彩賠率（中國體彩） | https://17500.cn | ❌ 免費 |
| 賽程/賽果/即時比分 | https://bracketmundial2026.com | ❌ 免費 |
| 比賽歷史數據 | martj42 GitHub CSV | ❌ 免費 |
| Elo 評分（可選） | https://eloratings.net | ❌ 免費 |
| 天氣數據（可選） | https://open-meteo.com | ❌ 免費（無需 key） |
| 預測市場（可選） | https://polymarket.com (Gamma API) | ❌ 免費 |
| 賠率API升級（付費選項） | https://the-odds-api.com | ✅ 需註冊（Business tier ~$99/月） |
| 傷病/xG/陣容（可選增強） | machina-sports/sports-skills | ❌ ## License

MIT 開源 |

### API 註冊指南

#### The Odds API（非必需，付費升級）
如需獲取 Pinnacle 收盤賠率（業界黃金標準），可註冊：
1. 前往 https://the-odds-api.com 註冊賬號
2. 選擇 Business 計劃（約 $99/月）
3. 獲取 API key 後設置環境變數：`export ODDS_API_KEY=your_key`
4. 模型會自動檢測 key 並使用 Pinnacle 賠率增強預測

#### 可選增強（machina-sports/sports-skills）
如需更詳細嘅傷病/xG/陣容數據：
```bash
pip install machina-sports
```
項目地址：https://github.com/machina-sports/sports-skills（## License

MIT License）

## 用法

```bash
# V7.0 預測（最新）
python predict_v7.py "西班牙" "阿根廷" 2.80 3.10 2.50 --final

# V7.0 季軍戰模式
python predict_v7.py "英格蘭" "法國" 3.50 3.40 2.00 --third

# V6.1 三重引擎預測
python predict_v61.py "隊A" "隊B" 主賠 和賠 客賠 [--cards] [--final]

# V5.6 預測（傷病/經驗參數）
python predict_v56.py "隊A" "隊B" 主賠 和賠 客賠 [--alt 海拔] [--inj_a -0.1] [--exp_a 0.8]

# V5 預測（淘汰賽模式）
python predict_v5.py "巴西" "日本" 1.65 3.60 5.00 --knockout

# V4 預測（通用）
python predict_v4.py odds "阿根廷" "法國" 2.50 3.20 2.80
```

## 自動數據獲取

```bash
# 下載世界盃 H2H 歷史數據
python worldcup_data.py fetch

# 查詢 H2H
python worldcup_data.py h2h "法國" "西班牙"

# 黃牌預測
python card_model.py "隊A" "隊B" --final

# Elo 排行榜
python predict_v61.py elo
```

## License

MIT

---

## 🏁 世界盃 2026 完結 — 致謝

2026 年 6 月 12 日至 7 月 20 日，48 日，52 場比賽。

由一個 50% 命中率嘅泊松模型開始，一路演化到三重集成引擎。V4 市場賠率引擎嘅 75% 命中率令人振奮，V5 Dixon-Coles 淘汰賽 83% 係最高峰——然後 8 強後斷崖式下跌，決賽 3 連錯，用最現實嘅方式證明咗模型嘅邊界。

```
📊 最終成績：~70% 方向命中／0 場小紅書全中
💀 最大失誤：決賽連錯 3 場
🏆 最大啟發：足球永遠比模型複雜
```

特別鳴謝以下開源項目：
- **openfootball** — 免費世界盃數據（worldcup.json / football.json），Public Domain
- **football-apis** — Python 足球數據封裝（GitHub: defnlnotme/football-apis），MIT License
- **ML-KevinHe/world-cup-predict** — V3 引擎參考
- **Dixon & Coles (1997)** — Bivariate Poisson 低比分修正論文

模型會繼續存在喺 GitHub，下屆世界盃或者任何有足球賠率嘅時候攞出嚟改一改就可以再用。

> 「足球係圓嘅。模型可以幫你搵出概率，但永遠唔會知道 106 分鐘費蘭托利斯會唔會入波。」

— 2026 年 7 月 20 日

*Made with 🤙 for the love of football*
