from typing import Optional, Any, Dict
from pydantic import BaseModel

class SettingUpdate(BaseModel):
    source_dir: str
    lora_output_path: str
    scheduling_minute: int
    mark_pan_dir: str
    lora_pan_upload_dir: str

class SettingResponse(BaseModel):
    source_dir: str
    lora_output_path: str
    scheduling_minute: int
    mark_pan_dir: str
    lora_pan_upload_dir: str
    
    class Config:
        orm_mode = True 