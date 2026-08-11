import React from 'react'
import { View, Text, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import classnames from 'classnames'
import styles from './index.module.scss'
import { monitorData, activeAlerts } from '../../data/warnings'

const WarningPage: React.FC = () => {
  const blueCount = activeAlerts.filter(a => a.level === 'blue').length
  const orangeCount = activeAlerts.filter(a => a.level === 'orange').length
  const redCount = activeAlerts.filter(a => a.level === 'red').length

  const getLevelIcon = (level: string) => {
    const map: Record<string, string> = { blue: '🔵', orange: '🟠', red: '🔴' }
    return map[level] || '✅'
  }

  const getLevelBg = (level: string) => {
    const map: Record<string, string> = {
      blue: styles.levelBlueBg, orange: styles.levelOrangeBg, red: styles.levelRedBg
    }
    return map[level] || styles.levelBlueBg
  }

  const getLevelTag = (level: string) => {
    const map: Record<string, string> = {
      blue: styles.tagBlue, orange: styles.tagOrange, red: styles.tagRed
    }
    return map[level] || styles.tagBlue
  }

  const getLevelText = (level: string) => {
    const map: Record<string, string> = { blue: '蓝色提醒', orange: '橙色风险', red: '红色紧急' }
    return map[level] || ''
  }

  const handleAlertClick = (id: string) => {
    Taro.navigateTo({ url: `/pages/warning-detail/index?id=${id}` })
  }

  return (
    <View className={styles.warningPage}>
      {/* 预警统计 */}
      <View className={styles.statsRow}>
        <View className={classnames(styles.statBox, styles.statBlue)}>
          <View className={styles.statNum}>{blueCount}</View>
          <View className={styles.statLabel}>蓝色提醒</View>
        </View>
        <View className={classnames(styles.statBox, styles.statOrange)}>
          <View className={styles.statNum}>{orangeCount}</View>
          <View className={styles.statLabel}>橙色风险</View>
        </View>
        <View className={classnames(styles.statBox, styles.statRed)}>
          <View className={styles.statNum}>{redCount}</View>
          <View className={styles.statLabel}>红色紧急</View>
        </View>
      </View>

      {/* 通知渠道 */}
      <View className={styles.notifyBar}>
        <Text className={styles.notifyIcon}>🔔</Text>
        <Text className={styles.notifyText}>三重推送：小程序弹窗 + 微信服务号 + 短信</Text>
        <Text className={styles.notifyBadge}>已开启</Text>
      </View>

      {/* 活跃预警 */}
      <View className={styles.section}>
        <View className={styles.sectionTitle}>活跃预警 ({activeAlerts.length})</View>
        {activeAlerts.map(alert => (
          <View key={alert.id} className={styles.alertCard} onClick={() => handleAlertClick(alert.id)}>
            <View className={styles.alertHeader}>
              <View className={classnames(styles.alertLevelIcon, getLevelBg(alert.level))}>
                <Text>{getLevelIcon(alert.level)}</Text>
              </View>
              <View className={styles.alertInfo}>
                <View className={styles.alertTitle}>{alert.title}</View>
                <View className={styles.alertMeta}>{alert.flatName} · {alert.createdAt}</View>
              </View>
              <Text className={classnames(styles.alertLevelTag, getLevelTag(alert.level))}>
                {getLevelText(alert.level)}
              </Text>
            </View>
            <View className={styles.alertBody}>
              <View className={styles.alertDesc}>{alert.description}</View>
              <View className={styles.alertIndicators}>
                {alert.indicators.map((ind, idx) => (
                  <Text key={idx} className={styles.indicatorTag}>
                    {ind.name}: {ind.value}{ind.unit} (阈值{ind.threshold}{ind.unit})
                  </Text>
                ))}
              </View>
              {/* 处置方案 */}
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
        ))}
      </View>

      {/* 实时水质监测 */}
      <View className={styles.section}>
        <View className={styles.sectionTitle}>实时水质监测</View>
        {monitorData.map(item => (
          <View key={item.flatId} className={styles.monitorCard}>
            <View className={styles.monitorHeader}>
              <Text className={styles.monitorName}>{item.flatName}</Text>
              <Text style={{ fontSize: '20rpx', color: '$color-text-tertiary' }}>{item.updatedAt}</Text>
            </View>
            <View className={styles.monitorGrid}>
              <View className={styles.monitorItem}>
                <View className={styles.monitorValue}>{item.waterQuality.temperature}℃</View>
                <View className={styles.monitorLabel}>水温</View>
              </View>
              <View className={styles.monitorItem}>
                <View className={styles.monitorValue}>{item.waterQuality.salinity}‰</View>
                <View className={styles.monitorLabel}>盐度</View>
              </View>
              <View className={styles.monitorItem}>
                <View className={styles.monitorValue}>{item.waterQuality.oxygen}</View>
                <View className={styles.monitorLabel}>溶氧</View>
              </View>
              <View className={styles.monitorItem}>
                <View className={styles.monitorValue}>{item.waterQuality.ph}</View>
                <View className={styles.monitorLabel}>pH</View>
              </View>
              <View className={styles.monitorItem}>
                <View className={styles.monitorValue}>{item.waterQuality.tide}cm</View>
                <View className={styles.monitorLabel}>潮汐</View>
              </View>
            </View>
          </View>
        ))}
      </View>
    </View>
  )
}

export default WarningPage
