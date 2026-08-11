import React, { useState } from 'react'
import { View, Text, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import classnames from 'classnames'
import styles from './index.module.scss'
import { knowledgeArticles } from '../../data/knowledge'

const categories = ['全部', '冬季育苗', '生态混养', '病害防治', '水质管理', '轮休制度']

const KnowledgePage: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('全部')

  const featuredArticles = knowledgeArticles.filter(a => a.isFeatured)
  const filteredArticles = activeCategory === '全部'
    ? knowledgeArticles
    : knowledgeArticles.filter(a => a.category === activeCategory)

  const handleArticleClick = (id: string) => {
    Taro.navigateTo({ url: `/pages/knowledge-detail/index?id=${id}` })
  }

  const handleExpertClick = () => {
    Taro.navigateTo({ url: '/pages/expert/index' })
  }

  return (
    <View className={styles.knowledgePage}>
      {/* 专家问诊入口 */}
      <View className={styles.expertBar} onClick={handleExpertClick}>
        <Text className={styles.expertIcon}>👨‍⚕️</Text>
        <View className={styles.expertText}>
          <View className={styles.expertTitle}>在线专家问诊</View>
          <View className={styles.expertDesc}>辽宁水产专家文字问诊，24小时内回复</View>
        </View>
        <Text style={{ color: '#fff', fontSize: '28rpx' }}>›</Text>
      </View>

      {/* 分类标签 */}
      <ScrollView scrollX className={styles.categoryTabs}>
        {categories.map(cat => (
          <Text
            key={cat}
            className={classnames(styles.categoryTab, activeCategory === cat && styles.categoryTabActive)}
            onClick={() => setActiveCategory(cat)}
          >{cat}</Text>
        ))}
      </ScrollView>

      {/* 精选文章 */}
      {activeCategory === '全部' && (
        <View className={styles.section}>
          <View className={styles.sectionTitle}>精选推荐</View>
          {featuredArticles.map(article => (
            <View key={article.id} className={styles.featuredCard} onClick={() => handleArticleClick(article.id)}>
              <View className={styles.featuredBadge}>⭐ 精选 · {article.category}</View>
              <View className={styles.featuredTitle}>{article.title}</View>
              <View className={styles.featuredSummary}>{article.summary}</View>
              <View className={styles.featuredMeta}>
                <Text>📝 {article.author}</Text>
                <Text>👀 {article.views}</Text>
                <Text>📍 {article.region}</Text>
                {article.hasVideo && <Text>▶️ 视频</Text>}
              </View>
            </View>
          ))}
        </View>
      )}

      {/* 文章列表 */}
      <View className={styles.section}>
        <View className={styles.sectionTitle}>
          {activeCategory === '全部' ? '全部文章' : activeCategory}
          <Text style={{ fontSize: '24rpx', color: '$color-text-tertiary', fontWeight: 400 }}>
            （{filteredArticles.length}篇）
          </Text>
        </View>
        {filteredArticles.map(article => (
          <View key={article.id} className={styles.articleCard} onClick={() => handleArticleClick(article.id)}>
            <View className={styles.articleHeader}>
              <View className={styles.articleContent}>
                <View className={styles.articleCategory}>{article.category}</View>
                <View className={styles.articleTitle}>{article.title}</View>
                <View className={styles.articleSummary}>{article.summary}</View>
                <View className={styles.articleMeta}>
                  <Text className={styles.articleRegion}>{article.region}</Text>
                  <Text>👀 {article.views}</Text>
                  {article.hasVideo && (
                    <Text className={styles.videoTag}>▶️ 含视频</Text>
                  )}
                </View>
              </View>
            </View>
          </View>
        ))}
      </View>
    </View>
  )
}

export default KnowledgePage
