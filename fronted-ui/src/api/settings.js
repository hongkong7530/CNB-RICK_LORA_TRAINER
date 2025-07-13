import request from '@/utils/request'
const BASE_URL = '/settings'

export const settingsApi = {
  /**
   * 获取设置
   * @returns {Promise<Object>} 系统设置
   */
  async getSettings() {
    return request.get(BASE_URL)
  },
  
  /**
   * 更新设置
   * @param {Object} data - 设置数据
   * @returns {Promise<Object>} 更新后的设置
   */
  async updateSettings(data) {
    return request.put(BASE_URL, data)
  },

  /**
   * 获取任务打标配置
   * @param {number} taskId - 任务ID
   * @returns {Promise<Object>} 打标配置
   */
  async getTaskMarkConfig(taskId) {
    return request.get(`${BASE_URL}/tasks/${taskId}/mark-config`)
  },

  /**
   * 获取任务训练配置
   * @param {number} taskId - 任务ID
   * @returns {Promise<Object>} 训练配置
   */
  async getTaskTrainingConfig(taskId) {
    return request.get(`${BASE_URL}/tasks/${taskId}/training-config`)
  }
} 