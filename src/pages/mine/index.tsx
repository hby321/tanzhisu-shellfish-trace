import React from 'react'
import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'
import styles from './index.module.scss'

const menuItems = [
  { id: '1', icon: '🏪', label: '产销撮合', color: '#ff7d00', path: '/pages/trade/index' },
  { id: '2', icon: '🔗', label: '我的溯源码', color: '#00b8a9', path: '/pages/traceability/index' },
  { id: '3', icon: '📅', label: '灾害历史记录', color: '#f53f3f', path: '/pages/disaster-history/index' },
  { id: '4', icon: '👨‍⚕️', label: '专家问诊记录', color: '#722ed1', path: '/pages/expert/index' },
  { id: '5', icon: '📄', label: 'PDF台账管理', color: '#52c41a', path: '/pages/ledger/index' },
  { id: '6', icon: '⚙️', label: '通知设置', color: '#86909c', path: '' },
  { id: '7', icon: '❓', label: '帮助与反馈', color: '#86909c', path: '' },
  { id: '8', icon: '📋', label: '关于滩智溯', color: '#86909c', path: '' }
]

const MinePage: React.FC = () => {
  const handleMenuClick = (path: string, label: string) => {
    if (!path) {
      Taro.showToast({ title: `${label}功能开发中`, icon: 'none' })
      return
    }
    Taro.navigateTo({ url: path }).catch(() => {
      Taro.switchTab({ url: path })
    })
  }

  const handleLogout = () => {
    Taro.showModal({
      title: '提示',
      content: '确定退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          Taro.showToast({ title: '已退出', icon: 'success' })
        }
      }
    })
  }

  return (
    <View className={styles.minePage}>
      {/* 用户信息 */}
      <View className={styles.profileHeader}>
        <View className={styles.avatar}>
          <Text>👨‍🌾</Text>
        </View>
        <View className={styles.profileInfo}>
          <View className={styles.profileName}>王建国</View>
          <View className={styles.profilePhone}>138****5678</View>
          <View className={styles.profileTag}>丹东东港 · 养殖户</View>
        </View>
      </View>

      {/* 统计 */}
      <View className={styles.statsCard}>
        <View className={styles.statItem}>
          <View className={styles.statValue}>10</View>
          <View className={styles.statLabel}>台账记录</View>
        </View>
        <View className={styles.statDivider} />
        <View className={styles.statItem}>
          <View className={styles.statValue}>5</View>
          <View className={styles.statLabel}>溯源码</View>
        </View>
        <View className={styles.statDivider} />
        <View className={styles.statItem}>
          <View className={styles.statValue}>4</View>
          <View className={styles.statLabel}>滩涂</View>
        </View>
        <View className={styles.statDivider} />
        <View className={styles.statItem}>
          <View className={styles.statValue}>28</View>
          <View className={styles.statLabel}>知识阅读</View>
        </View>
      </View>

      {/* 功能菜单 */}
      <View className={styles.menuSection}>
        {menuItems.map(item => (
          <View key={item.id} className={styles.menuItem} onClick={() => handleMenuClick(item.path, item.label)}>
            <View className={styles.menuIcon} style={{ background: item.color + '15' }}>
              <Text>{item.icon}</Text>
            </View>
            <Text className={styles.menuLabel}>{item.label}</Text>
            <Text className={styles.menuArrow}>›</Text>
          </View>
        ))}
      </View>

      {/* 退出 */}
      <View className={styles.logoutBtn} onClick={handleLogout}>退出登录</View>
    </View>
  )
}

export default MinePage
