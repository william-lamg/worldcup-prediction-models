# 世界盃預測模型 World Cup Prediction Model

從 V1 到 V5.5 嘅完整進化歷程。

## 模型版本演進

### V1 — 初始泊松模型（已廢棄）
- **日期**: 世界盃開賽前
- **核心**: Elo + 自寫泊松分佈
- **問題**: 方向命中率 ~50%

### V2 — 改進泊松版本（已廢棄）
- **核心**: 改進泊松參數
- **問題**: 依然 ~50%

### V3 — world-cup-predict 引擎（已廢棄）
- **日期**: 6月12日
- **核心**: GitHub 開源引擎 Elo + Dixon-Coles + 蒙特卡洛
- **來源**: https://github.com/ML-KevinHe/world-cup-predict
- **問題**: Confederation Bias（洲份偏誤）

### V3.5 — 校正層（已廢棄）
- **日期**: 6月15日
- **核心**: 自動識別洲份對戰組合，校正歐洲/非洲偏差
- **問題**: 治標唔治本

### V4 — 市場賠率引擎（現行）
- **日期**: 6月15日
- **核心**: 直接用 Bet365 賠率反推概率，泊松分佈生成比分
- **優點**: 冇洲份偏誤，28場方向命中率~75%
- **檔案**: `predict_v4.py`

### V4.5 — 競彩整合版
- **日期**: 6月21日
- **核心**: V4 + 競彩即時賠率 + 價值判斷
- **信心分級**: 🟢 ≥80% / 🟡 50-79% / 🔴 <50%

### V5 — Dixon-Coles + 淘汰賽調整（現行）
- **日期**: 6月28日
- **核心**: 市場賠率 → Dixon-Coles 低比分修正 → 淘汰賽和波調整
- **新增**: 高原主場因子（--altitude）、淘汰賽模式（--knockout）
- **來源**: Dixon-Coles (1997) 低比分修正模型
- **檔案**: `predict_v5.py`

### V5+ — 強化版（現行）
- **日期**: 7月3日
- **核心**: V5 + 加時/12碼概率 + 總入球分佈
- **新增**: 淘汰賽完整路徑分析（90分鐘→加時→12碼）
- **檔案**: `predict_v5_plus.py`

### V5.5 — 最新版 🆕
- **日期**: 7月6日
- **核心**: V5+ 全面強化
- **新增**:
  - ⭐ 巨星指數（Top 10 球星球隊 +5-8%）
  - 🏔️ 高原調整減半（5% → 2.5%）
  - 🧠 心理因子（強隊信心折讓 -3%）
  - ⚽ 淘汰賽大小球修正（大2.5 -5%）
- **檔案**: `predict_v55.py`

## 效能統計

| 版本 | 場次 | 方向命中率 | 備註 |
|:---|:---:|:---:|:---|
| V1/V2 | ~5 | ~50% | 廢棄 |
| V3 | ~8 | ~50% | 洲份偏誤 |
| V4 | 28 | ~75% | 現行主引擎 |
| V5 | 10 | 90% | 淘汰賽 |
| V5+ | 17 | 82% | 強化版 |
| **V5.5** 🆕 | — | — | **最新** |

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
| 傷病/xG/陣容（可選增強） | machina-sports/sports-skills | ❌ MIT 開源 |

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
項目地址：https://github.com/machina-sports/sports-skills（MIT License）

## 用法

```bash
# V5.5 預測
python predict_v55.py "葡萄牙" "西班牙" 2.80 3.10 2.50 --alt 0

# V5 預測（淘汰賽模式）
python predict_v5.py "巴西" "日本" 1.65 3.60 5.00 --knockout

# V5+ 強化預測（包含加時/12碼/總入球）
python predict_v5_plus.py 巴西 日本 1.65 3.60 5.00

# V4 預測（通用）
python predict_v4.py odds "阿根廷" "法國" 2.50 3.20 2.80
```

## License

MIT
