from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..database import Base
from ..config import config
from datetime import datetime

class TrainingMaterial(Base):
    __tablename__ = "training_materials"

    id = Column(Integer, primary_key=True, index=True)
    folder_name = Column(String, unique=True, index=True)
    source_path = Column(String)
    status = Column(String)  # PENDING, UPLOADED, PROCESSING, COMPLETED, FAILED
    extra_info = Column(JSON)  # 改用 extra_info 替代 metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    tasks = relationship("TrainingTask", back_populates="material")

class TrainingTask(Base):
    __tablename__ = "training_tasks"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("training_materials.id"))
    model_name = Column(String)
    status = Column(String)  # PENDING, TRAINING, COMPLETED, FAILED
    progress = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    config = Column(JSON)  # 训练配置参数
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)  # 关联的资产ID
    use_global_config = Column(Boolean, default=True)  # 是否使用全局配置
    output_path = Column(String, nullable=True)  # 模型输出路径
    sample_images = Column(JSON, default=[])  # 采样图片路径列表
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 关联关系
    material = relationship("TrainingMaterial", back_populates="tasks")
    asset = relationship("Asset", backref="training_tasks")
    
    def to_dict(self):
        return {
            'id': self.id,
            'material_id': self.material_id,
            'model_name': self.model_name,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'config': self.config,
            'asset_id': self.asset_id,
            'use_global_config': self.use_global_config,
            'output_path': self.output_path,
            'sample_images': self.sample_images,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
    def get_training_config(self):
        """获取训练配置，合并全局配置和任务特定配置"""
        if self.use_global_config:
            # 合并全局配置和任务特定配置
            training_config = config.LORA_TRAINING_CONFIG.copy()
            if self.config and isinstance(self.config, dict):
                training_config.update(self.config)
                
            # 如果有关联资产，还需要考虑资产特定配置
            if self.asset:
                asset_config = self.asset.get_lora_config()
                # 资产配置优先级低于任务特定配置
                for key, value in asset_config.items():
                    if key not in self.config:
                        training_config[key] = value
                        
            return training_config
        else:
            # 仅使用任务特定配置
            return self.config or {} 