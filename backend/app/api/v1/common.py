from flask import Blueprint, request, jsonify
from typing import List, Dict, Any
from ...services.common_service import CommonService
from ...services.config_service import ConfigService
from ...utils.response import error, success, success_json, error_json, exception_handler, response_template

common_bp = Blueprint('common_bp', __name__)

@common_bp.route('/translate', methods=['POST'])
def translate_text():
    """
    调用百度翻译API翻译文本
    """
    try:
        # 检查翻译功能是否开启
        if not ConfigService.is_translate_enabled():
            return error(msg="翻译功能未开启")
            
        data = request.get_json()
        if not data or 'text' not in data:
            return error(msg="缺少必要参数: text")
        
        text = data.get('text')
        to_lang = data.get('to_lang')
        from_lang = data.get('from_lang')
        provider = data.get('provider')
        whole_text = data.get('whole_text', True)  # 默认使用整体翻译模式
        
        result = CommonService.translate_text(
            text=text,
            to_lang=to_lang,
            from_lang=from_lang,
            provider=provider,
            whole_text=whole_text
        )
        
        if not result['success']:
            return error(msg=result.get('error', '翻译失败'))
        
        return success(data=result)
    except Exception as e:
        return error(msg=f"翻译失败: {str(e)}")

@common_bp.route('/batch-translate', methods=['POST'])
def batch_translate():
    """
    批量翻译多个文本
    """
    try:
        # 检查翻译功能是否开启
        if not ConfigService.is_translate_enabled():
            return error(msg="翻译功能未开启")
            
        data = request.get_json()
        if not data or 'texts' not in data:
            return error(msg="缺少必要参数: texts")
        
        texts = data.get('texts')
        to_lang = data.get('to_lang')
        from_lang = data.get('from_lang')
        provider = data.get('provider')
        
        if not isinstance(texts, list):
            return error(msg="texts参数必须是文本列表")
        
        result = CommonService.batch_translate(
            texts=texts,
            to_lang=to_lang,
            from_lang=from_lang,
            provider=provider
        )
        
        return success(data=result)
    except Exception as e:
        return error(msg=f"批量翻译失败: {str(e)}")

@common_bp.route('/translate', methods=['GET'])
def translate_text_get():
    """
    调用百度翻译API翻译文本(GET方式)
    """
    try:
        # 检查翻译功能是否开启
        if not ConfigService.is_translate_enabled():
            return error(msg="翻译功能未开启")
            
        text = request.args.get('text')
        to_lang = request.args.get('to_lang')
        from_lang = request.args.get('from_lang')
        provider = request.args.get('provider')
        whole_text = request.args.get('whole_text', 'true').lower() == 'true'  # GET参数转换为布尔值
        
        if not text:
            return error(msg="缺少必要参数: text")
        
        result = CommonService.translate_text(
            text=text,
            to_lang=to_lang,
            from_lang=from_lang,
            provider=provider,
            whole_text=whole_text
        )
        
        if not result['success']:
            return error(msg=result.get('error', '翻译失败'))
        
        return success(data=result)
    except Exception as e:
        return error(msg=f"翻译失败: {str(e)}")