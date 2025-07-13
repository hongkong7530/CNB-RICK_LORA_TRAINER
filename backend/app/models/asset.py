from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from ..database import Base

class Asset(Base):
    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    ip = Column(String(255), nullable=False, comment='IP地址或域名')
    ssh_port = Column(Integer, default=22)
    ssh_username = Column(String(50), nullable=False)
    ssh_password = Column(String(255))
    ssh_key_path = Column(String(255))
    ssh_auth_type = Column(String(20), default='KEY')
    status = Column(String(20), default='PENDING')
    is_local = Column(Boolean, default=False, comment='是否为本地系统资产')
    port_access_mode = Column(String(20), default='DIRECT', comment='端口访问模式: DIRECT直连模式, DOMAIN域名模式')
    enabled = Column(Boolean, default=True, comment='资产是否启用')
    
    # 存储为JSON字段，包含高级配置参数
    lora_training = Column(JSON, default={
        'enabled': False,
        'port': None,
        'params': {},  # 高级参数配置，可覆盖全局配置
        'verified': False,
        'headers': {  # 请求头配置
            'Content-Type': 'application/json',
            'Authorization': ''
        },
        'use_global_config': True,  # 是否使用全局配置
    })
    
    ai_engine = Column(JSON, default={
        'enabled': False,
        'port': None,
        'timeout': 300,
        'headers': {  # 请求头配置
            'Content-Type': 'application/json',
            'Authorization': ''
        },
        'max_retries': 3,
        'retry_interval': 5,
        'use_global_config': True,  # 是否使用全局配置
        'verified': False
    })
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 添加任务计数字段
    marking_tasks_count = Column(Integer, default=0, comment='当前标记任务数')
    training_tasks_count = Column(Integer, default=0, comment='当前训练任务数')
    max_concurrent_tasks = Column(Integer, default=10, comment='最大并发任务数（标记任务最大10个，训练任务最大1个）')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ip': self.ip,
            'ssh_port': self.ssh_port,
            'ssh_username': self.ssh_username,
            'ssh_auth_type': self.ssh_auth_type,
            'status': self.status,
            'port_access_mode': self.port_access_mode,
            'lora_training': self.lora_training,
            'ai_engine': self.ai_engine,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'marking_tasks_count': self.marking_tasks_count,
            'training_tasks_count': self.training_tasks_count,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'is_local': self.is_local,
            'enabled': self.enabled
        }