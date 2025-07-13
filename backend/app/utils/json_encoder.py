import json
import enum
from datetime import datetime, date
from decimal import Decimal

class CustomJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理特殊类型的序列化"""
    
    def default(self, obj):
        # 处理枚举类型
        if isinstance(obj, enum.Enum):
            return obj.value
            
        # 处理日期时间类型
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
            
        # 处理 Decimal 类型
        if isinstance(obj, Decimal):
            return float(obj)
            
        # 尝试将对象转换为字典（如果有 to_dict 方法）
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return obj.to_dict()
            
        # 默认行为
        return super().default(obj) 