from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from ..database import Base
from ..utils.common import logger
from ..config import config
import enum

class TaskStatus(enum.Enum):
    NEW = 'NEW'               # 新建
    SUBMITTED = 'SUBMITTED'   # 已提交
    MARKING = 'MARKING'       # 标记中
    MARKED = 'MARKED'         # 已标记
    TRAINING = 'TRAINING'     # 训练中
    COMPLETED = 'COMPLETED'   # 已完成
    ERROR = 'ERROR'           # 错误

class TaskStatusLog(Base):
    """任务状态日志"""
    __tablename__ = 'task_status_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    history_id = Column(Integer, ForeignKey('task_status_history.id', ondelete='CASCADE'), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'time': self.created_at.isoformat()
        }

class TaskStatusHistory(Base):
    """任务状态历史"""
    __tablename__ = 'task_status_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(20), nullable=False)  # 对应 TaskStatus 的值
    start_time = Column(DateTime, nullable=False, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    
    # 关联关系
    logs = relationship('TaskStatusLog', cascade='all, delete-orphan', order_by='TaskStatusLog.created_at')
    
    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'logs': [log.to_dict() for log in self.logs]
        }

class TaskImage(Base):
    """任务图片模型"""
    __tablename__ = 'task_images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    preview_url = Column(String(500))
    size = Column(Integer)  # 文件大小(字节)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'preview_url': self.preview_url,
            'size': self.size,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TaskExecutionHistory(Base):
    """任务执行历史记录"""
    __tablename__ = 'task_execution_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    start_time = Column(DateTime, default=datetime.now, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='RUNNING')  # RUNNING, COMPLETED, ERROR
    
    # 存储执行参数
    mark_config = Column(JSON, comment='打标参数配置')
    training_config = Column(JSON, comment='训练参数配置')
    
    # 存储资产ID
    marking_asset_id = Column(Integer, nullable=True, comment='打标使用的资产ID')
    training_asset_id = Column(Integer, nullable=True, comment='训练使用的资产ID')
    
    # 存储路径信息
    marked_images_path = Column(String(500), comment='打标后的图片文件路径')
    training_output_path = Column(String(500), comment='训练输出文件路径')
    
    # 存储训练结果
    training_results = Column(JSON, comment='训练结果，包括模型文件路径、预览图等')
    loss_data = Column(JSON, comment='训练loss数据，用于绘制loss曲线')
    
    # 存储标记进度数据
    marking_progress_data = Column(JSON, comment='标记进度数据，用于实时监控标记过程')
    
    # 其他信息
    description = Column(Text, nullable=True, comment='描述或备注')
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关联关系
    task = relationship('Task', back_populates='execution_history')

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'mark_config': self.mark_config,
            'training_config': self.training_config,
            'marking_asset_id': self.marking_asset_id,
            'training_asset_id': self.training_asset_id,
            'training_results': self.training_results,
            'loss_data': self.loss_data,
            'marking_progress_data': self.marking_progress_data,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Task(Base):
    """训练任务模型"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='任务名称')
    description = Column(Text, nullable=True, comment='任务描述')
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.NEW, comment='任务状态')
    progress = Column(Integer, default=0, comment='进度百分比')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    prompt_id = Column(String(50))  

    # 资产关联
    marking_asset_id = Column(Integer, ForeignKey('assets.id'), comment='标记资产ID')
    training_asset_id = Column(Integer, ForeignKey('assets.id'), comment='训练资产ID')
    
    # 打标参数配置
    mark_config = Column(JSON, comment='打标参数配置')
    use_global_mark_config = Column(Boolean, default=True, comment='是否使用全局打标配置')
    
    # 训练参数配置
    training_config = Column(JSON, comment='训练参数配置，包含可能需要修改的参数')
    use_global_training_config = Column(Boolean, default=True, comment='是否使用全局训练配置')
    
    # 自动训练标志
    auto_training = Column(Boolean, default=True, comment='标记完成后是否自动开始训练')
    
    # 关联关系
    marking_asset = relationship('Asset', foreign_keys=[marking_asset_id])
    training_asset = relationship('Asset', foreign_keys=[training_asset_id])
    status_history = relationship('TaskStatusHistory', cascade='all, delete-orphan', order_by='TaskStatusHistory.start_time')

    # 关联图片
    images = relationship('TaskImage', cascade='all, delete-orphan')
    # 关联执行历史记录
    execution_history = relationship('TaskExecutionHistory', back_populates='task', cascade='all, delete-orphan', order_by='TaskExecutionHistory.start_time.desc()')
    # 打标后的图片文件路径
    marked_images_path = Column(String(500), comment='打标后的图片文件路径')
    # 训练输出路径
    training_output_path = Column(String(500), comment='训练输出文件路径')
    
    # 当前执行历史ID
    execution_history_id = Column(Integer, nullable=True, comment='当前关联的执行历史ID')

    # 添加开始时间和结束时间
    started_at = Column(DateTime, comment='任务开始时间')
    completed_at = Column(DateTime, comment='任务完成时间')

    def update_status(self, new_status, message: str = None, db: object=None):
        """
        更新任务状态并记录历史
        
        Args:
            new_status: 新状态，可以是字符串或 TaskStatus 枚举值
            message: 状态变更消息
            db: 数据库会话对象，如果提供则自动提交更改
        """
        now = datetime.now()
        old_status = self.status.value if self.status else None
        
        # 确保 new_status 是字符串
        if isinstance(new_status, TaskStatus):
            new_status = new_status.value
            
        # 结束当前状态的历史记录
        current_history = None
        if old_status:
            current_history = next((h for h in self.status_history if h.status == old_status and h.end_time is None), None)
            if current_history:
                current_history.end_time = now
        
        # 创建新状态的历史记录
        new_history = TaskStatusHistory(
            task_id=self.id,
            status=new_status,
            start_time=now
        )
        self.status_history.append(new_history)
        # 添加到状态历史
        if db:
            db.add(new_history)
            db.flush()  # 确保 new_history.id 被生成
        
        # 更新任务状态
        self.status = TaskStatus(new_status)
        
        if message:
            # 添加自定义消息
            self.add_log(message, db=db)
        else:
            # 生成默认的状态变更消息
            default_message = f"任务状态从 {old_status or 'None'} 变更为 {new_status}"
            # 添加状态变更日志
            self.add_log(default_message, db=db)
        
        # 更新开始和结束时间
        if new_status in ['MARKING', 'TRAINING'] and not self.started_at:
            self.started_at = now
        elif new_status in ['MARKED', 'COMPLETED', 'ERROR']:
            self.completed_at = now

        logger.info(f"任务 {self.id} 状态更新为 {new_status}")
        if db:
            db.commit()

    def add_log(self, message: str, db: object = None):
        """
        添加日志到当前状态
        
        Args:
            message: 日志消息
            db: 数据库会话对象，如果提供则自动提交更改
        """
        # 当前状态
        status = self.status.value if self.status else None
        
        # 查找当前状态的历史记录
        current_history = next((h for h in self.status_history if h.status == status and h.end_time is None), None)
        
        # 如果没有找到当前状态的历史记录，创建一个
        if not current_history:
            current_history = TaskStatusHistory(
                task_id=self.id,
                status=status,
                start_time=datetime.now()
            )
            if db:
                db.add(current_history)
                db.flush()  # 确保 current_history.id 被生成
        
        # 创建日志条目
        log_entry = TaskStatusLog(
            history_id=current_history.id,
            message=message,
            created_at=datetime.now()
        )
        
        # 添加到数据库
        if db:
            db.add(log_entry)
            db.commit()

    def add_progress_log(self, progress: int, db: object = None):
        """
        添加进度日志
        
        Args:
            progress: 进度百分比
            db: 数据库会话对象，如果提供则自动提交更改
        """
        message = f"当前进度: {progress}%"
        self.add_log(message, db=db)
        self.progress = progress
        if db:
            db.commit()
            
    def get_all_logs(self, limit: int = 100):
        """获取所有日志列表（按时间倒序排列）"""
        # 从所有状态历史中收集日志
        all_logs = []
        for history in self.status_history:
            for log in history.logs:
                log_dict = log.to_dict()
                log_dict['status'] = history.status
                all_logs.append(log_dict)
        
        # 按时间排序（倒序）
        all_logs.sort(key=lambda x: x.get('time', ''), reverse=True)
        
        # 应用限制
        return all_logs[:limit]

    def to_dict(self):
        """转换为字典"""
        # 将状态历史转换为与之前 JSON 字段格式兼容的字典
        status_history_dict = {}
        for history in self.status_history:
            status_history_dict[history.status] = {
                'start_time': history.start_time.isoformat(),
                'end_time': history.end_time.isoformat() if history.end_time else None,
                'logs': [log.to_dict() for log in history.logs]
            }
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status_history': status_history_dict,
            'images': [img.to_dict() for img in self.images],
            'marked_images_path': self.marked_images_path,
            'training_output_path': self.training_output_path,
            'auto_training':self.auto_training,
            'marking_asset': self.marking_asset.to_dict() if self.marking_asset else None,
            'training_asset': self.training_asset.to_dict() if self.training_asset else None,
            'mark_config': self.mark_config,
            'use_global_mark_config': self.use_global_mark_config,
            'training_config': self.training_config,
            'use_global_training_config': self.use_global_training_config,
            'execution_history': [history.to_dict() for history in self.execution_history[:5]] if hasattr(self, 'execution_history') else [],
            'execution_history_id': self.execution_history_id
        }