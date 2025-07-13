from typing import Dict, Any, List, Optional
import requests
import random
import hashlib
import json
import time
import urllib.parse
from ..utils.logger import setup_logger
from ..services.config_service import ConfigService

logger = setup_logger('common_service')

class CommonService:
    """
    系统通用接口服务
    提供各种常用功能接口
    """
    
    @staticmethod
    def _preprocess_tags(text: str) -> List[str]:
        """
        预处理标签列表，处理逗号分隔的标签
        
        Args:
            text: 输入文本
            
        Returns:
            处理后的标签列表
        """
        # 检查是否是标签列表（包含逗号分隔的短语）
        if ',' in text:
            # 分割标签并清理
            tags = [tag.strip() for tag in text.split(',')]
            # 去重但保持顺序
            unique_tags = []
            seen = set()
            for tag in tags:
                if tag and tag not in seen:
                    unique_tags.append(tag)
                    seen.add(tag)
            return unique_tags
        else:
            return [text.strip()]
    
    @staticmethod
    def translate_text(text: str, to_lang: str = None, from_lang: str = None, provider: str = None, whole_text: bool = True) -> Dict[str, Any]:
        """
        调用翻译API翻译文本（支持百度翻译和谷歌翻译）
        
        Args:
            text: 要翻译的文本
            to_lang: 目标语言，默认为系统配置的默认目标语言
            from_lang: 源语言，默认为auto（自动检测）
            provider: 翻译服务提供商，默认从配置获取
            whole_text: 是否整体翻译，默认为True（保持文本完整性）
            
        Returns:
            包含翻译结果的字典
            {
                'success': True/False,
                'result': '翻译结果',
                'from': '源语言',
                'to': '目标语言',
                'provider': '翻译服务提供商',
                'error': '错误信息（如果失败）'
            }
        """
        try:
            # 获取翻译配置
            translate_config = ConfigService.get_value('translate_config', {})
            
            # 确定使用的翻译服务提供商
            if not provider:
                provider = translate_config.get('provider', 'baidu')
            
            # 如果启用整体翻译模式，直接翻译完整文本
            if whole_text:
                logger.info("使用整体翻译模式，保持文本完整性")
                if provider == 'google':
                    return CommonService.google_translate_text(text, to_lang, from_lang)
                else:
                    return CommonService.baidu_translate_text(text, to_lang, from_lang)
            
            # 传统分块翻译模式（向后兼容）
            # 预处理标签
            tags = CommonService._preprocess_tags(text)
            
            # 如果是单个标签，直接翻译
            if len(tags) == 1:
                # 根据提供商调用相应的翻译方法
                if provider == 'google':
                    return CommonService.google_translate_text(text, to_lang, from_lang)
                else:
                    return CommonService.baidu_translate_text(text, to_lang, from_lang)
            else:
                # 多个标签，使用批量翻译
                logger.info(f"检测到多个标签({len(tags)}个)，使用批量翻译")
                batch_result = CommonService.batch_translate(tags, to_lang, from_lang, provider)
                
                if batch_result['success']:
                    # 合并翻译结果
                    translated_tags = []
                    for result in batch_result['results']:
                        if result['success']:
                            translated_tags.append(result['result'])
                        else:
                            # 如果某个标签翻译失败，保持原文
                            logger.warning(f"标签翻译失败，保持原文: {result.get('error', '未知错误')}")
                    
                    combined_result = ', '.join(translated_tags)
                    return {
                        'success': True,
                        'result': combined_result,
                        'from': from_lang or 'auto',
                        'to': to_lang or 'zh',
                        'provider': provider,
                        'tag_count': len(tags)
                    }
                else:
                    # 批量翻译失败，尝试直接翻译原文
                    logger.warning("批量翻译失败，尝试直接翻译原文")
                    if provider == 'google':
                        return CommonService.google_translate_text(text, to_lang, from_lang)
                    else:
                        return CommonService.baidu_translate_text(text, to_lang, from_lang)
                
        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            return {
                'success': False,
                'error': f"翻译失败: {str(e)}",
                'provider': provider or 'unknown'
            }
    
    @staticmethod
    def baidu_translate_text(text: str, to_lang: str = None, from_lang: str = None) -> Dict[str, Any]:
        """
        调用百度翻译API翻译文本
        
        Args:
            text: 要翻译的文本
            to_lang: 目标语言，默认为系统配置的默认目标语言
            from_lang: 源语言，默认为auto（自动检测）
            
        Returns:
            包含翻译结果的字典
            {
                'success': True/False,
                'result': '翻译结果',
                'from': '源语言',
                'to': '目标语言',
                'error': '错误信息（如果失败）'
            }
        """
        try:
            # 获取百度翻译API配置
            config = ConfigService.get_value('baidu_translate_config', {})
            
            if not config or not isinstance(config, dict):
                return {
                    'success': False,
                    'error': '系统未配置百度翻译API',
                    'provider': 'baidu'
                }
            
            # 检查百度翻译是否启用
            if not config.get('enabled', False):
                return {
                    'success': False,
                    'error': '百度翻译功能未启用',
                    'provider': 'baidu'
                }
            
            app_id = config.get('app_id')
            secret_key = config.get('secret_key')
            api_url = config.get('api_url', 'https://fanyi-api.baidu.com/api/trans/vip/translate')
            
            if not app_id or not secret_key:
                return {
                    'success': False,
                    'error': '百度翻译API配置不完整',
                    'provider': 'baidu'
                }
            
            # 设置默认值
            if not from_lang:
                from_lang = config.get('default_from', 'auto')
            if not to_lang:
                to_lang = config.get('default_to', 'zh')
            
            # 处理过长的文本
            if len(text) > 2000:
                text = text[:2000]
                logger.warning('翻译文本过长，已截断至2000字符')
            
            # 准备请求参数
            salt = str(random.randint(32768, 65536))
            sign = app_id + text + salt + secret_key
            sign = hashlib.md5(sign.encode()).hexdigest()
            
            params = {
                'q': text,
                'from': from_lang,
                'to': to_lang,
                'appid': app_id,
                'salt': salt,
                'sign': sign
            }
            
            # 发送请求
            response = requests.get(api_url, params=params, timeout=10)
            result = response.json()
            
            if 'error_code' in result:
                return {
                    'success': False,
                    'error': f"百度翻译API错误: {result.get('error_code')} - {result.get('error_msg', '未知错误')}",
                    'provider': 'baidu'
                }
            
            # 处理翻译结果
            translated_text = ""
            src_lang = from_lang
            
            if 'trans_result' in result:
                translated_text = ' '.join([item['dst'] for item in result['trans_result']])
                src_lang = result.get('from', from_lang)
            
            return {
                'success': True,
                'result': translated_text,
                'from': src_lang,
                'to': to_lang,
                'provider': 'baidu'
            }
            
        except Exception as e:
            logger.error(f"百度翻译失败: {str(e)}")
            return {
                'success': False,
                'error': f"百度翻译失败: {str(e)}",
                'provider': 'baidu'
            }
    
    @staticmethod
    def batch_translate(texts: List[str], to_lang: str = None, from_lang: str = None, provider: str = None) -> Dict[str, Any]:
        """
        批量翻译多个文本
        
        Args:
            texts: 要翻译的文本列表
            to_lang: 目标语言，默认为系统配置的默认目标语言
            from_lang: 源语言，默认为auto（自动检测）
            provider: 翻译服务提供商，默认从配置获取
            
        Returns:
            包含所有翻译结果的字典
        """
        results = []
        success_count = 0
        
        # 获取翻译配置
        translate_config = ConfigService.get_value('translate_config', {})
        if not provider:
            provider = translate_config.get('provider', 'baidu')
        
        for text in texts:
            # 为避免API调用过于频繁，添加短暂延迟
            time.sleep(0.2)
            
            # 直接调用具体的翻译服务，避免递归调用
            if provider == 'google':
                result = CommonService.google_translate_text(text, to_lang, from_lang)
            else:
                result = CommonService.baidu_translate_text(text, to_lang, from_lang)
            
            results.append(result)
            if result['success']:
                success_count += 1
        
        return {
            'success': success_count == len(texts),
            'results': results,
            'total': len(texts),
            'success_count': success_count,
            'failed_count': len(texts) - success_count
        }
    
    @staticmethod
    def google_translate_text(text: str, to_lang: str = None, from_lang: str = None) -> Dict[str, Any]:
        """
        调用免费谷歌翻译API翻译文本
        
        Args:
            text: 要翻译的文本
            to_lang: 目标语言，默认为系统配置的默认目标语言
            from_lang: 源语言，默认为auto（自动检测）
            
        Returns:
            包含翻译结果的字典
            {
                'success': True/False,
                'result': '翻译结果',
                'from': '源语言',
                'to': '目标语言',
                'provider': 'google',
                'error': '错误信息（如果失败）'
            }
        """
        try:
            # 获取谷歌翻译配置
            config = ConfigService.get_value('google_translate_config', {})
            
            if not config or not isinstance(config, dict):
                # 使用默认配置
                config = {
                    'enabled': True,
                    'api_url': 'https://translate.googleapis.com/translate_a/single',
                    'default_from': 'auto',
                    'default_to': 'zh'
                }
            
            # 检查谷歌翻译是否启用
            if not config.get('enabled', True):
                return {
                    'success': False,
                    'error': '谷歌翻译功能未启用',
                    'provider': 'google'
                }
            
            # 设置默认值
            if not from_lang:
                from_lang = config.get('default_from', 'auto')
            if not to_lang:
                to_lang = config.get('default_to', 'zh')
            
            # 处理过长的文本
            if len(text) > 5000:
                text = text[:5000]
                logger.warning('谷歌翻译文本过长，已截断至5000字符')
            
            # 构建请求URL和参数
            api_url = config.get('api_url', 'https://translate.googleapis.com/translate_a/single')
            
            # 语言代码映射（百度到谷歌）
            lang_mapping = {
                'zh': 'zh-cn',
                'en': 'en',
                'jp': 'ja',
                'kor': 'ko',
                'fra': 'fr',
                'spa': 'es',
                'th': 'th',
                'ara': 'ar',
                'ru': 'ru',
                'pt': 'pt',
                'de': 'de',
                'it': 'it',
                'nl': 'nl',
                'pl': 'pl',
                'auto': 'auto'
            }
            
            # 转换语言代码
            google_from_lang = lang_mapping.get(from_lang, from_lang)
            google_to_lang = lang_mapping.get(to_lang, to_lang)
            
            # 准备请求参数
            params = {
                'client': 'gtx',
                'sl': google_from_lang,
                'tl': google_to_lang,
                'dt': 't',
                'q': text
            }
            
            # 设置请求头以模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 发送请求
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"谷歌翻译API请求失败，状态码: {response.status_code}",
                    'provider': 'google'
                }
            
            # 解析响应
            try:
                result = response.json()
                if result and len(result) > 0 and result[0]:
                    translated_text = ''.join([item[0] for item in result[0] if item[0]])
                    detected_lang = result[2] if len(result) > 2 else google_from_lang
                    
                    return {
                        'success': True,
                        'result': translated_text,
                        'from': detected_lang,
                        'to': google_to_lang,
                        'provider': 'google'
                    }
                else:
                    return {
                        'success': False,
                        'error': '谷歌翻译API返回数据格式错误',
                        'provider': 'google'
                    }
                    
            except (json.JSONDecodeError, IndexError, TypeError) as e:
                return {
                    'success': False,
                    'error': f"谷歌翻译API响应解析失败: {str(e)}",
                    'provider': 'google'
                }
            
        except Exception as e:
            logger.error(f"谷歌翻译失败: {str(e)}")
            return {
                'success': False,
                'error': f"谷歌翻译失败: {str(e)}",
                'provider': 'google'
            } 