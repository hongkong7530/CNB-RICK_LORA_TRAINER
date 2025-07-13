from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ...models.task import Task, TaskImage, TaskStatus
from ...database import get_db
from ...utils.logger import setup_logger
import os
from werkzeug.utils import secure_filename
from ...config import config

logger = setup_logger('task_image_service')

class TaskImageService:
    @staticmethod
    def upload_images(db: Session, task_id: int, files: List) -> Optional[Dict]:
        """上传任务图片 - 优化版，支持部分成功"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task or task.status != TaskStatus.NEW:
                return {
                    "success": False,
                    "message": f"任务不存在或状态不允许上传图片",
                    "uploaded": [],
                    "failed": []
                }

            # 创建任务专属的上传目录
            task_upload_dir = os.path.join(config.UPLOAD_DIR, str(task_id))
            os.makedirs(task_upload_dir, exist_ok=True)

            uploaded_files = []
            failed_files = []

            for file in files:
                try:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(task_upload_dir, filename)
                    
                    # 保存文件
                    file.save(file_path)
                    
                    # 创建图片记录（每个文件独立事务）
                    image = TaskImage(
                        task_id=task_id,
                        filename=filename,
                        file_path=file_path,
                        preview_url=f'/data/uploads/{task_id}/{filename}',
                        size=os.path.getsize(file_path)
                    )
                    db.add(image)
                    db.flush()  # 立即刷新以获取ID
                    
                    uploaded_files.append(image.to_dict())
                    logger.info(f"成功上传文件: {filename}")
                    
                except Exception as file_error:
                    logger.error(f"上传文件 {file.filename} 失败: {file_error}")
                    failed_files.append({
                        "filename": file.filename,
                        "error": str(file_error)
                    })
                    # 继续处理其他文件，不回滚整个事务

            # 提交成功的文件
            if uploaded_files:
                db.commit()
                task.add_log(f"上传了 {len(uploaded_files)} 个图片文件", db=db)
                
            return {
                "success": len(uploaded_files) > 0,
                "message": f"成功上传 {len(uploaded_files)} 个文件，失败 {len(failed_files)} 个文件",
                "uploaded": uploaded_files,
                "failed": failed_files
            }
            
        except Exception as e:
            logger.error(f"上传图片服务异常: {e}")
            db.rollback()
            return {
                "success": False,
                "message": f"上传服务异常: {str(e)}",
                "uploaded": [],
                "failed": []
            }

    @staticmethod
    def delete_image(db: Session, task_id: int, image_id: int) -> bool:
        """删除任务图片"""
        try:
            image = db.query(TaskImage).filter(
                TaskImage.id == image_id,
                TaskImage.task_id == task_id
            ).first()

            if not image:
                logger.warning(f"未找到图片: task_id={task_id}, image_id={image_id}")
                return False
                
            # 1. 删除原始图片文件
            if image.file_path and os.path.exists(image.file_path):
                os.remove(image.file_path)
                logger.info(f"已删除图片文件: {image.file_path}")
            
            # 2. 删除对应的打标文本文件（如果存在）
            name_without_ext = os.path.splitext(image.filename)[0]
            marked_dir = os.path.join(config.MARKED_DIR, str(task_id))
            text_file_path = os.path.join(marked_dir, f"{name_without_ext}.txt")
            
            if os.path.exists(text_file_path):
                os.remove(text_file_path)
                logger.info(f"已删除打标文本文件: {text_file_path}")
            
            # 3. 从数据库中删除图片记录
            db.delete(image)
            
            # 4. 记录操作日志
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.add_log(f"删除了图片: {image.filename}", db=db)
            else:
                db.commit()
                
            return True
        except Exception as e:
            logger.error(f"删除图片失败: {e}")
            db.rollback()
            return False

    @staticmethod
    def batch_delete_images(db: Session, task_id: int, image_ids: List[int]) -> Dict:
        """批量删除任务图片
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            image_ids: 要删除的图片ID列表
            
        Returns:
            包含操作结果的字典，包括成功删除的图片和失败的图片
        """
        # 检查任务是否存在
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {
                "success": False,
                "message": f"任务 {task_id} 不存在",
                "deleted": [],
                "failed": [{"id": image_id, "reason": "任务不存在"} for image_id in image_ids]
            }
            
        # 检查任务状态，只有NEW状态的任务可以删除图片
        if task.status != TaskStatus.NEW:
            return {
                "success": False,
                "message": f"任务状态为 {task.status}，不允许删除图片",
                "deleted": [],
                "failed": [{"id": image_id, "reason": f"任务状态为 {task.status}，不允许删除图片"} for image_id in image_ids]
            }
            
        results = {
            "success": True,
            "message": "批量删除图片完成",
            "deleted": [],
            "failed": []
        }
        
        for image_id in image_ids:
            try:
                # 查询图片
                image = db.query(TaskImage).filter(
                    TaskImage.id == image_id,
                    TaskImage.task_id == task_id
                ).first()
                
                if not image:
                    results["failed"].append({
                        "id": image_id,
                        "reason": f"图片不存在或不属于任务 {task_id}"
                    })
                    continue
                    
                image_info = image.to_dict()
                
                # 1. 删除原始图片文件
                if image.file_path and os.path.exists(image.file_path):
                    os.remove(image.file_path)
                
                # 2. 删除对应的打标文本文件（如果存在）
                name_without_ext = os.path.splitext(image.filename)[0]
                marked_dir = os.path.join(config.MARKED_DIR, str(task_id))
                text_file_path = os.path.join(marked_dir, f"{name_without_ext}.txt")
                
                if os.path.exists(text_file_path):
                    os.remove(text_file_path)
                
                # 3. 从数据库中删除图片记录
                db.delete(image)
                
                # 添加到成功列表
                results["deleted"].append(image_info)
                
            except Exception as e:
                logger.error(f"删除图片 {image_id} 失败: {str(e)}")
                results["failed"].append({
                    "id": image_id,
                    "reason": str(e)
                })
        
        # 记录操作日志
        if results["deleted"]:
            deleted_filenames = [img.get("filename", f"ID:{img.get('id')}") for img in results["deleted"]]
            task.add_log(f"批量删除了 {len(results['deleted'])} 个图片: {', '.join(deleted_filenames)}", db=db)
        
        # 如果全部失败，则整体标记为失败
        if not results["deleted"] and results["failed"]:
            results["success"] = False
            results["message"] = "所有图片删除都失败了"
        
        return results 