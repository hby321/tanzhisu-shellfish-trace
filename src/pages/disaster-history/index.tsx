import React, { useState } from 'react'
import { View, Text, ScrollView } from '@tarojs/components'
import classnames from 'classnames'
import styles from './index.module.scss'
import { disasterHistory } from '../../data/warnings'

const DisasterHistoryPage: React.FC = () => {
  const [activeYear, setActiveYear] = useState('全部')
  const years = ['全部', '2025', '2024', '2023']

  const filtered = activeYear === '全部'
    ? disasterHistory
    : disasterHistory.filter(d => d.date.startsWith(activeYear))

  const getLevelTag = (level: string) => {
    const map: Record<string, string> = { blue: styles.tagBlue, orange: styles.tagOrange, red: styles.tagRed }
    return map[level] || styles.tagBlue
  }

  const getLevelText = (level: string) => {
    const map: Record<string, string> = { blue: '蓝色提醒', orange: '橙色风险', red: '红色紧急' }
    return map[level] || ''
  }

  return (
    <View className={styles.disasterPage}>
      <View className={styles.yearTabs}>
        {years.map(y => (
          <Text
            key={y}
            className={classnames(styles.yearTab, activeYear === y && styles.yearTabActive)}
            onClick={() => setActiveYear(y)}
          >{y === '全部' ? '全部' : `${y}年`}</Text>
        ))}
      </View>

      <View className={styles.section}>
        <View style={{ fontSize: '$font-size-lg', fontWeight: 600, color: '$color-text-primary', marginBottom: '$spacing-sm' }}>
          灾害记录（近3年）
        </View>
        {filtered.map(record => (
          <View key={record.id} className={styles.card}>
            <View className={styles.cardHeader}>
              <Text className={styles.cardDate}>{record.date}</Text>
              <Text className={classnames(styles.levelTag, getLevelTag(record.level))}>{getLevelText(record.level)}</Text>
            </View>
            <Text className={styles.cardType}>{record.type} · {record.flatName}</Text>
            <View className={styles.cardDesc}>{record.description}</View>
            <View className={styles.cardLoss}>📉 {record.loss}</View>
            <View className={styles.cardReview}>
              <View className={styles.reviewTitle}>📋 减产复盘</View>
              <View className={styles.reviewText}>{record.review}</View>
            </View>
          </View>
        ))}
      </View>
    </View>
  )
}

export default DisasterHistoryPage
