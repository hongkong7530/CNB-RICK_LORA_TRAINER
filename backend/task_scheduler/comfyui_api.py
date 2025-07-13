import requests
import json
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path
import uuid
import logging
import os

# 配置日志，使用已有的日志配置
logger = logging.getLogger('ComfyUIAPI')

@dataclass
class ComfyUIConfig:
    """ComfyUI 配置类"""
    host: str = "http://127.0.0.1"
    port: int = 8188
    client_id: str = "RICK"
    output_dir: str = "output"

    def __post_init__(self):
        if not self.client_id:
            self.client_id = str(uuid.uuid4())
        if not self.host.startswith("http://"):
            self.host = f"http://{self.host}"
        self.base_url = f"{self.host}:{self.port}"

class ComfyUIAPI:
    """ComfyUI API 工具类"""
    
    def __init__(self, config: ComfyUIConfig):
        self.config = config
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """发送 HTTP 请求并处理响应"""
        url = f"{self.config.base_url}{endpoint}"
        logger.info(f"发送请求: {method} {url}")
        
        # 如果有 JSON 数据，记录它
        if "json" in kwargs:
            logger.debug(f"请求数据: {json.dumps(kwargs['json'], ensure_ascii=False)}")
        
        try:
            response = self.session.request(method, url, **kwargs)
            logger.info(f"响应状态码: {response.status_code}")
            
            # 尝试解析响应内容，无论是否成功
            response_text = response.text
            # logger.debug(f"原始响应内容: {response_text}")
            
            # 尝试解析 JSON
            try:
                response_json = response.json()
                # logger.debug(f"JSON 响应: {json.dumps(response_json, ensure_ascii=False)}")
            except:
                response_json = None
                logger.debug("响应不是有效的 JSON 格式")
            
            # 检查状态码
            response.raise_for_status()
            
            # 如果响应正常，返回 JSON 数据
            return response_json if response_json is not None else {"text": response_text}
            
        except requests.exceptions.HTTPError as e:
            error_message = f"HTTP 错误: {e}"
            
            # 尝试提取服务器返回的错误信息
            try:
                error_json = response.json()
                error_detail = json.dumps(error_json, ensure_ascii=False)
                error_message = f"{error_message}\n服务器错误信息: {error_detail}"
            except:
                if response_text:
                    error_message = f"{error_message}\n服务器响应: {response_text}"
            
            logger.error(error_message)
            raise Exception(error_message)
            
        except requests.exceptions.RequestException as e:
            error_message = f"请求异常: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)
        
        except Exception as e:
            error_message = f"未知错误: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)

    def get_queue_remaining(self) -> Dict:
        """获取队列剩余信息"""
        return self._make_request("GET", "/api/prompt")

    def submit_prompt(self, prompt: Dict, extra_data: Optional[Dict] = None) -> Dict:
        """提交生成任务"""
        data = {
            "client_id": self.config.client_id,
            "prompt": prompt
        }
        if extra_data:
            data["extra_data"] = extra_data
        
        logger.info(f"提交生成任务，客户端 ID: {self.config.client_id}")
        return self._make_request("POST", "/api/prompt", json=data)

    def get_history(self, max_items: Optional[int] = None) -> Dict:
        """获取历史记录"""
        params = {"max_items": max_items} if max_items else {}
        return self._make_request("GET", "/api/history", params=params)

    def get_history_by_id(self, prompt_id: str) -> Dict:
        """获取指定 ID 的历史记录"""
        return self._make_request("GET", f"/api/history/{prompt_id}")

    def get_queue(self) -> Dict:
        """获取队列信息"""
        return self._make_request("GET", "/api/queue")

    def get_embeddings(self) -> Dict:
        """获取嵌入信息"""
        return self._make_request("GET", "/api/embeddings")

    def get_models(self) -> List[str]:
        """获取模型目录列表"""
        return self._make_request("GET", "/api/models")

    def get_model_files(self, model_type: str) -> List[str]:
        """获取指定类型的模型文件列表"""
        return self._make_request("GET", f"/api/models/{model_type}")

    def get_extensions(self) -> Dict:
        """获取扩展文件信息"""
        return self._make_request("GET", "/api/extensions")

    def upload_image(self, image_path: Union[str, Path]) -> Dict:
        """上传图片"""
        with open(image_path, 'rb') as f:
            files = {'image': f}
            return self._make_request("POST", "/api/upload/image", files=files)

    def upload_mask(self, image_path: Union[str, Path], type: str = "input", 
                   subfolder: str = "", original_ref: str = "") -> Dict:
        """上传蒙版图片"""
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'type': type,
                'subfolder': subfolder,
                'original_ref': original_ref
            }
            return self._make_request("POST", "/api/upload/mask", files=files, data=data)

    def get_system_stats(self) -> Dict:
        """获取系统状态信息"""
        return self._make_request("GET", "/api/system_stats")

    def get_model_metadata(self, folder_name: str, filename: str) -> Dict:
        """获取模型元数据"""
        params = {'filename': filename}
        return self._make_request("GET", f"/api/view_metadata/{folder_name}", params=params)

    def get_object_info(self, node_type: Optional[str] = None) -> Dict:
        """获取节点对象信息"""
        endpoint = f"/api/object_info/{node_type}" if node_type else "/api/object_info"
        return self._make_request("GET", endpoint)

    def clear_queue(self) -> Dict:
        """清空队列"""
        return self._make_request("POST", "/api/queue", json={"clear": True})

    def delete_queue_items(self, items: List[str]) -> Dict:
        """删除指定的队列项"""
        return self._make_request("POST", "/api/queue", json={"delete": items})

    def clear_history(self) -> Dict:
        """清空历史记录"""
        return self._make_request("POST", "/api/history", json={"clear": True})

    def delete_history_items(self, items: List[str]) -> Dict:
        """删除指定的历史记录项"""
        return self._make_request("POST", "/api/history", json={"delete": items})

    def interrupt(self) -> Dict:
        """中断当前运行的任务"""
        return self._make_request("POST", "/api/interrupt")

    def get_image(self, filename: str) -> bytes:
        """获取生成的图片"""
        url = f"{self.config.base_url}/view?filename={filename}"
        logger.info(f"获取图片: {url}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            error_message = f"获取图片失败: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)

    def save_image(self, image_data: bytes, filename: str) -> None:
        """保存图片到本地"""
        logger.info(f"保存图片到: {filename}")
        try:
            with open(filename, 'wb') as f:
                f.write(image_data) 
        except Exception as e:
            error_message = f"保存图片失败: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message) 
        
    def process_successful_generation(self, prompt_id, history,local_dir):
        """
        处理成功生成的图像
        
        Args:
            prompt_id: 任务ID
            history: 任务历史记录
            
        Returns:
            包含处理结果的字典
        """
        # 输出响应结构以便调试
        logger.info(f"处理历史记录内容结构: {list(history.keys() if isinstance(history, dict) else [])}")
        
        # 找出 SaveImage 节点的输出
        output_images = []
        downloaded_images = []

        history_content = history[prompt_id]
        outputs = history_content.get("outputs", {})
        
        # 处理所有输出节点中的图像
        for node_id, node_output in outputs.items():
            logger.info(f"处理节点 {node_id} 的输出")
            if "images" in node_output:
                logger.info(f"节点 {node_id} 包含 {len(node_output['images'])} 个图像")
                
                for image_info in node_output["images"]:
                    # 提取图像信息
                    image_filename = image_info.get("filename", "")
                    subfolder = image_info.get("subfolder", "")
                    image_type = image_info.get("type", "output")
                    
                    # 如果没有文件名，跳过
                    if not image_filename:
                        logger.warning("图像信息中没有文件名，跳过")
                        continue
                    
                    logger.info(f"处理图像: 文件名={image_filename}, 子文件夹={subfolder}, 类型={image_type}")
                    
                    # 构建完整文件名(包含子文件夹)
                    full_filename = os.path.join(subfolder, image_filename) if subfolder else image_filename
                    output_images.append(full_filename)
                    
                    # 下载图像到output目录
                    try:
                        # 获取图像数据
                        image_data = self.get_image(full_filename)
                        
                        # 保存图像到output目录，保持子文件夹结构
                        # local_dir = os.path.join(self.output_dir, subfolder) if subfolder else self.output_dir
                        # os.makedirs(local_dir, exist_ok=True)
                        
                        local_path = os.path.join(local_dir, image_filename)
                        with open(local_path, 'wb') as f:
                            f.write(image_data)
                        logger.info(f"图像已保存到: {local_path}")
                        
                        downloaded_images.append(local_path)
                    except Exception as e:
                        logger.error(f"下载图像 {full_filename} 失败: {str(e)}")

        if output_images:
            logger.info(f"处理了 {len(output_images)} 个图像: {', '.join(output_images)}")
            return {
                "success": True,
                "prompt_id": prompt_id,
                "images": output_images,
                "local_images": downloaded_images,
                "history": history
            }
        else:
            logger.warning("没有找到任何图像，但任务未报错")
            return {
                "success": True,
                "prompt_id": prompt_id,
                "images": [],
                "local_images": [],
                "history": history
            }