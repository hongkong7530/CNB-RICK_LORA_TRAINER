from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ...models.task import Task, TaskStatus, TaskExecutionHistory
from ...models.asset import Asset
from ...database import get_db
from ...utils.logger import setup_logger
from ...services.config_service import ConfigService
from ...utils.file_handler import generate_unique_folder_path
from ...utils.mark_handler import MarkRequestHandler, MarkConfig
from ...utils.common import copy_attributes
from ...services.asset_service import AssetService
from ...config import Config
from ...utils.ssh import create_ssh_client_from_asset
import json
import traceback
import os
import time

logger = setup_logger('marking_service')

class MarkingService:
    @staticmethod
    def get_available_marking_assets() -> List[Asset]:
        """获取可用于标记的资产"""
        try:
            assets = AssetService.verify_all_assets('ai_engine')
            # 标记资产最大并发数固定为10
            return [asset for asset in assets if asset.marking_tasks_count < 10]
        except Exception as e:
            logger.error(f"获取可用标记资产失败: {str(e)}")
            return []
            
    @staticmethod
    def start_marking(db: Session, task_id: int) -> Optional[Dict]:
        """提交标记任务"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            
            # 检查任务是否存在
            if not task:
                raise ValueError("任务不存在")
            
            # 检查任务状态
            if task.status != TaskStatus.NEW:
                raise ValueError(f"任务状态 {task.status} 不允许提交标记")
            
            # 检查是否有图片
            if not task.images:
                raise ValueError("任务没有上传任何图片")

            # 生成唯一的打标路径
            marked_images_path = generate_unique_folder_path(Config.MARKED_DIR, task_id, 'mark')
            task.marked_images_path = marked_images_path

            # 更新任务状态为已提交，并传递数据库会话
            task.update_status(TaskStatus.SUBMITTED, '任务已提交', db=db)

            return task.to_dict()
            
        except ValueError as e:
            logger.warning(f"提交标记任务失败: {str(e)}")
            if task:
                task.update_status(TaskStatus.ERROR, str(e), db=db)
            return {
                'error': str(e),
                'error_type': 'VALIDATION_ERROR',
                'task': task.to_dict() if task else None
            }
            
        except Exception as e:
            logger.error(f"开始标记失败: {str(e)}", exc_info=True)
            if task:
                task.update_status(TaskStatus.ERROR, f"系统错误: {str(e)}", db=db)
            return {
                'error': f"系统错误: {str(e)}",
                'error_type': 'SYSTEM_ERROR',
                'task': task.to_dict() if task else None
            }
            
    @staticmethod
    def batch_start_marking(db: Session, task_ids: List[int]) -> List[int]:
        """批量提交标记任务
        
        Args:
            db: 数据库会话
            task_ids: 要提交标记的任务ID列表
            
        Returns:
            成功提交标记的任务ID列表
        """
        if not task_ids:
            raise ValueError("任务ID列表不能为空")
            
        succeeded_ids = []
        
        for task_id in task_ids:
            task = db.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
                
            # 检查任务状态，只有NEW状态的任务可以提交标记
            if task.status != TaskStatus.NEW:
                raise ValueError(f"任务 {task_id} 状态为 {task.status.value}，不允许提交标记（只有NEW状态的任务可以提交）")
                
            # 检查是否有图片
            if not task.images:
                raise ValueError(f"任务 {task_id} 没有上传任何图片")
            
            # 获取标记配置
            training_config = ConfigService.get_task_training_config(task_id)
            training_data_path = f"{training_config.get('repeat_num', 10)}_rick"
            # 生成唯一的打标路径
            marked_images_path = os.path.join(generate_unique_folder_path(Config.MARKED_DIR, task_id, 'mark'), training_data_path)
            task.marked_images_path = marked_images_path

            # 更新任务状态为已提交
            task.update_status(TaskStatus.SUBMITTED, '任务已批量提交标记', db=db)
            
            # 记录成功提交的任务ID
            succeeded_ids.append(task_id)
        
        return succeeded_ids
            
    @staticmethod
    def _process_marking(task_id: int, asset_id: int):
        """处理标记任务"""
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                asset = db.query(Asset).filter(Asset.id == asset_id).first()

                if not task or not asset:
                    raise ValueError("任务或资产不存在")

                logger.info(f"开始处理标记任务 {task_id}")
                
                # 更新任务状态，记录开始处理标记
                task.update_status(TaskStatus.MARKING, f'开始处理标记任务，使用资产: {asset.name}',db=db)

                mark_config = ConfigService.get_task_mark_config(task.id)
                
                # 准备输入输出目录
                input_dir = os.path.join(Config.UPLOAD_DIR, str(task_id))
                output_dir = task.marked_images_path
                task.add_log(f'输入目录: {input_dir}',db)
                task.add_log(f'输出目录: {output_dir}',db)

                # 定义远程目录路径
                remote_input_dir = f"{Config.REMOTE_UPLOAD_DIR}/{task_id}"
                # 从task.marked_images_path获取任务后缀部分
                output_suffix = task.marked_images_path.replace(Config.MARKED_DIR, '').replace('\\', '/')
                remote_output_dir = f"{Config.REMOTE_MARKED_DIR}{output_suffix}"
                
                # 将远程输出路径保存到任务的ai_engine配置中
                if not task.mark_config:
                    task.mark_config = {}
                
                # 创建一个新的字典来确保SQLAlchemy检测到变化
                mark_config['remote_output_dir'] = remote_output_dir
                task.mark_config = mark_config  # 重新赋值整个字典
                
                # 显式标记为已修改
                db.add(task)
                db.commit()
                
                # 如果不是本地资产，需要同步文件
                if not asset.is_local:
                    task.add_log('资产不是本地资产，需要同步文件...',db)
                    
                    # 使用同步工具上传图片到远程服务器
                    task.add_log(f'开始同步图片到远程服务器: {remote_input_dir}',db)
                    # 创建SSH客户端工具
                    ssh_client = create_ssh_client_from_asset(asset)
                    # 下载打标结果
                    success, message, stats = ssh_client.upload_directory(
                        local_path=input_dir,
                        remote_path=remote_input_dir
                    )
                    
                    if not success:
                        raise Exception(f"同步图片失败: {message}")
                    
                    task.add_log(f'图片同步成功: {message}',db)
                    
                    # 更新输入目录为远程目录
                    input_dir = remote_input_dir
                
                # 创建标记处理器
                task.add_log(f'准备发送标记请求: task_id={task_id}, asset_id={asset_id}, asset_ip={asset.ip}',db)
                
                try:
                    # 创建标记处理器，直接传入资产对象
                    handler = MarkRequestHandler(asset)
                    
                    # 创建MarkConfig对象
                    config = MarkConfig(
                        input_folder=input_dir,
                        output_folder=remote_output_dir if not asset.is_local else output_dir
                    )        
                    copy_attributes(mark_config, config)
                    
                    # 发送标记请求
                    prompt_id = handler.mark_request(config)
                except Exception as req_error:
                    # 捕获请求异常
                    error_detail = {
                        "message": str(req_error),
                        "type": type(req_error).__name__,
                        "traceback": str(traceback.format_exc())
                    }
                    error_json = json.dumps(error_detail, indent=2)
                    task.update_status(TaskStatus.ERROR, f'标记请求失败: {str(req_error)}', db=db)
                    task.add_log(error_json, db=db)
                    if task.marking_asset:
                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                        db.commit()
                    raise ValueError(f"标记请求失败: {str(req_error)}")

                if not prompt_id:
                    task.add_log('没有获取到有效的prompt_id', db=db)
                    raise ValueError("创建标记任务失败，未获取到prompt_id")

                # 记录成功获取prompt_id
                task.add_log(f'标记任务创建成功，prompt_id={prompt_id}', db=db)
                
                # 更新任务状态和prompt_id
                task.prompt_id = prompt_id
                db.commit()

                return prompt_id

        except Exception as e:
            logger.error(f"标记任务 {task_id} 处理失败: {str(e)}", exc_info=True)
            # 详细记录错误
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status(TaskStatus.ERROR, f'标记处理失败: {str(e)}', db=db)
                    task.add_log(json.dumps({
                        "message": str(e),
                        "type": type(e).__name__,
                        "traceback": str(traceback.format_exc())
                    }, indent=2), db=db)
                    if task.marking_asset:
                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                        db.commit()
            raise
            
    @staticmethod
    def _monitor_mark_status(task_id: int, asset_id: int, prompt_id: str):
        """监控标记任务状态"""
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                asset = db.query(Asset).filter(Asset.id == asset_id).first()

                if not task or not asset:
                    raise ValueError("任务或资产不存在")
                
                # 记录开始监控
                task.add_log(f'开始监控标记任务状态, prompt_id={prompt_id}', db=db)
                handler = MarkRequestHandler(asset)
                poll_interval = ConfigService.get_value('mark_poll_interval', 5)
                mark_config = ConfigService.get_task_mark_config(task.id)
                last_progress = 0
                error_count = 0
                
                while True:
                    try:
                        completed, success, task_info = handler.check_status(prompt_id, mark_config)
                        logger.info(f"检查标记任务状态: completed={completed}, success={success}, task_info={task_info}")
                        
                        # 收集实时进度数据并保存到数据库
                        try:
                            progress_data = handler.get_marking_progress_data(prompt_id)
                            if progress_data and task.execution_history_id:
                                with get_db() as progress_db:
                                    execution_history = progress_db.query(TaskExecutionHistory).filter(
                                        TaskExecutionHistory.id == task.execution_history_id
                                    ).first()
                                    if execution_history:
                                        execution_history.marking_progress_data = progress_data
                                        progress_db.commit()
                        except Exception as progress_err:
                            logger.warning(f"收集标记进度数据失败: {str(progress_err)}")
                        
                        with get_db() as complete_db:
                            task = complete_db.query(Task).filter(Task.id == task_id).first()
                            # 可能在打标过程中取消了任务，不再继续监听
                            if task and task.status != TaskStatus.MARKING:
                                logger.info("任务状态为非打标状态，退出监听")
                                break
                                
                            if completed and task:
                                if success:
                                    # 如果是非本地资产，需要下载结果
                                    if not asset.is_local and task.mark_config and task.mark_config.get('remote_output_dir'):
                                        task.add_log('打标完成，开始从远程服务器同步结果...', db=complete_db)
                                        
                                        # 创建SSH客户端工具
                                        ssh_client = create_ssh_client_from_asset(asset)
                                        # 下载打标结果
                                        success, message, stats = ssh_client.download_directory(
                                            local_path=task.marked_images_path,
                                            remote_path=task.mark_config['remote_output_dir']
                                        )
                                        
                                        if not success:
                                            task.add_log(f'同步结果失败: {message}', db=complete_db)
                                            task.update_status(TaskStatus.ERROR, f'同步打标结果失败: {message}', db=complete_db)
                                            break
                                        
                                        task.add_log(f'打标结果同步成功: {message}', db=complete_db)
                                    
                                    task.update_status(TaskStatus.MARKED, '标记完成', db=complete_db)
                                    task.progress = 100
                                    task.add_log('标记任务成功完成', db=complete_db)
                                    
                                    # 检查是否自动开始训练
                                    if task.auto_training:
                                        logger.info(f"任务 {task_id} 启用自动训练，将自动开始训练流程")
                                        task.add_log('启用自动训练，设置状态为训练中，等待调度器分配资产', db=complete_db)
                                        task.update_status(TaskStatus.TRAINING, '准备开始训练', db=complete_db)
                                    else:
                                        task.add_log('未启用自动训练，请手动提交训练任务', db=complete_db)
                                else:
                                    # 处理失败情况
                                    error_info = task_info.get("error_info", {})
                                    task.update_status(
                                        TaskStatus.ERROR,
                                        f'标记失败: {error_info.get("error_message")}',
                                        db=complete_db
                                    )
                                    task.add_log(json.dumps({
                                        "message": error_info.get("error_message"),
                                        "type": error_info.get("error_type"),
                                        "node": error_info.get("node_type"),
                                        "details": {
                                            "inputs": error_info.get("inputs"),
                                            "traceback": error_info.get("traceback")
                                        }
                                    }, indent=2), db=complete_db)
                                
                                # 更新资产任务计数
                                if task.marking_asset:
                                    task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                                    complete_db.commit()
                                break
                        
                        time.sleep(poll_interval)
                        # 重置错误计数
                        error_count = 0
                    except Exception as check_err:
                        # 处理检查状态的错误
                        error_count += 1
                        # 记录错误并在多次失败后停止监控
                        with get_db() as err_db:
                            task = err_db.query(Task).filter(Task.id == task_id).first()
                            if task:
                                task.add_log(f'检查任务状态出错 ({error_count}/3): {str(check_err)}', db=err_db)
                            if error_count >= 3:
                                task = err_db.query(Task).filter(Task.id == task_id).first()
                                if task:
                                    task.update_status(TaskStatus.ERROR, f'连续3次检查状态失败，停止监控: {str(check_err)}', db=err_db)
                                    if task.marking_asset:
                                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                                        err_db.commit()
                                break
                
                    time.sleep(poll_interval)

                logger.info("已退出监听标记任务状态")

        except Exception as e:
            # 处理整体监控异常
            logger.error(f"监控标记任务状态失败: {str(e)}")
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status(TaskStatus.ERROR, f'监控失败: {str(e)}', db=db)
                    task.add_log(json.dumps({
                        "message": str(e),
                        "type": type(e).__name__,
                        "traceback": str(traceback.format_exc())
                    }, indent=2), db=db)
                    if task.marking_asset:
                        task.marking_asset.marking_tasks_count = max(0, task.marking_asset.marking_tasks_count - 1)
                        db.commit() 