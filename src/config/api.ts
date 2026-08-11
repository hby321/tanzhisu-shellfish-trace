/**
 * API 配置文件
 * 软著《数据智能体综合应用平台 V1.0》
 *
 * H5模式：自动使用当前域名（与Flask后端同域部署）
 * 小程序模式：使用本地开发地址或配置的服务器地址
 */

// 动态获取后端地址
function getBackendUrl(): string {
  // H5环境 - 与后端同域部署时使用相对路径
  if (typeof window !== 'undefined' && window.location) {
    const host = window.location.origin
    // 如果H5部署在和后端同一个域名+端口下，直接用当前origin
    return host
  }
  // 小程序环境 - 使用配置的服务器地址
  // 部署到公网后，把这里改成你的公网域名，如 https://yourdomain.com
  return 'http://127.0.0.1:5000'
}

export const AI_BACKEND = getBackendUrl()
