import React from 'react'
import { View, Text } from '@tarojs/components'
import Taro, { useRouter } from '@tarojs/taro'
import styles from './index.module.scss'
import { knowledgeArticles } from '../../data/knowledge'

const KnowledgeDetailPage: React.FC = () => {
  const router = useRouter()
  const articleId = router.params.id
  const article = knowledgeArticles.find(a => a.id === articleId) || knowledgeArticles[0]

  const handleExpertClick = () => {
    Taro.navigateTo({ url: '/pages/expert/index' })
  }

  return (
    <View className={styles.detailPage}>
      <View className={styles.header}>
        <Text className={styles.category}>{article.category}</Text>
        <View className={styles.title}>{article.title}</View>
        <View className={styles.summary}>{article.summary}</View>
        <View className={styles.meta}>
          <Text>📝 {article.author}</Text>
          <Text>👀 {article.views}阅读</Text>
          <Text className={styles.region}>{article.region}</Text>
          <Text>📅 {article.createdAt}</Text>
        </View>
      </View>

      {article.hasVideo && (
        <View className={styles.videoBanner}>
          <Text className={styles.videoIcon}>▶️</Text>
          <Text className={styles.videoText}>本篇配有视频教程，点击观看</Text>
        </View>
      )}

      <View className={styles.section}>
        <View className={styles.card}>
          <View className={styles.contentText}>{article.content}</View>
        </View>
      </View>

      <View className={styles.expertBar} onClick={handleExpertClick}>
        <Text className={styles.expertIcon}>👨‍⚕️</Text>
        <View className={styles.expertText}>
          <View className={styles.expertTitle}>有问题？在线问专家</View>
          <View className={styles.expertDesc}>辽宁水产专家24小时内回复</View>
        </View>
        <Text style={{ color: '#fff' }}>›</Text>
      </View>
    </View>
  )
}

export default KnowledgeDetailPage
