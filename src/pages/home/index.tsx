import React, { useState, useEffect } from 'react'
import { View, Text, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import classnames from 'classnames'
import styles from './index.module.scss'
import { monitorData, activeAlerts } from '../../data/warnings'
import { ledgerRecords } from '../../data/ledger'
import type { QuickEntry } from '../../types'

import { AI_BACKEND } from '../../config/api'

const quickEntries: QuickEntry[] = [
  { id: '1', title: '养殖台账', icon: '📝', path: '/pages/ledger/index', color: '#0866c4' },
  { id: '2', title: '溯源码', icon: '🔗', path: '/pages/traceability/index', color: '#00b8a9' },
  { id: '3', title: '产销撮合', icon: '🏪', path: '/pages/trade/index', color: '#ff7d00' },
  { id: '4', title: '农技知识', icon: '📚', path: '/pages/knowledge/index', color: '#722ed1' },
  { id: '5', title: '灾害历史', icon: '📅', path: '/pages/disaster-history/index', color: '#f53f3f' },
  { id: '6', title: '专家问诊', icon: '👨‍⚕️', path: '/pages/expert/index', color: '#eb2f96' },
  { id: '7', title: '预警详情', icon: '⚠️', path: '/pages/warning/index', color: '#faad14' },
  { id: '8', title: 'PDF台账', icon: '📄', path: '/pages/ledger/index', color: '#52c41a' }
]

const HomePage: React.FC = () => {
  const [topAlert] = activeAlerts
  const [aiPlan, setAiPlan] = useState<string>('')
  const [aiLoading, setAiLoading] = useState(false)
  const [recentActivities] = useState(
    ledgerRecords.slice(0, 4).map(r => ({
      title: `${r.flatName} - ${r.content}`,
      time: r.date,
      color: r.type === '水质自检' ? '#165dff' : r.type === '捕捞' ? '#00b42a' : r.type === '消杀' ? '#f53f3f' : '#ff7d00'
    }))
  )

  const getLevelText = (level: string) => {
    const map: Record<string, string> = { normal: '正常', blue: '蓝色提醒', orange: '橙色风险', red: '红色紧急' }
    return map[level] || '正常'
  }

  const getLevelClass = (level: string) => {
    const map: Record<string, string> = {
      normal: styles.statusNormal, blue: styles.statusBlue,
      orange: styles.statusOrange, red: styles.statusRed
    }
    return map[level] || styles.statusNormal
  }

  const handleQuickEntry = (path: string) => {
    Taro.navigateTo({ url: path }).catch(() => {
      Taro.switchTab({ url: path })
    })
  }

  const handleAlertClick = () => {
    if (topAlert) {
      Taro.navigateTo({ url: `/pages/warning-detail/index?id=${topAlert.id}` })
    }
  }

  // 红色预警触发：调用软著平台-水质风险研判智能体，推送应急处理方案
  const handleAiEmergency = async () => {
    if (aiLoading) return
    setAiLoading(true)
    setAiPlan('🔍 AI智能体研判中...')
    try {
      // 取首个监测滩涂的水质作为研判输入
      const m = monitorData[0] || { flatName: '东港1号滩涂', waterQuality: { temperature: 3, salinity: 32, oxygen: 3.2, ph: 7.6 } }
      const res = await Taro.request({
        url: `${AI_BACKEND}/ai/api/mini-water-risk`,
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: {
          flat_name: m.flatName,
          temperature: m.waterQuality.temperature,
          salinity: m.waterQuality.salinity,
          oxygen: m.waterQuality.oxygen,
          ph: m.waterQuality.ph
        }
      })
      const data = res.data
      if (data.success && data.ai_reply) {
        const r = data.ai_reply
        setAiPlan(`【${r['风险等级']}】${r['处置方案']}`)
      } else {
        setAiPlan(`⚠️ ${data.message || '智能体平台未启动(8090)'}`)
      }
    } catch (err) {
      setAiPlan('⚠️ AI智能体平台未启动或网络异常')
    }
    setAiLoading(false)
  }

  return (
    <View className={styles.homePage}>
      {/* 顶部区域 */}
      <View className={styles.header}>
        <View className={styles.headerTop}>
          <View className={styles.location}>
            <Text>📍 丹东·东港</Text>
          </View>
          <View className={styles.weather}>
            <Text>🌡️ -3℃ | 多云转晴</Text>
          </View>
        </View>
        <View className={styles.greeting}>你好，王建国</View>
        <View className={styles.subGreeting}>今日有1条紧急预警，请及时处理</View>
      </View>

      {/* 预警横幅 */}
      {topAlert && (
        <View className={styles.alertBanner}>
          <View style={{ flex: 1, display: 'flex', alignItems: 'center' }} onClick={handleAlertClick}>
            <Text className={styles.alertIcon}>🚨</Text>
            <View className={styles.alertContent}>
              <View className={styles.alertTitle}>{topAlert.title}</View>
              <View className={styles.alertDesc}>{topAlert.description}</View>
            </View>
            <Text style={{ color: '#fff', fontSize: '24rpx' }}>查看 ›</Text>
          </View>
          {/* AI应急方案按钮 - 软著平台风险研判智能体 */}
          <View
            style={{ marginTop: '12rpx', padding: '10rpx 20rpx', background: 'rgba(255,255,255,0.25)', borderRadius: '32rpx', alignSelf: 'flex-start', display: 'flex', alignItems: 'center' }}
            onClick={(e) => { e.stopPropagation(); handleAiEmergency() }}
          >
            <Text style={{ color: '#fff', fontSize: '22rpx' }}>🤖 AI应急方案（软著）</Text>
          </View>
        </View>
      )}

      {/* AI应急方案展示 */}
      {aiPlan && (
        <View style={{ margin: '16rpx', padding: '20rpx', background: '#fff', borderRadius: '16rpx', borderLeft: '6rpx solid #722ed1', boxShadow: '0 4rpx 12rpx rgba(0,0,0,0.08)' }}>
          <View style={{ display: 'flex', alignItems: 'center', marginBottom: '8rpx' }}>
            <Text style={{ fontSize: '24rpx', color: '#722ed1', fontWeight: 'bold' }}>🤖 AI风险研判智能体 · 应急方案</Text>
            <Text style={{ fontSize: '20rpx', color: '#999', marginLeft: '12rpx' }}>数据智能体综合应用平台V1.0</Text>
          </View>
          <Text style={{ fontSize: '24rpx', color: '#333', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>{aiPlan}</Text>
        </View>
      )}

      {/* 水质指标概览 */}
      <View className={styles.section}>
        <View className={styles.sectionTitle}>
          <Text>实时水质指标</Text>
          <Text className={styles.sectionMore}>更新于 08:30 ›</Text>
        </View>
        <View className={styles.indicatorGrid}>
          {[
            { name: '水温', value: '3.2', unit: '℃' },
            { name: '盐度', value: '32.5', unit: '‰' },
            { name: '溶氧', value: '5.8', unit: 'mg/L' },
            { name: 'pH', value: '7.8', unit: '' },
            { name: '潮汐', value: '185', unit: 'cm' }
          ].map(item => (
            <View key={item.name} className={styles.indicatorCard}>
              <View className={styles.indicatorValue}>{item.value}</View>
              <View className={styles.indicatorName}>{item.name}</View>
              <View className={styles.indicatorUnit}>{item.unit}</View>
            </View>
          ))}
        </View>
      </View>

      {/* 快捷入口 */}
      <View className={styles.section}>
        <View className={styles.quickGrid}>
          {quickEntries.map(entry => (
            <View
              key={entry.id}
              className={styles.quickItem}
              onClick={() => handleQuickEntry(entry.path)}
            >
              <View className={styles.quickIcon} style={{ background: entry.color }}>
                <Text>{entry.icon}</Text>
              </View>
              <Text className={styles.quickLabel}>{entry.title}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* 滩涂监测 */}
      <View className={styles.section}>
        <View className={styles.sectionTitle}>
          <Text>我的滩涂</Text>
          <Text className={styles.sectionMore}>全部 ›</Text>
        </View>
        {monitorData.map(item => (
          <View key={item.flatId} className={styles.flatCard}>
            <View className={styles.flatHeader}>
              <Text className={styles.flatName}>{item.flatName}</Text>
              <Text className={classnames(styles.flatStatus, getLevelClass(item.alertLevel))}>
                {getLevelText(item.alertLevel)}
              </Text>
            </View>
            <View className={styles.flatIndicators}>
              <View className={styles.flatIndicator}>
                <View className={styles.flatIndicatorValue}>{item.waterQuality.temperature}℃</View>
                <View className={styles.flatIndicatorLabel}>水温</View>
              </View>
              <View className={styles.flatIndicator}>
                <View className={styles.flatIndicatorValue}>{item.waterQuality.salinity}‰</View>
                <View className={styles.flatIndicatorLabel}>盐度</View>
              </View>
              <View className={styles.flatIndicator}>
                <View className={styles.flatIndicatorValue}>{item.waterQuality.oxygen}</View>
                <View className={styles.flatIndicatorLabel}>溶氧</View>
              </View>
              <View className={styles.flatIndicator}>
                <View className={styles.flatIndicatorValue}>{item.waterQuality.ph}</View>
                <View className={styles.flatIndicatorLabel}>pH</View>
              </View>
              <View className={styles.flatIndicator}>
                <View className={styles.flatIndicatorValue}>{item.waterQuality.tide}cm</View>
                <View className={styles.flatIndicatorLabel}>潮汐</View>
              </View>
            </View>
            <View className={styles.flatTime}>更新于 {item.updatedAt}</View>
          </View>
        ))}
      </View>

      {/* 最近活动 */}
      <View className={styles.section}>
        <View className={styles.sectionTitle}>
          <Text>最近活动</Text>
          <Text className={styles.sectionMore}>更多 ›</Text>
        </View>
        {recentActivities.map((activity, idx) => (
          <View key={idx} className={styles.activityCard}>
            <View className={styles.activityDot} style={{ background: activity.color }} />
            <View className={styles.activityContent}>
              <View className={styles.activityTitle}>{activity.title}</View>
              <View className={styles.activityTime}>{activity.time}</View>
            </View>
          </View>
        ))}
      </View>
    </View>
  )
}

export default HomePage
