import React from 'react'
import { View, Text } from '@tarojs/components'
import Taro, { useRouter } from '@tarojs/taro'
import classnames from 'classnames'
import styles from './index.module.scss'
import { activeAlerts } from '../../data/warnings'

const WarningDetailPage: React.FC = () => {
  const router = useRouter()
  const alertId = router.params.id
  const alert = activeAlerts.find(a => a.id === alertId) || activeAlerts[0]

  const getLevelBadge = (level: string) => {
    const map: Record<string, string> = {
      red: styles.badgeRed, orange: styles.badgeOrange, blue: styles.badgeBlue
    }
    return map[level] || styles.badgeBlue
  }

  const getLevelText = (level: string) => {
    const map: Record<string, string> = { red: '🔴 红色紧急', orange: '🟠 橙色风险', blue: '🔵 蓝色提醒' }
    return map[level] || ''
  }

  return (
    <View className={styles.detailPage}>
      <View className={styles.header}>
        <View className={classnames(styles.levelBadge, getLevelBadge(alert.level))}>
          <Text>{getLevelText(alert.level)}</Text>
        </View>
        <View className={styles.detailTitle}>{alert.title}</View>
        <View className={styles.detailMeta}>📍 {alert.flatName} · 📅 {alert.createdAt}</View>
      </View>

      <View className={styles.section}>
        <View className={styles.card}>
          <View className={styles.cardTitle}>📋 预警描述</View>
          <View className={styles.descText}>{alert.description}</View>
        </View>
      </View>

      <View className={styles.section}>
        <View className={styles.card}>
          <View className={styles.cardTitle}>📊 异常指标</View>
          {alert.indicators.map((ind, idx) => (
            <View key={idx} className={styles.indicatorRow}>
              <Text className={styles.indicatorName}>{ind.name}（阈值{ind.threshold}{ind.unit}）</Text>
              <Text className={styles.indicatorVal}>{ind.value}{ind.unit}</Text>
            </View>
          ))}
        </View>
      </View>

      <View className={styles.section}>
        <View className={styles.card}>
          <View className={styles.solutionBox}>
            <View className={styles.solutionTitle}>🛠️ 辽宁滩涂专属处置方案</View>
            {alert.solution.map((s, idx) => (
              <View key={idx} className={styles.solutionItem}>
                <Text className={styles.solutionNum}>{idx + 1}.</Text>
                <Text>{s}</Text>
              </View>
            ))}
          </View>
        </View>
      </View>

      <View className={styles.section}>
        <View className={styles.card}>
          <View className={styles.cardTitle}>📢 通知渠道</View>
          <View className={styles.notifyList}>
            <Text className={styles.notifyItem}>✅ 小程序弹窗</Text>
            <Text className={styles.notifyItem}>✅ 微信服务号</Text>
            <Text className={styles.notifyItem}>✅ 短信通知</Text>
          </View>
        </View>
      </View>
    </View>
  )
}

export default WarningDetailPage
