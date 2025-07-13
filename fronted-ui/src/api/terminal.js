import request from '@/utils/request'

const BASE_URL = '/terminal'

export const terminalApi = {
  /**
   * 列出远程目录文件
   * @param {number|string} assetId - 资产ID
   * @param {string} path - 远程路径
   * @returns {Promise<Object>} 文件列表
   */
  async listFiles(assetId, path = '/') {
    return request.get(`${BASE_URL}/files/list/${assetId}`, {
      params: { path }
    })
  },

  /**
   * 浏览远程目录（带排序和过滤功能）
   * @param {number|string} assetId - 资产ID
   * @param {string} path - 远程路径
   * @param {string} sortBy - 排序字段
   * @param {string} sortOrder - 排序顺序
   * @returns {Promise<Object>} 文件和目录信息
   */
  async browseDirectory(assetId, path = '/', sortBy = 'name', sortOrder = 'asc') {
    return request.get(`${BASE_URL}/files/browse/${assetId}`, {
      params: { 
        path,
        sort_by: sortBy,
        sort_order: sortOrder
      }
    })
  },

  /**
   * 上传文件到远程服务器
   * @param {number|string} assetId - 资产ID
   * @param {File} file - 文件对象
   * @param {string} remotePath - 远程路径
   * @returns {Promise<Object>} 上传结果
   */
  async uploadFile(assetId, file, remotePath = '/') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('remote_path', remotePath)

    const response = await request.post(`${BASE_URL}/files/stream-upload/${assetId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    console.log("上传返回值response",response)
    return response
  },

  /**
   * 从远程服务器下载文件
   * @param {number|string} assetId - 资产ID
   * @param {string} remotePath - 远程文件路径
   * @returns {Promise<Blob>} 文件Blob对象
   */
  async downloadFile(assetId, remotePath) {
    return fetch(`/api/v1/${BASE_URL}/files/stream-download/${assetId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ remote_path: remotePath })
    }).then(response => {
      if (!response.ok) {
        throw new Error(`下载失败: ${response.statusText}`)
      }
      return response.blob()
    })
  },

  /**
   * 获取WebSocket连接URL
   * @param {number|string} assetId - 资产ID
   * @returns {string} WebSocket URL
   */
  getWebSocketUrl(assetId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/api/v1/${BASE_URL}/${assetId}`
  },

  /**
   * 删除远程服务器上的文件或目录
   * @param {number|string} assetId - 资产ID
   * @param {string} remotePath - 远程文件或目录路径
   * @returns {Promise<Object>} 删除结果
   */
  async deleteRemoteFile(assetId, remotePath) {
    return request.post(`${BASE_URL}/files/delete/${assetId}`, {
      remote_path: remotePath
    })
  }
} 