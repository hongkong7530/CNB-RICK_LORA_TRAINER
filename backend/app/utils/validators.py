from typing import Dict, Any, List
from ..middleware.error_handler import ValidationError
from ..config import config

def validate_task_create(data: dict) -> bool:
    """验证任务创建数据"""
    required_fields = ['name']  # 修改为只需要 name 字段
    
    # 检查必填字段
    for field in required_fields:
        if field not in data or not data[field]:
            return False
            
    return True

def validate_asset_create(data: Dict[str, Any]) -> None:
    """验证创建资产的数据"""
    required_fields = ['name', 'folder_name']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

def validate_file_upload(files: List[Any]) -> None:
    """验证文件上传"""
    if not files:
        raise ValidationError("没有上传文件")
    
    for file in files:
        # 检查文件扩展名
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in config.ALLOWED_EXTENSIONS:
            raise ValidationError(f"不支持的文件类型。支持的类型: {', '.join(config.ALLOWED_EXTENSIONS)}")
        
        # 检查文件大小
        if file.content_length > config.MAX_CONTENT_LENGTH:
            max_size_mb = config.MAX_CONTENT_LENGTH / (1024 * 1024)
            raise ValidationError(f"文件过大。最大允许: {max_size_mb}MB") 