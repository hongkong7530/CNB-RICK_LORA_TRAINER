from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.task import Task, TaskStatus
from ..models.asset import Asset as AssetModel
from ..schemas.asset import AssetCreate, AssetUpdate, Asset
from ..database import get_db
from ..utils.logger import setup_logger
from ..utils.common import copy_attributes, generate_domain_url
from ..services.terminal_service import TerminalService
from ..models.constants import DOMAIN_ACCESS_CONFIG
from ..utils.train_handler import TrainRequestHandler
from task_scheduler.comfyui_api import ComfyUIAPI,ComfyUIConfig
from urllib.parse import urlparse

logger = setup_logger('asset_service')

class AssetService:
    @staticmethod
    def list_assets() -> List[Asset]:
        """获取资产列表"""
        with get_db() as db:
            assets = db.query(AssetModel).all()
            return [Asset.from_orm(asset) for asset in assets]

    @staticmethod
    def create_asset(asset_data: AssetCreate) -> Optional[Asset]:
        """创建新资产"""
        try:
            logger.debug(f"开始创建资产: {asset_data.dict()}")
            with get_db() as db:
                # 检查资产名称是否已存在
                existing = db.query(AssetModel).filter(AssetModel.name == asset_data.name).first()
                if existing:
                    logger.error(f"资产名称已存在: {asset_data.name}")
                    raise ValueError("资产名称已存在")

                asset = AssetModel(**asset_data.dict())
                
                # 自动检测是否为域名访问模式
                if DOMAIN_ACCESS_CONFIG['SSH_DOMAIN_SUFFIX'] in asset.ip:
                    asset.port_access_mode = 'DOMAIN'
                    logger.info(f"检测到SSH域名格式，设置为域名访问模式: {asset.ip}")
                else:
                    asset.port_access_mode = 'DIRECT'
                
                # 设置初始状态为 PENDING
                asset.status = 'PENDING'
                
                # 如果是本地资产，无需验证SSH连接
                if asset.is_local:
                    asset.status = 'CONNECTED'  # 本地资产始终为已连接状态
                else:
                    # 验证SSH连接
                    try:
                        success, message = TerminalService.verify_asset_ssh_connection(asset)
                        if success:
                            asset.status = 'CONNECTED'
                        else:
                            asset.status = 'CONNECTION_ERROR'
                            logger.error(f"SSH connection verification failed: {message}")
                    except Exception as e:
                        logger.error(f"SSH connection verification failed: {str(e)}")
                        asset.status = 'CONNECTION_ERROR'
                
                logger.debug("添加资产到数据库")
                db.add(asset)
                try:
                    db.commit()
                    logger.debug("数据库提交成功")
                    db.refresh(asset)
                    logger.info(f"资产创建成功: ID={asset.id}, 名称={asset.name}")
                    return Asset.from_orm(asset)
                except Exception as e:
                    logger.error(f"数据库操作失败: {str(e)}")
                    db.rollback()
                    raise
        except Exception as e:
            logger.error(f"创建资产失败: {str(e)}", exc_info=True)
            if isinstance(e, ValueError):
                raise
            return None

    @staticmethod
    def update_asset(asset_id: int, update_data: AssetUpdate) -> Optional[Asset]:
        """更新资产"""
        try:
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    return None
                
                # 更新资产数据
                update_dict = update_data.dict(exclude_unset=True)
                copy_attributes(update_dict, asset)
                
                # 如果IP被更新，自动检测是否为域名访问模式
                if 'ip' in update_dict:
                    if DOMAIN_ACCESS_CONFIG['SSH_DOMAIN_SUFFIX'] in asset.ip:
                        asset.port_access_mode = 'DOMAIN'
                        logger.info(f"检测到SSH域名格式，设置为域名访问模式: {asset.ip}")
                    else:
                        asset.port_access_mode = 'DIRECT'
                
                # 如果是本地资产，无需验证SSH连接
                if asset.is_local:
                    asset.status = 'CONNECTED'  # 本地资产始终为已连接状态
                # 如果不是本地资产且更新了连接信息，重新验证SSH连接
                elif any(key in update_dict for key in ['ip', 'ssh_port', 'ssh_username', 'ssh_key_path']):
                    try:
                        success, message = TerminalService.verify_asset_ssh_connection(asset)
                        if success:
                            asset.status = 'CONNECTED'
                        else:
                            asset.status = 'CONNECTION_ERROR'
                            logger.error(f"SSH connection verification failed: {message}")
                    except Exception as e:
                        logger.error(f"SSH connection verification failed: {str(e)}")
                        asset.status = 'CONNECTION_ERROR'
                
                db.commit()
                db.refresh(asset)
                return Asset.from_orm(asset)
        except Exception as e:
            logger.error(f"Update asset failed: {str(e)}")
            return None

    @staticmethod
    def delete_asset(asset_id: int) -> bool:
        """删除资产"""
        try:
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if asset:
                    db.delete(asset)
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Delete asset failed: {str(e)}")
            return False

    @staticmethod
    def verify_capabilities(asset_id: int, capability_type: str = None) -> dict:
        """
        验证资产能力
        
        Args:
            asset_id: 资产ID
            capability_type: 指定验证的能力类型，可选值为 'lora_training' 或 'ai_engine'，
                            如果不指定则验证所有能力
        """
        try:
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    raise ValueError("资产不存在")

                results = {
                    'lora_training': False,
                    'ai_engine': False,
                    'ssh_connection': True  # 默认本地资产SSH连接为True
                }

                # 如果是本地资产，确保使用127.0.0.1作为连接地址
                if not asset.is_local:
                    # 非本地资产需要验证SSH连接
                    ssh_success, ssh_message = TerminalService.verify_asset_ssh_connection(asset)
                    results['ssh_connection'] = ssh_success
                    
                    if not ssh_success:
                        logger.debug(f"资产 {asset_id} SSH连接验证失败: {ssh_message}")
                        # SSH连接失败，无需继续验证其他能力
                        return results

                # 准备基本连接信息
                # 对于本地资产，始终使用127.0.0.1
                base_ip = '127.0.0.1' if asset.is_local else asset.ip
                    
                # 验证Lora训练能力
                if (capability_type is None or capability_type == 'lora_training') and asset.lora_training.get('enabled'):
                    try:
                        handler = TrainRequestHandler(asset)
                        tasks_data = handler.get_tasks()
                        results['lora_training'] = True
                        asset.lora_training = {**asset.lora_training, 'verified': True}
                        logger.info(f"Lora训练服务通过域名验证成功: {asset.ip}:{asset.lora_training.get('port')}")
                    except Exception as e:
                        asset.lora_training = {**asset.lora_training, 'verified': False}

                # 验证AI引擎能力
                if (capability_type is None or capability_type == 'ai_engine') and asset.ai_engine.get('enabled'):
                    try:
                        port = asset.ai_engine.get('port')
                        if not port:
                            asset.ai_engine = {**asset.ai_engine, 'verified': False}
                            logger.warning("AI引擎服务未配置端口")
                        else:
                            # 如果是域名访问模式，尝试使用特殊域名格式
                            if asset.port_access_mode == 'DOMAIN':
                                domain_url,port = generate_domain_url(asset.ip, port)
                                if domain_url:
                                    try:
                                        comfy_config = ComfyUIConfig(
                                            host=domain_url,
                                            port=port
                                        )
                                        api = ComfyUIAPI(comfy_config)
                                        stats = api.get_system_stats()
                                        
                                        if stats:
                                            results['ai_engine'] = True
                                            asset.ai_engine = {**asset.ai_engine, 'verified': True}
                                            logger.info(f"AI引擎服务通过域名验证成功: {domain_url}")
                                    except Exception as e:
                                        logger.warning(f"通过域名验证AI引擎服务失败: {str(e)}")
                            
                            # 如果域名模式失败或不是域名模式，尝试直接连接
                            if not results['ai_engine']:
                                try:
                                    comfy_config = ComfyUIConfig(
                                        host=base_ip,
                                        port=port
                                    )
                                    api = ComfyUIAPI(comfy_config)
                                    stats = api.get_system_stats()
                                    
                                    if stats:
                                        results['ai_engine'] = True
                                        asset.ai_engine = {**asset.ai_engine, 'verified': True}
                                        logger.info(f"AI引擎服务直接连接验证成功: {base_ip}:{port}")
                                    else:
                                        logger.warning("获取ComfyUI系统状态失败")
                                        asset.ai_engine = {**asset.ai_engine, 'verified': False}
                                except Exception as e:
                                    logger.warning(f"直接连接验证AI引擎服务失败: {str(e)}")
                                    asset.ai_engine = {**asset.ai_engine, 'verified': False}
                    except Exception as e:
                        logger.warning(f"验证AI引擎能力时发生错误: {str(e)}")
                        asset.ai_engine = {**asset.ai_engine, 'verified': False}

                # 提交所有变更
                db.commit()
                return results
        except Exception as e:
            raise

    @staticmethod
    def verify_all_assets(capability_type: str) -> List[Dict]:
        """
        立即验证所有资产，并返回可用的资产列表
        
        Args:
            capability_type: 要验证的能力类型，必传参数，可选值: 'ai_engine', 'lora_training'
            
        Returns:
            List[Dict]: 可用资产列表
        """
        if not capability_type:
            logger.error("验证资产失败: capability_type 参数必须指定")
            raise ValueError("必须指定验证引擎类型")
            
        try:
            logger.info(f"开始验证所有资产，能力类型: {capability_type}")
            available_assets = []
            
            with get_db() as db:
                # 获取所有已启用的资产
                assets = db.query(AssetModel).filter(AssetModel.enabled == True).all()
                
                for asset in assets:
                    try:
                        # 验证资产能力
                        results = AssetService.verify_capabilities(asset.id, capability_type)
                        
                        # 首先检查SSH连接是否成功（对于非本地资产）
                        if not asset.is_local and not results.get('ssh_connection', False):
                            logger.debug(f"资产 {asset.id} SSH连接验证失败，跳过该资产")
                            continue
                        
                        # 根据验证结果筛选可用资产
                        if capability_type == 'ai_engine' and results.get('ai_engine'):
                            available_assets.append(asset)
                        elif capability_type == 'lora_training' and results.get('lora_training'):
                            available_assets.append(asset)
                            
                    except Exception as e:
                        logger.error(f"验证资产 {asset.id} 时出错: {str(e)}")
            
            logger.info(f"资产验证完成，可用资产数量: {len(available_assets)}")
            return available_assets
        except Exception as e:
            logger.error(f"验证所有资产失败: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def get_asset(asset_id: int) -> Optional[Asset]:
        """获取单个资产"""
        try:
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if asset:
                    return Asset.from_orm(asset)
                return None
        except Exception as e:
            logger.error(f"获取资产失败: {str(e)}")
            return None

    @staticmethod
    def toggle_asset_status(asset_id: int, enabled: bool) -> Optional[Asset]:
        """
        开启或关闭资产
        
        Args:
            asset_id: 资产ID
            enabled: True表示启用，False表示禁用
            
        Returns:
            更新后的资产对象，如果资产不存在则返回None
        """
        try:
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    logger.warning(f"资产不存在: {asset_id}")
                    return None
                
                asset.enabled = enabled
                logger.info(f"资产 {asset_id} ({asset.name}) 状态已更新为: {'启用' if enabled else '禁用'}")
                
                db.commit()
                db.refresh(asset)
                return Asset.from_orm(asset)
        except Exception as e:
            logger.error(f"更新资产状态失败: {str(e)}", exc_info=True)
            return None