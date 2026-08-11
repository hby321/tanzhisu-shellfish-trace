import React from 'react'
import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'
import styles from './index.module.scss'
import { traceRecords } from '../../data/traceability'

const TraceabilityPage: React.FC = () => {
  const handleGenerate = () => {
    Taro.showToast({ title: '请先录入捕捞和质检信息', icon: 'none' })
  }

  const handleDownload = (code: string) => {
    Taro.showToast({ title: `溯源码 ${code} 已保存到相册`, icon: 'success' })
  }

  const handlePrint = (code: string) => {
    Taro.showToast({ title: '连接打印机中...', icon: 'loading', duration: 1500 })
  }

  return (
    <View className={styles.tracePage}>
      <View className={styles.header}>
        <Text className={styles.headerIcon}>🔗</Text>
        <View className={styles.headerText}>
          <View className={styles.headerTitle}>区块链溯源码</View>
          <View className={styles.headerDesc}>不可篡改 · 一键生成 · 可下载打印</View>
        </View>
      </View>

      <View className={styles.section}>
        <View className={styles.sectionTitle}>已生成溯源码 ({traceRecords.length})</View>
        {traceRecords.map(record => (
          <View key={record.id} className={styles.card}>
            <View className={styles.cardHeader}>
              <Text className={styles.batchCode}>{record.batchCode}</Text>
              <Text style={{ fontSize: '20rpx', color: '$color-text-tertiary' }}>{record.createdAt}</Text>
            </View>
            <View className={styles.cardInfo}>
              <View style={{ flex: 1 }}>
                <View className={styles.infoRow}><Text className={styles.infoLabel}>产品：</Text>{record.product}</View>
                <View className={styles.infoRow}><Text className={styles.infoLabel}>滩涂：</Text>{record.flatName}</View>
                <View className={styles.infoRow}><Text className={styles.infoLabel}>养殖户：</Text>{record.farmer}</View>
                <View className={styles.infoRow}><Text className={styles.infoLabel}>捕捞日期：</Text>{record.harvestDate}</View>
                <View className={styles.infoRow}><Text className={styles.infoLabel}>质检：</Text>{record.qualityCheck}</View>
              </View>
              <View className={styles.qrPlaceholder}>
                <Text>📋</Text>
              </View>
            </View>
            <View className={styles.cardFooter}>
              <View className={`${styles.btnSmall} ${styles.btnDownload}`} onClick={() => handleDownload(record.batchCode)}>📥 下载二维码</View>
              <View className={`${styles.btnSmall} ${styles.btnPrint}`} onClick={() => handlePrint(record.batchCode)}>🖨️ 打印</View>
            </View>
          </View>
        ))}
      </View>

      <View className={styles.bottomBtn} onClick={handleGenerate}>+ 生成新溯源码</View>
    </View>
  )
}

export default TraceabilityPage
