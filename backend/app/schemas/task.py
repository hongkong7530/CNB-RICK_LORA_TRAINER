from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from datetime import datetime

class TaskBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    marking_asset_id: Optional[int] = None
    training_asset_id: Optional[int] = None
    
    # 配置字段
    mark_config: Optional[Dict[str, Any]] = None
    use_global_mark_config: Optional[bool] = True
    
    training_config: Optional[Dict[str, Any]] = None
    use_global_training_config: Optional[bool] = True

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    marking_asset_id: Optional[int] = None
    training_asset_id: Optional[int] = None
    
    # 配置字段
    mark_config: Optional[Dict[str, Any]] = None
    use_global_mark_config: Optional[bool] = None
    
    training_config: Optional[Dict[str, Any]] = None
    use_global_training_config: Optional[bool] = None

class TaskStatus(BaseModel):
    status: str
    message: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    status: str
    progress: int = 0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class TaskDetail(TaskResponse):
    images: Optional[List[Dict[str, Any]]] = []
    status_history: Optional[Dict[str, Any]] = {}
    marking_asset: Optional[Dict[str, Any]] = None
    training_asset: Optional[Dict[str, Any]] = None

class TaskImage(BaseModel):
    id: int
    filename: str
    preview_url: Optional[str] = None
    size: Optional[int] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class TaskLog(BaseModel):
    id: int
    message: str
    time: str
    status: str 