import axios from 'axios'
import message from './message'
import router from '@/router'

// 安全地获取环境变量
const getEnvVariable = (key, defaultValue = '') => {
  try {
    return import.meta.env[key] || defaultValue
  } catch (error) {
    console.warn(`无法读取环境变量: ${key}，使用默认值`, error)
    return defaultValue
  }
}

// 创建 axios 实例
const service = axios.create({
  baseURL: getEnvVariable('VITE_API_BASE_URL', '/api/v1'),
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 可以在这里添加认证令牌等通用头部
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    // 适配统一的响应格式 {code, data, msg}
    const res = response.data
    console.log('API响应详情:', { url: response.config.url, status: response.status, data: res })
    // 如果响应中包含统一格式字段
    if (res.code !== undefined) {
      // 业务成功
      if (res.code === 0 || res.code === 200) {
        return res.data
      } 
      // 未授权
      else if (res.code === 401) {
        message.error(res.msg || '登录状态已失效，请重新登录')
        // 清除token并跳转到登录页
        localStorage.removeItem('token')
        router.replace('/login')
        return Promise.reject(new Error(res.msg || '未授权'))
      }
      // 其他业务错误
      else {
        message.error(res.msg || '操作失败')
        return Promise.reject(new Error(res.msg || '请求失败'))
      }
    }
    
    // 保持向下兼容
    return response.data
  },
  error => {
    console.error('请求错误详情:', { 
      url: error.config?.url, 
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message 
    })
    // 处理HTTP错误
    if (error.response) {
      const status = error.response.status
      let errorMsg = '请求失败'
      
      // 根据HTTP状态码定制错误消息
      if (status === 400) errorMsg = '请求参数错误'
      else if (status === 401) {
        errorMsg = '未授权，请重新登录'
        // 清除token并跳转到登录页
        localStorage.removeItem('token')
        router.replace('/login')
      }
      else if (status === 403) errorMsg = '拒绝访问'
      else if (status === 404) errorMsg = '请求的资源不存在'
      else if (status === 500) errorMsg = '服务器内部错误'
      
      message.error(error.response.data?.msg || errorMsg)
    } else {
      message.error('网络异常，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

export default service 