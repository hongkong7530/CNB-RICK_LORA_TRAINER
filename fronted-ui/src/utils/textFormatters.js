/**
 * 文本格式化相关工具函数
 */

/**
 * 高亮标记文本中的特定字符
 * @param {string} text - 需要高亮的文本
 * @param {Array} highlightChars - 需要高亮的字符数组，默认为逗号
 * @param {string} highlightColor - 高亮颜色，默认为红色
 * @returns {string} 处理后的带HTML标签的字符串
 */
export function highlightMarkedText(text, highlightChars = [',', '，'], highlightColor = '#ff3333') {
  if (!text) return '';
  
  // 创建临时div以确保HTML安全
  const tempDiv = document.createElement('div');
  tempDiv.textContent = text;
  const safeText = tempDiv.innerHTML;
  
  // 构建正则表达式匹配所有需要高亮的字符
  const regex = new RegExp(`[${highlightChars.join('')}]`, 'g');
  
  // 高亮匹配的字符
  return safeText.replace(regex, `<span style="color: ${highlightColor}; font-weight: bold;">$&</span>`);
}

/**
 * 清除HTML标签获取纯文本
 * @param {string} html - 包含HTML标签的文本
 * @returns {string} 纯文本内容
 */
export function stripHtml(html) {
  return html ? html.replace(/<[^>]*>?/gm, '') : '';
} 