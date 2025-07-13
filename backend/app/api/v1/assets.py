from flask import Blueprint, request
from ...services.asset_service import AssetService
from ...services.config_service import ConfigService
from ...utils.logger import setup_logger
from ...utils.validators import validate_asset_create
from ...schemas.asset import SshVerifyRequest,AssetCreate, AssetUpdate
from ...utils.response import success_json, error_json, exception_handler, response_template
from ...models.asset import Asset as AssetModel
from ...utils.common import copy_attributes

logger = setup_logger('assets_api')
assets_bp = Blueprint('assets', __name__)

@assets_bp.route('', methods=['GET'])
@exception_handler
def list_assets():
    """获取资产列表"""
    assets = AssetService.list_assets()
    return success_json([asset.dict() for asset in assets])

@assets_bp.route('', methods=['POST'])
@exception_handler
def create_asset():
    """创建新资产"""
    asset_data = AssetCreate(**request.json)
    asset = AssetService.create_asset(asset_data)
    if not asset:
        return error_json(2001, "创建资产失败")
    return response_template("created", data=asset.dict())

@assets_bp.route('/<int:asset_id>', methods=['PUT'])
@exception_handler
def update_asset(asset_id):
    """更新资产"""
    logger.debug(f"更新资产: {asset_id}, 原始请求数据: {request.json}")
    
    # 检查是否为本地资产
    from ...services.local_asset_service import LocalAssetService
    is_local = LocalAssetService.is_local_asset(asset_id)
    logger.info(f"资产 {asset_id} 是否为本地资产: {is_local}")
    
    # 如果是本地资产，确保is_local字段为True
    if is_local and 'is_local' not in request.json:
        request_data = dict(request.json)
        request_data['is_local'] = True
        logger.info(f"为本地资产 {asset_id} 添加is_local=True标志")
    else:
        request_data = request.json
        
    logger.debug(f"处理后的请求数据: {request_data}")
    update_data = AssetUpdate(**request_data)
    logger.debug(f"验证后的更新数据: {update_data}")
    
    asset = AssetService.update_asset(asset_id, update_data)
    if not asset:
        logger.warning(f"资产不存在或更新失败: {asset_id}")
        return response_template("not_found", code=2002, msg="资产不存在或更新失败")
        
    return response_template("updated", data=asset.dict())

@assets_bp.route('/<int:asset_id>', methods=['DELETE'])
@exception_handler
def delete_asset(asset_id):
    """删除资产"""
    if AssetService.delete_asset(asset_id):
        return response_template("deleted")
    return error_json(2003, "删除资产失败")

@assets_bp.route('/<int:asset_id>/verify', methods=['POST'])
@exception_handler
def verify_capabilities(asset_id):
    """验证资产能力"""
    logger.info(f"开始验证资产 {asset_id} 的能力")
    results = AssetService.verify_capabilities(asset_id)
    logger.info(f"验证资产 {asset_id} 能力成功: {results}")
    return success_json(results)

@assets_bp.route('/verify-ssh', methods=['POST'])
@exception_handler
def verify_ssh_connection():
    """验证SSH连接"""
    # 验证请求数据
    asset_data = SshVerifyRequest(**request.json)
    
    # 创建临时资产对象用于验证
    asset = AssetModel()
    
    # 使用copy_attributes工具函数拷贝属性
    copy_attributes(asset_data, asset)
    
    # 执行SSH连接验证
    from ...services.terminal_service import TerminalService
    success, message = TerminalService.verify_asset_ssh_connection(asset)
    
    if success:
        return success_json(None, message)
    else:
        return error_json(4001, message)

@assets_bp.route('/<int:asset_id>/configs/lora', methods=['GET'])
@exception_handler
def get_asset_lora_config(asset_id):
    """获取资产的Lora训练配置"""
    config = ConfigService.get_asset_lora_config(asset_id)
    if config is None:
        return response_template("not_found", code=1004, msg="资产不存在")
    return success_json(config)

@assets_bp.route('/<int:asset_id>/configs/ai-engine', methods=['GET'])
@exception_handler
def get_asset_ai_engine_config(asset_id):
    """获取资产的AI引擎配置"""
    config = ConfigService.get_asset_ai_engine_config(asset_id)
    if config is None:
        return response_template("not_found", code=1004, msg="资产不存在")
    return success_json(config)

@assets_bp.route('/<int:asset_id>/headers/lora', methods=['GET'])
@exception_handler
def get_asset_lora_headers(asset_id):
    """获取资产的Lora训练请求头"""
    headers = ConfigService.get_asset_lora_headers(asset_id)
    if headers is None:
        return response_template("not_found", code=1004, msg="资产不存在")
    return success_json(headers)

@assets_bp.route('/<int:asset_id>/headers/ai-engine', methods=['GET'])
@exception_handler
def get_asset_ai_engine_headers(asset_id):
    """获取资产的AI引擎请求头"""
    headers = ConfigService.get_asset_ai_engine_headers(asset_id)
    if headers is None:
        return response_template("not_found", code=1004, msg="资产不存在")
    return success_json(headers) 

@assets_bp.route('/<int:asset_id>/toggle', methods=['POST'])
@exception_handler
def toggle_asset(asset_id):
    """开启或关闭资产"""
    data = request.json
    if 'enabled' not in data:
        return error_json(2004, "请提供enabled参数")
    
    enabled = bool(data['enabled'])
    asset = AssetService.toggle_asset_status(asset_id, enabled)
    
    if not asset:
        return response_template("not_found", code=2002, msg="资产不存在")
    
    return success_json(asset.dict(), f"资产已{'启用' if enabled else '禁用'}") 