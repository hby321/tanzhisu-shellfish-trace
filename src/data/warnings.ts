import type { AlertInfo, MonitorData, DisasterRecord } from '../types'

// 实时监测数据
export const monitorData: MonitorData[] = [
  {
    flatId: '1',
    flatName: '丹东东港1号滩涂',
    waterQuality: { temperature: 3.2, salinity: 32.5, oxygen: 5.8, ph: 7.8, tide: 185 },
    alertLevel: 'red',
    updatedAt: '2026-01-15 08:30'
  },
  {
    flatId: '2',
    flatName: '盘锦大洼2号滩涂',
    waterQuality: { temperature: 5.1, salinity: 29.8, oxygen: 6.5, ph: 8.1, tide: 210 },
    alertLevel: 'orange',
    updatedAt: '2026-01-15 08:25'
  },
  {
    flatId: '3',
    flatName: '大连庄河3号滩涂',
    waterQuality: { temperature: 7.8, salinity: 31.2, oxygen: 7.2, ph: 8.0, tide: 195 },
    alertLevel: 'normal',
    updatedAt: '2026-01-15 08:20'
  },
  {
    flatId: '4',
    flatName: '葫芦岛绥中4号滩涂',
    waterQuality: { temperature: 4.5, salinity: 33.1, oxygen: 6.0, ph: 7.9, tide: 178 },
    alertLevel: 'blue',
    updatedAt: '2026-01-15 08:15'
  }
]

// 当前活跃预警
export const activeAlerts: AlertInfo[] = [
  {
    id: 'a1',
    level: 'red',
    title: '红色紧急：水温骤降至3.2℃',
    description: '丹东东港1号滩涂水温低于贝类存活临界值4℃，需立即采取保温措施',
    indicators: [
      { name: '水温', value: 3.2, threshold: 4.0, unit: '℃' },
      { name: '溶解氧', value: 5.8, threshold: 6.0, unit: 'mg/L' }
    ],
    solution: [
      '立即启动保温棚覆盖，提高水温2-3℃',
      '开启增氧机，提高溶解氧至6mg/L以上',
      '暂停投喂，减少贝类代谢消耗',
      '蓄水加深水位至1.5米以上，利用地热保温'
    ],
    createdAt: '2026-01-15 06:00',
    status: 'active',
    flatName: '丹东东港1号滩涂'
  },
  {
    id: 'a2',
    level: 'orange',
    title: '橙色风险：盐度异常偏高',
    description: '盘锦大洼2号滩涂盐度达29.8‰，超出适宜范围，影响贝类渗透压调节',
    indicators: [
      { name: '盐度', value: 29.8, threshold: 28.0, unit: '‰' }
    ],
    solution: [
      '引入淡水调节盐度至25-28‰',
      '检查进排水系统是否正常',
      '增加换水频率，每日换水30%'
    ],
    createdAt: '2026-01-15 07:30',
    status: 'active',
    flatName: '盘锦大洼2号滩涂'
  },
  {
    id: 'a3',
    level: 'blue',
    title: '蓝色提醒：溶解氧偏低',
    description: '葫芦岛绥中4号滩涂溶解氧6.0mg/L，接近预警阈值',
    indicators: [
      { name: '溶解氧', value: 6.0, threshold: 6.0, unit: 'mg/L' }
    ],
    solution: [
      '建议开启增氧设备',
      '关注天气变化，阴雨天提前增氧',
      '适当减少投喂量'
    ],
    createdAt: '2026-01-15 08:00',
    status: 'active',
    flatName: '葫芦岛绥中4号滩涂'
  }
]

// 灾害历史记录（近3年）
export const disasterHistory: DisasterRecord[] = [
  { id: 'd1', date: '2025-12-20', type: '寒潮', level: 'red', description: '强寒潮侵袭，水温骤降至2.1℃', loss: '减产35%，损失约8万元', flatName: '丹东东港1号滩涂', review: '保温措施启动过晚，应提前24小时覆盖保温棚' },
  { id: 'd2', date: '2025-11-05', type: '盐度骤变', level: 'orange', description: '暴雨导致盐度从32‰降至18‰', loss: '减产15%，损失约3万元', flatName: '盘锦大洼2号滩涂', review: '排水系统不畅，需改造进排水渠道' },
  { id: 'd3', date: '2025-02-10', type: '低温', level: 'red', description: '持续低温-5℃达7天', loss: '越冬贝类死亡率40%', flatName: '大连庄河3号滩涂', review: '越冬前应加深水位并铺设保温材料' },
  { id: 'd4', date: '2024-12-15', type: '寒潮', level: 'orange', description: '寒潮伴随大风，水温降至3.5℃', loss: '减产20%，损失约5万元', flatName: '丹东东港1号滩涂', review: '防风设施不足，需加固防风网' },
  { id: 'd5', date: '2024-08-20', type: '赤潮', level: 'red', description: '赤潮导致溶解氧骤降', loss: '减产25%，损失约6万元', flatName: '葫芦岛绥中4号滩涂', review: '应建立赤潮预警监测机制' },
  { id: 'd6', date: '2024-01-08', type: '冰封', level: 'red', description: '滩涂结冰达15天', loss: '贝类缺氧死亡30%', flatName: '盘锦大洼2号滩涂', review: '冰封期需破冰增氧' },
  { id: 'd7', date: '2023-12-25', type: '寒潮', level: 'red', description: '十年一遇强寒潮，水温1.8℃', loss: '减产50%，损失约12万元', flatName: '丹东东港1号滩涂', review: '极端天气需提前48小时启动应急预案' },
  { id: 'd8', date: '2023-07-15', type: '高温', level: 'orange', description: '水温持续32℃以上', loss: '减产10%', flatName: '大连庄河3号滩涂', review: '高温期需加深水位并增加换水' },
  { id: 'd9', date: '2023-03-01', type: '盐度骤变', level: 'orange', description: '融雪导致盐度从30‰降至20‰', loss: '减产18%', flatName: '葫芦岛绥中4号滩涂', review: '春季融雪期需密切监测盐度变化' },
  { id: 'd10', date: '2025-06-12', type: '暴雨', level: 'blue', description: '连续暴雨3天，盐度降至22‰', loss: '轻微减产5%', flatName: '大连庄河3号滩涂', review: '及时换水调节，损失较小' }
]
