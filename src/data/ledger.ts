import type { LedgerRecord } from '../types'

export const ledgerRecords: LedgerRecord[] = [
  { id: 'l1', type: 'seedling', flatName: '丹东东港1号滩涂', date: '2026-01-10', content: '投放菲律宾蛤仔苗种2000斤', operator: '王建国', status: 'completed', details: { '苗种来源': '山东威海育苗场', '规格': '400粒/斤', '单价': '8.5元/斤', '总金额': '17000元' } },
  { id: 'l2', type: '水质自检', flatName: '丹东东港1号滩涂', date: '2026-01-12', content: '常规水质检测', operator: '李秀兰', status: 'completed', details: { '水温': '5.2℃', '盐度': '31.5‰', '溶解氧': '7.2mg/L', 'pH': '8.0' } },
  { id: 'l3', type: '消杀', flatName: '盘锦大洼2号滩涂', date: '2026-01-08', content: '生石灰全池消杀', operator: '张大海', status: 'completed', details: { '用药名称': '生石灰', '用量': '50kg/亩', '用药原因': '预防寄生虫' } },
  { id: 'l4', type: '投放', flatName: '盘锦大洼2号滩涂', date: '2026-01-05', content: '补充投喂人工饵料', operator: '张大海', status: 'completed', details: { '饵料类型': '配合饲料', '投喂量': '30斤', '投喂时间': '上午9点' } },
  { id: 'l5', type: '捕捞', flatName: '大连庄河3号滩涂', date: '2025-12-28', content: '冬季采捕牡蛎1500斤', operator: '刘德海', status: 'completed', details: { '品种': '大连湾牡蛎', '产量': '1500斤', '销售单价': '12元/斤', '销售总额': '18000元' } },
  { id: 'l6', type: '水质自检', flatName: '大连庄河3号滩涂', date: '2026-01-14', content: '寒潮前水质检测', operator: '刘德海', status: 'completed', details: { '水温': '7.8℃', '盐度': '31.2‰', '溶解氧': '7.2mg/L', 'pH': '8.0' } },
  { id: 'l7', type: 'seedling', flatName: '葫芦岛绥中4号滩涂', date: '2025-12-20', content: '投放虾夷扇贝苗种500笼', operator: '陈立志', status: 'completed', details: { '苗种来源': '大连旅顺育苗场', '规格': '3cm', '单价': '1.2元/粒', '总金额': '15000元' } },
  { id: 'l8', type: '消杀', flatName: '丹东东港1号滩涂', date: '2026-01-03', content: '漂白粉消毒进水渠道', operator: '王建国', status: 'completed', details: { '用药名称': '漂白粉', '用量': '10ppm', '用药原因': '渠道消毒' } },
  { id: 'l9', type: '捕捞', flatName: '盘锦大洼2号滩涂', date: '2025-12-15', content: '采捕文蛤800斤', operator: '张大海', status: 'completed', details: { '品种': '文蛤', '产量': '800斤', '销售单价': '15元/斤', '销售总额': '12000元' } },
  { id: 'l10', type: '水质自检', flatName: '葫芦岛绥中4号滩涂', date: '2026-01-13', content: '日常水质监测', operator: '陈立志', status: 'pending', details: { '水温': '4.5℃', '盐度': '33.1‰', '溶解氧': '6.0mg/L', 'pH': '7.9' } }
]
