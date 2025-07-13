from flask import Blueprint, request, current_app, send_file
from werkzeug.utils import secure_filename
import os
import time
from ...database import get_db
from ...services.task_service import TaskService
from ...services.config_service import ConfigService
from ...utils.logger import setup_logger
from ...utils.validators import validate_task_create, validate_file_upload
from ...utils.response import success_json, error_json, exception_handler, response_template
from ...models.task import Task, TaskImage, TaskStatus
from ...models.constants import COMMON_TRAINING_PARAMS, COMMON_MARK_PARAMS, FLUX_LORA_PARAMS
import tempfile


logger = setup_logger('tasks_api')
tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
@exception_handler
def list_tasks():
    """获取任务列表"""
    status = request.args.get('status')
    search = request.args.get('search')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    with get_db() as db:
        tasks = TaskService.list_tasks(
            db,
            status=status,
            search=search,
            start_date=start_date,
            end_date=end_date
        )
        return success_json(tasks)

@tasks_bp.route('', methods=['POST'])
@exception_handler
def create_task():
    """创建任务"""
    data = request.get_json()
    
    if not validate_task_create(data):
        return response_template("bad_request", msg="无效的任务数据，任务名称不能为空")
        
    with get_db() as db:
        task = TaskService.create_task(db, data)
        if task:
            return response_template("created", data=task)
        return error_json(1003, "创建任务失败")

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@exception_handler
def update_task(task_id):
    """更新任务"""
    data = request.get_json()
    
    with get_db() as db:
        task = TaskService.update_task(db, task_id, data)
        if task:
            return response_template("updated", data=task)
        return error_json(1004, "更新任务失败")

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@exception_handler
def delete_task(task_id):
    """删除任务"""
    with get_db() as db:
        if TaskService.delete_task(db, task_id):
            return response_template("deleted")
        return error_json(1005, "删除任务失败")

@tasks_bp.route('/<int:task_id>/log', methods=['GET'])
@exception_handler
def get_task_log(task_id):
    """获取任务日志"""
    content = TaskService.get_task_log(task_id)
    if content is not None:
        return success_json({"content": content})
    return response_template("not_found", msg="获取日志失败", code=404)

@tasks_bp.route('/stats', methods=['GET'])
@exception_handler
def get_stats():
    """获取任务统计"""
    with get_db() as db:
        return success_json(TaskService.get_stats(db))

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@exception_handler
def get_task(task_id):
    """获取任务详情"""
    with get_db() as db:
        task = TaskService.get_task_by_id(db, task_id)
        if task:
            return success_json(task)
        return response_template("not_found", code=1001, msg=f"未找到ID为 {task_id} 的任务")

@tasks_bp.route('/<int:task_id>/images', methods=['POST'])
@exception_handler
def upload_images(task_id):
    """上传任务图片"""
    if 'files' not in request.files:
        return response_template("bad_request", msg="没有上传文件")
        
    files = request.files.getlist('files')
    try:
        validate_file_upload(files)
    except Exception as e:
        return response_template("bad_request", msg=str(e))
        
    with get_db() as db:
        result = TaskService.upload_images(db, task_id, files)
        if result:
            # 根据上传结果返回不同的状态
            if result["success"]:
                return success_json(result, msg=result["message"])
            else:
                # 部分成功或完全失败
                if result["uploaded"]:
                    # 有成功上传的文件，返回警告状态但数据正常
                    return success_json(result, msg=result["message"])
                else:
                    # 完全失败
                    return error_json(msg=result["message"], data=result)
        return error_json(msg="上传图片失败")

@tasks_bp.route('/<int:task_id>/images/<int:image_id>', methods=['DELETE'])
@exception_handler
def delete_image(task_id, image_id):
    """删除任务图片及相关打标文本"""
    with get_db() as db:
        # 先获取图片信息，用于返回
        image = db.query(TaskImage).filter(
            TaskImage.id == image_id,
            TaskImage.task_id == task_id
        ).first()
        
        if not image:
            return response_template("not_found", msg="未找到指定图片")
        
        image_info = image.to_dict()
        
        if TaskService.delete_image(db, task_id, image_id):
            return success_json({
                "deleted_image": image_info,
                "deleted_text": os.path.splitext(image.filename)[0] + ".txt"
            }, "删除图片及相关文本成功")
        return error_json(msg="删除图片失败")

@tasks_bp.route('/<int:task_id>/images/batch', methods=['DELETE'])
@exception_handler
def batch_delete_images(task_id):
    """批量删除任务图片及相关打标文本"""
    data = request.get_json()
    if not data or 'image_ids' not in data or not isinstance(data['image_ids'], list):
        return response_template("bad_request", msg="请提供有效的图片ID列表")
    
    image_ids = data['image_ids']
    if not image_ids:
        return response_template("bad_request", msg="图片ID列表不能为空")
    
    with get_db() as db:
        result = TaskService.batch_delete_images(db, task_id, image_ids)
        if result.get('success', False):
            return success_json(result, result.get('message', '批量删除成功'))
        return error_json(msg=result.get('message', '批量删除失败'), data=result)

@tasks_bp.route('/<int:task_id>/mark', methods=['POST'])
@exception_handler
def start_marking(task_id):
    """开始标记"""
    with get_db() as db:
        result = TaskService.start_marking(db, task_id)
        if result:
            if 'error' in result:
                error_code = 2003 if result.get('error_type') == 'SYSTEM_ERROR' else 1002
                return error_json(error_code, result['error'], result.get('task'))
            return success_json(result)
        return error_json(msg="开始标记失败")

@tasks_bp.route('/<int:task_id>/train', methods=['POST'])
@exception_handler
def start_training(task_id):
    """开始训练"""
    try:
        with get_db() as db:
            result = TaskService.start_training(db, task_id)
        return success_json(result)
    except Exception as e:
        logger.error(f"开始训练失败: {str(e)}", exc_info=True)
        return error_json(msg=str(e))

@tasks_bp.route('/<int:task_id>/stop', methods=['POST'])
@exception_handler
def stop_task(task_id):
    """终止任务"""
    with get_db() as db:
        if TaskService.stop_task(db, task_id):
            return success_json(None, "任务已终止")
        return error_json(msg="终止任务失败")

@tasks_bp.route('/<int:task_id>/restart', methods=['POST'])
@exception_handler
def restart_task(task_id):
    """重启任务"""
    with get_db() as db:
        result = TaskService.restart_task(db, task_id)
        if result:
            if not result.get('success', False):
                error_code = 500 if result.get('error_type') == 'SYSTEM_ERROR' else 1002
                return error_json(error_code, result.get('error', "重启任务失败"))
            return success_json(result.get('task'))
        return error_json(msg="重启任务失败")

@tasks_bp.route('/<int:task_id>/cancel', methods=['POST'])
@exception_handler
def cancel_task(task_id):
    """取消任务"""
    with get_db() as db:
        from app.services.task_services.base_task_service import BaseTaskService
        result = BaseTaskService.cancel_task(db, task_id)
        if result:
            if not result.get('success', False):
                error_code = 500 if result.get('error_type') == 'SYSTEM_ERROR' else 1002
                return error_json(error_code, result.get('error', "取消任务失败"))
            return success_json(result.get('task'))
        return error_json(msg="取消任务失败")

@tasks_bp.route('/<int:task_id>/status', methods=['GET'])
@exception_handler
def get_task_status(task_id):
    """获取任务状态"""
    with get_db() as db:
        task_status = TaskService.get_task_status(db, task_id)
        if task_status:
            return success_json(task_status)
        return response_template("not_found", code=1001, msg=f"未找到ID为 {task_id} 的任务")
    
@tasks_bp.route('/<int:task_id>/marked_texts', methods=['GET'])
@exception_handler
def get_marked_texts(task_id):
    """获取打标后的文本内容"""
    with get_db() as db:
        marked_texts = TaskService.get_marked_texts(db, task_id)
        if marked_texts:
            return success_json(marked_texts)
        return response_template("not_found", code=1001, msg=f"未找到ID为 {task_id} 的任务打标文本")
    
@tasks_bp.route('/<int:task_id>/marked_texts', methods=['PUT'])
@exception_handler
def update_marked_text(task_id):
    """更新打标文本内容"""
    data = request.get_json()
    if not data or 'filename' not in data or 'content' not in data:
        return response_template("bad_request", msg="缺少必要的参数: filename 和 content")
    
    with get_db() as db:
        result = TaskService.update_marked_text(db, task_id, data['filename'], data['content'])
        if result.get('success', False):
            return success_json(result, result.get('message', '更新成功'))
        return error_json(msg=result.get('message', '更新失败'))

@tasks_bp.route('/<int:task_id>/marked_texts/batch', methods=['PUT'])
@exception_handler
def batch_update_marked_texts(task_id):
    """批量更新打标文本内容"""
    data = request.get_json()
    if not data or not isinstance(data, dict) or not data:
        return response_template("bad_request", msg="请提供有效的文件名到文本内容的映射字典")
    
    with get_db() as db:
        result = TaskService.batch_update_marked_texts(db, task_id, data)
        if result.get('success', False):
            return success_json(result, result.get('message', '批量更新成功'))
        return error_json(msg=result.get('message', '批量更新失败'))
        
#创建一个测试接口，修改任务ID为2的状态为完成
@tasks_bp.route('/test/complete', methods=['POST'])
@exception_handler
def test_complete_task():
    """测试接口：将任务ID为2的状态修改为完成"""
    with get_db() as db:
        task = db.query(Task).filter(Task.id == 2).first()
        if task:
            task.update_status('COMPLETED', '测试接口：任务已完成', db=db)
            return success_json(task.to_dict(), msg="测试成功：任务状态已修改为完成")
        return error_json(msg="测试失败：未找到ID为2的任务")

@tasks_bp.route('/<int:task_id>/mark-config', methods=['GET'])
@exception_handler
def get_task_mark_config(task_id):
    """获取任务的打标配置"""
    mark_config = ConfigService.get_task_mark_config(task_id)
    if mark_config is None:
        return response_template("not_found", code=1004, msg="任务不存在")
    return success_json(mark_config)

@tasks_bp.route('/<int:task_id>/training-config', methods=['GET'])
@exception_handler
def get_task_training_config(task_id):
    """获取任务的训练配置"""
    training_config = ConfigService.get_task_training_config(task_id)
    if training_config is None:
        return response_template("not_found", code=1004, msg="任务不存在")
    return success_json(training_config)

@tasks_bp.route('/<int:task_id>/training-results', methods=['GET'])
def get_training_results(task_id):
    """
    获取任务的训练结果，包括模型文件和预览图
    """
    try:
        result = TaskService.get_training_results(task_id)
        return success_json(data=result)
    except Exception as e:
        logger.error(f"获取训练结果失败: {str(e)}")
        return error_json(msg=f"获取训练结果失败: {str(e)}")

@tasks_bp.route('/<int:task_id>/marking-progress', methods=['GET'])
def get_marking_progress(task_id):
    """
    获取任务的标记进度数据，包括队列状态和系统信息
    """
    try:
        result = TaskService.get_marking_progress_data(task_id)
        return success_json(data=result)
    except Exception as e:
        logger.error(f"获取标记进度数据失败: {str(e)}")
        return error_json(msg=f"获取标记进度数据失败: {str(e)}")

@tasks_bp.route('/<int:task_id>/training-loss', methods=['GET'])
def get_training_loss(task_id):
    """
    获取任务的训练loss曲线数据和训练进度
    """
    try:
        result = TaskService.get_training_loss_data(task_id)
        return success_json(data=result)
    except Exception as e:
        logger.error(f"获取训练loss数据失败: {str(e)}")
        return error_json(msg=f"获取训练loss数据失败: {str(e)}")

@tasks_bp.route('/<int:task_id>/execution-history', methods=['GET'])
@exception_handler
def get_execution_history(task_id):
    """
    获取任务的执行历史记录列表
    """
    with get_db() as db:
        history_records = TaskService.get_execution_history(db, task_id)
        return success_json(data=history_records)

@tasks_bp.route('/execution-history/<int:history_id>', methods=['DELETE'])
@exception_handler
def delete_execution_history(history_id):
    """
    删除指定的执行历史记录及其相关文件
    """
    try:
        with get_db() as db:
            result = TaskService.delete_execution_history(db, history_id)
            return success_json(result, f"执行历史记录 {history_id} 已成功删除")
    except ValueError as e:
        return error_json(1006, str(e))
    except Exception as e:
        logger.error(f"删除执行历史记录失败: {str(e)}", exc_info=True)
        return error_json(1006, f"删除执行历史记录失败: {str(e)}")

@tasks_bp.route('/execution-history/<int:history_id>', methods=['GET'])
@exception_handler
def get_execution_history_by_id(history_id):
    """
    获取任务的单个执行历史记录详情
    """
    with get_db() as db:
        history_record = TaskService.get_execution_history_by_id(db, history_id)
        if history_record:
            return success_json(data=history_record)
        return response_template("not_found", code=1006, msg=f"未找到ID为 {history_id} 的执行历史记录")

@tasks_bp.route('/<int:task_id>/config', methods=['GET'])
@exception_handler
def get_task_config(task_id):
    """
    获取任务的打标配置和训练配置
    """
    with get_db() as db:
        task_config = TaskService.get_task_config(db, task_id)
        if task_config:
            return success_json(data=task_config)
        return response_template("not_found", code=1007, msg=f"未找到ID为 {task_id} 的任务配置")

@tasks_bp.route('/<int:task_id>/config', methods=['PUT'])
@exception_handler
def update_task_config(task_id):
    """
    更新任务的打标配置和训练配置
    """
    data = request.get_json()
    if not data:
        return response_template("bad_request", msg="请提供有效的配置数据")
        
    with get_db() as db:
        task = TaskService.update_task_config(db, task_id, data)
        if task:
            return response_template("updated", data=task)
        return error_json(1004, "更新任务失败")

@tasks_bp.route('/batch/mark', methods=['POST'])
@exception_handler
def batch_start_marking():
    """批量提交任务进行标记"""
    data = request.get_json()
    if not data or 'task_ids' not in data or not isinstance(data['task_ids'], list):
        return response_template("bad_request", msg="请提供有效的任务ID列表")
        
    task_ids = data['task_ids']
    if not task_ids:
        return response_template("bad_request", msg="任务ID列表不能为空")
    
    with get_db() as db:
        try:
            succeeded_ids = TaskService.batch_start_marking(db, task_ids)
            return success_json({"task_ids": succeeded_ids}, "批量提交标记成功")
        except ValueError as e:
            return error_json(1002, str(e))
        except Exception as e:
            logger.error(f"批量提交标记失败: {str(e)}", exc_info=True)
            return error_json(2003, f"系统错误: {str(e)}")

@tasks_bp.route('/<int:task_id>/export', methods=['GET'])
@exception_handler
def export_marked_files(task_id):
    """
    导出任务打标后的文件为ZIP压缩包
    只有任务已完成打标才可导出
    """
    try:
        # 导出打标文件
        result = TaskService.export_marked_files(task_id)
        
        if not result:
            return error_json(1009, "导出打标文件失败，可能任务未完成打标或没有可导出的文件")
        
        # 使用服务返回的文件路径和下载名称
        zip_file_path = result["file_path"]
        download_name = result["download_name"]
        
        # 返回文件下载
        return send_file(
            zip_file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/zip'
        )
    except Exception as e:
        logger.error(f"导出打标文件失败: {str(e)}", exc_info=True)
        return error_json(1010, f"导出打标文件失败: {str(e)}")

@tasks_bp.route('/import', methods=['POST'])
@exception_handler
def import_marked_files():
    """
    导入打标文件（ZIP文件）
    可以选择导入到已有任务或创建新任务
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return response_template("bad_request", msg="没有上传文件")
            
        file = request.files['file']
        if file.filename == '':
            return response_template("bad_request", msg="未选择文件")
            
        # 获取任务ID（可选）
        task_id = request.form.get('task_id')
        if task_id:
            try:
                task_id = int(task_id)
            except ValueError:
                return response_template("bad_request", msg="无效的任务ID")
        else:
            task_id = None
            
        # 检查文件类型
        if not file.filename.lower().endswith('.zip'):
            return response_template("bad_request", msg="仅支持ZIP格式的文件")
            
        # 保存上传文件到临时目录
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(temp_file_path)
        
        try:
            # 导入文件
            with get_db() as db:
                result = TaskService.import_marked_files(
                    db=db,
                    task_id=task_id,
                    file_path=temp_file_path,
                    original_name=file.filename,
                    is_zip=True
                )
                
            # 清理临时文件
            try:
                os.remove(temp_file_path)
                os.rmdir(temp_dir)
            except:
                pass
                
            if result.get('success', False):
                return success_json(result, result.get('message', '导入成功'))
            else:
                return error_json(1011, result.get('message', '导入失败'))
                
        except Exception as e:
            # 清理临时文件
            try:
                os.remove(temp_file_path)
                os.rmdir(temp_dir)
            except:
                pass
            raise e
            
    except Exception as e:
        logger.error(f"导入打标文件失败: {str(e)}", exc_info=True)
        return error_json(1012, f"导入打标文件失败: {str(e)}")

@tasks_bp.route('/<int:task_id>/import', methods=['POST'])
@exception_handler
def import_marked_files_to_task(task_id):
    """
    导入打标文件到指定任务
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return response_template("bad_request", msg="没有上传文件")
            
        file = request.files['file']
        if file.filename == '':
            return response_template("bad_request", msg="未选择文件")
            
        # 检查文件类型
        if not file.filename.lower().endswith('.zip'):
            return response_template("bad_request", msg="仅支持ZIP格式的文件")
            
        # 保存上传文件到临时目录
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(temp_file_path)
        
        try:
            # 导入文件
            with get_db() as db:
                result = TaskService.import_marked_files(
                    db=db,
                    task_id=task_id,
                    file_path=temp_file_path,
                    original_name=file.filename,
                    is_zip=True
                )
                
            # 清理临时文件
            try:
                os.remove(temp_file_path)
                os.rmdir(temp_dir)
            except:
                pass
                
            if result.get('success', False):
                return success_json(result, result.get('message', '导入成功'))
            else:
                return error_json(1011, result.get('message', '导入失败'))
                
        except Exception as e:
            # 清理临时文件
            try:
                os.remove(temp_file_path)
                os.rmdir(temp_dir)
            except:
                pass
            raise e
            
    except Exception as e:
        logger.error(f"导入打标文件失败: {str(e)}", exc_info=True)
        return error_json(1012, f"导入打标文件失败: {str(e)}")