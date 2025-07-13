from sqlalchemy import Column, String, Integer, JSON, Text
from ..database import Base
from ..config import config
import json

class Setting(Base):
    __tablename__ = 'settings'
    
    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)  # 使用Text类型以支持更长的配置值
    type = Column(String(20), nullable=False)  # string, integer, json
    description = Column(String(200))

    # 添加默认配置
    @staticmethod
    def get_defaults():
        return {
            'mark_workflow_api': {
                'type': 'string',
                'value': 'data/workflow/mark_workflow_api.json',  # 从文件加载的默认工作流
                'description': 'ComfyUI标记工作流配置'
            },
            'mark_poll_interval': {
                'type': 'integer',
                'value': '5',
                'description': '标记任务轮询间隔(秒)'
            },
            'train_poll_interval': {
                'type': 'integer',
                'value': '15',
                'description': '训练任务轮询间隔(秒)'
            },
            'scheduling_minute': {
                'type': 'integer',
                'value': '5',
                'description': '调度间隔(分钟)'
            },
            'mark_pan_dir': {
                'type': 'string',
                'value': config.SYSTEM_CONFIG['mark_pan_dir'],
                'description': '标记中间目录'
            },
            'lora_pan_upload_dir': {
                'type': 'string',
                'value': config.SYSTEM_CONFIG['lora_pan_upload_dir'],
                'description': 'Lora上传中间目录'
            },
            'mark_config': {
                'type': 'json',
                'value': json.dumps(config.MARK_CONFIG),
                'description': '打标全局配置'
            },
            'lora_training_config': {
                'type': 'json',
                'value': json.dumps(config.LORA_TRAINING_CONFIG),
                'description': 'Lora训练全局配置'
            },
            'ai_engine_config': {
                'type': 'json',
                'value': json.dumps(config.AI_ENGINE_CONFIG),
                'description': 'AI引擎全局配置'
            },
            'lora_training_headers': {
                'type': 'json',
                'value': json.dumps(config.HEADERS_CONFIG['lora_training']),
                'description': 'Lora训练引擎请求头'
            },
            'ai_engine_headers': {
                'type': 'json',
                'value': json.dumps(config.HEADERS_CONFIG['ai_engine']),
                'description': 'AI引擎请求头'
            },
            'baidu_translate_config': {
                'type': 'json',
                'value': json.dumps({
                    'enabled': False,
                    'app_id': '20250327002316619',
                    'secret_key': '67qaSQg_WdfWqQFvx7ml',
                    'api_url': 'https://fanyi-api.baidu.com/api/trans/vip/translate',
                    'default_from': 'auto',
                    'default_to': 'zh'
                }),
                'description': '百度翻译API配置'
            },
            'google_translate_config': {
                'type': 'json',
                'value': json.dumps({
                    'enabled': True,
                    'api_url': 'https://translate.googleapis.com/translate_a/single',
                    'default_from': 'auto',
                    'default_to': 'zh'
                }),
                'description': '谷歌翻译API配置'
            },
            'translate_config': {
                'type': 'json',
                'value': json.dumps({
                    'enabled': True,
                    'provider': 'baidu',
                    'default_from': 'auto',
                    'default_to': 'zh'
                }),
                'description': '翻译全局配置'
            }
        }
        
    def parse_value(self):
        """根据类型解析值"""
        if self.type == 'integer':
            return int(self.value)
        elif self.type == 'json':
            try:
                return json.loads(self.value)
            except:
                return {}
        else:
            return self.value 