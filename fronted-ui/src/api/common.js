import request from '@/utils/request'

const BASE_URL = '/common'

export const commonApi = {
  /**
   * 翻译文本
   * @param {string} text - 需要翻译的文本
   * @param {string} [to_lang='zh'] - 目标语言
   * @param {string} [from_lang='auto'] - 源语言
   * @param {string} [provider] - 翻译服务提供商
   * @param {boolean} [whole_text=true] - 是否整体翻译，默认为true保持文本完整性
   * @returns {Promise<Object>} 翻译结果
   */
  async translateText(text, to_lang = 'zh', from_lang = 'auto', provider = null, whole_text = true) {
    const params = {
      text,
      to_lang,
      from_lang,
      whole_text
    }
    
    // 如果指定了provider，添加到参数中
    if (provider) {
      params.provider = provider
    }
    
    return request.post(`${BASE_URL}/translate`, params)
  },

  /**
   * 批量翻译文本
   * @param {Array<string>} texts - 需要翻译的文本数组
   * @param {string} [to_lang='zh'] - 目标语言
   * @param {string} [from_lang='auto'] - 源语言
   * @returns {Promise<Object>} 翻译结果
   */
  async batchTranslate(texts, to_lang = 'zh', from_lang = 'auto') {
    return request.post(`${BASE_URL}/batch-translate`, {
      texts,
      to_lang,
      from_lang
    })
  },

  /**
   * GET方式翻译文本（适用于简单翻译）
   * @param {string} text - 需要翻译的文本
   * @param {string} [to_lang='zh'] - 目标语言
   * @param {string} [from_lang='auto'] - 源语言
   * @param {boolean} [whole_text=true] - 是否整体翻译
   * @returns {Promise<Object>} 翻译结果
   */
  async translateTextGet(text, to_lang = 'zh', from_lang = 'auto', whole_text = true) {
    return request.get(`${BASE_URL}/translate`, {
      params: {
        text,
        to_lang,
        from_lang,
        whole_text
      }
    })
  }
} 