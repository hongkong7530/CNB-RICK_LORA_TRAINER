import request from '@/utils/request'

const BASE_URL = '/upload'

export const uploadApi = {
  /**
   * 上传文件
   * @param {File} file - 要上传的文件对象
   * @param {string} description - 文件描述
   * @returns {Promise<Object>} 上传结果
   */
  async uploadFile(file, description = '') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('description', description)
    
    return request.post(`${BASE_URL}/files`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  /**
   * 获取所有文件列表
   * @returns {Promise<Array>} 文件列表
   */
  async getFiles() {
    return request.get(`${BASE_URL}/files`)
  },
  
  /**
   * 获取单个文件信息
   * @param {number} fileId - 文件ID
   * @returns {Promise<Object>} 文件信息
   */
  async getFile(fileId) {
    return request.get(`${BASE_URL}/files/${fileId}`)
  },
  
  /**
   * 删除文件
   * @param {number} fileId - 文件ID
   * @returns {Promise<Object>} 删除结果
   */
  async deleteFile(fileId) {
    return request.delete(`${BASE_URL}/files/${fileId}`)
  },
  
  /**
   * 获取文件下载链接
   * @param {number} fileId - 文件ID
   * @returns {string} 下载链接
   */
  getDownloadUrl(fileId) {
    return `${request.defaults.baseURL}${BASE_URL}/files/${fileId}/download`
  }
} 