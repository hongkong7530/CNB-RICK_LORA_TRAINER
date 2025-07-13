import json
import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Any, Callable, List
from enum import Enum
import os

from comfyui_api import ComfyUIAPI, ComfyUIConfig
from comfyui_ws_api import ComfyUIWebSocketAPI, WebSocketCallbacks
from comfyui_error_parser import ComfyUIErrorParser
from comfyui_precheck import ComfyUIPreCheck

# 配置日志，使用已有的日志配置
logger = logging.getLogger('TaskScheduler')

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"       # 执行失败
    INTERRUPTED = "interrupted"  # 被中断

@dataclass
class Task:
    """任务数据类"""
    task_id: str
    prompt: Dict
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: float = time.time()
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    prompt_id: Optional[str] = None

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, config: ComfyUIConfig,enable_precheck=False):
        """
        初始化任务调度器
        
        Args:
            config: ComfyUI配置
        """
        self.config = config
        self.http_api = ComfyUIAPI(config)
        self.ws_api = None
        self.task_queue = queue.Queue()
        self.tasks: Dict[str, Task] = {}
        self.current_task: Optional[Task] = None
        self.is_running = False
        self.worker_thread = None
        self.error_parser = ComfyUIErrorParser()

        self.precheck_enabled = enable_precheck
        if self.precheck_enabled:
            self.init_precheck()
        
        # 确保输出目录存在
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # 创建WebSocket回调
        callbacks = WebSocketCallbacks(
            on_connected=self._on_ws_connected,
            on_executing=self._on_ws_executing,
            on_executed=self._on_ws_executed,
            on_execution_error=self._on_ws_error,
            on_progress=self._on_ws_progress
        )
        self.ws_api = ComfyUIWebSocketAPI(config, callbacks)

    def init_precheck(self) -> None:
        logger.info("正在初始化预检测，缓存系统信息...")
        # 创建预检测实例
        self.precheck = ComfyUIPreCheck(self.http_api)
        self.precheck.pre_cache()
            
            
    
    def start(self) -> None:
        """启动任务调度器"""
        if self.is_running:
            logger.warning("任务调度器已在运行中")
            return
            
        logger.info("启动任务调度器")
        self.is_running = True
        
        # 启动WebSocket连接
        self.ws_api.connect()
        
        # 启动工作线程
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
    def stop(self) -> None:
        """停止任务调度器"""
        if not self.is_running:
            logger.warning("任务调度器未运行")
            return
            
        logger.info("停止任务调度器")
        self.is_running = False
        
        # 中断当前任务
        if self.current_task:
            self.interrupt_task(self.current_task.task_id)
            
        # 等待工作线程结束
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
            
        # 断开WebSocket连接
        self.ws_api.disconnect()
        
    def submit_task(self, prompt: Dict) -> str:
        """
        提交新任务
        
        Args:
            prompt: 任务提示词
            
        Returns:
            任务ID
        """
        task_id = f"task_{int(time.time())}_{len(self.tasks)}"
        task = Task(task_id=task_id, prompt=prompt)
        self.tasks[task_id] = task
        
        logger.info(f"提交新任务: {task_id}")
        self.task_queue.put(task)
        
        return task_id
        
    def interrupt_task(self, task_id: str) -> bool:
        """
        中断指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功中断
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return False
            
        if task.status != TaskStatus.RUNNING:
            logger.warning(f"任务未在运行中: {task_id}")
            return False
            
        logger.info(f"中断任务: {task_id}")
        try:
            self.http_api.interrupt()
            task.status = TaskStatus.INTERRUPTED
            task.completed_at = time.time()
            return True
        except Exception as e:
            logger.error(f"中断任务失败: {str(e)}")
            return False
            
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象
        """
        return self.tasks.get(task_id)
        
    def get_all_tasks(self) -> List[Task]:
        """
        获取所有任务
        
        Returns:
            任务列表
        """
        return list(self.tasks.values())
        
    def _worker_loop(self) -> None:
        """工作线程循环"""
        while self.is_running:
            try:
                # 如果WebSocket未连接，则跳过任务
                if not self.ws_api.is_connected:
                    continue
                # 从队列获取任务
                task = self.task_queue.get(timeout=1)
                
                # 执行任务
                self._execute_task(task)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"工作线程异常: {str(e)}")
                
    def _execute_task(self, task: Task) -> None:
        """
        执行任务
        
        Args:
            task: 任务对象
        """
        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            self.current_task = task
            
            logger.info(f"开始执行任务: {task.task_id}")
            
            # 提交任务到ComfyUI
            if self.precheck_enabled:
                # 使用预检测结果
                precheck_result = self.precheck.validate_workflow(task.prompt,True)
                if precheck_result.get("valid", False):
                    response = self.http_api.submit_prompt(task.prompt)
                else:
                    # 显示验证结果
                    print(f"工作流有效: {precheck_result['valid']}")
                    print(f"问题数量: {precheck_result['issues_count']}")
                    
                    if precheck_result["structure_issues"]:
                        print("\n结构问题:")
                        for issue in precheck_result["structure_issues"]:
                            print(f"- {issue['message']}")
                    
                    if precheck_result["parameter_issues"]:
                        print("\n参数问题:")
                        for issue in precheck_result["parameter_issues"]:
                            print(f"- {issue['message']}")
                    
                    if precheck_result["model_issues"]:
                        print("\n模型问题:")
                        for issue in precheck_result["model_issues"]:
                            print(f"- {issue['message']}")

                    task.status = TaskStatus.FAILED
                    task.error = ("工作流验证无效", None)
                    return
            else:
                response = self.http_api.submit_prompt(task.prompt)
            task.prompt_id = response.get("prompt_id")
            
            # 等待任务完成
            if not self.ws_api.wait_for_execution(task.prompt_id):
                # 获取任务结果
                history = self.http_api.get_history_by_id(task.prompt_id)
                # 检查任务是否执行成功
                has_error, error_message, detailed_error = self.error_parser.process_history_error(history, task.prompt)
                if has_error:
                    logger.error(f"任务执行失败: {error_message}")
                    if detailed_error:
                        logger.debug(f"详细错误信息:\n{detailed_error}")

                task.result = history.get("outputs", {})
                task.status = TaskStatus.FAILED
                task.error = (error_message, detailed_error)
                return
                
            # 获取任务结果
            history = self.http_api.get_history_by_id(task.prompt_id)
            task.result = history.get("outputs", {})
            task.status = TaskStatus.COMPLETED
            
            # 异步处理图像，避免阻塞主任务流程
            threading.Thread(
                target=self.http_api.process_successful_generation,
                args=(task.prompt_id, history, self.config.output_dir),
                daemon=True
            ).start()

        except Exception as e:
            logger.error(f"执行任务异常: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error = (self.error_parser.process_error(str(e),task.prompt),None)
            
        finally:
            task.completed_at = time.time()
            self.current_task = None
            
    def _on_ws_connected(self) -> None:
        """WebSocket连接建立回调"""
        logger.info("WebSocket连接已建立")
        
    def _on_ws_executing(self, data: Dict) -> None:
        """任务开始执行回调"""
        if self.current_task:
            logger.info(f"任务开始执行: {self.current_task.task_id}")
            
    def _on_ws_executed(self, data: Dict) -> None:
        """任务执行完成回调"""
        if self.current_task:
            logger.info(f"任务执行完成: {self.current_task.task_id}")
            
    def _on_ws_error(self, data: Dict) -> None:
        """任务执行错误回调"""
        if self.current_task:
            logger.error(f"任务执行错误: {self.current_task.task_id}")
            
    def _on_ws_progress(self, data: Dict) -> None:
        """任务进度更新回调"""
        if self.current_task:
            value = data.get("value", 0)
            max_value = data.get("max", 100)
            progress = (value / max_value) * 100 if max_value > 0 else 0
            logger.debug(f"任务进度: {progress:.2f}%")

# 使用示例
def example_usage():
    """任务调度器使用示例"""
    config = ComfyUIConfig(host="http://127.0.0.1", port=8188)
    
    # 创建任务调度器
    scheduler = TaskScheduler(config,True)
    
    try:
        # 启动调度器
        scheduler.start()
        
        # 读取工作流文件作为prompt
        workflow_path = os.path.join("workflows", "default.json")
        if not os.path.exists(workflow_path):
            raise FileNotFoundError(f"工作流文件不存在: {workflow_path}")
            
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                prompt = json.load(f)
            logger.info(f"已加载工作流: {workflow_path}")
        except Exception as e:
            logger.error(f"加载工作流失败: {str(e)}")
            raise
        
        task_id = scheduler.submit_task(prompt)
        print(f"提交任务: {task_id}")
        
        # 等待任务完成
        while True:
            task = scheduler.get_task_status(task_id)
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.INTERRUPTED]:
                print(f"任务状态: {task.status.value}")
                if task.result:
                    print(f"任务结果: {task.result}")
                if task.error:
                    print(f"任务错误: {task.error}")
                break
            time.sleep(1)
            
        # 等待用户操作
        print("按Enter键退出...")
        input()
        
    finally:
        # 停止调度器
        scheduler.stop()

if __name__ == "__main__":
    example_usage() 