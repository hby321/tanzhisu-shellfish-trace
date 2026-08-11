export default defineAppConfig({
  pages: [
    'pages/home/index',
    'pages/warning/index',
    'pages/ledger/index',
    'pages/knowledge/index',
    'pages/mine/index',
    'pages/trade/index',
    'pages/traceability/index',
    'pages/disaster-history/index',
    'pages/warning-detail/index',
    'pages/knowledge-detail/index',
    'pages/ledger-detail/index',
    'pages/expert/index'
  ],
  window: {
    backgroundTextStyle: 'light',
    navigationBarBackgroundColor: '#0866c4',
    navigationBarTitleText: '滩智溯',
    navigationBarTextStyle: 'white'
  },
  tabBar: {
    color: '#999999',
    selectedColor: '#0866c4',
    backgroundColor: '#ffffff',
    borderStyle: 'white',
    list: [
      {
        pagePath: 'pages/home/index',
        text: '首页',
        iconPath: 'assets/tabbar/home.png',
        selectedIconPath: 'assets/tabbar/home-selected.png'
      },
      {
        pagePath: 'pages/warning/index',
        text: '预警',
        iconPath: 'assets/tabbar/warning.png',
        selectedIconPath: 'assets/tabbar/warning-selected.png'
      },
      {
        pagePath: 'pages/ledger/index',
        text: '台账',
        iconPath: 'assets/tabbar/ledger.png',
        selectedIconPath: 'assets/tabbar/ledger-selected.png'
      },
      {
        pagePath: 'pages/knowledge/index',
        text: '知识',
        iconPath: 'assets/tabbar/knowledge.png',
        selectedIconPath: 'assets/tabbar/knowledge-selected.png'
      },
      {
        pagePath: 'pages/mine/index',
        text: '我的',
        iconPath: 'assets/tabbar/mine.png',
        selectedIconPath: 'assets/tabbar/mine-selected.png'
      }
    ]
  }
})
