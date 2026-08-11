import type { TradeItem } from '../types'

export const tradeItems: TradeItem[] = [
  { id: 't1', type: 'supply', product: '菲律宾蛤仔', quantity: 2000, unit: '斤', price: 8.5, date: '2026-01-20', publisher: '王建国', phone: '138****5678', region: '丹东东港', status: 'active' },
  { id: 't2', type: 'demand', product: '大连湾牡蛎', quantity: 5000, unit: '斤', price: 12.0, date: '2026-01-18', publisher: '大连海鲜预制菜厂', phone: '139****1234', region: '大连', status: 'active' },
  { id: 't3', type: 'supply', product: '虾夷扇贝', quantity: 800, unit: '斤', price: 35.0, date: '2026-01-22', publisher: '陈立志', phone: '137****8888', region: '葫芦岛绥中', status: 'active' },
  { id: 't4', type: 'demand', product: '文蛤', quantity: 3000, unit: '斤', price: 15.0, date: '2026-01-19', publisher: '盘锦商超采购中心', phone: '136****6666', region: '盘锦', status: 'active' },
  { id: 't5', type: 'supply', product: '大连湾牡蛎', quantity: 1500, unit: '斤', price: 11.5, date: '2026-01-15', publisher: '刘德海', phone: '135****3333', region: '大连庄河', status: 'closed' },
  { id: 't6', type: 'demand', product: '菲律宾蛤仔', quantity: 10000, unit: '斤', price: 9.0, date: '2026-01-25', publisher: '沈阳海鲜批发市场', phone: '138****9999', region: '沈阳', status: 'active' },
  { id: 't7', type: 'supply', product: '文蛤', quantity: 800, unit: '斤', price: 14.5, date: '2026-01-12', publisher: '张大海', phone: '139****0000', region: '盘锦大洼', status: 'closed' },
  { id: 't8', type: 'demand', product: '虾夷扇贝', quantity: 2000, unit: '斤', price: 38.0, date: '2026-01-28', publisher: '营口海鲜加工厂', phone: '137****5555', region: '营口', status: 'active' },
  { id: 't9', type: 'supply', product: '杂色蛤', quantity: 3000, unit: '斤', price: 7.5, date: '2026-02-01', publisher: '孙有财', phone: '136****7777', region: '丹东东港', status: 'active' },
  { id: 't10', type: 'demand', product: '牡蛎', quantity: 8000, unit: '斤', price: 13.0, date: '2026-02-05', publisher: '北京京深海鲜市场', phone: '135****2222', region: '北京', status: 'active' }
]
