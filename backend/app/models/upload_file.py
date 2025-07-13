from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from ..database import Base

class UploadFile(Base):
    """上传文件记录模型"""
    __tablename__ = 'upload_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, comment='文件原始名称')
    storage_path = Column(String(500), nullable=False, comment='存储路径')
    file_type = Column(String(50), comment='文件类型')
    file_size = Column(Float, comment='文件大小(KB)')
    mime_type = Column(String(100), comment='MIME类型')
    md5 = Column(String(32), comment='文件MD5')
    description = Column(Text, comment='文件描述')
    created_at = Column(DateTime, default=datetime.now, comment='上传时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'storage_path': self.storage_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'md5': self.md5,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 