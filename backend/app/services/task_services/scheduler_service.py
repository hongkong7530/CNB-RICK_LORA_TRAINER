from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from ...models.task import Task, TaskStatus
from ...models.asset import Asset
from ...database import get_db
from ...utils.logger import setup_logger
import threading
import traceback
from .marking_service import MarkingService
from .training_service import TrainingService
import time
import os
from concurrent.futures import ThreadPoolExecutor

logger = setup_logger('scheduler_service')
scheduler_lock = threading.Lock()
scheduler_thread = None
scheduler_running = False

# 添加线程池用于监控任务
monitor_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="MonitorWorker")

# 添加一个任务处理中的标记集合
_processing_task_ids = set()
_processing_lock = threading.Lock()

class SchedulerService:

    @staticmethod
    def get_pending_tasks() -> Tuple[List[Task], List[Task]]:
        """
        获取待处理的任务列表（提交状态和训练状态的任务）
        
        Returns:
            (提交状态的任务列表, 训练状态的任务列表)
        """
        with get_db() as db:
            # 获取已提交但未开始处理的任务
            submitted_tasks = db.query(Task).filter(
                Task.status == TaskStatus.SUBMITTED,
                Task.marking_asset_id.is_(None)  # 未分配资产
            ).order_by(Task.created_at.asc()).all()
            
            # 获取处于训练状态但未分配训练资产的任务
            training_tasks = db.query(Task).filter(
                Task.status == TaskStatus.TRAINING,
                Task.training_asset_id.is_(None)  # 未分配训练资产
            ).order_by(Task.updated_at.asc()).all()
            
            return submitted_tasks, training_tasks
    
    @staticmethod
    def process_task(task: Task):
        """
        根据任务状态处理单个任务
        
        Args:
            task: 任务对象
        """
        try:
            if task.status == TaskStatus.SUBMITTED:
                # 处理已提交的打标任务
                SchedulerService._process_submitted_task(task)
            elif task.status == TaskStatus.TRAINING:
                # 处理训练任务
                SchedulerService._process_training_task(task)
        except Exception as e:
            logger.error(f"处理任务 {task.id} 失败: {str(e)}")
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task.id).first()
                if task:
                    task.update_status(TaskStatus.ERROR, f"任务调度失败: {str(e)}", db=db)
    
    @staticmethod
    def _process_submitted_task(task: Task):
        """
        处理已提交的打标任务
        
        Args:
            task: 任务对象
        """
        # 检查任务是否已经在处理中
        with _processing_lock:
            task_key = f"marking_{task.id}"
            if task_key in _processing_task_ids:
                logger.info(f"标记任务 {task.id} 已在处理中，跳过本次处理")
                return
            # 标记任务为处理中
            _processing_task_ids.add(task_key)
        
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task.id).first()
                if not task or task.status != TaskStatus.SUBMITTED:
                    return
                
                # 获取可用的标记资产
                available_assets = MarkingService.get_available_marking_assets()
                
                if not available_assets:
                    logger.info(f"没有可用于标记的资产，任务 {task.id} 将继续等待")
                    
                    # 检查最近的日志，避免重复添加相同的等待消息
                    recent_logs = task.get_all_logs(limit=5)
                    wait_message = "任务正在等待可用标记资产中..."
                    
                    # 检查最近的日志中是否已有等待资源的消息
                    if not any(log.get('message') == wait_message for log in recent_logs):
                        # 添加任务日志，记录任务正在等待可用标记资产
                        task.add_log(wait_message, db=db)
                    
                    return
                    
                # 获取第一个可用资产
                asset = available_assets[0]
                
                # 分配资产并更新任务
                task.marking_asset_id = asset.id
                # 更新资产的任务计数
                asset.marking_tasks_count += 1
                db.add(asset)
                db.commit()
                
                # 启动新线程执行标记任务处理
                logger.info(f"为标记任务 {task.id} 分配资产 {asset.id} ({asset.name})")
                
                try:
                    # 执行标记处理
                    start_time = time.time()
                    prompt_id = MarkingService._process_marking(task.id, asset.id)
                    end_time = time.time()
                    logger.info(f"标记任务 {task.id} 提交完成，耗时: {end_time - start_time:.2f}秒")
                    
                    # 如果获取到prompt_id，启动监控
                    if prompt_id:
                        logger.info(f"标记任务 {task.id} 获取到prompt_id: {prompt_id}，启动监控")
                        monitor_pool.submit(
                            MarkingService._monitor_mark_status,
                            task.id,
                            asset.id,
                            prompt_id
                        )
                except Exception as e:
                    logger.error(f"标记任务 {task.id} 处理或启动监控失败: {str(e)}", exc_info=True)
        finally:
            # 处理完成后，移除任务处理中的标记
            with _processing_lock:
                _processing_task_ids.discard(task_key)
    
    
    @staticmethod
    def _process_training_task(task: Task):
        """
        处理训练任务
        
        Args:
            task: 任务对象
        """
        # 检查任务是否已经在处理中
        with _processing_lock:
            task_key = f"training_{task.id}"
            if task_key in _processing_task_ids:
                logger.info(f"任务 {task.id} 已在处理中，跳过本次处理")
                return
            # 标记任务为处理中
            _processing_task_ids.add(task_key)
        logger.info(f"开始处理训练任务 {task.id}》》》》》")
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task.id).first()
                if not task or task.status != TaskStatus.TRAINING or task.training_asset_id:
                    return
                
                # 获取可用的训练资产
                available_assets = TrainingService.get_available_training_assets()
                
                if not available_assets:
                    logger.info(f"没有可用于训练的资产，任务 {task.id} 将继续等待")
                    
                    # 检查最近的日志，避免重复添加相同的等待消息
                    recent_logs = task.get_all_logs(limit=5)
                    wait_message = "任务正在等待可用训练资产中..."
                    
                    # 检查最近的日志中是否已有等待资源的消息
                    if not any(log.get('message') == wait_message for log in recent_logs):
                        # 添加任务日志，记录任务正在等待可用训练资产
                        task.add_log(wait_message, db=db)
                    return
                    
                try:
                    # 获取第一个可用资产
                    asset = available_assets[0]
                    
                    # 分配资产并更新任务
                    logger.info(f"为训练任务 {task.id} 分配资产 {asset.id} ({asset.name})")
                    task.training_asset_id = asset.id
                    # 更新资产的任务计数
                    asset.training_tasks_count += 1
                    db.add(asset)
                    db.commit()
                    
                    # 执行训练处理并记录耗时
                    start_time = time.time()
                    training_task_id = TrainingService._process_training(task.id, asset.id)
                    end_time = time.time()
                    logger.info(f"训练任务 {task.id} 提交完成，耗时: {end_time - start_time:.2f}秒")
                    
                    # 如果获取到training_task_id，启动监控
                    if training_task_id:
                        logger.info(f"训练任务 {task.id} 获取到training_task_id: {training_task_id}，启动监控")
                        monitor_pool.submit(
                            TrainingService._monitor_training_status,
                            task.id,
                            asset.id,
                            training_task_id
                        )
                except Exception as e:
                    logger.error(f"训练任务 {task.id} 处理或启动监控失败: {str(e)}", exc_info=True)
        finally:
            # 处理完成后，移除任务处理中的标记
            with _processing_lock:
                _processing_task_ids.discard(task_key)
    
    @staticmethod
    def run_scheduler_once():
        """
        运行一次调度器
        """
        try:
            # 使用锁保证同一时间只有一个线程在执行调度逻辑
            with scheduler_lock:
                # 获取待处理的任务
                submitted_tasks, training_tasks = SchedulerService.get_pending_tasks()
                # 处理提交的打标任务
                for task in submitted_tasks:
                    SchedulerService.process_task(task)
                    
                # 处理训练任务
                for task in training_tasks:
                    SchedulerService.process_task(task)
                    
        except Exception as e:
            logger.error(f"调度器运行失败: {str(e)}")
            logger.error(traceback.format_exc())
    
    @staticmethod
    def _scheduler_loop():
        """
        调度器循环，定期检查并分配任务
        """
        global scheduler_running
        
        try:
            while scheduler_running:
                try:
                    # 执行一次调度
                    SchedulerService.run_scheduler_once()
                    
                    # 等待一段时间再次执行
                    time.sleep(10)  # 10秒检查一次，减少重复检查的频率
                    # logger.info(f"调度器循环执行完成，当前线程ID: {threading.get_ident()}")
                except Exception as loop_error:
                    logger.error(f"调度循环出错: {str(loop_error)}")
                    time.sleep(30)  # 错误后等待30秒再次尝试
                    
        except Exception as e:
            logger.error(f"调度器意外终止: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            logger.info("任务调度器已停止")
            
    @staticmethod
    def start_scheduler():
        """
        启动任务调度器
        """
        global scheduler_thread, scheduler_running
        
        with scheduler_lock:
            if scheduler_thread is None or not scheduler_thread.is_alive():
                scheduler_running = True
                scheduler_thread = threading.Thread(
                    target=SchedulerService._scheduler_loop,
                    name="task_scheduler",
                    daemon=True
                )
                scheduler_thread.start()
                logger.info("任务调度器已启动")
                return True
            else:
                logger.warning("任务调度器已经在运行中")
                return False
    
    @staticmethod
    def stop_scheduler():
        """
        停止任务调度器
        """
        global scheduler_running
        
        with scheduler_lock:
            if scheduler_running:
                scheduler_running = False
                logger.info("正在停止任务调度器...")
                # 关闭监控线程池
                monitor_pool.shutdown(wait=False)
                return True
            else:
                logger.warning("任务调度器已经停止")
                return False
                
    @staticmethod
    def init_scheduler():
        """
        初始化任务调度器，应用启动时调用
        """
        # 检查可能中断的任务，重置状态
        with get_db() as db:
            # 找到所有处于SUBMITTED状态但已分配资产的任务
            pending_mark_tasks = db.query(Task).filter(
                Task.status == TaskStatus.SUBMITTED,
                Task.marking_asset_id.is_not(None)  # 已分配资产
            ).all()
            
            # 找到所有处于MARKING状态的任务
            marking_tasks = db.query(Task).filter(
                Task.status == TaskStatus.MARKING
            ).all()
            
            # 找到所有处于TRAINING状态但已分配资产的任务
            pending_train_tasks = db.query(Task).filter(
                Task.status == TaskStatus.TRAINING,
                Task.training_asset_id.is_not(None),  # 已分配资产
                Task.prompt_id.is_(None)  # 但还没有开始训练（没有prompt_id）
            ).all()
            
            # 重置打标任务状态
            for task in pending_mark_tasks + marking_tasks:
                # 检查任务的输出目录是否存在并有文件
                if task.marked_images_path and os.path.exists(task.marked_images_path) and os.listdir(task.marked_images_path):
                    # 有输出文件，说明打标可能已完成
                    task.update_status(TaskStatus.MARKED, "系统重启，检测到打标输出，标记为已完成", db=db)
                else:
                    # 没有输出文件，重置为SUBMITTED状态
                    if task.marking_asset:
                        # 减少资产的计数
                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                    task.marking_asset_id = None
                    task.update_status(TaskStatus.SUBMITTED, "系统重启，打标任务重置为等待状态", db=db)
            
            # 重置训练任务状态
            for task in pending_train_tasks:
                if task.training_asset:
                    # 减少资产的计数
                    task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                task.training_asset_id = None
                task.update_status(TaskStatus.TRAINING, "系统重启，训练任务重置为等待状态", db=db)
                
            # 恢复处理中的任务监控
            SchedulerService._recover_task_monitors(db)
            
        # 启动调度器
        SchedulerService.start_scheduler()
        
    @staticmethod
    def _recover_task_monitors(db: Session):
        """恢复任务状态监控"""
        try:
            # 恢复标记中的任务监控
            marking_tasks = db.query(Task).filter(
                Task.status == TaskStatus.MARKING,
                Task.prompt_id.isnot(None)  # 已有prompt_id的任务
            ).all()
            
            for task in marking_tasks:
                if task.marking_asset_id and task.prompt_id:
                    logger.info(f"恢复标记任务 {task.id} 的状态监控")
                    monitor_pool.submit(
                        MarkingService._monitor_mark_status,
                        task.id,
                        task.marking_asset_id,
                        task.prompt_id
                    )

            # 恢复训练中的任务监控
            training_tasks = db.query(Task).filter(
                Task.status == TaskStatus.TRAINING,
                Task.prompt_id.isnot(None),  # 已有训练任务ID的任务
                Task.training_asset_id.isnot(None)  # 已分配训练资产的任务
            ).all()
            
            for task in training_tasks:
                if task.training_asset_id and task.prompt_id:
                    logger.info(f"恢复训练任务 {task.id} 的状态监控")
                    monitor_pool.submit(
                        TrainingService._monitor_training_status,
                        task.id,
                        task.training_asset_id,
                        task.prompt_id
                    )
                    
        except Exception as e:
            logger.error(f"恢复任务监控失败: {str(e)}", exc_info=True) 