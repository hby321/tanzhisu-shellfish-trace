import React, { useState } from 'react'
import { View, Text, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import classnames from 'classnames'
import styles from './index.module.scss'
import { ledgerRecords } from '../../data/ledger'
import type { LedgerType } from '../../types'

const typeConfig: Record<string, { icon: string; color: string; label: string }> = {
  seedling: { icon: '🌱', color: '#00b42a', label: '苗种' },
  '投放': { icon: '🐟', color: '#0866c4', label: '投放' },
  '消杀': { icon: '🧴', color: '#f53f3f', label: '消杀' },
  '捕捞': { icon: '🎣', color: '#ff7d00', label: '捕捞' },
  '水质自检': { icon: '💧', color: '#165dff', label: '水质' }
}

const LedgerPage: React.FC = () => {
  const [activeFilter, setActiveFilter] = useState<string>('all')
  const [records, setRecords] = useState(ledgerRecords)

  const filteredRecords = activeFilter === 'all'
    ? records
    : records.filter(r => r.type === activeFilter)

  const handleRecordClick = (id: string) => {
    Taro.navigateTo({ url: `/pages/ledger-detail/index?id=${id}` })
  }

  const handlePdfGenerate = () => {
    Taro.showToast({ title: 'PDF台账生成中...', icon: 'loading', duration: 2000 })
    setTimeout(() => {
      Taro.showToast({ title: 'PDF已生成，可下载打印', icon: 'success' })
    }, 2000)
  }

  const handleQuickAdd = (type: string) => {
    Taro.showToast({ title: `录入${type}记录`, icon: 'none' })
  }

  return (
    <View className={styles.ledgerPage}>
      {/* 快捷录入 */}
      <View className={styles.quickSection}>
        <View className={styles.quickTitle}>一键录入</View>
        <View className={styles.quickGrid}>
          {Object.entries(typeConfig).map(([key, cfg]) => (
            <View key={key} className={styles.quickBtn} onClick={() => handleQuickAdd(cfg.label)}>
              <View className={styles.quickBtnIcon} style={{ background: cfg.color + '15' }}>
                <Text>{cfg.icon}</Text>
              </View>
              <Text className={styles.quickBtnLabel}>{cfg.label}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* PDF生成 */}
      <View className={styles.pdfBar} onClick={handlePdfGenerate}>
        <Text className={styles.pdfIcon}>📄</Text>
        <View className={styles.pdfText}>
          <View className={styles.pdfTitle}>生成PDF合规台账</View>
          <View className={styles.pdfDesc}>自动汇总记录，可下载打印提交渔业局</View>
        </View>
        <Text className={styles.pdfArrow}>›</Text>
      </View>

      {/* 筛选 */}
      <ScrollView scrollX className={styles.filterTabs}>
        <Text
          className={classnames(styles.filterTab, activeFilter === 'all' && styles.filterTabActive)}
          onClick={() => setActiveFilter('all')}
        >全部</Text>
        {Object.entries(typeConfig).map(([key, cfg]) => (
          <Text
            key={key}
            className={classnames(styles.filterTab, activeFilter === key && styles.filterTabActive)}
            onClick={() => setActiveFilter(key)}
          >{cfg.label}</Text>
        ))}
      </ScrollView>

      {/* 记录列表 */}
      <View className={styles.recordList}>
        {filteredRecords.map(record => {
          const cfg = typeConfig[record.type] || typeConfig['投放']
          return (
            <View key={record.id} className={styles.recordCard} onClick={() => handleRecordClick(record.id)}>
              <View className={styles.recordHeader}>
                <View className={styles.recordType}>
                  <View className={styles.recordTypeIcon} style={{ background: cfg.color + '15' }}>
                    <Text>{cfg.icon}</Text>
                  </View>
                  <Text className={styles.recordTypeName}>{cfg.label}记录</Text>
                </View>
                <Text className={classnames(
                  styles.recordStatus,
                  record.status === 'completed' ? styles.statusDone : styles.statusPending
                )}>
                  {record.status === 'completed' ? '已完成' : '待处理'}
                </Text>
              </View>
              <View className={styles.recordContent}>{record.content}</View>
              <View className={styles.recordMeta}>
                <Text>📍 {record.flatName}</Text>
                <Text>📅 {record.date}</Text>
                <Text>👤 {record.operator}</Text>
              </View>
            </View>
          )
        })}
      </View>

      {/* 底部按钮 */}
      <View className={styles.bottomBtn}>
        <View className={styles.addBtn} onClick={() => handleQuickAdd('新')}>+ 新增台账记录</View>
      </View>
    </View>
  )
}

export default LedgerPage
