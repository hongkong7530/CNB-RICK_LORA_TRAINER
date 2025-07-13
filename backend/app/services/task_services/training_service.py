from typing import List, Dict,Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ...models.task import Task, TaskStatus, TaskExecutionHistory
from ...models.asset import Asset
from ...database import get_db
from ...utils.logger import setup_logger
from ...services.config_service import ConfigService
from ...utils.file_handler import generate_unique_folder_path
from ...utils.train_handler import TrainRequestHandler
from ...utils.common import copy_attributes
from ...utils.ssh import create_ssh_client_from_asset, SSHClientTool
from ...services.asset_service import AssetService
from ...config import Config
import json
import traceback
import os
import time
import re
import shutil

logger = setup_logger('training_service')

class TrainingService:
    @staticmethod
    def get_available_training_assets() -> List[Asset]:
        """获取可用于训练的资产"""
        try:
            assets = AssetService.verify_all_assets('lora_training')
            # 训练资产最大并发数固定为1
            return [asset for asset in assets if asset.training_tasks_count < 1]
        except Exception as e:
            logger.error(f"获取可用训练资产失败: {str(e)}")
            return []
            
    @staticmethod
    def start_training(db: Session, task_id: int) -> Dict[str, Any]:
        """启动训练流程"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")
        
        # 检查当前状态
        if task.status != TaskStatus.MARKED:
            raise ValueError(f"当前任务状态为{task.status}，无法启动训练")
            
        # 获取训练配置，校验模型路径
        training_config = ConfigService.get_task_training_config(task_id)
        if not training_config:
            raise ValueError("无法获取训练配置")
        
        # 创建任务训练配置的副本
        temp_config = task.training_config.copy() if task.training_config else {}
        
        # 检查模型训练类型和对应模型路径
        model_train_type = training_config.get('model_train_type')
        network_module_updated = False
        
        if model_train_type == 'flux-lora':
            model_path = training_config.get('flux_model_path')
            if not model_path:
                raise ValueError("flux-lora训练类型需要设置有效的flux模型路径")
            
            # 检查网络模块是否匹配
            flux_network_modules = ['networks.lora_flux', 'networks.oft_flux', 'lycoris.kohya']
            network_module = training_config.get('network_module')
            if network_module not in flux_network_modules:
                temp_config['network_module'] = 'networks.lora_flux'
                network_module_updated = True
                logger.info(f"已将任务{task_id}的网络模块修正为networks.lora_flux")
                
        elif model_train_type == 'sd-lora' or model_train_type == 'sdxl-lora':
            # 检查对应模型路径
            if model_train_type == 'sd-lora':
                model_path = training_config.get('sd_model_path')
                if not model_path:
                    raise ValueError("sd-lora训练类型需要设置有效的SD模型路径")
            else:  # sdxl-lora
                model_path = training_config.get('sdxl_model_path')
                if not model_path:
                    raise ValueError("sdxl-lora训练类型需要设置有效的SDXL模型路径")
            
            # 两种类型都使用相同的网络模块列表
            sd_network_modules = ['networks.lora', 'networks.dylora', 'networks.oft', 'lycoris.kohya']
            network_module = training_config.get('network_module')
            if network_module not in sd_network_modules:
                temp_config['network_module'] = 'networks.lora'
                network_module_updated = True
                logger.info(f"已将任务{task_id}的网络模块修正为networks.lora")
        else:
            raise ValueError(f"不支持的模型训练类型: {model_train_type}")
        
        # 如果网络模块被更新，使用setattr设置回任务对象
        if network_module_updated:
            logger.info(f"更新任务{task_id}的训练配置: {temp_config}")
            setattr(task, 'training_config', temp_config)
            db.add(task)
            db.commit()
            logger.info(f"成功保存任务{task_id}的更新后的训练配置")
        
        # 更新任务状态
        task.update_status(TaskStatus.TRAINING, '准备开始训练', db=db)
        return task.to_dict()
    
    @staticmethod
    def _generate_sample_prompts(task_id: int, training_config: Dict) -> str:
        """
        根据任务配置生成sample_prompts
        
        Args:
            task_id: 任务ID
            training_config: 训练配置
            
        Returns:
            生成的sample_prompts文件路径
        """
        try:
            # 获取配置参数，确保类型安全
            use_image_tags = training_config.get('use_image_tags', False)
            # 安全转换 max_image_tags，处理空字符串和非数字值
            max_image_tags_raw = training_config.get('max_image_tags', 5)
            try:
                max_image_tags = int(max_image_tags_raw) if max_image_tags_raw not in ['', None] else 5
            except (ValueError, TypeError):
                max_image_tags = 5
            
            positive_prompt = training_config.get('positive_prompts', '')
            negative_prompt = training_config.get('negative_prompts', 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,signature, watermark, username, blurry')
            
            # 获取采样参数，确保类型安全
            def safe_int(value, default):
                try:
                    return int(value) if value not in ['', None] else default
                except (ValueError, TypeError):
                    return default
            
            width = safe_int(training_config.get('sample_width'), 512)
            height = safe_int(training_config.get('sample_height'), 768)
            cfg = safe_int(training_config.get('sample_cfg'), 7)
            steps = safe_int(training_config.get('sample_steps'), 24)
            seed = safe_int(training_config.get('sample_seed'), 1337)
            
            # 准备保存提示词的文件
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                # 创建输出目录（如果不存在）
                os.makedirs(task.marked_images_path, exist_ok=True)
                
                # 提示词文件路径
                sample_prompts_file = os.path.join(task.marked_images_path, "sample_prompts.txt")
            
            # 如果使用图片标签
            if use_image_tags:
                with get_db() as db:
                    from ...services.task_services.result_service import ResultService
                    # 获取任务的打标文本
                    marked_texts = ResultService.get_marked_texts(db, task_id)
                    
                    if not marked_texts:
                        # 如果没有打标文本，使用默认提示词
                        default_prompt = f"(masterpiece, best quality:1.2), 1girl, solo --n {negative_prompt} --w {width} --h {height} --l {cfg} --s {steps} --d {seed}"
                        with open(sample_prompts_file, "w", encoding="utf-8") as f:
                            f.write(default_prompt)
                        return sample_prompts_file
                    
                    # 构建多行提示词
                    prompts = []
                    count = 0
                    
                    for _, text in marked_texts.items():
                        if count >= max_image_tags:
                            break
                        
                        # 提取文本的第一行作为提示词
                        first_line = text.strip().split('\n')[0] if text else ""
                        if first_line:
                            # 添加基本质量词和采样参数
                            prompt = f"(masterpiece, best quality:1.2), {first_line} --n {negative_prompt} --w {width} --h {height} --l {cfg} --s {steps} --d {seed}"
                            prompts.append(prompt)
                            count += 1
                    
                    # 如果没有有效的提示词，使用默认提示词
                    if not prompts:
                        default_prompt = f"(masterpiece, best quality:1.2), 1girl, solo --n {negative_prompt} --w {width} --h {height} --l {cfg} --s {steps} --d {seed}"
                        with open(sample_prompts_file, "w", encoding="utf-8") as f:
                            f.write(default_prompt)
                        return sample_prompts_file
                    
                    # 写入多行提示词到文件
                    with open(sample_prompts_file, "w", encoding="utf-8") as f:
                        f.write("\n".join(prompts))
                    
                    return sample_prompts_file
            else:
                # 使用配置中的正向提示词
                prompt = f"(masterpiece, best quality:1.2), {positive_prompt} --n {negative_prompt} --w {width} --h {height} --l {cfg} --s {steps} --d {seed}"
                with open(sample_prompts_file, "w", encoding="utf-8") as f:
                    f.write(prompt)
                return sample_prompts_file
        
        except Exception as e:
            logger.error(f"生成sample_prompts失败: {str(e)}", exc_info=True)
            # 如果生成失败，创建一个简单的默认提示词文件
            try:
                with get_db() as db:
                    task = db.query(Task).filter(Task.id == task_id).first()
                    if task:
                        os.makedirs(task.marked_images_path, exist_ok=True)
                        sample_prompts_file = os.path.join(task.marked_images_path, "sample_prompts.txt")
                        default_prompt = "(masterpiece, best quality:1.2), 1girl, solo"
                        with open(sample_prompts_file, "w", encoding="utf-8") as f:
                            f.write(default_prompt)
                        logger.info(f"已创建默认sample_prompts文件: {sample_prompts_file}")
                        return sample_prompts_file
            except Exception as fallback_error:
                logger.error(f"创建默认sample_prompts文件也失败: {str(fallback_error)}")
            # 返回空字符串，让调用方处理
            return ""
            
    @staticmethod
    def _prepare_training_execution_history(task_id: int, db: Session, asset=None) -> Optional[Dict[str, Any]]:
        """
        准备训练执行历史记录和相关配置
        
        Args:
            task_id: 任务ID
            db: 数据库会话
            asset: 训练资产（可选）
            
        Returns:
            Dictionary containing training configuration
        """
        # 1. 获取任务和配置
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")
        
        mark_config = ConfigService.get_task_mark_config(task_id)
        training_config = ConfigService.get_task_training_config(task_id)
        
        # 2. 设置目录路径
        input_dir = task.marked_images_path
        training_output_path = generate_unique_folder_path(Config.OUTPUT_DIR, task_id, 'train')
        task.training_output_path = training_output_path

        # 3. 创建训练数据目录
        repeat_num = training_config.get('repeat_num', 10)
        train_data_dir = os.path.join(task.marked_images_path, f"{repeat_num}_rick")
        
        # 准备训练数据目录
        TrainingService._prepare_train_data_dir(input_dir, train_data_dir)
        task.add_log(f'训练数据目录: {train_data_dir}', db=db)
        
        # 4. 处理远程路径
        remote_path = None
        remote_train_data_dir = None
        remote_output_dir = None
        
        if task.mark_config and task.mark_config.get('remote_output_dir'):
            # 设置远程路径
            remote_path = task.mark_config['remote_output_dir'].replace('\\', '/')
            remote_train_data_dir = os.path.join(remote_path, f"{repeat_num}_rick").replace('\\', '/')
            task.add_log(f'远程训练数据目录: {remote_train_data_dir}', db=db)
            
        # 设置远程输出路径
        output_suffix = training_output_path.replace(Config.OUTPUT_DIR, '').replace('\\', '/')
        remote_output_dir = f"{Config.REMOTE_OUTPUT_DIR}{output_suffix}"
        training_config['remote_output_dir'] = remote_output_dir
        
        # 5. 对于远程资产，同步文件
        if asset and not asset.is_local and remote_path:
            TrainingService._sync_files_to_remote(task, asset, input_dir, remote_path, remote_train_data_dir, db)
            # 更新输入目录为远程目录
            input_dir = remote_path
        
        # 6. 更新训练配置
        training_config['train_data_dir'] = input_dir
        training_config['output_dir'] = remote_output_dir if asset and not asset.is_local else training_output_path
        training_config['output_name'] = task.name
        
        # 7. 处理生成预览图的配置
        if training_config.get('generate_preview'):
            # 生成sample_prompts.txt文件
            prompts_file = TrainingService._generate_sample_prompts(task_id, training_config)
            
            # 如果生成了提示词文件，将其路径添加到配置中
            if prompts_file:
                if asset and not asset.is_local and remote_path:
                    # 对于远程资产，上传提示词文件
                    remote_prompts_file = os.path.join(remote_path, "sample_prompts.txt").replace('\\', '/')
                    TrainingService._upload_prompts_file(task, asset, prompts_file, remote_prompts_file, db)
                    training_config['prompt_file'] = remote_prompts_file
                else:
                    # 本地资产，直接使用本地文件路径
                    training_config['prompt_file'] = prompts_file
            else:
                # 如果sample_prompts生成失败，禁用预览图生成
                logger.warning(f"sample_prompts文件生成失败，禁用预览图生成功能")
                training_config['generate_preview'] = False
                # 移除相关的预览图参数，避免训练脚本报错
                preview_params = ['sample_every_n_epochs', 'sample_sampler', 'sample_scheduler', 'sample_steps', 'sample_cfg']
                for param in preview_params:
                    if param in training_config:
                        training_config.pop(param)
        
        # 8. 创建执行历史记录
        execution_history = TaskExecutionHistory(
            task_id=task_id,
            status='RUNNING',
            mark_config=mark_config,
            training_config=training_config,  # 保存原始业务配置
            marked_images_path=task.marked_images_path,
            training_output_path=training_output_path,
            training_asset_id=asset.id if asset else None,
            marking_asset_id=task.marking_asset_id,
            description=f"训练开始于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        # 设置任务的training_config属性，避免检测不到更新
        setattr(task, 'training_config', training_config)
        db.add(execution_history)
        db.commit()
        db.refresh(execution_history)
        
        # 记录历史ID到任务
        task.execution_history_id = execution_history.id
        db.commit()
        
        # 记录训练配置
        task.add_log(f'训练配置: {json.dumps(training_config, indent=2, ensure_ascii=False)}', db=db)

        return training_config
    
    @staticmethod
    def _prepare_train_data_dir(input_dir: str, train_data_dir: str):
        """准备训练数据目录"""
        # 确保训练数据目录为空
        if os.path.exists(train_data_dir):
            shutil.rmtree(train_data_dir)
        
        # 创建训练数据目录
        os.makedirs(train_data_dir, exist_ok=True)
        
        # 复制文件
        for item in os.listdir(input_dir):
            src_path = os.path.join(input_dir, item)
            dst_path = os.path.join(train_data_dir, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
    
    @staticmethod
    def _sync_files_to_remote(task, asset, input_dir, remote_path, remote_train_data_dir, db):
        """同步文件到远程服务器"""
        task.add_log('资产不是本地资产，需要同步文件...', db=db)
        
        # 创建SSH客户端工具
        ssh_client = create_ssh_client_from_asset(asset)
        
        # 在远程服务器上创建训练数据目录
        success, message = ssh_client.mkdir(remote_train_data_dir)
        if not success:
            raise ValueError(f"创建远程训练数据目录失败: {message}")
        
        # 清空远程训练数据目录
        result = ssh_client.execute_command(f"rm -rf {remote_train_data_dir}/*")
        if result.returncode != 0:
            task.add_log(f'清空目录警告: {result.stderr}', db=db)

        # 检查是否需要同步标记结果（如果训练和打标资产不同）
        if not task.marking_asset or task.marking_asset_id != asset.id:
            task.add_log('训练和打标资产不同，需要同步打标结果到训练资产...', db=db)
            
            # 上传打标结果
            success, message, stats = ssh_client.upload_directory(
                local_path=input_dir,
                remote_path=remote_train_data_dir,
                recursive = False
            )
            
            if not success:
                raise ValueError(f"同步打标结果失败: {message}")
            
            task.add_log(f'打标结果同步成功: {message}', db=db)
        else:
            task.add_log('训练和打标使用相同资产，无需同步打标结果', db=db)
    
    @staticmethod
    def _upload_prompts_file(task, asset, local_file, remote_file, db):
        """上传提示词文件到远程服务器"""
        task.add_log(f'上传提示词文件到远程服务器: {remote_file}', db=db)
        
        # 创建SSH客户端工具
        ssh_client = create_ssh_client_from_asset(asset)
        
        # 创建远程目录
        ssh_client.mkdir(os.path.dirname(remote_file))
        
        # 上传提示词文件
        success, message = ssh_client.upload_file(
            local_path=local_file,
            remote_path=remote_file,
        )
        
        if success:
            task.add_log(f'提示词文件上传成功', db=db)
        else:
            task.add_log(f'提示词文件上传失败: {message}，将使用默认提示词', db=db)
    
    @staticmethod
    def _convert_training_config(training_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        将业务配置转换为训练配置
        
        Args:
            training_config: 业务配置
            
        Returns:
            转换后的训练配置
        """
        # 创建配置的副本，避免修改原始配置
        config = training_config.copy()
        
        # 根据模型训练类型设置预训练模型路径
        model_train_type = config.get('model_train_type')
        if model_train_type == 'flux-lora':
            config['pretrained_model_name_or_path'] = config.get('flux_model_path')
        elif model_train_type == 'sd-lora':
            config['pretrained_model_name_or_path'] = config.get('sd_model_path')
            config['vae'] = config.get('sd_vae')
        elif model_train_type == 'sdxl-lora':
            config['pretrained_model_name_or_path'] = config.get('sdxl_model_path')
            config['vae'] = config.get('sdxl_vae')
        
        # 移除业务参数
        business_params = ['use_image_tags', 'max_image_tags', 'generate_preview','flux_model_path','sd_model_path','sdxl_model_path','sd_vae','sdxl_vae','remote_output_dir','repeat_num']
        
        for param in business_params:
            if param in config:
                config.pop(param)
                
        return config
    
    @staticmethod
    def _process_training(task_id: int, asset_id: int):
        """处理训练任务"""
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                asset = db.query(Asset).filter(Asset.id == asset_id).first()

                if not task or not asset:
                    raise ValueError("任务或资产不存在")
                
                # 更新任务状态，记录开始处理训练
                task.add_log(f'开始处理训练任务，使用资产: {asset.name}', db=db)

                # 准备训练执行历史记录和配置
                business_config = TrainingService._prepare_training_execution_history(task_id, db, asset)
                
                # 将业务配置转换为训练配置
                training_config = TrainingService._convert_training_config(business_config)
                
                # 获取训练请求头
                training_headers = ConfigService.get_asset_lora_headers(asset.id)
                
                # 创建训练处理器，直接传入资产对象
                handler = TrainRequestHandler(asset)
                
                # 记录请求准备信息
                task.add_log(f'准备发送训练请求: task_id={task_id}, asset_id={asset_id}, asset_ip={asset.ip}', db=db)
                
                try:
                    # 发送训练请求
                    logger.info(f"发送训练请求: task_id={task_id}, asset_id={asset_id}")
                    task_id_str = handler.train_request(training_config, training_headers)
                    
                    if not task_id_str:
                        task.add_log('没有获取到有效的训练任务ID', db=db)
                        raise ValueError("创建训练任务失败，未获取到任务ID")
                    
                    # 记录成功获取task_id
                    task.add_log(f'训练任务创建成功，task_id={task_id_str}', db=db)
                    
                    # 更新任务的prompt_id字段存储训练任务ID
                    task.prompt_id = task_id_str
                    db.commit()
                    
                    # 返回训练任务ID
                    return task_id_str
                    
                except Exception as req_error:
                    # 处理请求异常
                    error_detail = {
                        "message": str(req_error),
                        "type": type(req_error).__name__,
                        "traceback": str(traceback.format_exc())
                    }
                    error_json = json.dumps(error_detail, indent=2)
                    task.update_status(TaskStatus.ERROR, f'训练请求失败: {str(req_error)}', db=db)
                    task.add_log(error_json, db=db)
                    if task.training_asset:
                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                        db.commit()
                    raise ValueError(f"训练请求失败: {str(req_error)}")
                    
        except Exception as e:
            logger.error(f"训练任务 {task_id} 处理失败: {str(e)}", exc_info=True)
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status(TaskStatus.ERROR, f'训练处理失败: {str(e)}', db=db)
                    task.add_log(json.dumps({
                        "message": str(e),
                        "type": type(e).__name__,
                        "traceback": str(traceback.format_exc())
                    }, indent=2), db=db)
                    if task.training_asset:
                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                        db.commit()
            raise
            
    @staticmethod
    def _monitor_training_status(task_id: int, asset_id: int, training_task_id: str):
        """监控训练任务状态"""
        try:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                asset = db.query(Asset).filter(Asset.id == asset_id).first()

                if not task or not asset:
                    raise ValueError("任务或资产不存在")
                
                # 记录开始监控
                task.add_log(f'开始监控训练任务状态, training_task_id={training_task_id}', db=db)
                poll_interval = ConfigService.get_value('train_poll_interval', 30)
                error_count = 0
                max_error_retries = 10
                
                while True:
                    try:
                        # 在每次循环中使用新的数据库会话获取新的asset对象
                        with get_db() as status_db:
                            current_asset = status_db.query(Asset).filter(Asset.id == asset_id).first()
                            if not current_asset:
                                raise ValueError(f"资产ID {asset_id} 不存在")
                                
                            # 创建训练处理器，使用新获取的资产对象
                            handler = TrainRequestHandler(current_asset)
                            
                            # 获取训练状态
                            training_headers = ConfigService.get_asset_lora_headers(asset.id)
                            status = handler.check_status(training_task_id, training_headers)
                            logger.info(f"检查训练任务状态: {status}")
                        
                        # 判断任务状态
                        is_completed = False
                        is_success = False
                        
                        if status == "FINISHED":
                            is_completed = True
                            is_success = True
                        elif status in ["FAILED", "TERMINATED"]:
                            is_completed = True
                            is_success = False
                        elif status == "NOT_FOUND":
                            logger.warning("训练任务未找到，可能训练引擎已经重启")
                            is_completed = True
                            is_success = False
                        
                        with get_db() as complete_db:
                            task = complete_db.query(Task).filter(Task.id == task_id).first()
                            # 检查任务是否被取消
                            if task and task.status != TaskStatus.TRAINING:
                                logger.info("监听训练过程中任务被取消")
                                
                                # 更新执行历史记录状态为ERROR
                                if task.execution_history_id:
                                    execution_history = complete_db.query(TaskExecutionHistory).filter(
                                        TaskExecutionHistory.id == task.execution_history_id
                                    ).first()
                                    if execution_history:
                                        execution_history.status = 'ERROR'
                                        execution_history.end_time = datetime.now()
                                        execution_history.description += f"\n任务被取消于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                        complete_db.commit()
                                
                                break
                            
                            # 任务完成处理
                            if is_completed and task:
                                # 获取执行历史记录
                                execution_history = None
                                if task.execution_history_id:
                                    execution_history = complete_db.query(TaskExecutionHistory).filter(
                                        TaskExecutionHistory.id == task.execution_history_id
                                    ).first()
                                
                                if is_success:
                                    # 获取最新的asset对象，避免会话分离问题
                                    current_asset = complete_db.query(Asset).filter(Asset.id == asset_id).first()
                                    
                                    # 如果是非本地资产，需要下载训练结果
                                    if current_asset and not current_asset.is_local and execution_history.training_config and execution_history.training_config.get('output_dir'):
                                        task.add_log('训练完成，开始从远程服务器同步结果...', db=complete_db)
                                        
                                        # 创建SSH客户端工具
                                        ssh_client = create_ssh_client_from_asset(current_asset)
                                        
                                        # 使用SSH客户端下载远程输出目录到本地
                                        success, message, stats = ssh_client.download_directory(
                                            remote_path=execution_history.training_config['output_dir'],
                                            local_path=execution_history.training_output_path
                                        )
                                        
                                        if not success:
                                            task.add_log(f'同步结果失败: {message}', db=complete_db)
                                            task.update_status(TaskStatus.ERROR, f'同步训练结果失败: {message}', db=complete_db)
                                            break
                                        
                                        task.add_log(f'训练结果同步成功: {message}', db=complete_db)
                                    
                                    # 更新任务状态为完成
                                    task.update_status(TaskStatus.COMPLETED, '训练完成', db=complete_db)
                                    task.progress = 100
                                    task.add_log('训练任务成功完成', db=complete_db)
                                    
                                    # 记录输出文件路径
                                    output_dir = execution_history.training_output_path
                                    task.add_log(f'训练输出目录: {output_dir}', db=complete_db)
                                    
                                    # 获取训练结果
                                    from ...services.task_services.result_service import ResultService
                                    training_results = ResultService.get_training_results(task_id)
                                    
                                    # 获取训练loss数据
                                    try:
                                        loss_result = ResultService.get_training_loss_data(task_id)
                                        if loss_result and loss_result.get('success') and loss_result.get('series'):
                                            loss_data = {'series': loss_result.get('series')}
                                        else:
                                            loss_data = None
                                    except Exception as loss_err:
                                        logger.error(f"获取训练loss数据失败: {str(loss_err)}")
                                        loss_data = None
                                    
                                    # 如果有执行历史记录，更新其状态和结果
                                    if execution_history:
                                        execution_history.status = 'COMPLETED'
                                        execution_history.end_time = datetime.now()
                                        execution_history.training_results = training_results
                                        # 保存loss数据
                                        if loss_data:
                                            execution_history.loss_data = loss_data
                                        execution_history.description += f"\n训练成功完成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                        complete_db.commit()
                                else:
                                    # 处理训练失败情况
                                    task.update_status(
                                        TaskStatus.ERROR,
                                        f'训练失败，任务状态为: {status}',
                                        db=complete_db
                                    )
                                    
                                    # 更新执行历史记录状态
                                    if execution_history:
                                        execution_history.status = 'ERROR'
                                        execution_history.end_time = datetime.now()
                                        execution_history.description += f"\n训练失败于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {status}"
                                        complete_db.commit()
                            
                                # 更新资产任务计数
                                if task.training_asset:
                                    task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                                    complete_db.commit()
                                break
                    
                        # 重置错误计数
                        if error_count > 0:
                            logger.info(f"从错误状态恢复，重置错误计数器。之前错误次数: {error_count}")
                        error_count = 0
                    
                    except Exception as check_err:
                        # 处理检查状态时的错误
                        error_count += 1
                        
                        # 根据错误次数决定等待时间
                        wait_time = 5 if error_count <= max_error_retries // 2 else poll_interval
                        logger.error(f"检查训练状态时出错 ({error_count}/{max_error_retries}): {str(check_err)}, 将在{wait_time}秒后重试")
                        
                        with get_db() as err_db:
                            task = err_db.query(Task).filter(Task.id == task_id).first()
                            if task:
                                task.add_log(f'检查任务状态出错 ({error_count}/{max_error_retries}): {str(check_err)}', db=err_db)
                            
                            # 如果错误次数达到上限，停止监控
                            if error_count >= max_error_retries:
                                task = err_db.query(Task).filter(Task.id == task_id).first()
                                if task:
                                    task.update_status(
                                        TaskStatus.ERROR, 
                                        f'连续{max_error_retries}次检查状态失败，停止监控: {str(check_err)}', 
                                        db=err_db
                                    )
                                    if task.training_asset:
                                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                                        err_db.commit()
                                break
                        
                        # 等待一段时间后重试
                        time.sleep(wait_time)
                        continue
                
                    # 正常轮询间隔
                    time.sleep(poll_interval)

        except Exception as e:
            # 处理整体监控异常
            logger.error(f"监控训练任务状态失败: {str(e)}")
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.update_status(TaskStatus.ERROR, f'监控失败: {str(e)}', db=db)
                    task.add_log(json.dumps({
                        "message": str(e),
                        "type": type(e).__name__,
                        "traceback": str(traceback.format_exc())
                    }, indent=2), db=db)
                    if task.training_asset:
                        task.training_asset.training_tasks_count = max(0, task.training_asset.training_tasks_count - 1)
                        db.commit() 