from flask import Blueprint, request
from ...database import get_db
from ...services.config_service import ConfigService
from ...utils.logger import setup_logger
from ...utils.response import success_json, error_json, exception_handler, response_template
from ...models.constants import COMMON_TRAINING_PARAMS, COMMON_MARK_PARAMS, FLUX_LORA_PARAMS

logger = setup_logger('settings_api')
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('', methods=['GET'])
@exception_handler
def get_settings():
    """获取所有设置"""
    settings = ConfigService.get_config()
    return success_json(settings)

@settings_bp.route('', methods=['PUT'])
@exception_handler
def update_settings():
    """更新设置"""
    data = request.get_json()
    if not data:
        return response_template("bad_request", msg="无效的设置数据")
        
    result = ConfigService.update_config(data)
    if result:
        return success_json(None, "设置更新成功")
    return error_json(msg="设置更新失败")

@settings_bp.route('/<key>', methods=['GET'])
@exception_handler
def get_setting_value(key):
    """获取指定设置值"""
    value = ConfigService.get_value(key)
    if value is not None:
        return success_json({key: value})
    return response_template("not_found", msg=f"设置项 {key} 不存在")

@settings_bp.route('/common-training-params', methods=['GET'])
@exception_handler
def get_common_training_params():
    """获取常用训练参数列表"""
    return success_json(COMMON_TRAINING_PARAMS)

@settings_bp.route('/common-mark-params', methods=['GET'])
@exception_handler
def get_common_mark_params():
    """获取常用标记参数列表"""
    return success_json(COMMON_MARK_PARAMS)

@settings_bp.route('/flux-lora-params', methods=['GET'])
@exception_handler
def get_flux_lora_params():
    """获取Flux-Lora特有参数列表"""
    return success_json(FLUX_LORA_PARAMS)

@settings_bp.route('/tasks/<int:task_id>/mark-config', methods=['GET'])
@exception_handler
def get_task_mark_config(task_id):
    """获取任务的打标配置"""
    mark_config = ConfigService.get_task_mark_config(task_id)
    if mark_config is None:
        return response_template("not_found", code=1004, msg="任务不存在或无法获取打标配置")
    return success_json(mark_config)

@settings_bp.route('/tasks/<int:task_id>/training-config', methods=['GET'])
@exception_handler
def get_task_training_config(task_id):
    """获取任务的训练配置"""
    training_config = ConfigService.get_task_training_config(task_id)
    if training_config is None:
        return response_template("not_found", code=1004, msg="任务不存在或无法获取训练配置")
    return success_json(training_config) 

@settings_bp.route('/assets/<int:asset_id>/training-config', methods=['GET'])
@exception_handler
def get_asset_lora_config(asset_id):
    """获取资产的Lora训练配置"""
    config = ConfigService.get_asset_lora_config(asset_id)
    if config is None:
        return response_template("not_found", code=1004, msg="资产不存在或获取配置失败")
    return success_json(config)

@settings_bp.route('/assets/<int:asset_id>/ai-engine-config', methods=['GET'])
@exception_handler
def get_asset_ai_engine_config(asset_id):
    """获取资产的AI引擎配置"""
    config = ConfigService.get_asset_ai_engine_config(asset_id)
    if config is None:
        return response_template("not_found", code=1004, msg="资产不存在或获取配置失败")
    return success_json(config) 