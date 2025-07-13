import json
import os
import random
from typing import Tuple, Dict, Optional, Any
from ..utils.logger import setup_logger
from ..config import Config
from dataclasses import dataclass
from task_scheduler.comfyui_api import ComfyUIAPI, ComfyUIConfig

logger = setup_logger('mark_handler')

@dataclass
class MarkConfig:
    """标记配置参数类"""
    input_folder: str
    output_folder: str
    auto_crop: bool = True
    resolution: int = 1024
    default_crop_ratio: str = '1:1'
    max_tokens: int = 300
    min_confidence: float = 0.6
    trigger_words: str = ''
    mark_algorithm: str = 'wd-v1-4-convnext-tagger-v2'

class MarkRequestHandler:
    def __init__(self, asset=None):
        """
        初始化标记处理器
        :param asset: 资产对象，如果不提供则使用本地地址127.0.0.1:8188
        """
        self.asset_ip = f'http://{asset.ip}'
        self.mark_port = asset.ai_engine.get('port', 8188)
        
        if asset.port_access_mode == 'DOMAIN':
            # 域名访问模式
            from ..utils.common import generate_domain_url
            domain_url,port = generate_domain_url(asset.ip, self.mark_port)
            # 使用域名格式访问，端口设置为80
            self.asset_ip = domain_url
            self.mark_port = port
            
        # 创建ComfyUIConfig和ComfyUIAPI实例
        self.comfy_config = ComfyUIConfig(
            host=self.asset_ip,
            port=self.mark_port,
            client_id="lora_tool"
        )
        self.api = ComfyUIAPI(self.comfy_config)

    def load_workflow_api(self, algorithm: str) -> Dict:
        """
        加载标记工作流配置
        
        Args:
            algorithm: 打标算法名称
        
        Returns:
            工作流配置字典
        """
        try:
            # 根据算法选择工作流文件
            if algorithm == 'joycaption2':
                workflow_file = os.path.join(Config.DATA_DIR, 'workflow', 'mark_workflow_api_joycaption2.json')
            else:
                # 所有WD系列算法使用相同的工作流文件
                workflow_file = os.path.join(Config.DATA_DIR, 'workflow', 'mark_workflow_api_wd.json')
            
            # 如果文件不存在，使用默认工作流
            if not os.path.exists(workflow_file):
                logger.warning(f"工作流文件 {workflow_file} 不存在，使用默认工作流")
                workflow_file = os.path.join(Config.DATA_DIR, 'workflow', 'mark_workflow_api_list.json')
                
            with open(workflow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载工作流配置失败: {str(e)}")
            return {}
            
    def mark_request(self, mark_config: MarkConfig) -> str:
        """
        发送标记请求
        :param mark_config: 标记配置参数
        :return: prompt_id
        :raises: ValueError 如果请求失败或返回无效数据
        """
        try:
            # 获取打标算法
            algorithm = mark_config.mark_algorithm
            
            # 更新工作流配置
            workflow = self.load_workflow_api(algorithm)
            
            # 设置基本参数
            workflow["209"]["inputs"]["boolean"] = mark_config.auto_crop
            workflow["35"]["inputs"]["aspect_ratio"] = mark_config.default_crop_ratio
            workflow["35"]["inputs"]["scale_to_length"] = mark_config.resolution
            workflow["208"]["inputs"]["string"] = mark_config.input_folder
            workflow["155"]["inputs"]["string"] = mark_config.output_folder
            workflow["210"]["inputs"]["string"] = mark_config.trigger_words
            
            # 如果是WD系列算法，设置模型名称
            if algorithm != 'joycaption2' and "220" in workflow:
                workflow["220"]["inputs"]["threshold"] = mark_config.min_confidence
                workflow["220"]["inputs"]["model"] = algorithm
            
            # 保存修改后的工作流配置
            workflow_new_file = os.path.join(Config.DATA_DIR, 'workflow', 'mark_workflow_api_new.json')
            with open(workflow_new_file, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, ensure_ascii=False, indent=4)

            logger.debug(f"发送标记请求到 http://{self.asset_ip}:{self.mark_port}，使用算法: {algorithm}")
            
            # 使用ComfyUIAPI提交任务
            response = self.api.submit_prompt(workflow)
            
            prompt_id = response.get("prompt_id")
            
            if not prompt_id:
                raise ValueError("API返回成功但未获取到prompt_id")
                
            logger.info(f"标记请求发送成功，prompt_id: {prompt_id}，使用算法: {algorithm}")
            return prompt_id

        except Exception as e:
            logger.error(f"发送标记请求失败: {str(e)}", exc_info=True)
            
            # 构建结构化错误信息
            error_info = {
                "message": str(e),
                "type": type(e).__name__
            }
            
            raise ValueError(json.dumps(error_info))
            
    def check_status(self, prompt_id: str, mark_config: MarkConfig) -> Tuple[bool, bool, Dict[str, Any]]:
        """
        检查标记任务状态
        :param prompt_id: 任务ID
        :param mark_config: 标记配置参数
        :return: (is_completed, is_success, task_info)
        """
        try:
            # 使用ComfyUIAPI获取任务历史
            history_data = self.api.get_history_by_id(prompt_id)
            
            # 检查响应是否为空
            if not history_data or not isinstance(history_data, dict) or prompt_id not in history_data:
                logger.debug(f"任务 {prompt_id} 执行中...")
                return False, False, {"status": "processing", "progress": 0}
    
            # 获取任务状态
            task_info = history_data.get(prompt_id, {}).get("status", {})
            status = task_info.get("status_str")
    
            # 提取错误信息
            error_info = self._extract_error_info(task_info)
    
            result_info = {
                "status": status,
                "progress": task_info.get("progress", 0),
                "execution_time": task_info.get("exec_time", 0),
                "error_info": error_info
            }
    
            if status == "success":
                logger.info(f"任务 {prompt_id} 完成")
                return True, True, result_info
            elif status == "error":
                error_msg = error_info.get("error_message", "未知错误")
                logger.error(f"任务 {prompt_id} 失败: {error_msg}")
                return True, False, result_info
            else:
                logger.debug(f"任务 {prompt_id} 状态: {status}, 进度: {result_info['progress']}%")
                return False, False, result_info
                
        except Exception as e:
            logger.error(f"检查任务状态出错: {str(e)}", exc_info=True)
            # 返回处理中状态，允许后续重试
            return False, False, {"status": "error_checking", "error": str(e), "progress": 0}
            
    def _extract_error_info(self, task_info: Dict) -> Dict:
        """从任务状态中提取错误信息"""
        error_info = {}
        
        if task_info.get("status_str") == "error":
            messages = task_info.get("messages", [])
            for msg in messages:
                if msg[0] == "execution_error":
                    error_data = msg[1]
                    error_info = {
                        "node_id": error_data.get("node_id"),
                        "node_type": error_data.get("node_type"),
                        "error_type": error_data.get("exception_type"),
                        "error_message": error_data.get("exception_message"),
                        "traceback": error_data.get("traceback"),
                        "inputs": error_data.get("current_inputs")
                    }
                    break
                    
        return error_info
        
    def interrupt(self) -> bool:
        """
        中断正在进行的标记任务
        
        Returns:
            操作是否成功
        """
        try:
            result = self.api.interrupt()
            return result.get("success", False)
        except Exception as e:
            logger.error(f"中断任务失败: {str(e)}")
            return False
            
    def get_marking_progress_data(self, prompt_id: str = None) -> Dict:
        """
        获取标记进度数据，包括队列状态和系统信息
        :param prompt_id: 可选的任务ID，用于获取特定任务的进度
        :return: 进度数据字典
        """
        try:
            progress_data = {
                "progress": {
                    "submitted_count": 0,
                    "processing_count": 0,
                    "completed_count": 0,
                    "current_task_id": None,
                    "total_images": 0,
                    "percentage": 0
                },
                "system_stats": {},
                "timeline": []
            }
            
            # 获取队列状态
            queue_data = self.api.get_queue()
            if queue_data:
                queue_running = queue_data.get('queue_running', [])
                queue_pending = queue_data.get('queue_pending', [])
                
                progress_data["progress"]["processing_count"] = len(queue_running)
                progress_data["progress"]["submitted_count"] = len(queue_pending)
                
                # 如果有正在运行的任务，获取当前任务ID
                if queue_running:
                    current_task = queue_running[0]
                    if len(current_task) > 0:
                        progress_data["progress"]["current_task_id"] = current_task[0]
            
            # 获取系统状态
            system_stats = self.get_system_stats()
            if system_stats:
                progress_data["system_stats"] = system_stats
            
            # 如果提供了prompt_id，获取具体任务的进度
            if prompt_id:
                history_data = self.api.get_history_by_id(prompt_id)
                if history_data and prompt_id in history_data:
                    task_info = history_data[prompt_id].get("status", {})
                    if task_info.get("status_str") == "success":
                        progress_data["progress"]["completed_count"] = 1
                        progress_data["progress"]["percentage"] = 100
                    elif task_info.get("status_str") == "error":
                        progress_data["progress"]["percentage"] = 0
                    else:
                        # 任务进行中
                        progress_data["progress"]["percentage"] = task_info.get("progress", 0)
            
            return progress_data
            
        except Exception as e:
            logger.error(f"获取标记进度数据失败: {str(e)}")
            return {
                "progress": {
                    "submitted_count": 0,
                    "processing_count": 0,
                    "completed_count": 0,
                    "current_task_id": None,
                    "total_images": 0,
                    "percentage": 0
                },
                "system_stats": {},
                "timeline": [],
                "error": str(e)
            }
    
    def get_system_stats(self) -> Dict:
        """
        获取ComfyUI系统状态信息
        :return: 系统状态字典
        """
        try:
            # 使用ComfyUI API获取系统状态
            stats_data = self.api.get_system_stats()
            
            if not stats_data:
                return {}
            
            system_info = stats_data.get('system', {})
            devices = stats_data.get('devices', [])
            
            result = {
                "cpu_usage": 0,
                "ram_usage": 0,
                "ram_used_gb": 0,
                "ram_total_gb": 0
            }
            
            # 处理内存信息
            ram_total = system_info.get('ram_total', 0)
            ram_free = system_info.get('ram_free', 0)
            if ram_total > 0:
                ram_used = ram_total - ram_free
                result["ram_usage"] = round((ram_used / ram_total) * 100, 1)
                result["ram_used_gb"] = round(ram_used / (1024**3), 1)
                result["ram_total_gb"] = round(ram_total / (1024**3), 1)
            
            # 处理GPU信息
            if devices:
                gpu_device = devices[0]  # 取第一个GPU设备
                vram_total = gpu_device.get('vram_total', 0)
                vram_free = gpu_device.get('vram_free', 0)
                
                if vram_total > 0:
                    vram_used = vram_total - vram_free
                    result["gpu_usage"] = round((vram_used / vram_total) * 100, 1)
                    result["gpu_memory_used"] = round(vram_used / (1024**3), 1)
                    result["gpu_memory_total"] = round(vram_total / (1024**3), 1)
                    result["gpu_temperature"] = gpu_device.get('gpu_temperature', 0)
                    result["gpu_utilization"] = gpu_device.get('gpu_utilization', 0)
            
            return result
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {}