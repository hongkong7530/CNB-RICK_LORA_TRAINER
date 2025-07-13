import request from '@/utils/request'

const BASE_URL = '/tasks'

export const tasksApi = {
  // 获取任务列表
  async getTasks(params) {
    return request.get(BASE_URL, { params })
  },
  
  // 创建任务
  async createTask(data) {
    return request.post(BASE_URL, data)
  },
  
  // 获取任务详情
  async getTaskById(id) {
    return request.get(`${BASE_URL}/${id}`)
  },
  
  // 更新任务
  async updateTask(id, data) {
    return request.put(`${BASE_URL}/${id}`, data)
  },
  
  // 删除任务
  async deleteTask(id) {
    return request.delete(`${BASE_URL}/${id}`)
  },
  
  // 上传图片
  async uploadImages(taskId, formData) {
    return request.post(`${BASE_URL}/${taskId}/images`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除图片
  async deleteImage(taskId, imageId) {
    return request.delete(`${BASE_URL}/${taskId}/images/${imageId}`)
  },
  
  // 开始标记
  async startMarking(taskId) {
    return request.post(`${BASE_URL}/${taskId}/mark`)
  },
  
  // 开始训练
  async startTraining(taskId) {
    return request.post(`${BASE_URL}/${taskId}/train`)
  },
  
  /**
   * 重启任务
   * @param {number|string} taskId - 任务ID
   * @returns {Promise<Object>} 任务信息
   */
  async restartTask(taskId) {
    return request.post(`${BASE_URL}/${taskId}/restart`)
  },
  
  /**
   * 取消任务
   * @param {number|string} taskId - 任务ID
   * @returns {Promise<Object>} 任务信息
   */
  async cancelTask(taskId) {
    return request.post(`${BASE_URL}/${taskId}/cancel`)
  },
  
  /**
   * 获取任务状态
   * @param {number|string} taskId - 任务ID
   * @returns {Promise<Object>} 任务状态信息
   */
  async getTaskStatus(taskId) {
    return request.get(`${BASE_URL}/${taskId}/status`)
  },
  
  /**
   * 获取打标文本
   * @param {number|string} taskId - 任务ID
   * @returns {Promise<Object>} 打标文本信息，key为图片名称，value为打标文本
   */
  async getMarkedTexts(taskId) {
    return request.get(`${BASE_URL}/${taskId}/marked_texts`)
  },
  
  /**
   * 更新打标文本
   * @param {number|string} taskId - 任务ID
   * @param {string} filename - 图片文件名
   * @param {string} content - 打标文本内容
   * @returns {Promise<Object>} 更新后的打标文本信息
   */
  async updateMarkedText(taskId, filename, content) {
    return request.put(`${BASE_URL}/${taskId}/marked_texts`, {
      filename,
      content
    })
  },
  
  /**
   * 停止任务
   * @param {number} taskId 任务ID
   * @returns {Promise<Object>} 任务对象
   */
  async stopTask(taskId) {
    return request.post(`${BASE_URL}/${taskId}/stop`)
  },
  
  /**
   * 批量删除任务图片
   * @param {number|string} taskId 任务ID
   * @param {Array<number>} imageIds 图片ID数组
   * @returns {Promise<Object>}
   */
  async batchDeleteImages(taskId, imageIds) {
    return request.delete(`${BASE_URL}/${taskId}/images/batch`, {
      data: { image_ids: imageIds }
    })
  },
  
  /**
   * 批量更新打标文本
   * @param {number|string} taskId 任务ID
   * @param {Object} markedTexts 文件名到文本内容的映射
   * @returns {Promise<Object>}
   */
  async batchUpdateMarkedTexts(taskId, markedTexts) {
    return request.put(`${BASE_URL}/${taskId}/marked_texts/batch`, markedTexts)
  },
  
  /**
   * 获取训练结果
   * @param {number|string} taskId 任务ID
   * @returns {Promise<Object>} 训练结果信息，包含模型列表等
   */
  async getTrainingResults(taskId) {
    return request.get(`${BASE_URL}/${taskId}/training-results`)
  },
  
  /**
   * 获取训练loss曲线数据
   * @param {number|string} taskId 任务ID
   * @returns {Promise<Object>} 训练loss数据，包含数据点和训练进度
   */
  async getTrainingLoss(taskId) {
    return request.get(`${BASE_URL}/${taskId}/training-loss`)
  },
  
  /**
   * 获取标记进度数据
   * @param {number|string} taskId 任务ID
   * @returns {Promise<Object>} 标记进度数据，包含队列状态和系统信息
   */
  async getMarkingProgress(taskId) {
    return request.get(`${BASE_URL}/${taskId}/marking-progress`)
  },
  
  /**
   * 批量提交任务进行标记
   * @param {Array<number>} taskIds 任务ID数组
   * @returns {Promise<Object>} 成功提交的任务ID列表
   */
  async batchStartMarking(taskIds) {
    return request.post(`${BASE_URL}/batch/mark`, { task_ids: taskIds })
  },
  
  // 获取任务训练历史
  async getTaskTrainingHistory(taskId) {
    const response = await request.get(`${BASE_URL}/${taskId}/execution-history`)
    return response
  },
  
  // 获取特定历史记录详情
  async getTrainingHistoryDetails(historyId) {
    const response = await request.get(`${BASE_URL}/execution-history/${historyId}`)
    return response
  },
  
  // 获取执行历史记录详情(通用方法)
  async getExecutionHistoryById(historyId) {
    const response = await request.get(`${BASE_URL}/execution-history/${historyId}`)
    return response
  },
  
  /**
   * 获取任务配置
   * @param {number|string} taskId 任务ID
   * @returns {Promise<Object>} 任务配置，包含打标和训练配置
   */
  async getTaskConfig(taskId) {
    return request.get(`${BASE_URL}/${taskId}/config`)
  },
  
  /**
   * 更新任务配置
   * @param {number|string} taskId 任务ID
   * @param {Object} configData 配置数据
   * @returns {Promise<Object>} 更新后的配置信息
   */
  async updateTaskConfig(taskId, configData) {
    return request.put(`${BASE_URL}/${taskId}/config`, configData)
  }
} 

// 导出个别方法供直接使用
export const getTasks = tasksApi.getTasks
export const createTask = tasksApi.createTask
export const getTaskById = tasksApi.getTaskById
export const updateTask = tasksApi.updateTask
export const deleteTask = tasksApi.deleteTask
export const uploadImages = tasksApi.uploadImages
export const deleteImage = tasksApi.deleteImage
export const startMarking = tasksApi.startMarking
export const startTraining = tasksApi.startTraining
export const restartTask = tasksApi.restartTask
export const cancelTask = tasksApi.cancelTask
export const getTaskStatus = tasksApi.getTaskStatus
export const getMarkedTexts = tasksApi.getMarkedTexts
export const updateMarkedText = tasksApi.updateMarkedText
export const batchUpdateMarkedTexts = tasksApi.batchUpdateMarkedTexts
export const getTrainingResults = tasksApi.getTrainingResults
export const getTrainingLoss = tasksApi.getTrainingLoss
export const getMarkingProgress = tasksApi.getMarkingProgress
export const batchStartMarking = tasksApi.batchStartMarking
export const getTaskTrainingHistory = tasksApi.getTaskTrainingHistory
export const getTrainingHistoryDetails = tasksApi.getTrainingHistoryDetails
export const getExecutionHistoryById = tasksApi.getExecutionHistoryById
export const getTaskConfig = tasksApi.getTaskConfig
export const updateTaskConfig = tasksApi.updateTaskConfig