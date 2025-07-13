from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# 训练素材相关模型
class TrainingMaterialBase(BaseModel):
    folder_name: str
    source_path: str
    metadata: Optional[Dict[str, Any]] = None

class TrainingMaterialCreate(TrainingMaterialBase):
    pass

class TrainingMaterialUpdate(BaseModel):
    folder_name: Optional[str] = None
    source_path: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TrainingMaterial(TrainingMaterialBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 训练任务相关模型
class TrainingTaskBase(BaseModel):
    material_id: int
    node_id: int

class TrainingTaskCreate(TrainingTaskBase):
    pass

class TrainingTaskUpdate(BaseModel):
    status: Optional[str] = None
    lora_path: Optional[str] = None
    error: Optional[str] = None

class TrainingTask(TrainingTaskBase):
    id: int
    status: str
    lora_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 