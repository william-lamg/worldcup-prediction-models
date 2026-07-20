combos = [
    {
        'name': 'A: 高賠率組合（進取型）',
        'picks': [
            ('西班牙 vs 沙特', '西班牙 -2 勝', 1.57, 0.70),
            ('比利時 vs 伊朗', '比利時 -1 勝', 1.89, 0.67),
            ('烏拉圭 vs 佛得角', '烏拉圭 -1 勝', 2.08, 0.59),
            ('紐西蘭 vs 埃及', '埃及勝', 1.42, 0.62),
        ]
    },
    {
        'name': 'B: 穩健組合（保守型）',
        'picks': [
            ('西班牙 vs 沙特', '西班牙 -2 勝', 1.57, 0.70),
            ('比利時 vs 伊朗', '比利時勝', 1.26, 0.67),
            ('烏拉圭 vs 佛得角', '烏拉圭勝', 1.29, 0.81),
            ('紐西蘭 vs 埃及', '埃及勝', 1.42, 0.62),
        ]
    },
    {
        'name': 'C: 混合型（讓球+勝平負）',
        'picks': [
            ('西班牙 vs 沙特', '西班牙 -2 勝', 1.57, 0.70),
            ('比利時 vs 伊朗', '比利時 -1 勝', 1.89, 0.67),
            ('烏拉圭 vs 佛得角', '烏拉圭勝', 1.29, 0.81),
            ('紐西蘭 vs 埃及', '小 2.5 球', None, 0.60),
        ]
    },
    {
        'name': 'D: 性價比最高 🏆',
        'picks': [
            ('西班牙 vs 沙特', '西班牙 -2 勝', 1.57, 0.70),
            ('比利時 vs 伊朗', '比利時 -1 勝', 1.89, 0.67),
            ('烏拉圭 vs 佛得角', '烏拉圭 -1 勝', 2.08, 0.59),
            ('紐西蘭 vs 埃及', '小 2.5 球', None, 0.60),
        ]
    },
]

for combo in combos:
    total_odds = 1
    total_prob = 1
    print("="*50)
    print(f'  {combo["name"]}')
    print("="*50)
    for match, pick, odds, prob in combo['picks']:
        if odds:
            total_odds *= odds
        total_prob *= prob
        print(f'  {match}: {pick}')
        if odds:
            print(f'    賠率 {odds} | 單場概率 {prob*100:.0f}%')
        else:
            print(f'    概率 {prob*100:.0f}%（無固定賠率）')
    print(f'  ---')
    print(f'  4串1 總賠率: {total_odds:.2f}')
    print(f'  4串1 中獎概率: {total_prob*100:.1f}%')
    print(f'  期望回報(¥100): ¥{total_odds*total_prob*100:.0f}')
    print(f'  盈虧平衡: 需 {1/total_odds*100:.1f}%')
    print(f'  價值比: {total_prob*total_odds:.2f}')
    print()
