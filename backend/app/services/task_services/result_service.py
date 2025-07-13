from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session
from ...models.task import Task, TaskStatus, TaskExecutionHistory, TaskImage
from ...database import get_db
from ...utils.logger import setup_logger
from ...config import config, Config
from ...utils.train_handler import TrainRequestHandler
from ...utils.mark_handler import MarkRequestHandler
import os
import re
from ...models.asset import Asset
from ...services.task_services.base_task_service import BaseTaskService
from ...services.config_service import ConfigService
import json
import zipfile
import tempfile
import time

logger = setup_logger('result_service')

class ResultService:
    @staticmethod
    def get_marked_texts(db: Session, task_id: int) -> Optional[Dict]:
        """
        获取打标后的文本内容
        返回文件名称和打标文本内容的映射
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.warning(f"任务 {task_id} 不存在")
                return None
            
            if task.status not in [TaskStatus.MARKED, TaskStatus.TRAINING, TaskStatus.COMPLETED]:
                logger.warning(f"任务 {task_id} 状态为 {task.status}，未完成打标")
                return None
            
            # 打标后的文本存储目录
            if not os.path.exists(task.marked_images_path):
                logger.warning(f"打标目录不存在: {task.marked_images_path}")
                return None
            
            # 构建图片文件名到原始文件名的映射
            image_name_map = {}
            for image in task.images:
                # 获取不带扩展名的文件名作为key
                name_without_ext = os.path.splitext(image.filename)[0]
                image_name_map[name_without_ext] = image.filename
            
            # 获取marked_images_path的相对路径（从/data开始）
            if task.marked_images_path:
                # 从完整路径中提取相对路径
                relative_path = task.marked_images_path.replace(config.PROJECT_ROOT, "")
                # 确保路径以/data开头
                relative_path = relative_path.replace("\\", "/")
            else:
                # 如果没有marked_images_path，使用上传路径
                relative_path = f"/data/{config.UPLOAD_DIR}/{task_id}"
            
            # 确保路径使用正斜杠并以斜杠结尾
            if not relative_path.endswith("/"):
                relative_path += "/"
            
            result = {}
            # 遍历目录中的所有txt文件
            for filename in os.listdir(task.marked_images_path):
                if filename.endswith('.txt') and filename != "sample_prompts.txt":
                    file_path = os.path.join(task.marked_images_path, filename)
                    try:
                        # 获取不带扩展名的文件名
                        name_without_ext = os.path.splitext(filename)[0]
                        # 查找原始图片文件名
                        original_filename = image_name_map.get(name_without_ext)
                        
                        if original_filename:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # 使用相对路径作为键的前缀
                                result_key = f"{relative_path}{original_filename}"
                                result[result_key] = content
                        else:
                            logger.warning(f"找不到与打标文本 {filename} 对应的原始图片")
                    except Exception as e:
                        logger.error(f"读取文件 {file_path} 失败: {str(e)}")
                        if original_filename:
                            result_key = f"{relative_path}{original_filename}"
                            result[result_key] = f"读取失败: {str(e)}"
            
            return result
        except Exception as e:
            logger.error(f"获取打标文本失败: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def update_marked_text(db: Session, task_id: int, image_filename: str, content: str) -> Dict:
        """
        更新某张图片的打标文本
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            image_filename: 图片文件名或从/data开始的相对路径+文件名
            content: 新的打标文本内容
            
        Returns:
            包含操作结果的字典
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"success": False, "message": f"任务 {task_id} 不存在"}
            
            if task.status not in [TaskStatus.MARKED, TaskStatus.TRAINING, TaskStatus.COMPLETED]:
                return {"success": False, "message": f"任务状态为 {task.status}，不允许编辑打标文本"}
            
            # 检查marked_images_path是否存在
            if not task.marked_images_path or not os.path.exists(task.marked_images_path):
                return {"success": False, "message": f"打标目录不存在: {task.marked_images_path}"}
            
            # 使用任务的marked_images_path作为打标目录
            marked_dir = task.marked_images_path
            
            # 处理可能是从/data开始的相对路径的情况
            original_filename = None
            
            # 如果是相对路径（以/data开头），需要提取实际的文件名
            if image_filename.startswith('/data/'):
                original_filename = os.path.basename(image_filename)
            else:
                # 直接使用传入的文件名
                image = next((img for img in task.images if img.filename == image_filename), None)
                if image:
                    original_filename = image_filename
            
            # 如果无法找到对应的原始文件名，返回错误
            if not original_filename:
                return {"success": False, "message": f"图片 {image_filename} 不属于该任务或路径无法识别"}
            
            # 获取不带扩展名的文件名
            name_without_ext = os.path.splitext(original_filename)[0]
            # 打标文本文件路径
            text_file_path = os.path.join(marked_dir, f"{name_without_ext}.txt")
            
            # 写入新的打标文本内容
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 记录日志
            task.add_log(f"更新了图片 {original_filename} 的打标文本", db=db)
            
            return {
                "success": True, 
                "message": "打标文本更新成功",
                "filename": original_filename,
                "original_path": image_filename,
                "text_path": text_file_path
            }
            
        except Exception as e:
            logger.error(f"更新打标文本失败: {str(e)}", exc_info=True)
            return {"success": False, "message": f"更新打标文本失败: {str(e)}"}
            
    @staticmethod
    def batch_update_marked_texts(db: Session, task_id: int, texts_map: Dict[str, str]) -> Dict:
        """
        批量更新多个图片的打标文本
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            texts_map: 从/data开始的相对路径+文件名到文本内容的映射字典
            
        Returns:
            包含操作结果的字典
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"success": False, "message": f"任务 {task_id} 不存在"}
            
            if task.status not in [TaskStatus.MARKED, TaskStatus.TRAINING, TaskStatus.COMPLETED]:
                return {"success": False, "message": f"任务状态为 {task.status}，不允许编辑打标文本"}
            
            # 检查marked_images_path是否存在
            if not task.marked_images_path or not os.path.exists(task.marked_images_path):
                return {"success": False, "message": f"打标目录不存在: {task.marked_images_path}"}
            
            # 使用任务的marked_images_path作为打标目录
            marked_dir = task.marked_images_path
            
            results = {
                "success": True,
                "message": "批量更新打标文本完成",
                "updated": [],
                "failed": []
            }
            
            # 获取任务中所有图片的文件名和/data路径的映射
            image_name_map = {}
            marked_data_path = task.marked_images_path.replace(config.PROJECT_ROOT, "")
            # 确保路径使用正斜杠
            marked_data_path = marked_data_path.replace("\\", "/")
            if not marked_data_path.endswith("/"):
                marked_data_path += "/"
                
            for image in task.images:
                marked_path = f"{marked_data_path}{image.filename}"
                image_name_map[marked_path] = image.filename
            
            for path_filename, content in texts_map.items():
                try:
                    # 从路径中提取原始文件名
                    original_filename = None
                    
                    # 直接在映射中查找
                    if path_filename in image_name_map:
                        original_filename = image_name_map[path_filename]
                    
                    if not original_filename:
                        results["failed"].append({
                            "filename": path_filename,
                            "reason": f"无法匹配路径 {path_filename} 到任务中的图片"
                        })
                        continue
                    
                    # 获取不带扩展名的文件名
                    name_without_ext = os.path.splitext(original_filename)[0]
                    # 打标文本文件路径
                    text_file_path = os.path.join(marked_dir, f"{name_without_ext}.txt")
                    
                    # 写入新的打标文本内容
                    with open(text_file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    results["updated"].append({
                        "filename": original_filename,
                        "path": path_filename,
                        "text_path": text_file_path
                    })
                    
                except Exception as e:
                    logger.error(f"更新图片 {path_filename} 的打标文本失败: {str(e)}")
                    results["failed"].append({
                        "filename": path_filename,
                        "reason": str(e)
                    })
            
            # 记录日志
            if results["updated"]:
                updated_files = [item["filename"] for item in results["updated"]]
                task.add_log(f"批量更新了 {len(updated_files)} 个图片的打标文本: {', '.join(updated_files)}", db=db)
            
            # 如果全部失败，则整体标记为失败
            if not results["updated"] and results["failed"]:
                results["success"] = False
                results["message"] = "所有打标文本更新都失败了"
            
            return results
            
        except Exception as e:
            logger.error(f"批量更新打标文本失败: {str(e)}", exc_info=True)
            return {"success": False, "message": f"批量更新打标文本失败: {str(e)}"}

    @staticmethod
    def get_training_results(task_id: int) -> Dict:
        """
        获取训练结果，包括模型文件和预览图的相对路径
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含训练结果的字典
        """
        with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    return {"success": False, "message": f"任务 {task_id} 不存在"}
                
                # 使用任务指定的训练输出目录
                if not task.training_output_path or not os.path.exists(task.training_output_path):
                    return {"success": False, "message": f"训练输出目录不存在: {task.training_output_path}"}
                    
                output_dir = task.training_output_path
                    
                # 获取相对路径前缀（从/data开始）
                output_data_path = output_dir.replace(config.PROJECT_ROOT, "")
                output_data_path = output_data_path.replace("\\", "/")
                if not output_data_path.startswith("/data"):
                    output_data_path = f"/data{output_data_path}"
                if not output_data_path.endswith("/"):
                    output_data_path += "/"
                
                # 读取预览图的提示词
                preview_prompts = []
                sample_prompts_path = os.path.join(task.marked_images_path, "sample_prompts.txt")
                if os.path.exists(sample_prompts_path):
                    try:
                        with open(sample_prompts_path, "r", encoding="utf-8") as f:
                            for line in f:
                                # 提取--n前面的正向提示词
                                prompt_parts = line.split("--n")
                                if len(prompt_parts) > 0:
                                    preview_prompts.append(prompt_parts[0].strip())
                                else:
                                    preview_prompts.append(line.strip())
                    except Exception as e:
                        logger.error(f"读取预览图提示词失败: {str(e)}")
                
                # 提示词和预览图序号的映射字典
                prompt_index_map = {}
                if preview_prompts:
                    for i, prompt in enumerate(preview_prompts):
                        prompt_index_map[f"{i:02d}"] = prompt
                    
                # 预先加载sample目录中的所有预览图及其修改时间
                sample_dir = os.path.join(output_dir, "sample")
                preview_images_by_epoch = {}  # 按轮次分组的预览图
                max_epoch = "000000"  # 初始化最大轮次
                
                if os.path.exists(sample_dir) and os.path.isdir(sample_dir):
                    # 使用一次循环处理所有预览图
                    for img_file in os.listdir(sample_dir):
                        if img_file.endswith('.png'):
                            # 尝试从文件名中提取epoch数字
                            epoch_match = re.search(r'_e(\d{6})_', img_file)
                            if epoch_match:
                                epoch_num = epoch_match.group(1)
                                # 如果这个轮次还没有预览图列表，创建一个
                                if epoch_num not in preview_images_by_epoch:
                                    preview_images_by_epoch[epoch_num] = []
                                
                                # 构建预览图对象
                                image_path = f"{output_data_path}sample/{img_file}"
                                preview_image = {"path": image_path, "prompt": ""}
                                
                                # 从文件名中提取提示词索引并关联提示词
                                prompt_index_match = re.search(r'_(\d{2})_', img_file)
                                if prompt_index_match and prompt_index_map:
                                    prompt_index = prompt_index_match.group(1)
                                    if prompt_index in prompt_index_map:
                                        preview_image["prompt"] = prompt_index_map[prompt_index]
                                
                                # 添加预览图对象到对应轮次的列表
                                preview_images_by_epoch[epoch_num].append(preview_image)
                                
                                # 更新最大轮次
                                if epoch_num > max_epoch:
                                    max_epoch = epoch_num
                
                # 查找所有模型文件
                models = []
                for filename in os.listdir(output_dir):
                    file_path = os.path.join(output_dir, filename)
                    if os.path.isfile(file_path) and (filename.endswith('.safetensors') or filename.endswith('.pt')):
                        # 获取模型名称（不含扩展名）
                        model_name_base = os.path.splitext(filename)[0]
                        
                        # 初始化预览图为空数组
                        preview_images = []
                        
                        # 尝试从模型名称中提取轮次编号
                        epoch_match = re.search(r'-(\d{6})', model_name_base)
                        
                        if epoch_match:
                            # 如果是有轮次的模型，查找对应的预览图数组
                            epoch_num = epoch_match.group(1)
                            if epoch_num in preview_images_by_epoch:
                                # 使用所有匹配的预览图对象
                                preview_images = preview_images_by_epoch[epoch_num]
                        else:
                            # 如果是最后一轮模型（没有轮次数字），使用轮数最大的预览图
                            if max_epoch in preview_images_by_epoch:
                                preview_images = preview_images_by_epoch[max_epoch]
                        
                        # 构建模型信息
                        model_info = {
                            "name": filename,
                            "path": f"{output_data_path}{filename}",
                            "preview_images": preview_images,  # 现在是包含路径和提示词的对象数组
                            "size": os.path.getsize(file_path),
                            "modified_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        }
                        models.append(model_info)
                
                return {
                    "task_id": task_id,
                    "task_name": task.name,
                    "output_dir": output_data_path,
                    "models": models,
                    "total_models": len(models)
                }
            
    @staticmethod
    def get_training_loss_data(task_id: int) -> Dict:
        """
        获取训练loss曲线数据并计算训练进度
        
        Args:
            task_id: 任务ID
            history_id: 历史记录ID（可选）
            
        Returns:
            包含loss曲线数据和训练进度的字典
        """
        with get_db() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
            
            # 检查任务状态
            if task.status not in [TaskStatus.TRAINING, TaskStatus.COMPLETED]:
                raise ValueError(f"任务状态 {task.status} 不支持获取训练数据")
            
            # 检查是否有训练资产和prompt_id
            if not task.training_asset or not task.prompt_id:
                raise ValueError("任务没有关联的训练资产或训练ID")
    
        # 获取训练配置（从执行历史记录中获取）
        training_config = None
        
        execution_history = db.query(TaskExecutionHistory).filter(
            TaskExecutionHistory.id == task.execution_history_id
        ).first()
        
        if execution_history and execution_history.training_config:
            training_config = execution_history.training_config
        
        # 如果从执行历史记录中没有获取到配置，则回退到使用ConfigService
        if not training_config:
            training_config = ConfigService.get_task_training_config(task_id)
            if not training_config:
                raise ValueError("无法获取训练配置")
            
        # 计算总步数
        image_count = db.query(TaskImage).filter(TaskImage.task_id == task_id).count()
        repeat_num = training_config.get('repeat_num', 10)  # 默认重复次数为10
        max_epochs = training_config.get('max_train_epochs', 10)  # 默认训练轮次为10
        train_batch_size = training_config.get('train_batch_size', 1)  # 默认训练batch size为1
        total_steps = image_count * repeat_num * max_epochs / train_batch_size
            
        # 创建训练处理器并获取loss数据
        handler = TrainRequestHandler(task.training_asset)
        
        loss_data = handler.get_training_loss_data(task.prompt_id)
            
        # 如果获取失败，抛出异常
        if not loss_data:
            raise RuntimeError("获取训练loss数据失败")
        
        # 计算当前步数和进度
        current_step = 0
        series_data = None
        
        if loss_data and isinstance(loss_data, list) and len(loss_data) > 0:
            run_to_series = loss_data[0].get('runToSeries', {})
            
            # 由于我们已经在TrainRequestHandler中匹配了正确的key
            # 所以这里run_to_series应该只有一个元素，直接获取其值
            if run_to_series:
                # 获取第一个(唯一的)key对应的数据
                first_key = next(iter(run_to_series))
                series_data = run_to_series[first_key]
                
                # 如果找到了数据系列，获取最后一个数据点的步数
                if series_data and len(series_data) > 0:
                    current_step = series_data[-1].get('step', 0)
                else:
                    logger.warning(f"训练数据系列为空")
            else:
                logger.warning(f"未找到任何训练数据系列")
                raise ValueError("未找到任何训练数据系列")
        
        result = {
            "success": True,
            "series": series_data,  # 返回匹配到的数据系列
            "training_progress": {
                "current_step": current_step,
                "total_steps": total_steps,
                "image_count": image_count,
                "repeat_num": repeat_num,
                "max_epochs": max_epochs
            }
        }
        
        # 如果任务有执行历史记录ID，保存loss数据到历史记录
        if task.execution_history_id:
            execution_history = db.query(TaskExecutionHistory).filter(
                TaskExecutionHistory.id == task.execution_history_id
            ).first()
            
            if execution_history:
                execution_history.loss_data = {"series": series_data}
                db.commit()
        
        return result

    @staticmethod
    def get_marking_progress_data(task_id: int) -> Dict:
        """
        获取标记进度数据，包括队列状态和系统信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含标记进度数据的字典
        """
        with get_db() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
            
            # 检查任务状态
            if task.status not in [TaskStatus.MARKING, TaskStatus.MARKED, TaskStatus.TRAINING, TaskStatus.COMPLETED]:
                raise ValueError(f"任务状态 {task.status} 不支持获取标记进度数据")
            
            # 优先从数据库获取已保存的进度数据
            marking_progress_from_db = None
            if task.execution_history_id:
                execution_history = db.query(TaskExecutionHistory).filter(
                    TaskExecutionHistory.id == task.execution_history_id
                ).first()
                
                if execution_history and execution_history.marking_progress_data:
                    marking_progress_from_db = execution_history.marking_progress_data

            # 如果任务已完成标记且数据库中有数据，直接返回
            if task.status in [TaskStatus.MARKED, TaskStatus.TRAINING, TaskStatus.COMPLETED] and marking_progress_from_db:
                return {
                    "success": True,
                    "progress": marking_progress_from_db.get("progress", {}),
                    "system_stats": marking_progress_from_db.get("system_stats", {}),
                    "timeline": marking_progress_from_db.get("timeline", []),
                    "from_database": True
                }
            
            # 检查是否有标记资产和prompt_id
            if not task.marking_asset or not task.prompt_id:
                # 如果没有实时数据但有数据库数据，返回数据库数据
                if marking_progress_from_db:
                    return {
                        "success": True,
                        "progress": marking_progress_from_db.get("progress", {}),
                        "system_stats": marking_progress_from_db.get("system_stats", {}),
                        "timeline": marking_progress_from_db.get("timeline", []),
                        "from_database": True
                    }
                raise ValueError("任务没有关联的标记资产或标记ID")

            try:
                # 创建标记处理器并获取进度数据
                handler = MarkRequestHandler(task.marking_asset)
                
                # 获取实时进度数据
                progress_data = handler.get_marking_progress_data(task.prompt_id)
                
                # 如果获取失败，使用数据库数据作为降级方案
                if not progress_data and marking_progress_from_db:
                    return {
                        "success": True,
                        "progress": marking_progress_from_db.get("progress", {}),
                        "system_stats": marking_progress_from_db.get("system_stats", {}),
                        "timeline": marking_progress_from_db.get("timeline", []),
                        "from_database": True
                    }
                
                if not progress_data:
                    raise RuntimeError("获取标记进度数据失败")
                
                # 保存进度数据到数据库（如果任务有执行历史记录ID）
                if task.execution_history_id:
                    execution_history = db.query(TaskExecutionHistory).filter(
                        TaskExecutionHistory.id == task.execution_history_id
                    ).first()
                    
                    if execution_history:
                        execution_history.marking_progress_data = progress_data
                        db.commit()
                
                result = {
                    "success": True,
                    "progress": progress_data.get("progress", {}),
                    "system_stats": progress_data.get("system_stats", {}),
                    "timeline": progress_data.get("timeline", []),
                    "from_database": False
                }
                
                return result
                
            except Exception as marking_error:
                # 使用数据库数据作为最终降级方案
                if marking_progress_from_db:
                    logger.warning(f"获取实时标记进度失败，使用数据库历史数据: {str(marking_error)}")
                    return {
                        "success": True,
                        "progress": marking_progress_from_db.get("progress", {}),
                        "system_stats": marking_progress_from_db.get("system_stats", {}),
                        "timeline": marking_progress_from_db.get("timeline", []),
                        "from_database": True
                    }
                else:
                    raise RuntimeError(f"获取标记进度数据失败: {str(marking_error)}")

    @staticmethod
    def get_execution_history(db: Session, task_id: int) -> List[Dict]:
        """
        获取任务的执行历史记录列表，不包括状态为RUNNING的记录
        同时关联查询资产名称
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            
        Returns:
            执行历史记录列表，包含资产名称
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return []
            
            # 获取所有执行历史记录，排除状态为RUNNING的记录
            history_records = db.query(TaskExecutionHistory).filter(
                TaskExecutionHistory.task_id == task_id,
                TaskExecutionHistory.status != 'RUNNING'  # 过滤掉RUNNING状态的记录
            ).order_by(TaskExecutionHistory.start_time.desc()).all()
            
            # 创建资产ID到名称的映射
            asset_ids = set()
            for record in history_records:
                if record.marking_asset_id:
                    asset_ids.add(record.marking_asset_id)
                if record.training_asset_id:
                    asset_ids.add(record.training_asset_id)
            
            # 批量查询所有需要的资产
            asset_map = {}
            if asset_ids:
                assets = db.query(Asset).filter(Asset.id.in_(list(asset_ids))).all()
                for asset in assets:
                    asset_map[asset.id] = asset.name
            
            # 转换为字典并添加资产名称
            result = []
            for record in history_records:
                record_dict = record.to_dict()
                
                # 添加资产名称
                if record.marking_asset_id and record.marking_asset_id in asset_map:
                    record_dict['marking_asset_name'] = asset_map[record.marking_asset_id]
                else:
                    record_dict['marking_asset_name'] = None
                    
                if record.training_asset_id and record.training_asset_id in asset_map:
                    record_dict['training_asset_name'] = asset_map[record.training_asset_id]
                else:
                    record_dict['training_asset_name'] = None
                
                result.append(record_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"获取执行历史记录失败: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def get_execution_history_by_id(db: Session, history_id: int) -> Optional[Dict]:
        """
        获取任务的单个执行历史记录详情，并关联查询资产名称
        
        Args:
            db: 数据库会话
            history_id: 历史记录ID
            
        Returns:
            执行历史记录详情，未找到则返回None
        """
        try:
            # 查询指定的执行历史记录
            history_record = db.query(TaskExecutionHistory).filter(
                TaskExecutionHistory.id == history_id
            ).first()
            
            if not history_record:
                logger.warning(f"未找到执行历史记录 {history_id}")
                return None
            
            result = history_record.to_dict()
            
            # 查询关联的资产名称
            if history_record.marking_asset_id:
                marking_asset = db.query(Asset).filter(Asset.id == history_record.marking_asset_id).first()
                result['marking_asset_name'] = marking_asset.name if marking_asset else None
            else:
                result['marking_asset_name'] = None
                
            if history_record.training_asset_id:
                training_asset = db.query(Asset).filter(Asset.id == history_record.training_asset_id).first()
                result['training_asset_name'] = training_asset.name if training_asset else None
            else:
                result['training_asset_name'] = None
                
            return result
            
        except Exception as e:
            logger.error(f"获取执行历史记录详情失败: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def update_execution_history_result(db: Session, execution_history_id: int, results: Dict, loss_data: Dict = None, status: str = 'COMPLETED') -> bool:
        """
        更新执行历史记录的结果
        
        Args:
            db: 数据库会话
            execution_history_id: 执行历史记录ID
            results: 结果数据
            loss_data: loss数据
            status: 状态（COMPLETED或ERROR）
            
        Returns:
            是否更新成功
        """
        try:
            execution_history = db.query(TaskExecutionHistory).filter(TaskExecutionHistory.id == execution_history_id).first()
            if not execution_history:
                return False
            
            execution_history.training_results = results
            
            # 如果提供了loss数据，更新loss_data字段
            if loss_data:
                execution_history.loss_data = loss_data
            
            execution_history.status = status
            execution_history.end_time = datetime.now()
            
            if status == 'COMPLETED':
                execution_history.description += f"\n结果更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                execution_history.description += f"\n失败状态更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新执行历史记录结果失败: {str(e)}", exc_info=True)
            db.rollback()
            return False

    @staticmethod
    def delete_execution_history(db: Session, history_id: int) -> Dict:
        """
        删除执行历史记录及其相关文件

        Args:
            db: 数据库会话
            history_id: 历史记录ID

        Returns:
            包含操作结果的字典
        """
        try:
            # 查询指定的执行历史记录
            history_record = db.query(TaskExecutionHistory).filter(
                TaskExecutionHistory.id == history_id
            ).first()
            
            if not history_record:
                raise ValueError(f"未找到执行历史记录 {history_id}")
            
            # 获取相关任务
            task = db.query(Task).filter(Task.id == history_record.task_id).first()
            
            # 检查是否是当前任务绑定的执行历史记录
            if task and task.execution_history_id == history_id:
                raise ValueError(f"无法删除当前任务绑定的执行历史记录 {history_id}，请先取消任务或等待任务完成")
            
            # 存储需要删除的文件路径
            directories_to_delete = []
            if history_record.marked_images_path and os.path.exists(history_record.marked_images_path):
                directories_to_delete.append(history_record.marked_images_path)
            
            if history_record.training_output_path and os.path.exists(history_record.training_output_path):
                directories_to_delete.append(history_record.training_output_path)
            
            # 从数据库中删除历史记录
            db.delete(history_record)
            db.commit()
            
            # 处理远程资产的远程目录删除
            BaseTaskService._delete_remote_directories(db, history_record)
            
            # 删除本地目录
            BaseTaskService._delete_local_directories(directories_to_delete)
            
            return {
                "success": True,
                "message": "执行历史记录已删除",
                "task_id": history_record.task_id,
                "history_id": history_id
            }
            
        except Exception as e:
            logger.error(f"删除执行历史记录失败: {str(e)}", exc_info=True)
            db.rollback()
            raise e

    @staticmethod
    def export_marked_files(task_id: int) -> Optional[Dict]:
        """
        导出打标后的文件为ZIP压缩包
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含ZIP文件路径和下载文件名的字典，如果任务不存在或未打标则返回None
        """
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    logger.warning(f"任务不存在: {task_id}")
                    return None
                    
                # 检查任务是否已完成打标
                if task.status not in [TaskStatus.MARKED, TaskStatus.COMPLETED, TaskStatus.TRAINING, TaskStatus.TRAINED]:
                    logger.warning(f"任务 {task_id} 尚未完成打标，当前状态: {task.status}")
                    return None
                
                # 检查打标输出目录是否存在
                if not task.marked_images_path or not os.path.exists(task.marked_images_path):
                    logger.warning(f"任务 {task_id} 的打标输出目录不存在: {task.marked_images_path}")
                    return None
                    
                # 创建临时文件用于存储ZIP
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                temp_file.close()
                
                # 创建ZIP文件
                with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # 遍历打标输出目录中的所有文件
                    for root, dirs, files in os.walk(task.marked_images_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 计算相对路径，保持目录结构
                            arcname = os.path.relpath(file_path, task.marked_images_path)
                            # 添加文件到ZIP（不包含子目录）
                            if os.path.dirname(arcname) == '':
                                zipf.write(file_path, arcname)
                
                # 生成下载文件名（包含任务名称）
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                # 确保任务名称中不包含非法字符
                safe_task_name = re.sub(r'[\\/*?:"<>|]', "_", task.name)
                download_name = f"{safe_task_name}_marked_files_{timestamp}.zip"
                
                logger.info(f"任务 {task_id} ({task.name}) 的打标文件已导出到: {temp_file.name}")
                return {
                    "file_path": temp_file.name,
                    "download_name": download_name
                }
                
        except Exception as e:
            logger.error(f"导出任务 {task_id} 打标文件失败: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def import_marked_files(db: Session, task_id: Optional[int], file_path: str, original_name: str, is_zip: bool = True) -> Dict:
        """
        导入打标文件（ZIP压缩包或文件夹）
        
        Args:
            db: 数据库会话
            task_id: 任务ID，如果为None则创建新任务
            file_path: 上传文件的临时路径
            original_name: 原始文件名或文件夹名（用于创建任务名称）
            is_zip: 是否为ZIP文件，False表示已解压的文件夹
            
        Returns:
            包含导入结果的字典
        """
        try:
            imported_files = []
            name_without_ext = os.path.splitext(original_name)[0]
            task_name = name_without_ext
            
            # 创建新任务或获取现有任务
            if task_id is None:
                # 创建新任务
                task = Task(
                    name=task_name,
                    status=TaskStatus.SUBMITTED,
                    description=f"从 {original_name} 导入的任务"
                )
                db.add(task)
                db.flush()  # 获取任务ID
                task_id = task.id
                
                # 创建任务目录结构
                BaseTaskService._create_task_directories(task)
                db.commit()
                
                logger.info(f"已创建新任务: {task_id} - {task_name}")
            else:
                # 获取现有任务
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    return {
                        "success": False,
                        "message": f"任务 {task_id} 不存在"
                    }
                
                # 任务必须处于UPLOADED或SUBMITTED状态才能导入
                if task.status not in [TaskStatus.UPLOADED, TaskStatus.SUBMITTED]:
                    return {
                        "success": False,
                        "message": f"任务状态为 {task.status}，不能导入打标文件"
                    }
                
                # 确保任务有标记目录
                if not task.marked_images_path:
                    # 初始化目录
                    BaseTaskService._create_task_directories(task)
                    db.commit()
            
            # 创建或确保marked_images_path存在
            if not os.path.exists(task.marked_images_path):
                os.makedirs(task.marked_images_path, exist_ok=True)
            
            # 处理ZIP文件
            if is_zip:
                # 解压文件到marked_images_path
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    for file_info in zip_ref.infolist():
                        # 跳过目录和以.开头的隐藏文件
                        if file_info.filename.endswith('/') or os.path.basename(file_info.filename).startswith('.'):
                            continue
                        
                        # 只提取根目录下的文件，不包含子目录
                        if '/' not in file_info.filename and '\\' not in file_info.filename:
                            zip_ref.extract(file_info, task.marked_images_path)
                            imported_files.append(file_info.filename)
            else:
                # 复制文件夹中的文件到marked_images_path
                src_files = os.listdir(file_path)
                for file_name in src_files:
                    src_file_path = os.path.join(file_path, file_name)
                    # 只复制文件，不包含目录和隐藏文件
                    if os.path.isfile(src_file_path) and not file_name.startswith('.'):
                        dst_file_path = os.path.join(task.marked_images_path, file_name)
                        import shutil
                        shutil.copy2(src_file_path, dst_file_path)
                        imported_files.append(file_name)
            
            # 更新任务状态为已标记
            task.update_status(TaskStatus.MARKED, f"已导入 {len(imported_files)} 个打标文件", db=db)
            
            # 返回结果
            return {
                "success": True,
                "message": f"成功导入 {len(imported_files)} 个打标文件",
                "task_id": task.id,
                "task_name": task.name,
                "imported_files": imported_files
            }
            
        except Exception as e:
            logger.error(f"导入打标文件失败: {str(e)}", exc_info=True)
            db.rollback()
            return {
                "success": False,
                "message": f"导入打标文件失败: {str(e)}"
            }