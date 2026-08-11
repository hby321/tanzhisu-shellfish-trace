import React, { useState } from 'react'
import { View, Text, ScrollView, Input } from '@tarojs/components'
import Taro from '@tarojs/taro'
import styles from './index.module.scss'
import type { ConsultMessage } from '../../types'

import { AI_BACKEND } from '../../config/api'

const initialMessages: ConsultMessage[] = [
  { id: '1', role: 'expert', content: '您好，我是AI养殖顾问（数据智能体综合应用平台V1.0软著）。可上传贝类实拍图或描述症状，由贝类病害识别智能体(YOLO-v8)进行病害识别并输出防治方案。', createdAt: '09:00' }
]

const quickQuestions = ['贝类消瘦闭壳无力', '肉质变色有黑斑', '大规模突发死亡', '低温不摄食', '赤潮中毒缺氧']

const ExpertPage: React.FC = () => {
  const [messages, setMessages] = useState<ConsultMessage[]>(initialMessages)
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)

  const nowTime = () => {
    const now = new Date()
    return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  }

  // 调用软著平台 - 贝类病害识别智能体
  const callDiseaseAgent = async (symptom: string) => {
    try {
      const res = await Taro.request({
        url: `${AI_BACKEND}/ai/api/disease-detect`,
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: { symptom, description: symptom, image_uploaded: false }
      })
      const data = res.data
      if (data.success && data.ai_reply) {
        const r = data.ai_reply
        return `【AI病害识别智能体 · YOLO-v8】\n识别结果：${r['识别结果']}\n置信度：${r['置信度']}\n\n防治方案：${r['防治方案']}\n\n预防建议：${r['预防建议']}\n\n⚠️ ${r['温馨提示']}`
      }
      return `⚠️ ${data.message || '智能体响应异常，请稍后重试'}`
    } catch (err) {
      return '⚠️ AI智能体平台未启动或网络异常，请先启动 agent_server.py（端口8090）'
    }
  }

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return
    const userMsg: ConsultMessage = { id: Date.now().toString(), role: 'user', content: inputValue, createdAt: nowTime() }
    setMessages(prev => [...prev, userMsg])
    const question = inputValue
    setInputValue('')
    setLoading(true)

    // 显示"推理中"提示
    const loadingId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, { id: loadingId, role: 'expert', content: '🔍 AI智能体推理中...', createdAt: nowTime() }])

    // 调用软著平台病害识别智能体
    const reply = await callDiseaseAgent(question)
    setMessages(prev => prev.map(m => m.id === loadingId ? { ...m, content: reply } : m))
    setLoading(false)
  }

  const handleQuickQuestion = (q: string) => {
    setInputValue(q)
  }

  // 模拟上传图片
  const handleUploadImage = () => {
    Taro.chooseImage({ count: 1 }).then(() => {
      const userMsg: ConsultMessage = { id: Date.now().toString(), role: 'user', content: '📷 [已上传贝类实拍图] 请识别病害', createdAt: nowTime() }
      setMessages(prev => [...prev, userMsg])
      setInputValue('贝类实拍图，疑似病害')
    }).catch(() => {})
  }

  return (
    <View className={styles.expertPage}>
      <View className={styles.expertHeader}>
        <View className={styles.expertAvatar}><Text>🤖</Text></View>
        <View className={styles.expertInfo}>
          <View className={styles.expertName}>AI病害识别智能体 · YOLO-v8</View>
          <View className={styles.expertDesc}>数据智能体综合应用平台V1.0 · 软著</View>
        </View>
      </View>

      <ScrollView scrollY className={styles.msgList}>
        {messages.map(msg => (
          <View key={msg.id} className={styles.msgItem} style={{ flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
            <View className={msg.role === 'user' ? styles.msgAvatarUser : styles.msgAvatarExpert}>
              <Text>{msg.role === 'user' ? '👨‍🌾' : '🤖'}</Text>
            </View>
            <View>
              <View className={msg.role === 'user' ? styles.msgBubbleUser : styles.msgBubbleExpert}>
                {msg.content}
              </View>
              <View className={styles.msgTime} style={{ textAlign: msg.role === 'user' ? 'right' : 'left' }}>{msg.createdAt}</View>
            </View>
          </View>
        ))}
      </ScrollView>

      <View className={styles.quickQuestions}>
        <ScrollView scrollX>
          {quickQuestions.map(q => (
            <Text key={q} className={styles.quickQ} onClick={() => handleQuickQuestion(q)}>{q}</Text>
          ))}
        </ScrollView>
      </View>

      <View className={styles.inputBar}>
        <View className={styles.uploadBtn} onClick={handleUploadImage}>📷</View>
        <Input
          className={styles.inputBox}
          placeholder="描述贝类症状或上传图片..."
          value={inputValue}
          onInput={(e) => setInputValue(e.detail.value)}
          confirmType="send"
          onConfirm={handleSend}
        />
        <View className={styles.sendBtn} onClick={handleSend}>{loading ? '...' : '发送'}</View>
      </View>
    </View>
  )
}

export default ExpertPage
