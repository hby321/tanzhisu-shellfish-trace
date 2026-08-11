import React from 'react'
import { View, Text } from '@tarojs/components'
import Taro, { useRouter } from '@tarojs/taro'
import classnames from 'classnames'
import styles from './index.module.scss'
import { ledgerRecords } from '../../data/ledger'
import type { LedgerType } from '../../types'

const typeConfig: Record<string, { icon: string; color: string; label: string }> = {
  seedling: { icon: '🌱', color: '#00b42a', label: '苗种记录' },
  '投放': { icon: '🐟', color: '#0866c4', label: '投放记录' },
  '消杀': { icon: '🧴', color: '#f53f3f', label: '消杀记录' },
  '捕捞': { icon: '🎣', color: '#ff7d00', label: '捕捞记录' },
  '水质自检': { icon: '💧', color: '#165dff', label: '水质检测' }
}

const LedgerDetailPage: React.FC = () => {
  const router = useRouter()
  const recordId = router.params.id
  const record = ledgerRecords.find(r => r.id === recordId) || ledgerRecords[0]
  const cfg = typeConfig[record.type] || typeConfig['投放']

  const handlePdf = () => {
    Taro.showToast({ title: 'PDF生成中...', icon: 'loading', duration: 2000 })
    setTimeout(() => Taro.showToast({ title: 'PDF已生成', icon: 'success' }), 2000)
  }

  return (
    <View className={styles.detailPage}>
      <View className={styles.header}>
        <View className={styles.typeRow}>
          <View className={styles.typeIcon} style={{ background: cfg.color + '15' }}>
            <Text>{cfg.icon}</Text>
          </View>
          <Text className={styles.typeName}>{cfg.label}</Text>
        </View>
        <View className={styles.contentTitle}>{record.content}</View>
        <Text className={classnames(styles.statusTag, record.status === 'completed' ? styles.statusDone : styles.statusPending)}>
          {record.status === 'completed' ? '✅ 已完成' : '⏳ 待处理'}
        </Text>
        <View className={styles.metaRow}>
          <Text>📍 {record.flatName}</Text>
          <Text>📅 {record.date}</Text>
          <Text>👤 {record.operator}</Text>
        </View>
      </View>

      {record.details && (
        <View className={styles.section}>
          <View className={styles.sectionTitle}>详细信息</View>
          <View className={styles.card}>
            {Object.entries(record.details).map(([key, value]) => (
              <View key={key} className={styles.detailRow}>
                <Text className={styles.detailLabel}>{key}</Text>
                <Text className={styles.detailValue}>{value}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      <View className={styles.bottomBtn}>
        <View className={`${styles.btn} ${styles.btnEdit}`} onClick={() => Taro.showToast({ title: '编辑功能开发中', icon: 'none' })}>编辑</View>
        <View className={`${styles.btn} ${styles.btnPdf}`} onClick={handlePdf}>生成PDF</View>
      </View>
    </View>
  )
}

export default LedgerDetailPage
