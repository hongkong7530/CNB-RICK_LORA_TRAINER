import json
import requests
import os
import uuid
from typing import Tuple, Dict, Optional, Any, List
from ..utils.logger import setup_logger
from dataclasses import dataclass, field

logger = setup_logger('train_handler')

class TrainRequestHandler:
    def __init__(self, asset=None):
        """
        初始化训练处理器
        :param asset: 资产对象，如果提供则从资产获取连接信息
        :param asset_ip: 资产IP地址，如果同时提供asset和asset_ip，优先使用asset_ip
        :param training_port: 训练端口，如果同时提供asset和training_port，优先使用training_port
        """
        self.asset_ip = f'http://{asset.ip}'
        self.training_port = asset.lora_training.get('port')
        if asset.port_access_mode == 'DOMAIN':
            # 域名访问模式
            from ..utils.common import generate_domain_url
            domain_url,port = generate_domain_url(asset.ip, self.training_port)
            # 使用域名格式访问，端口设置为80
            self.asset_ip = domain_url
            self.training_port = port
        
        self.api_base_url = f"{self.asset_ip}:{self.training_port}/api"

    def train_request(self, train_config: Dict[str, Any],train_headers: Optional[Dict[str, Any]] = None) -> str:
        """
        发送训练请求
        :param train_config: 训练配置参数
        :return: 训练任务ID
        """
        # 构建请求
        url = f"{self.api_base_url}/run"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        if train_headers:
            headers.update(train_headers)
        
        logger.debug(f"发送训练请求到 {url}")
        
        # 发送请求
        response = requests.post(url, json=train_config, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # 检查响应
        if data.get('status') != 'success':
            error_msg = data.get('message', '未知错误')
            raise ValueError(f"训练请求失败: {error_msg}")
        
        # 提取训练任务ID
        message = data.get('message', '')
        task_id = None
        
        # 尝试从消息中提取ID
        if 'ID:' in message:
            task_id = message.split('ID:')[-1].strip()
        
        if not task_id:
            # 如果没有找到ID，使用UUID作为备用
            task_id = str(uuid.uuid4())
            logger.warning(f"未能从响应中提取训练ID，使用生成的UUID: {task_id}")
            
        logger.info(f"训练请求发送成功，task_id: {task_id}")
        return task_id

    def check_status(self, task_id: str, train_headers: Optional[Dict[str, Any]] = None) -> Tuple[bool, bool, Dict[str, Any]]:
        """
        检查训练任务状态
        :param task_id: 任务ID
        :param train_config: 可选的训练配置参数
        :return: (is_completed, is_success, status_message)
        """
        try:
            # 获取所有任务列表
            tasks_data = self.get_tasks(train_headers)
            
            # 从任务列表中查找指定任务
            task_info = None
            for task in tasks_data:
                if task.get('id') == task_id:
                    task_info = task
                    break
                    
            # 如果没有找到任务，返回处理中状态
            if not task_info:
                return "NOT_FOUND"
                
            # 提取任务状态信息
            task_status = task_info.get('status', '')
            # 根据状态判断任务是否完成
            return task_status
                
        except Exception as e:
            logger.error(f"检查任务状态出错: {str(e)}", exc_info=True)
            # 返回处理中状态，允许后续重试
            raise e
        
    def cancel_training(self, task_id: str, train_headers: Optional[Dict[str,any]] = None) -> bool:
        """
        取消训练任务
        :param task_id: 任务ID
        :param train_config: 可选的训练配置参数
        :return: 是否成功取消
        """
        url = f"{self.api_base_url}/tasks/terminate/{task_id}"
        logger.debug(f"取消训练任务: {url}")
        
        headers = {}
        if train_headers:
            headers.update(train_headers)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'success':
            logger.info(f"成功取消训练任务: {task_id}")
            return True
        else:
            logger.warning(f"取消训练任务失败: {data.get('message', '未知错误')}")
            return False
        
    def get_all_training_logs(self) -> List[str]:
        """
        获取所有训练日志key
        :return: 所有训练日志key的列表
        """
        url = f"{self.asset_ip}:{self.training_port}/proxy/tensorboard/data/runs"
        logger.debug(f"获取所有训练日志key: {url}")
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'X-TensorBoard-Feature-Flags': '{"enabledColorGroup":true,"enabledColorGroupByRegex":true,"enabledExperimentalPlugins":[],"enabledLinkedTime":false,"enabledCardWidthSetting":true,"enabledScalarDataTable":false,"forceSvg":false,"enableDarkModeOverride":null,"defaultEnableDarkMode":false,"isAutoDarkModeAllowed":true,"inColab":false,"metricsImageSupportEnabled":true,"enableTimeSeriesPromotion":false}'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"获取到所有训练日志key: {data}")
        
        return data
        
    def get_training_loss_data(self, task_id: str) -> Dict:
        """
        获取训练loss曲线数据
        :param task_id: 训练任务ID
        :return: loss曲线数据
        """
        # 先获取所有训练日志key
        all_logs = self.get_all_training_logs()
        if not all_logs:
            raise ValueError("无法获取训练日志列表")
            
        # 匹配当前任务ID对应的key
        matched_key = None
        for key in all_logs:
            # 检查key是否包含任务ID
            if task_id in key:
                matched_key = key
                logger.info(f"找到匹配的训练日志key: {matched_key}")
                break
                
        if not matched_key:
            raise ValueError(f"未找到与任务ID {task_id} 匹配的训练日志key")
            
        # 使用匹配到的key获取loss数据
        url = f"{self.asset_ip}:{self.training_port}/proxy/tensorboard/experiment/defaultExperimentId/data/plugin/timeseries/timeSeries"
        logger.debug(f"获取训练loss曲线数据: {url}")
        
        # 构建正确的multipart/form-data请求
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'X-XSRF-Protected': '1'
        }
        
        # 使用正确的请求参数格式，使用匹配到的key
        files = {
            'requests': (None, json.dumps([{"plugin":"scalars","tag":"loss/average","run":matched_key}]))
        }
        
        response = requests.post(url, files=files, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"获取到训练loss曲线数据: {data}")
        
        return data

    def get_tasks(self, train_headers: Optional[Dict[str, Any]] = None) -> Dict:
        """
        获取所有训练任务列表
        :param train_config: 可选的训练配置参数
        :return: 任务列表数据
        """
        url = f"{self.api_base_url}/tasks"
        logger.debug(f"获取训练任务列表: {url}")
        
        headers = {}
        if train_headers:
            headers.update(train_headers)
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查响应是否有效
            if data.get('status') != 'success' or 'data' not in data:
                logger.warning(f"训练任务列表响应格式无效: {data}")
                raise ValueError("训练任务列表响应格式无效")
            
            # 标准化返回格式
            return data.get('data', {}).get('tasks', [])
        except Exception as e:
            raise ValueError(f"获取训练任务列表失败: {str(e)}") 