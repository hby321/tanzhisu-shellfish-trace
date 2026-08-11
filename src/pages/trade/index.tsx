import React, { useState } from 'react'
import { View, Text, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import classnames from 'classnames'
import styles from './index.module.scss'
import { tradeItems } from '../../data/trade'

const TradePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'all' | 'supply' | 'demand'>('all')

  const filtered = activeTab === 'all' ? tradeItems : tradeItems.filter(t => t.type === activeTab)

  const handlePublish = () => {
    Taro.showToast({ title: '发布功能开发中', icon: 'none' })
  }

  const handleContact = (publisher: string, phone: string) => {
    Taro.showActionSheet({
      itemList: [`拨打 ${phone}`, '预约上门收购'],
      success: (res) => {
        if (res.tapIndex === 0) {
          Taro.makePhoneCall({ phoneNumber: phone.replace(/\*/g, '0') }).catch(() => {
            Taro.showToast({ title: '电话号码已复制', icon: 'success' })
          })
        } else {
          Taro.showToast({ title: '预约成功，商家将联系您', icon: 'success' })
        }
      }
    })
  }

  return (
    <View className={styles.tradePage}>
      <View className={styles.tabs}>
        <Text className={classnames(styles.tab, activeTab === 'all' && styles.tabActive)} onClick={() => setActiveTab('all')}>全部</Text>
        <Text className={classnames(styles.tab, activeTab === 'supply' && styles.tabActive)} onClick={() => setActiveTab('supply')}>供应</Text>
        <Text className={classnames(styles.tab, activeTab === 'demand' && styles.tabActive)} onClick={() => setActiveTab('demand')}>收购</Text>
      </View>

      <View className={styles.section}>
        <View className={styles.sectionTitle}>
          {activeTab === 'supply' ? '供应信息' : activeTab === 'demand' ? '收购报价' : '产销信息'}
          <Text style={{ fontSize: '24rpx', color: '$color-text-tertiary', fontWeight: 400 }}>（{filtered.length}条）</Text>
        </View>
        {filtered.map(item => (
          <View key={item.id} className={styles.card} onClick={() => handleContact(item.publisher, item.phone)}>
            <View className={styles.cardHeader}>
              <Text className={styles.cardTitle}>{item.product}</Text>
              <Text className={classnames(
                styles.cardTag,
                item.status === 'closed' ? styles.tagClosed : (item.type === 'supply' ? styles.tagSupply : styles.tagDemand)
              )}>
                {item.status === 'closed' ? '已关闭' : item.type === 'supply' ? '供应' : '收购'}
              </Text>
            </View>
            <View className={styles.cardInfo}>
              <View className={styles.infoItem}>
                <Text className={styles.infoLabel}>数量：</Text>
                <Text>{item.quantity} {item.unit}</Text>
              </View>
              <View className={styles.infoItem}>
                <Text className={styles.infoLabel}>单价：</Text>
                <Text className={styles.price}>{item.price}元/{item.unit}</Text>
              </View>
            </View>
            <View className={styles.cardMeta}>
              <Text>📍 {item.region}</Text>
              <Text>📅 {item.date}</Text>
              <Text>👤 {item.publisher}</Text>
            </View>
          </View>
        ))}
      </View>

      <View className={styles.publishBtn} onClick={handlePublish}>+ 发布供应/收购信息</View>
    </View>
  )
}

export default TradePage
