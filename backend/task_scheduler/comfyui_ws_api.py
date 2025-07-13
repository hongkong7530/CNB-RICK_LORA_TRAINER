import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable, Union

from websocket import WebSocketApp

from comfyui_api import ComfyUIConfig

# 配置日志，使用已有的日志配置
logger = logging.getLogger('ComfyUIWebSocketAPI')

@dataclass
class WebSocketCallbacks:
    """WebSocket回调函数集合"""
    on_connecting: Optional[Callable[[], None]] = None
    on_connected: Optional[Callable[[], None]] = None
    on_disconnected: Optional[Callable[[], None]] = None
    on_error: Optional[Callable[[str], None]] = None
    on_executing: Optional[Callable[[Dict], None]] = None
    on_executed: Optional[Callable[[Dict], None]] = None
    on_execution_start: Optional[Callable[[Dict], None]] = None
    on_execution_cached: Optional[Callable[[Dict], None]] = None
    on_progress: Optional[Callable[[Dict], None]] = None
    on_status: Optional[Callable[[Dict], None]] = None
    on_execution_error: Optional[Callable[[Dict], None]] = None
    on_custom_message: Optional[Callable[[Dict], None]] = None

class ComfyUIWebSocketAPI:
    """ComfyUI WebSocket API 客户端"""
    
    def __init__(self, config: ComfyUIConfig, callbacks: Optional[WebSocketCallbacks] = None):
        """
        初始化WebSocket客户端
        
        Args:
            config: ComfyUI配置
            callbacks: 回调函数集合
        """
        self.config = config
        self.callbacks = callbacks or WebSocketCallbacks()
        self.ws = None
        self.ws_thread = None
        self.is_connected = False
        self.is_running = False
        self.current_prompt_id = None
        
    def connect(self) -> None:
        """建立WebSocket连接"""
        if self.is_connected:
            logger.warning("WebSocket已连接，无需重复连接")
            return
            
        ws_url = f"ws://{self.config.host.replace('http://', '')}:{self.config.port}/ws?clientId={self.config.client_id}"
        logger.info(f"正在连接WebSocket: {ws_url}")
        
        if self.callbacks.on_connecting:
            self.callbacks.on_connecting()
            
        self.ws = WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        self.is_running = True
        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()
        
    def disconnect(self) -> None:
        """断开WebSocket连接"""
        if not self.is_connected:
            logger.warning("WebSocket未连接，无需断开")
            return
            
        logger.info("正在断开WebSocket连接")
        self.is_running = False
        
        if self.ws:
            self.ws.close()
            self.ws = None
            
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=1)
            
        self.is_connected = False
        logger.info("WebSocket连接已断开")
        
    def _run_websocket(self) -> None:
        """在后台线程中运行WebSocket连接"""
        retry_count = 0
        max_retries = 5
        
        while self.is_running and retry_count < max_retries:
            try:
                self.ws.run_forever()
                
                if not self.is_running:
                    break
                    
                retry_count += 1
                wait_time = min(30, 2 ** retry_count)  # 指数退避策略
                logger.warning(f"WebSocket连接断开，{wait_time}秒后重试 ({retry_count}/{max_retries})")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"WebSocket运行异常: {str(e)}")
                retry_count += 1
                time.sleep(5)
                
        if retry_count >= max_retries:
            logger.error(f"WebSocket连接重试次数超过限制 ({max_retries})，停止重试")
            
    def _on_open(self, ws) -> None:
        """WebSocket连接打开回调"""
        self.is_connected = True
        logger.info("WebSocket连接已建立")
        
        if self.callbacks.on_connected:
            self.callbacks.on_connected()
            
    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """WebSocket连接关闭回调"""
        self.is_connected = False
        logger.info(f"WebSocket连接已关闭: 状态码={close_status_code}, 消息={close_msg}")
        
        if self.callbacks.on_disconnected:
            self.callbacks.on_disconnected()
            
    def _on_error(self, ws, error) -> None:
        """WebSocket错误回调"""
        logger.error(f"WebSocket错误: {str(error)}")
        
        if self.callbacks.on_error:
            self.callbacks.on_error(str(error))
            
    def _on_message(self, ws, message) -> None:
        """WebSocket消息回调"""
        try:
            # 检查消息类型，如果是二进制数据则跳过JSON解析
            if isinstance(message, bytes):
                logger.debug("收到二进制WebSocket消息，跳过处理")
                return
                
            data = json.loads(message)
            msg_type = data.get("type", "")
            
            # logger.debug(f"收到WebSocket消息: {msg_type}")
            # logger.info(f"消息内容: {json.dumps(data, ensure_ascii=False)}")
            
            # 根据消息类型调用对应的回调函数
            if msg_type == "executing":
                # 任务开始执行
                self.current_prompt_id = data.get("data", {}).get("prompt_id")
                logger.info(f"开始执行任务: {self.current_prompt_id}")
                if self.callbacks.on_executing:
                    self.callbacks.on_executing(data.get("data", {}))
                    
            elif msg_type == "executed":
                # 任务执行完成
                logger.info(f"任务执行完成: {self.current_prompt_id}")
                if self.callbacks.on_executed:
                    self.callbacks.on_executed(data.get("data", {}))
                    
            elif msg_type == "execution_start":
                # 开始执行工作流
                logger.info("开始执行工作流")
                if self.callbacks.on_execution_start:
                    self.callbacks.on_execution_start(data.get("data", {}))
                    
            elif msg_type == "execution_cached":
                # 使用缓存的执行结果
                logger.info("使用缓存执行结果")
                if self.callbacks.on_execution_cached:
                    self.callbacks.on_execution_cached(data.get("data", {}))
                    
            elif msg_type == "progress":
                logger.info(f"进度: {json.dumps(data, ensure_ascii=False)}")
                # 执行进度更新
                if self.callbacks.on_progress:
                    self.callbacks.on_progress(data.get("data", {}))
                    
            elif msg_type == "status":
                # 状态更新
                if self.callbacks.on_status:
                    self.callbacks.on_status(data.get("data", {}))
                    
            elif msg_type == "execution_error":
                # 执行错误
                logger.error(f"任务执行错误: {json.dumps(data.get('data', {}), ensure_ascii=False)}")
                if self.callbacks.on_execution_error:
                    self.callbacks.on_execution_error(data.get("data", {}))
            elif msg_type == "crystools.monitor":
                # 监控信息
                # logger.info(f"监控信息: {json.dumps(data.get('data', {}), ensure_ascii=False)}")
                pass
            else:
                # 其他自定义消息
                if self.callbacks.on_custom_message:
                    self.callbacks.on_custom_message(data)
                    
        except json.JSONDecodeError:
            logger.warning(f"无法解析WebSocket消息为JSON: {message[:100]}...")
        except Exception as e:
            logger.error(f"处理WebSocket消息异常: {str(e)}")
            
    def wait_for_execution(self, prompt_id: str, timeout: int = 300) -> bool:
        """
        等待特定任务执行完成
        
        Args:
            prompt_id: 任务ID
            timeout: 超时时间(秒)
            
        Returns:
            是否成功执行完成
        """
        if not self.is_connected:
            logger.error("WebSocket未连接，无法等待任务执行")
            return False
            
        self.current_prompt_id = prompt_id
        logger.info(f"等待任务执行完成: {prompt_id}, 超时时间: {timeout}秒")
        
        # 创建事件用于同步
        execution_completed = threading.Event()
        execution_failed = threading.Event()
        
        # 临时回调函数
        def on_executed(data):
            if data.get("prompt_id") == prompt_id:
                execution_completed.set()
                
        def on_execution_error(data):
            if data.get("prompt_id") == prompt_id:
                execution_failed.set()
                
        # 保存原回调函数
        original_executed_callback = self.callbacks.on_executed
        original_error_callback = self.callbacks.on_execution_error
        
        # 设置临时回调函数
        self.callbacks.on_executed = on_executed
        self.callbacks.on_execution_error = on_execution_error
        
        try:
            # 等待任务执行完成或失败
            completed = execution_completed.wait(timeout=timeout)
            failed = execution_failed.wait(timeout=0)  # 立即检查是否失败
            
            if failed:
                logger.error(f"任务执行失败: {prompt_id}")
                return False
            elif not completed:
                logger.error(f"等待任务执行超时: {prompt_id}")
                return False
            else:
                logger.info(f"任务执行成功完成: {prompt_id}")
                return True
                
        finally:
            # 恢复原回调函数
            self.callbacks.on_executed = original_executed_callback
            self.callbacks.on_execution_error = original_error_callback

# 使用示例
def example_usage():
    """WebSocket API使用示例"""
    config = ComfyUIConfig(host="http://127.0.0.1", port=8188)
    
    # 定义回调函数
    def on_connected():
        logger.info("已连接到ComfyUI WebSocket服务器")
        
    def on_progress(data):
        value = data.get("value", 0)
        max_value = data.get("max", 100)
        progress = (value / max_value) * 100 if max_value > 0 else 0
        print(f"生成进度: {progress:.2f}%")
        
    def on_executed(data):
        print(f"任务执行完成: {data.get('prompt_id')}")
        print(f"输出节点: {data.get('output', {}).keys()}")
        
    callbacks = WebSocketCallbacks(
        on_connected=on_connected,
        on_progress=on_progress,
        on_executed=on_executed
    )
    
    ws_api = ComfyUIWebSocketAPI(config, callbacks)
    
    try:
        # 连接WebSocket
        ws_api.connect()
        
        # 等待连接建立
        time.sleep(2)
        
        # 等待用户操作
        print("按Enter键退出...")
        input()
        
    finally:
        # 断开连接
        ws_api.disconnect()

if __name__ == "__main__":
    example_usage() 