import json
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import re

logger = logging.getLogger('ComfyUIErrorParser')

class ComfyUIErrorParser:
    """ComfyUI 错误解析器，将错误信息转换为语义化的中文提示"""
    
    def __init__(self, custom_error_messages: Optional[Dict[str, str]] = None):
        """
        初始化错误解析器
        
        Args:
            custom_error_messages: 自定义错误消息映射 {错误类型: 自定义错误消息}
        """
        # 默认错误类型映射
        self.error_type_mapping = {
            # 全局错误类型
            "prompt_outputs_failed_validation": "工作流验证失败",
            "invalid_prompt": "无效的工作流",
            "missing_parameter": "缺少参数",
            "execution_error": "执行错误",
            
            # 节点错误类型
            "value_not_in_list": "参数值不在有效列表中",
            "value_not_found": "找不到指定的值",
            "invalid_value": "无效的参数值",
            "missing_input": "缺少必要的输入参数",
            "invalid_type": "参数类型不正确",
            "out_of_range": "参数值超出范围",
            "file_not_found": "找不到文件",
            "model_not_found": "找不到模型",
            "cuda_out_of_memory": "CUDA 内存不足",
            "execution_failure": "节点执行失败",
            "model_detection_error": "模型类型检测失败",
            "unsupported_format": "不支持的文件格式",
            "model_load_error": "模型加载失败",
            "vae_error": "VAE 错误",
            "clip_error": "CLIP 错误",
            "io_error": "输入/输出错误",
            "permission_error": "权限错误",
            "network_error": "网络错误"
        }
        
        # 错误消息模式匹配规则
        self.error_patterns = [
            # 模型检测错误
            (r"Could not detect model type of: (.+)", "model_detection_error", "无法检测模型 '{}' 的类型，可能是模型文件损坏或格式不受支持"),
            # CUDA 内存不足
            (r"CUDA out of memory", "cuda_out_of_memory", "CUDA 显存不足，请尝试减小图像分辨率或批处理大小，或使用更小的模型"),
            # 文件不存在
            (r"No such file or directory: (.+)", "file_not_found", "文件不存在: '{}'"),
            # VAE 解码错误
            (r"VAE Decode error", "vae_error", "VAE 解码错误，可能是 VAE 与模型不匹配"),
            # 权限错误
            (r"Permission denied", "permission_error", "权限被拒绝，请检查文件权限"),
            # 网络错误
            (r"Connection refused|Connection timed out|Network is unreachable", "network_error", "网络连接错误"),
            # 支持的格式错误
            (r"not a supported format|Unsupported format", "unsupported_format", "不支持的文件格式"),
            (r"Error while deserializing header: (.+)", "model_load_error", "模型加载失败"),
        ]
        
        # 若有自定义映射，则更新默认映射
        if custom_error_messages:
            self.error_type_mapping.update(custom_error_messages)
    
    def update_error_mappings(self, custom_error_messages: Dict[str, str]) -> None:
        """
        更新错误消息映射
        
        Args:
            custom_error_messages: 自定义错误消息映射 {错误类型: 自定义错误消息}
        """
        self.error_type_mapping.update(custom_error_messages)
    
    def _translate_error_type(self, error_type: str) -> str:
        """
        翻译错误类型
        
        Args:
            error_type: 错误类型
            
        Returns:
            翻译后的错误类型
        """
        return self.error_type_mapping.get(error_type, f"未知错误类型 ({error_type})")
    
    def _detect_error_type(self, error_message: str) -> tuple:
        """
        根据错误消息检测错误类型
        
        Args:
            error_message: 错误消息
            
        Returns:
            (错误类型, 格式化的错误消息)
        """
        for pattern, error_type, message_template in self.error_patterns:
            match = re.search(pattern, error_message)
            if match:
                # 格式化错误消息，如果有捕获组，则用捕获组替换 {}
                if len(match.groups()) > 0:
                    return error_type, message_template.format(*match.groups())
                else:
                    return error_type, message_template
        
        return None, None
    
    def _format_node_error(self, node_id: str, node_error: Dict, prompt: Optional[Dict] = None) -> Dict[str, Any]:
        """
        格式化节点错误信息
        
        Args:
            node_id: 节点ID
            node_error: 节点错误信息
            prompt: 原始工作流，用于获取更多节点信息
            
        Returns:
            格式化后的节点错误信息
        """
        class_type = node_error.get("class_type", "未知节点类型")
        
        # 获取节点名称（如果有提供 prompt）
        node_name = class_type
        if prompt and node_id in prompt:
            if "name" in prompt[node_id]:
                node_name = prompt[node_id]["name"]
        
        errors = []
        for error in node_error.get("errors", []):
            error_type = error.get("type", "unknown")
            message = error.get("message", "未知错误")
            details = error.get("details", "")
            extra_info = error.get("extra_info", {})
            
            # 构建语义化的错误提示
            translated_type = self._translate_error_type(error_type)
            
            # 处理特定类型的错误
            if error_type == "value_not_in_list":
                input_name = extra_info.get("input_name", "未知参数")
                received_value = extra_info.get("received_value", "未知值")
                
                # 从详情中提取更多信息
                available_options = []
                if "not in (" in details:
                    options_part = details.split("not in (")[-1].strip(")")
                    if "list of length" in options_part:
                        list_length = options_part.split("list of length")[-1].strip()
                        error_message = f"参数 '{input_name}' 的值 '{received_value}' 不在可用选项列表中 (共有 {list_length} 个可用选项)"
                    else:
                        error_message = f"参数 '{input_name}' 的值 '{received_value}' 不在可用选项列表中"
                else:
                    error_message = f"参数 '{input_name}' 的值 '{received_value}' 不在可用选项列表中"
            
            elif error_type == "file_not_found" or error_type == "model_not_found":
                input_name = extra_info.get("input_name", "未知参数")
                received_value = extra_info.get("received_value", "未知值")
                error_message = f"找不到文件: 参数 '{input_name}' 指定的文件 '{received_value}' 不存在"
            
            elif error_type == "missing_input":
                input_name = extra_info.get("input_name", "未知参数")
                error_message = f"缺少必要的输入参数: '{input_name}'"
            
            elif error_type == "invalid_type":
                input_name = extra_info.get("input_name", "未知参数")
                received_type = extra_info.get("received_type", "未知类型")
                expected_type = extra_info.get("expected_type", "未知类型")
                error_message = f"参数 '{input_name}' 的类型错误: 期望 '{expected_type}'，实际为 '{received_type}'"
            
            elif error_type == "execution_failure":
                # 尝试从消息中检测特定错误类型
                detected_type, formatted_message = self._detect_error_type(message)
                
                if detected_type:
                    error_type = detected_type
                    translated_type = self._translate_error_type(detected_type)
                    error_message = formatted_message
                else:
                    # 如果无法检测特定类型，则使用一般性错误消息
                    # 清理堆栈跟踪中的路径信息，以提高可读性
                    clean_message = self._clean_exception_message(message)
                    error_message = f"{translated_type}: {clean_message}"
                
                # 如果有详情，添加到错误消息中
                if details:
                    # 尝试从详情中提取有用信息
                    clean_details = self._clean_traceback(details)
                    if clean_details and len(clean_details) > 0:
                        logger.debug(f"清理后的错误详情: {clean_details}")
                        # 只取最相关的第一行
                        relevant_detail = clean_details.split('\n')[0] if '\n' in clean_details else clean_details
                        error_message += f" - {relevant_detail}"
            
            else:
                # 通用错误信息
                error_message = f"{translated_type}: {details}" if details else translated_type
            
            errors.append({
                "type": error_type,
                "translated_type": translated_type,
                "message": error_message,
                "details": details,
                "extra_info": extra_info
            })
        
        # 构建受影响的节点列表
        dependent_outputs = node_error.get("dependent_outputs", [])
        dependent_nodes = []
        for output_id in dependent_outputs:
            if prompt and output_id in prompt:
                node_class = prompt[output_id].get("class_type", "未知节点类型")
                if "name" in prompt[output_id]:
                    dependent_nodes.append(f"{prompt[output_id]['name']} (ID: {output_id}, 类型: {node_class})")
                else:
                    dependent_nodes.append(f"节点 {output_id} (类型: {node_class})")
            else:
                dependent_nodes.append(f"节点 {output_id}")
        
        return {
            "node_id": node_id,
            "class_type": class_type,
            "node_name": node_name,
            "errors": errors,
            "dependent_nodes": dependent_nodes
        }
    
    def _clean_exception_message(self, message: str) -> str:
        """清理异常消息中的路径信息"""
        # 移除文件路径
        clean_message = re.sub(r'([A-Z]:\\|/)(Users|home|Program Files|Windows).*?[/\\]([^/\\]+\.py|[^/\\]+\.safetensors)', r'...\3', message)
        # 移除引号和特殊字符
        clean_message = re.sub(r'[\'"`]', '', clean_message)
        # 如果消息以 "ERROR: " 开头，则去除
        clean_message = re.sub(r'^ERROR:\s*', '', clean_message)
        return clean_message
    
    def _clean_traceback(self, traceback: str) -> str:
        """清理堆栈跟踪信息，提取有用部分"""
        if not traceback:
            return ""
        
        # 分割堆栈跟踪为行
        lines = traceback.split('\n')
        clean_lines = []
        
        for line in lines:
            # 跳过包含文件路径的行
            if "File " in line and (r":\\" in line or "/" in line):
                continue
            # 跳过包含 ^ 的行（通常是指向错误位置的箭头）
            if "^" in line and line.strip() == "^" * len(line.strip()):
                continue
            # 移除行号信息
            line = re.sub(r', line \d+,', '', line)
            # 移除文件路径
            line = re.sub(r'([A-Z]:\\|/)(Users|home|Program Files|Windows).*?[/\\]([^/\\]+\.py)', r'...\3', line)
            # 去除前导空白
            line = line.strip()
            # 如果行不为空，则添加
            if line:
                clean_lines.append(line)
        
        # 只返回有用的行，跳过通用的异常框架信息
        useful_lines = []
        for line in clean_lines:
            if not any(skip in line for skip in ["Traceback (most recent call last)", "raise ", "Exception", "Error"]):
                useful_lines.append(line)
        
        return '\n'.join(useful_lines)
    
    def process_history_error(self, history: Dict, prompt: Optional[Dict] = None, verbose: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        处理 ComfyUI 任务历史记录中的错误
        
        Args:
            history: ComfyUI 任务历史记录，可能是嵌套结构 {"prompt_id": {真实历史}}
            prompt: 原始工作流，用于获取更多节点信息
            verbose: 是否输出详细信息
            
        Returns:
            (是否有错误, 错误消息, 详细错误信息)
        """
        # 检查历史记录是否是嵌套结构 {"prompt_id": {真实历史}}
        if len(history) == 1 and all(isinstance(k, str) and isinstance(v, dict) for k, v in history.items()):
            # 提取第一个键的值作为真实历史记录
            prompt_id = list(history.keys())[0]
            history = history[prompt_id]
            logger.debug(f"检测到嵌套历史记录，提取 prompt_id: {prompt_id} 的历史")
        
        # 检查是否有错误
        if "status" not in history or history["status"].get("status_str") != "error":
            return False, "", None
        
        # 查找执行错误信息
        execution_error = None
        for message in history["status"].get("messages", []):
            if message[0] == "execution_error":
                execution_error = message[1]
                break
        
        if not execution_error:
            return True, "任务执行失败，但无法提取详细错误信息", None
        
        # 提取错误信息
        node_id = execution_error.get("node_id", "未知节点")
        node_type = execution_error.get("node_type", "未知类型")
        exception_message = execution_error.get("exception_message", "未知错误")
        exception_type = execution_error.get("exception_type", "未知异常类型")
        traceback = execution_error.get("traceback", [])
        
        # 检测错误类型
        detected_type, formatted_message = self._detect_error_type(exception_message)
        error_type = detected_type if detected_type else "execution_error"
        error_message = formatted_message if formatted_message else exception_message
        
        # 构建用户友好的错误消息
        translated_type = self._translate_error_type(error_type)
        
        # 简洁错误消息
        cleaned_message = self._clean_exception_message(error_message)
        simple_error = f"{translated_type}: 节点 {node_id} ({node_type}) - {cleaned_message}"
        
        if not verbose:
            return True, simple_error, None
        
        # 详细错误消息
        detailed_error = [
            f"错误类型: {translated_type} ({error_type})",
            f"错误消息: {cleaned_message}",
            f"异常类型: {exception_type}",
            f"节点: {node_id} ({node_type})"
        ]
        
        # 添加堆栈跟踪
        if traceback:
            clean_traceback = self._clean_traceback("\n".join(traceback))
            if clean_traceback:
                detailed_error.append(f"\n堆栈跟踪:\n{clean_traceback}")
        
        # 添加受影响的节点
        dependent_outputs = execution_error.get("current_outputs", [])
        if dependent_outputs and prompt:
            affected_nodes = []
            for output_id in dependent_outputs:
                if output_id == node_id:
                    continue  # 跳过错误节点本身
                
                if prompt and output_id in prompt:
                    node_class = prompt[output_id].get("class_type", "未知类型")
                    affected_nodes.append(f"节点 {output_id} ({node_class})")
                else:
                    affected_nodes.append(f"节点 {output_id}")
            
            if affected_nodes:
                detailed_error.append(f"\n受影响的节点: {', '.join(affected_nodes)}")
        
        return True, simple_error, "\n".join(detailed_error)
    
    def parse_error(self, error_message: Union[str, Dict], prompt: Optional[Dict] = None) -> Dict[str, Any]:
        """
        解析错误信息
        
        Args:
            error_message: 错误消息字符串或字典
            prompt: 原始工作流，用于获取更多节点信息
            
        Returns:
            解析后的错误信息
        """
        # 如果错误信息是字符串，尝试解析为 JSON
        if isinstance(error_message, str):
            try:
                # 检查是否包含 HTTP 错误信息
                if "HTTP 错误" in error_message and "服务器错误信息" in error_message:
                    # 提取服务器错误信息部分
                    error_json_str = error_message.split("服务器错误信息:", 1)[1].strip()
                    error_data = json.loads(error_json_str)
                else:
                    # 尝试直接解析整个字符串
                    error_data = json.loads(error_message)
            except (json.JSONDecodeError, IndexError) as e:
                return {
                    "parsed": False,
                    "original_error": error_message,
                    "reason": f"无法解析错误信息: {str(e)}"
                }
        else:
            error_data = error_message
        
        # 检查是否包含 error 字段
        if "error" not in error_data:
            return {
                "parsed": False,
                "original_error": error_data,
                "reason": "错误数据格式不正确: 缺少 'error' 字段"
            }
        
        # 提取基本错误信息
        error_info = error_data["error"]
        error_type = error_info.get("type", "unknown")
        error_message = error_info.get("message", "未知错误")
        error_details = error_info.get("details", "")
        
        # 对于执行错误，尝试检测更具体的错误类型
        if error_type == "execution_error":
            detected_type, formatted_message = self._detect_error_type(error_message)
            if detected_type:
                error_type = detected_type
                error_message = formatted_message
        
        # 翻译错误类型
        translated_type = self._translate_error_type(error_type)
        
        # 构建基本结果
        result = {
            "parsed": True,
            "error_type": error_type,
            "translated_type": translated_type,
            "message": error_message,
            "details": error_details,
            "node_errors": [],
            "summary": ""
        }
        
        # 解析节点错误
        if "node_errors" in error_data:
            node_errors = error_data["node_errors"]
            for node_id, node_error in node_errors.items():
                formatted_error = self._format_node_error(node_id, node_error, prompt)
                result["node_errors"].append(formatted_error)
        
        # 生成摘要
        if result["node_errors"]:
            node_error_summaries = []
            for node_error in result["node_errors"]:
                node_class = node_error["class_type"]
                node_id = node_error["node_id"]
                
                error_msgs = []
                for error in node_error["errors"]:
                    error_msgs.append(error["message"])
                
                node_error_summary = f"节点 {node_id} ({node_class}) 错误: {'; '.join(error_msgs)}"
                node_error_summaries.append(node_error_summary)
            
            result["summary"] = f"{translated_type}: {'; '.join(node_error_summaries)}"
        else:
            result["summary"] = f"{translated_type}: {error_message}"
            if error_details:
                result["summary"] += f" - {error_details}"
        
        return result
    
    def format_error_message(self, error_data: Dict[str, Any], verbose: bool = False) -> str:
        """
        格式化错误消息为人类可读的文本
        
        Args:
            error_data: 解析后的错误数据 (parse_error 方法的输出)
            verbose: 是否输出详细信息
            
        Returns:
            格式化后的错误消息
        """
        if not error_data.get("parsed", False):
            return f"无法解析错误信息: {error_data.get('reason', '未知原因')}\n原始错误: {error_data.get('original_error', '未提供')}"
        
        # 简洁模式只返回摘要
        if not verbose:
            return error_data["summary"]
        
        # 详细模式
        lines = [f"错误类型: {error_data['translated_type']} ({error_data['error_type']})"]
        lines.append(f"错误消息: {error_data['message']}")
        
        if error_data["details"]:
            lines.append(f"详细信息: {error_data['details']}")
        
        if error_data["node_errors"]:
            lines.append("\n节点错误详情:")
            
            for node_error in error_data["node_errors"]:
                node_id = node_error["node_id"]
                node_type = node_error["class_type"]
                lines.append(f"\n- 节点 {node_id} ({node_type}):")
                
                for error in node_error["errors"]:
                    lines.append(f"  * {error['message']}")
                    if error.get("details") and error["details"] != error["message"]:
                        lines.append(f"    细节: {error['details']}")
                
                if node_error["dependent_nodes"]:
                    lines.append(f"  * 影响的节点: {', '.join(node_error['dependent_nodes'])}")
        
        return "\n".join(lines)
    
    def process_error(self, error_message: Union[str, Dict], prompt: Optional[Dict] = None, verbose: bool = False) -> str:
        """
        处理错误信息并返回格式化的错误消息
        
        Args:
            error_message: 错误消息字符串或字典
            prompt: 原始工作流，用于获取更多节点信息
            verbose: 是否输出详细信息
            
        Returns:
            格式化后的错误消息
        """
        parsed_error = self.parse_error(error_message, prompt)
        return self.format_error_message(parsed_error, verbose)


# 示例用法
if __name__ == "__main__":
    # 示例错误消息
    example_error = """HTTP 错误: 400 Client Error: Bad Request for url: http://127.0.0.1:8188/api/prompt
服务器错误信息: {"error": {"type": "prompt_outputs_failed_validation", "message": "Prompt outputs failed validation", "details": "", "extra_info": {}}, "node_errors": {"4": {"errors": [{"type": "value_not_in_list", "message": "Value not in list", "details": "ckpt_name: 'v1-5-pruned-emaonly.safetensors' not in (list of length 99)", "extra_info": {"input_name": "ckpt_name", "input_config": null, "received_value": "v1-5-pruned-emaonly.safetensors"}}], "dependent_outputs": ["9"], "class_type": "CheckpointLoaderSimple"}}}"""
    
    # 执行错误示例
    execution_error = {
        "error": {
            "type": "execution_error",
            "message": "ERROR: Could not detect model type of: L:\\ComfyUI-aki-v1.6\\ComfyUI\\models\\checkpoints\\EnvyZoomSliderXL01.safetensors",
            "details": "类型: RuntimeError"
        },
        "node_errors": {
            "4": {
                "errors": [
                    {
                        "type": "execution_failure",
                        "message": "ERROR: Could not detect model type of: L:\\ComfyUI-aki-v1.6\\ComfyUI\\models\\checkpoints\\EnvyZoomSliderXL01.safetensors",
                        "details": "Traceback (most recent call last):\n  File \"L:\\ComfyUI-aki-v1.6\\ComfyUI\\execution.py\", line 327...",
                        "extra_info": {
                            "exception_type": "RuntimeError"
                        }
                    }
                ],
                "class_type": "CheckpointLoaderSimple",
                "dependent_outputs": ["9", "3", "6", "5", "8", "4", "7"]
            }
        }
    }
    
    # 工作流信息
    example_prompt = {
        "3": {
            "inputs": {
                "seed": 123456789,
                "steps": 20,
                "cfg": 8,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "4": {
            "inputs": {
                "ckpt_name": "EnvyZoomSliderXL01.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "9": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": ["8", 0]
            },
            "class_type": "SaveImage"
        }
    }
    
    # 创建解析器
    parser = ComfyUIErrorParser()
    
    # 解析验证错误
    error_text = parser.process_error(example_error, example_prompt)
    print("简洁错误信息 (验证错误):")
    print(error_text)
    
    print("\n详细错误信息 (验证错误):")
    error_text_verbose = parser.process_error(example_error, example_prompt, verbose=True)
    print(error_text_verbose)
    
    # 解析执行错误
    error_text = parser.process_error(execution_error, example_prompt)
    print("\n简洁错误信息 (执行错误):")
    print(error_text)
    
    print("\n详细错误信息 (执行错误):")
    error_text_verbose = parser.process_error(execution_error, example_prompt, verbose=True)
    print(error_text_verbose) 