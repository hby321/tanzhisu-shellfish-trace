import type { KnowledgeArticle } from '../types'

export const knowledgeArticles: KnowledgeArticle[] = [
  { id: 'k1', category: '冬季育苗', title: '东北寒地贝类冬季育苗技术要点', summary: '水温控制、饵料投喂、病害预防三位一体', content: '东北寒地贝类冬季育苗需注意：1.水温控制在8-12℃；2.投喂单胞藻和人工配合饵料；3.每周进行一次病害检查，重点预防弧菌感染。', author: '辽宁省水产研究院', views: 328, isFeatured: true, hasVideo: true, region: '丹东', createdAt: '2025-12-01' },
  { id: 'k2', category: '生态混养', title: '贝类+海带生态混养模式实践', summary: '丹东东港三年实践验证的生态混养方案', content: '贝类与海带混养可实现营养互补：贝类排出二氧化碳和氨氮供海带生长，海带释放氧气改善水质。推荐放养密度：蛤仔500斤/亩+海带200kg/亩。', author: '丹东水产技术推广站', views: 256, isFeatured: true, hasVideo: true, region: '丹东', createdAt: '2025-11-15' },
  { id: 'k3', category: '病害防治', title: '低温季节贝类常见病害防治指南', summary: '冬季弧菌病、寄生虫病识别与防治', content: '低温季节高发病害：1.弧菌病——症状为贝壳发黑、闭合不全，用聚维酮碘浸泡；2.寄生虫病——定期用淡水浸泡5分钟驱虫。', author: '大连海洋大学', views: 412, isFeatured: false, hasVideo: false, region: '大连', createdAt: '2025-12-10' },
  { id: 'k4', category: '水质管理', title: '寒潮期间水质调控关键技术', summary: '保温、增氧、调盐三步走策略', content: '寒潮来临前24小时：1.加深水位至1.5米；2.开启增氧机；3.如盐度过高引入淡水调节。寒潮期间暂停投喂，减少代谢消耗。', author: '盘锦水产技术推广站', views: 385, isFeatured: true, hasVideo: true, region: '盘锦', createdAt: '2025-12-20' },
  { id: 'k5', category: '轮休制度', title: '三年两养轮休制度实施方案', summary: '科学轮休提升滩涂可持续产能', content: '三年两养轮休：第一年养殖菲律宾蛤仔，第二年养殖牡蛎，第三年休养滩涂。休养期种植海草修复底质，可提升后续产量20-30%。', author: '辽宁省海洋水产科学研究院', views: 198, isFeatured: false, hasVideo: false, region: '全省', createdAt: '2025-11-01' },
  { id: 'k6', category: '冬季育苗', title: '盘锦文蛤冬季育苗实操手册', summary: '从亲贝选择到稚贝培育的全流程', content: '盘锦文蛤育苗：1.亲贝选择2龄以上、壳长4cm以上；2.催产水温25-28℃；3.D形幼虫期投喂金藻和扁藻；4.附着后投放沙粒底质。', author: '盘锦水产技术推广站', views: 276, isFeatured: false, hasVideo: true, region: '盘锦', createdAt: '2025-12-05' },
  { id: 'k7', category: '生态混养', title: '虾夷扇贝与海带立体养殖技术', summary: '上层海带+底层扇贝的立体养殖模式', content: '立体养殖：上层（0-1米）挂养海带，中层（1-3米）吊养扇贝。优势：充分利用水体空间，提高单位面积产值40%。', author: '大连海洋大学', views: 315, isFeatured: true, hasVideo: false, region: '大连', createdAt: '2025-11-20' },
  { id: 'k8', category: '病害防治', title: '春季贝类复苏期病害预防要点', summary: '气温回升期的健康管理', content: '春季气温回升，贝类从休眠中复苏，免疫力低：1.逐步恢复投喂，从正常量的1/3开始；2.全池泼洒生石灰消毒；3.观察贝类开口情况。', author: '辽宁省水产研究院', views: 224, isFeatured: false, hasVideo: false, region: '全省', createdAt: '2025-12-15' },
  { id: 'k9', category: '水质管理', title: '滩涂养殖溶解氧管理全攻略', summary: '从监测到增氧的完整方案', content: '溶解氧管理：1.配备溶解氧在线监测仪；2.低于6mg/L启动增氧机；3.阴雨天提前增氧；4.定期换水保持水体活力。', author: '葫芦岛水产技术推广站', views: 189, isFeatured: false, hasVideo: true, region: '葫芦岛', createdAt: '2025-12-08' },
  { id: 'k10', category: '轮休制度', title: '滩涂底质修复与改良技术', summary: '休养期底质改良操作指南', content: '底质修复：1.休养期翻耕滩涂20cm深；2.投放沸石粉100kg/亩吸附有害物质；3.种植大叶藻修复底质生态；4.6个月后恢复养殖。', author: '辽宁省海洋水产科学研究院', views: 156, isFeatured: false, hasVideo: false, region: '全省', createdAt: '2025-11-10' }
]
