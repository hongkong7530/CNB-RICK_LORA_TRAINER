from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.task import Task, TaskStatus
from ..database import get_db
from ..utils.logger import setup_logger

# 导入拆分后的服务
from .task_services.base_task_service import BaseTaskService
from .task_services.task_image_service import TaskImageService
from .task_services.marking_service import MarkingService
from .task_services.training_service import TrainingService
from .task_services.result_service import ResultService
from .task_services.scheduler_service import SchedulerService

logger = setup_logger('task_service')

class TaskService:
    """任务服务，作为统一入口调用各个子服务"""
    
    # 基本任务管理（委托给BaseTaskService）
    list_tasks = BaseTaskService.list_tasks
    get_task_by_id = BaseTaskService.get_task_by_id
    create_task = BaseTaskService.create_task
    update_task = BaseTaskService.update_task
    delete_task = BaseTaskService.delete_task
    get_task_log = BaseTaskService.get_task_log
    get_task_status = BaseTaskService.get_task_status
    get_stats = BaseTaskService.get_stats
    stop_task = BaseTaskService.stop_task
    restart_task = BaseTaskService.restart_task
    cancel_task = BaseTaskService.cancel_task
    get_task_config = BaseTaskService.get_task_config
    update_task_config = BaseTaskService.update_task_config
    
    # 任务图片管理（委托给TaskImageService）
    upload_images = TaskImageService.upload_images
    delete_image = TaskImageService.delete_image
    batch_delete_images = TaskImageService.batch_delete_images
    
    # 打标任务管理（委托给MarkingService）
    start_marking = MarkingService.start_marking
    batch_start_marking = MarkingService.batch_start_marking
    get_available_marking_assets = MarkingService.get_available_marking_assets
    
    # 训练任务管理（委托给TrainingService）
    start_training = TrainingService.start_training
    get_available_training_assets = TrainingService.get_available_training_assets
    
    # 结果管理（委托给ResultService）
    get_marked_texts = ResultService.get_marked_texts
    update_marked_text = ResultService.update_marked_text
    batch_update_marked_texts = ResultService.batch_update_marked_texts
    get_training_results = ResultService.get_training_results
    get_training_loss_data = ResultService.get_training_loss_data
    get_marking_progress_data = ResultService.get_marking_progress_data
    get_execution_history = ResultService.get_execution_history
    get_execution_history_by_id = ResultService.get_execution_history_by_id
    delete_execution_history = ResultService.delete_execution_history
    export_marked_files = ResultService.export_marked_files
    import_marked_files = ResultService.import_marked_files
    
    # 调度器管理（委托给SchedulerService）
    init_scheduler = SchedulerService.init_scheduler
    start_scheduler = SchedulerService.start_scheduler
    stop_scheduler = SchedulerService.stop_scheduler
    run_scheduler_once = SchedulerService.run_scheduler_once