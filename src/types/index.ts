// ============================================
// 类型定义 - 滩智溯养殖户小程序
// ============================================

// 预警等级
export type AlertLevel = 'blue' | 'orange' | 'red'

// 预警状态
export type AlertStatus = 'active' | 'resolved'

// 水质指标
export interface WaterQuality {
  temperature: number  // 水温 ℃
  salinity: number     // 盐度 ‰
  oxygen: number       // 溶解氧 mg/L
  ph: number           // pH
  tide: number         // 潮汐 cm
}

// 预警信息
export interface AlertInfo {
  id: string
  level: AlertLevel
  title: string
  description: string
  indicators: { name: string; value: number; threshold: number; unit: string }[]
  solution: string[]
  createdAt: string
  status: AlertStatus
  flatName: string
}

// 实时监测数据
export interface MonitorData {
  flatId: string
  flatName: string
  waterQuality: WaterQuality
  alertLevel: AlertLevel | 'normal'
  updatedAt: string
}

// 台账记录类型
export type LedgerType = 'seedling' | '投放' | '消杀' | '捕捞' | '水质自检'

// 台账记录
export interface LedgerRecord {
  id: string
  type: LedgerType
  flatName: string
  date: string
  content: string
  operator: string
  status: 'pending' | 'completed'
  details?: Record<string, string>
}

// 知识文章
export interface KnowledgeArticle {
  id: string
  category: string
  title: string
  summary: string
  content: string
  author: string
  views: number
  isFeatured: boolean
  hasVideo: boolean
  region: string
  createdAt: string
}

// 产销信息
export interface TradeItem {
  id: string
  type: 'supply' | 'demand'
  product: string
  quantity: number
  unit: string
  price: number
  date: string
  publisher: string
  phone: string
  region: string
  status: 'active' | 'closed'
}

// 溯源记录
export interface TraceRecord {
  id: string
  batchCode: string
  product: string
  flatName: string
  farmer: string
  harvestDate: string
  qualityCheck: string
  qrCodeUrl: string
  createdAt: string
}

// 灾害历史记录
export interface DisasterRecord {
  id: string
  date: string
  type: string
  level: AlertLevel
  description: string
  loss: string
  flatName: string
  review: string
}

// 专家问诊
export interface ConsultMessage {
  id: string
  role: 'user' | 'expert'
  content: string
  createdAt: string
}

// 快捷功能入口
export interface QuickEntry {
  id: string
  title: string
  icon: string
  path: string
  color: string
}
