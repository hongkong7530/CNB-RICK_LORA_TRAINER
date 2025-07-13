import request from '@/utils/request'

const BASE_URL = '/assets'

export const assetApi = {
  /**
   * 获取资产列表
   * @returns {Promise<Array>} 资产列表
   */
  async getAssets() {
    return request.get(BASE_URL)
  },

  /**
   * 创建资产
   * @param {Object} data - 资产数据
   * @returns {Promise<Object>} 创建的资产
   */
  async createAsset(data) {
    return request.post(BASE_URL, data)
  },

  /**
   * 更新资产
   * @param {number|string} id - 资产ID
   * @param {Object} data - 更新数据
   * @returns {Promise<Object>} 更新后的资产
   */
  async updateAsset(id, data) {
    return request.put(`${BASE_URL}/${id}`, data)
  },

  /**
   * 删除资产
   * @param {number|string} id - 资产ID
   * @returns {Promise<void>}
   */
  async deleteAsset(id) {
    return request.delete(`${BASE_URL}/${id}`)
  },

  /**
   * 验证资产能力
   * @param {number|string} id - 资产ID
   * @returns {Promise<Object>} 验证结果
   */
  async verifyCapabilities(id) {
    return request.post(`${BASE_URL}/${id}/verify`)
  },

  /**
   * 验证SSH连接
   * @param {Object} data - SSH连接参数
   * @returns {Promise<Object>} 验证结果
   */
  async verifySshConnection(data) {
    return request.post(`${BASE_URL}/verify-ssh`, data)
  },

  /**
   * 切换资产启用状态
   * @param {number} assetId 资产ID
   * @param {boolean} enabled 是否启用
   * @returns {Promise}
   */
  async toggleAssetStatus(assetId, enabled) {
    return request({
      url: `${BASE_URL}/${assetId}/toggle`,
      method: 'post',
      data: { enabled }
    })
  }
} 