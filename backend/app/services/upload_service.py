import os
import hashlib
import uuid
from typing import Optional, Dict, Any
from werkzeug.utils import secure_filename
from ..database import get_db
from ..models.upload_file import UploadFile
from ..config import config
from ..utils.logger import setup_logger
from ..utils.file_handler import calculate_md5

logger = setup_logger('upload_service')

class UploadService:
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """检查文件类型是否允许上传"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_file(file, description: str = None) -> Optional[Dict[str, Any]]:
        """
        保存上传文件并记录到数据库
        
        Args:
            file: 上传的文件对象
            description: 文件描述
            
        Returns:
            保存成功返回文件信息字典，失败返回None
        """
        try:
            if not file:
                logger.error("没有接收到文件")
                return None
                
            # 安全处理文件名
            original_filename = file.filename
            # 检查文件类型
            if not UploadService.allowed_file(original_filename):
                logger.error(f"不允许的文件类型: {original_filename}")
                return None
                
            # 生成唯一文件名
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            timestamp = str(int(uuid.uuid1().time_low))  # 生成短时间戳
            filename_without_extension = original_filename.rsplit('.', 1)[0]
            unique_filename = f"{filename_without_extension}_{timestamp}.{file_extension}"
            
            # 构建存储路径
            relative_path = os.path.join('uploads', unique_filename)
            file_path = os.path.join(config.UPLOAD_DIR, unique_filename)
            
            # 保存文件
            file.save(file_path)
            file_size = os.path.getsize(file_path) / 1024  # 转换为KB
            
            # 计算MD5
            md5 = calculate_md5(file_path)
            
            # 记录到数据库
            with get_db() as db:
                upload_file = UploadFile(
                    filename=original_filename,
                    storage_path=relative_path,
                    file_type=file_extension,
                    file_size=file_size,
                    mime_type=file.content_type if hasattr(file, 'content_type') else None,
                    md5=md5,
                    description=description
                )
                db.add(upload_file)
                db.commit()
                db.refresh(upload_file)
                
                logger.info(f"文件上传成功: {original_filename}, ID: {upload_file.id}")
                return upload_file.to_dict()
                
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return None
    
    @staticmethod
    def get_file_by_id(file_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取文件信息"""
        try:
            with get_db() as db:
                file = db.query(UploadFile).filter(UploadFile.id == file_id).first()
                if file:
                    return file.to_dict()
                return None
        except Exception as e:
            logger.error(f"获取文件信息失败, ID: {file_id}, 错误: {str(e)}")
            return None
    
    @staticmethod
    def get_all_files() -> list:
        """获取所有上传的文件"""
        try:
            with get_db() as db:
                files = db.query(UploadFile).order_by(UploadFile.created_at.desc()).all()
                return [file.to_dict() for file in files]
        except Exception as e:
            logger.error(f"获取所有文件列表失败: {str(e)}")
            return []
    
    @staticmethod
    def delete_file(file_id: int) -> bool:
        """删除文件"""
        try:
            with get_db() as db:
                file = db.query(UploadFile).filter(UploadFile.id == file_id).first()
                if not file:
                    logger.error(f"文件不存在, ID: {file_id}")
                    return False
                
                # 删除物理文件
                file_path = os.path.join(config.PROJECT_ROOT, file.storage_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # 删除数据库记录
                db.delete(file)
                db.commit()
                
                logger.info(f"文件删除成功, ID: {file_id}")
                return True
        except Exception as e:
            logger.error(f"删除文件失败, ID: {file_id}, 错误: {str(e)}")
            return False 