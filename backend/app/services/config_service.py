from typing import Dict, Any, Optional
from ..database import get_db
from ..models.setting import Setting
from ..models.task import Task
from ..models.asset import Asset
from ..schemas.setting import SettingUpdate
from ..utils.logger import setup_logger
import json

logger = setup_logger('config_service')

class ConfigService:
    @staticmethod
    def init_settings():
        """初始化系统设置"""
        try:
            with get_db() as db:
                # 检查是否需要初始化
                if db.query(Setting).count() == 0:
                    # 获取默认设置
                    default_settings = Setting.get_defaults()
                    
                    # 插入默认设置
                    for key, config_item in default_settings.items():
                        setting = Setting(
                            key=key,
                            value=config_item['value'],
                            type=config_item['type'],
                            description=config_item['description']
                        )
                        db.add(setting)
                    db.commit()
                    logger.info("系统设置初始化完成")
                else:
                    # 检查是否有新增的默认配置需要添加
                    default_settings = Setting.get_defaults()
                    existing_keys = [s.key for s in db.query(Setting.key).all()]
                    
                    for key, config_item in default_settings.items():
                        if key not in existing_keys:
                            setting = Setting(
                                key=key,
                                value=config_item['value'],
                                type=config_item['type'],
                                description=config_item['description']
                            )
                            db.add(setting)
                    
                    if db.new or db.dirty or db.deleted:
                        db.commit()
                        logger.info("系统设置更新完成")
        except Exception as e:
            logger.error(f"初始化系统设置失败: {str(e)}")
            raise

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """获取所有配置"""
        try:
            with get_db() as db:
                settings = db.query(Setting).all()
                config_dict = {}
                for setting in settings:
                    if hasattr(setting, 'parse_value'):
                        config_dict[setting.key] = setting.parse_value()
                    else:
                        if setting.type == 'integer':
                            config_dict[setting.key] = int(setting.value)
                        elif setting.type == 'json':
                            try:
                                config_dict[setting.key] = json.loads(setting.value)
                            except:
                                config_dict[setting.key] = {}
                        else:
                            config_dict[setting.key] = setting.value
                return config_dict
        except Exception as e:
            logger.error(f"获取配置失败: {str(e)}")
            # 返回默认值
            default_settings = Setting.get_defaults()
            return {k: ConfigService._parse_default_value(v) for k, v in default_settings.items()}

    @staticmethod
    def _parse_default_value(config_item):
        """解析默认配置值"""
        if config_item['type'] == 'integer':
            return int(config_item['value'])
        elif config_item['type'] == 'json':
            try:
                return json.loads(config_item['value'])
            except:
                return {}
        return config_item['value']

    @staticmethod
    def update_config(config_data: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            with get_db() as db:
                for key, value in config_data.items():
                    setting = db.query(Setting).filter(Setting.key == key).first()
                    if setting:
                        # 根据类型转换值
                        if setting.type == 'json' and not isinstance(value, str):
                            setting.value = json.dumps(value)
                        else:
                            setting.value = str(value)
                    else:
                        # 如果配置项不存在，尝试从默认配置中获取类型
                        default_settings = Setting.get_defaults()
                        if key in default_settings:
                            setting_type = default_settings[key]['type']
                            description = default_settings[key]['description']
                            
                            # 根据类型转换值
                            setting_value = value
                            if setting_type == 'json' and not isinstance(value, str):
                                setting_value = json.dumps(value)
                            else:
                                setting_value = str(value)
                                
                            # 创建新的配置项
                            new_setting = Setting(
                                key=key,
                                value=setting_value,
                                type=setting_type,
                                description=description
                            )
                            db.add(new_setting)
                
                db.commit()
                logger.info("配置更新成功")
                return True
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False 

    @staticmethod
    def get_value(key: str, default: Any = None) -> Any:
        """
        获取指定配置值
        :param key: 配置键
        :param default: 默认值
        :return: 配置值
        """
        try:
            with get_db() as db:
                setting = db.query(Setting).filter(Setting.key == key).first()
                if not setting:
                    # 如果数据库中没有，返回默认配置或传入的默认值
                    default_settings = Setting.get_defaults()
                    if key in default_settings:
                        return ConfigService._parse_default_value(default_settings[key])
                    return default

                if hasattr(setting, 'parse_value'):
                    return setting.parse_value()
                elif setting.type == 'integer':
                    return int(setting.value)
                elif setting.type == 'json':
                    try:
                        return json.loads(setting.value)
                    except:
                        return {}
                return setting.value

        except Exception as e:
            logger.error(f"获取配置值失败 [{key}]: {str(e)}")
            # 如果出错，返回默认配置或传入的默认值
            default_settings = Setting.get_defaults()
            if key in default_settings:
                return ConfigService._parse_default_value(default_settings[key])
            return default 

    @staticmethod
    def get_global_mark_config() -> Dict[str, Any]:
        """
        从数据库获取全局打标配置
        
        Returns:
            全局打标配置字典
        """
        try:
            with get_db() as db:
                setting = db.query(Setting).filter(Setting.key == 'mark_config').first()
                if setting and setting.type == 'json':
                    try:
                        return json.loads(setting.value)
                    except json.JSONDecodeError:
                        logger.error("解析mark_config失败，返回空字典")
                        return {}
                return {}
        except Exception as e:
            logger.error(f"获取全局打标配置失败: {str(e)}")
            return {}
            
    @staticmethod
    def get_global_lora_training_config() -> Dict[str, Any]:
        """
        从数据库获取全局Lora训练配置
        
        Returns:
            全局Lora训练配置字典
        """
        try:
            with get_db() as db:
                setting = db.query(Setting).filter(Setting.key == 'lora_training_config').first()
                if setting and setting.type == 'json':
                    try:
                        return json.loads(setting.value)
                    except json.JSONDecodeError:
                        logger.error("解析lora_training_config失败，返回空字典")
                        return {}
                return {}
        except Exception as e:
            logger.error(f"获取全局Lora训练配置失败: {str(e)}")
            return {}
            
    @staticmethod
    def get_global_ai_engine_config() -> Dict[str, Any]:
        """
        从数据库获取全局AI引擎配置
        
        Returns:
            全局AI引擎配置字典
        """
        try:
            with get_db() as db:
                setting = db.query(Setting).filter(Setting.key == 'ai_engine_config').first()
                if setting and setting.type == 'json':
                    try:
                        return json.loads(setting.value)
                    except json.JSONDecodeError:
                        logger.error("解析ai_engine_config失败，返回空字典")
                        return {}
                return {}
        except Exception as e:
            logger.error(f"获取全局AI引擎配置失败: {str(e)}")
            return {}
            
    @staticmethod
    def get_global_headers_config(header_type: str = None) -> Dict[str, Any]:
        """
        从数据库获取全局请求头配置
        
        Args:
            header_type: 请求头类型，可选值为 'lora_training', 'ai_engine', 'mark_engine'
                        如果不指定则返回所有请求头配置
        
        Returns:
            全局请求头配置字典
        """
        try:
            with get_db() as db:
                if header_type:
                    # 获取特定类型的请求头
                    key = f'{header_type}_headers'
                    setting = db.query(Setting).filter(Setting.key == key).first()
                    if setting and setting.type == 'json':
                        try:
                            return json.loads(setting.value)
                        except json.JSONDecodeError:
                            logger.error(f"解析{key}失败，返回空字典")
                            return {}
                    return {}
                else:
                    # 获取所有请求头配置
                    setting = db.query(Setting).filter(Setting.key == 'headers_config').first()
                    if setting and setting.type == 'json':
                        try:
                            return json.loads(setting.value)
                        except json.JSONDecodeError:
                            logger.error("解析headers_config失败，返回空字典")
                            return {}
                    return {}
        except Exception as e:
            logger.error(f"获取全局请求头配置失败: {str(e)}")
            return {}

    @staticmethod
    def get_task_mark_config(task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务的打标配置
        如果use_global_mark_config为true，使用全局配置，但仍然应用任务的trigger_words
        如果use_global_mark_config为false，混合全局配置和任务配置
        
        Args:
            task_id: 任务ID
            
        Returns:
            打标配置，如果任务不存在则返回None
        """
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    logger.error(f"任务不存在: {task_id}")
                    return None
                
                if task.use_global_mark_config:
                    # 使用全局配置
                    mark_params = ConfigService.get_global_mark_config()
                    
                    # 即使使用全局配置，也要应用任务配置中的trigger_words属性（如果存在且不为空）
                    if task.mark_config and isinstance(task.mark_config, dict) and 'trigger_words' in task.mark_config:
                        trigger_words = task.mark_config.get('trigger_words')
                        # 只有当trigger_words不为空字符串时才应用
                        if trigger_words is not None and trigger_words.strip() != '':
                            mark_params['trigger_words'] = trigger_words
                    
                    return mark_params
                else:
                    # 混合全局配置和任务配置
                    mark_params = ConfigService.get_global_mark_config()
                
                    # 如果有资产特定配置，优先使用资产配置
                    if task.marking_asset_id:
                        # 获取资产的AI引擎配置
                        asset_config = ConfigService.get_asset_ai_engine_config(task.marking_asset_id)
                        if asset_config:
                            mark_params.update(asset_config)
                
                    # 如果有任务特定配置，混合到全局配置中
                    if task.mark_config and isinstance(task.mark_config, dict):
                        mark_params.update(task.mark_config)
                    
                    return mark_params
                    
        except Exception as e:
            logger.error(f"获取任务打标配置失败, 任务ID: {task_id}, 错误: {str(e)}")
            return None
            
    @staticmethod
    def get_task_training_config(task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务的训练配置
        如果use_global_training_config为true，使用全局配置
        如果use_global_training_config为false，混合全局配置和任务配置
        
        Args:
            task_id: 任务ID
            
        Returns:
            训练配置，如果任务不存在则返回None
        """
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    logger.error(f"任务不存在: {task_id}")
                    return None
                
                if task.use_global_training_config:
                    # 使用全局配置
                    return ConfigService.get_asset_lora_config(task.training_asset_id)
                else:
                    # 混合全局配置和任务配置
                    training_params = ConfigService.get_global_lora_training_config()
                
                    # 如果有资产特定配置，优先使用资产配置
                    if task.training_asset_id:
                        # 获取资产的Lora训练配置
                        asset_config = ConfigService.get_asset_lora_config(task.training_asset_id)
                        if asset_config:
                            training_params.update(asset_config)
                
                    # 如果有任务特定配置，混合到配置中
                    if task.training_config and isinstance(task.training_config, dict):
                        training_params.update(task.training_config)
                    
                    return training_params
                    
        except Exception as e:
            logger.error(f"获取任务训练配置失败, 任务ID: {task_id}, 错误: {str(e)}")
            return None
        
    @staticmethod
    def get_asset_lora_config(asset_id: int) -> Optional[Dict[str, Any]]:
        """
        获取资产的Lora训练配置
        
        Args:
            asset_id: 资产ID
            
        Returns:
            合并后的Lora训练配置，如果资产不存在则返回None
        """
        try:
            with get_db() as db:
                asset = db.query(Asset).filter(Asset.id == asset_id).first()
                if not asset or asset.lora_training.get('use_global_config', True):
                    # 使用全局配置，直接返回全局配置
                    return ConfigService.get_global_lora_training_config()
                else:
                    # 不使用全局配置，在全局配置的基础上合并资产特定配置
                    config_params = ConfigService.get_global_lora_training_config()
                    
                    # 合并资产特定配置
                    if 'params' in asset.lora_training and isinstance(asset.lora_training['params'], dict):
                        config_params.update(asset.lora_training['params'])
                        
                    return config_params
        except Exception as e:
            logger.error(f"获取资产Lora训练配置失败, 资产ID: {asset_id}, 错误: {str(e)}")
            return None
            
    @staticmethod
    def get_asset_ai_engine_config(asset_id: int) -> Optional[Dict[str, Any]]:
        """
        获取资产的AI引擎配置
        
        Args:
            asset_id: 资产ID
            
        Returns:
            合并后的AI引擎配置，如果资产不存在则返回None
        """
        try:
            with get_db() as db:
                asset = db.query(Asset).filter(Asset.id == asset_id).first()
                if not asset or asset.ai_engine.get('use_global_config', True):
                    # 使用全局配置，直接返回全局配置
                    return ConfigService.get_global_ai_engine_config()
                else:
                    # 不使用全局配置，在全局配置的基础上合并资产特定配置
                    engine_config = ConfigService.get_global_ai_engine_config()
                    
                    # 合并资产特定配置
                    for key, value in asset.ai_engine.items():
                        if key not in ['use_global_config', 'verified', 'enabled'] and value:
                            engine_config[key] = value
                        
                    return engine_config
        except Exception as e:
            logger.error(f"获取资产AI引擎配置失败, 资产ID: {asset_id}, 错误: {str(e)}")
            return None
            
    @staticmethod
    def get_asset_lora_headers(asset_id: int) -> Optional[Dict[str, Any]]:
        """
        获取资产的Lora训练请求头
        
        Args:
            asset_id: 资产ID
            
        Returns:
            合并后的Lora训练请求头，如果资产不存在则返回None
        """
        try:
            with get_db() as db:
                asset = db.query(Asset).filter(Asset.id == asset_id).first()
                if not asset:
                    logger.error(f"资产不存在: {asset_id}")
                    return None
                
                if not asset.lora_training.get('use_global_config', True):
                    # 不使用全局配置，直接返回资产特定配置
                    return asset.lora_training.get('headers', {})
                    
                # 使用全局配置作为基础
                headers = ConfigService.get_global_headers_config('lora_training')
                
                # 合并资产特定配置
                if 'headers' in asset.lora_training and isinstance(asset.lora_training['headers'], dict):
                    headers.update(asset.lora_training['headers'])
                    
                return headers
        except Exception as e:
            logger.error(f"获取资产Lora训练请求头失败, 资产ID: {asset_id}, 错误: {str(e)}")
            return None
            
    @staticmethod
    def get_asset_ai_engine_headers(asset_id: int) -> Optional[Dict[str, Any]]:
        """
        获取资产的AI引擎请求头
        
        Args:
            asset_id: 资产ID
            
        Returns:
            合并后的AI引擎请求头，如果资产不存在则返回None
        """
        try:
            with get_db() as db:
                asset = db.query(Asset).filter(Asset.id == asset_id).first()
                if not asset:
                    logger.error(f"资产不存在: {asset_id}")
                    return None
                
                if not asset.ai_engine.get('use_global_config', True):
                    # 不使用全局配置，直接返回资产特定配置
                    return asset.ai_engine.get('headers', {})
                    
                # 使用全局配置作为基础
                headers = ConfigService.get_global_headers_config('ai_engine')
                
                # 合并资产特定配置
                if 'headers' in asset.ai_engine and isinstance(asset.ai_engine['headers'], dict):
                    headers.update(asset.ai_engine['headers'])
                    
                return headers
        except Exception as e:
            logger.error(f"获取资产AI引擎请求头失败, 资产ID: {asset_id}, 错误: {str(e)}")
            return None
            
    # 保留翻译相关功能
    @staticmethod
    def get_translate_config() -> Dict[str, Any]:
        """
        获取翻译配置
        
        Returns:
            翻译配置字典
        """
        try:
            with get_db() as db:
                setting = db.query(Setting).filter(Setting.key == 'baidu_translate_config').first()
                if setting and setting.type == 'json':
                    try:
                        return json.loads(setting.value)
                    except json.JSONDecodeError:
                        logger.error("解析baidu_translate_config失败，返回空字典")
                        return {}
                return {}
        except Exception as e:
            logger.error(f"获取翻译配置失败: {str(e)}")
            return {}
            
    @staticmethod
    def is_translate_enabled() -> bool:
        """
        检查翻译功能是否启用
        支持多翻译提供商：根据全局配置和具体提供商配置进行检查
        
        Returns:
            翻译功能是否启用
        """
        try:
            # 获取全局翻译配置
            global_translate_config = ConfigService.get_value('translate_config', {})
            
            # 首先检查全局翻译开关
            if not global_translate_config.get('enabled', False):
                return False
            
            # 获取当前选择的翻译提供商
            provider = global_translate_config.get('provider', 'baidu')
            
            # 根据提供商检查对应的翻译服务是否启用
            if provider == 'google':
                google_config = ConfigService.get_value('google_translate_config', {})
                return google_config.get('enabled', False)
            elif provider == 'baidu':
                baidu_config = ConfigService.get_translate_config()  # 这里获取百度翻译配置
                return baidu_config.get('enabled', False)
            else:
                # 未知提供商，默认返回False
                logger.warning(f"未知的翻译提供商: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"检查翻译功能启用状态失败: {str(e)}")
            # 出错时回退到检查百度翻译配置（向后兼容）
            try:
                translate_config = ConfigService.get_translate_config()
                return translate_config.get('enabled', False)
            except:
                return False