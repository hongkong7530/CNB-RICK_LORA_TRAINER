import json
from typing import Dict, List, Optional, Any, Union
import os
from comfyui_api import ComfyUIAPI
import time
#comfyui执行预检测
class ComfyUIPreCheck:
    """ComfyUI 预检测工具类"""
    
    def __init__(self, api: ComfyUIAPI):
        self.api = api
        # 缓存相关属性
        self._node_types_cache = {}  # 节点类型缓存
        self._model_files_cache = {} # 模型文件缓存
        self._cache_timestamp = 0    # 缓存时间戳
    
    def pre_cache(self, cache_models: bool = True, model_types: Optional[List[str]] = None) -> Dict:
        """
        预缓存可用节点、模型等信息，方便后续快速获取
        
        Args:
            cache_models: 是否缓存模型文件
            model_types: 要缓存的模型类型列表，None表示所有类型
            
        Returns:
            缓存结果统计信息
        """
        cache_result = {
            "success": True,
            "timestamp": time.time(),
            "node_types_count": 0,
            "model_types_count": 0,
            "model_files_count": 0,
            "errors": []
        }
        
        try:
            # 缓存节点类型
            self._node_types_cache = self.analyze_node_types()
            node_count = sum(len(nodes) for nodes in self._node_types_cache.values())
            cache_result["node_types_count"] = node_count
            
            # 缓存模型文件(如果需要)
            if cache_models:
                if model_types is None:
                    try:
                        model_types = self.api.get_models()
                    except Exception as e:
                        cache_result["errors"].append(f"获取模型类型列表失败: {str(e)}")
                        model_types = []
                
                cache_result["model_types_count"] = len(model_types)
                self._model_files_cache = self.analyze_model_files(model_types)
                model_files_count = sum(len(files) for files in self._model_files_cache.values())
                cache_result["model_files_count"] = model_files_count
            
            # 更新缓存时间戳
            self._cache_timestamp = cache_result["timestamp"]
            
        except Exception as e:
            cache_result["success"] = False
            cache_result["errors"].append(f"预缓存过程出错: {str(e)}")
        
        return cache_result
    
    def update_cache(self, cache_models: bool = True, model_types: Optional[List[str]] = None) -> Dict:
        """
        更新缓存信息
        
        Args:
            cache_models: 是否更新模型文件缓存
            model_types: 要更新的模型类型列表
            
        Returns:
            更新结果统计信息
        """
        return self.pre_cache(cache_models, model_types)
    
    def get_cached_node_types(self) -> Dict[str, List[str]]:
        """
        获取缓存的节点类型
        
        Returns:
            节点类型字典 {分类: [节点类型列表]}
        """
        if not self._node_types_cache:
            return self.analyze_node_types()
        return self._node_types_cache
    
    def get_cached_node_info(self, node_type: str) -> Dict:
        """
        获取缓存的节点详细信息
        
        Args:
            node_type: 节点类型名称
            
        Returns:
            节点详细信息
        """
        if node_type not in self._node_types_cache:
            self._node_types_cache[node_type] = self.analyze_node_detail(node_type)
        return self._node_types_cache[node_type]
    
    def get_cached_model_files(self, model_type: Optional[str] = None) -> Union[Dict[str, List[str]], List[str]]:
        """
        获取缓存的模型文件
        
        Args:
            model_type: 模型类型，None表示获取所有类型
            
        Returns:
            模型文件字典或列表
        """
        if not self._model_files_cache:
            self._model_files_cache = self.analyze_model_files()
        
        if model_type:
            return self._model_files_cache.get(model_type, [])
        return self._model_files_cache
    
    def get_cache_timestamp(self) -> float:
        """
        获取缓存时间戳
        
        Returns:
            缓存创建时间戳
        """
        return self._cache_timestamp
    
    def is_cache_valid(self, max_age_seconds: int = 3600) -> bool:
        """
        检查缓存是否有效
        
        Args:
            max_age_seconds: 最大有效时间(秒)
            
        Returns:
            是否有效
        """
        if self._cache_timestamp == 0:
            return False
        return (time.time() - self._cache_timestamp) < max_age_seconds
    
    def analyze_node_types(self) -> Dict[str, List[str]]:
        """分析可用的节点类型"""
        try:
            return self.api.get_object_info()
        except Exception as e:
            print(f"分析节点类型失败: {str(e)}")
            return {}
    
    def analyze_node_detail(self, node_type: str, use_cache: bool = True) -> Dict:
        """
        分析特定节点的详细信息
        
        Args:
            node_type: 节点类型
            use_cache: 是否使用缓存的节点信息
            
        Returns:
            节点详细信息
        """
        try:
            if use_cache and self._node_types_cache and node_type in self._node_types_cache:
                return self._node_types_cache[node_type]

            return self.api.get_object_info(node_type)
        except Exception as e:
            print(f"分析节点 {node_type} 失败: {str(e)}")
            return {}
    
    def analyze_workflow(self, prompt: Dict, use_cache: bool = True) -> Dict:
        """
        分析工作流结构
        
        Args:
            prompt: 工作流数据
            use_cache: 是否使用缓存的节点信息
            
        Returns:
            工作流分析结果
        """
        result = {
            "node_count": len(prompt),
            "node_types": {},
            "connections": [],
            "inputs": {},
            "outputs": [],
            "parameter_issues": [] # 添加参数问题列表
        }
        
        # 分析节点类型数量
        for node_id, node_data in prompt.items():
            node_type = node_data.get("class_type")
            if node_type not in result["node_types"]:
                result["node_types"][node_type] = 0
            result["node_types"][node_type] += 1
            
            # 分析连接
            inputs = node_data.get("inputs", {})
            for input_name, input_value in inputs.items():
                if isinstance(input_value, list) and len(input_value) == 2:
                    source_node, source_output = input_value
                    result["connections"].append({
                        "from_node": source_node,
                        "from_output": source_output,
                        "to_node": node_id,
                        "to_input": input_name
                    })
            
            # 标识可能的输入和输出节点
            if "CheckpointLoader" in node_type or ("Image" in node_type and "Empty" not in node_type):
                result["inputs"][node_id] = node_type
            
            if "SaveImage" in node_type or "Preview" in node_type:
                result["outputs"].append(node_id)
                
            # 使用缓存检查节点参数有效性
            if use_cache and self._node_types_cache and node_type in self._node_types_cache:
                node_info = self._node_types_cache[node_type]
                if "input" in node_info:
                    required_inputs = node_info["input"].get("required",{})
                    optional_inputs = node_info["input"].get("optional",{})
                    
                    # 检查必需输入是否存在
                    for req_input, input_info in required_inputs.items():
                        if req_input not in inputs:
                            result["parameter_issues"].append({
                                "node_id": node_id,
                                "node_type": node_type,
                                "issue_type": "missing_required_input",
                                "message": f"节点 {node_id} ({node_type}) 缺少必需的输入参数 '{req_input}'"
                            })
                    
                    # 检查输入类型和值的有效性
                    for input_name, input_value in inputs.items():
                        input_info = required_inputs.get(input_name) or optional_inputs.get(input_name)
                        if not input_info:
                            result["parameter_issues"].append({
                                "node_id": node_id,
                                "node_type": node_type,
                                "issue_type": "unknown_input",
                                "message": f"节点 {node_id} ({node_type}) 使用了未知的输入参数 '{input_name}'"
                            })
                            continue
                        
                        # 如果是连接类型的输入，跳过值检查
                        if isinstance(input_value, list) and len(input_value) == 2:
                            continue
                        
                        # 检查枚举值
                        # if "values" in input_info and input_value not in input_info["values"]:
                        #     result["parameter_issues"].append({
                        #         "node_id": node_id,
                        #         "node_type": node_type,
                        #         "issue_type": "invalid_enum_value",
                        #         "message": f"节点 {node_id} ({node_type}) 参数 '{input_name}' 的值 '{input_value}' 不在有效值列表中"
                        #     })
        
        return result

    def validate_prompt(self, prompt: Dict, use_cache: bool = True) -> Dict[str, List[str]]:
        """
        验证工作流是否有问题
        
        Args:
            prompt: 工作流数据
            use_cache: 是否使用缓存的节点信息
            
        Returns:
            包含问题列表的字典
        """
        issues = {
            "missing_connections": [],
            "invalid_node_types": [],
            "other_issues": []
        }
        
        # 获取有效的节点类型
        try:
            # 使用缓存或从API获取节点信息
            if use_cache and self._node_types_cache:
                # 从缓存中提取所有节点类型
                valid_node_types = self._node_types_cache
            else:
                valid_node_types = self.api.get_object_info()
            
            # 检查节点类型是否有效
            for node_id, node_data in prompt.items():
                node_type = node_data.get("class_type")
                
                if node_type not in valid_node_types:
                    issues["invalid_node_types"].append(f"节点 {node_id} 的类型 '{node_type}' 无效")
                
                # 检查输入连接
                inputs = node_data.get("inputs", {})
                for input_name, input_value in inputs.items():
                    if isinstance(input_value, list) and len(input_value) == 2:
                        source_node, source_output = input_value
                        
                        # 检查源节点是否存在
                        if source_node not in prompt:
                            issues["missing_connections"].append(
                                f"节点 {node_id} 的输入 '{input_name}' 引用了不存在的节点 {source_node}"
                            )
            
            return issues
        except Exception as e:
            issues["other_issues"].append(f"验证过程出错: {str(e)}")
            return issues
    
    def analyze_model_files(self, model_types: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """分析可用的模型文件"""
        try:
            if model_types is None:
                model_types = self.api.get_models()
            
            model_files = {}
            for model_type in model_types:
                try:
                    files = self.api.get_model_files(model_type)
                    model_files[model_type] = files
                except Exception as e:
                    print(f"获取模型类型 {model_type} 的文件列表失败: {str(e)}")
            
            return model_files
        except Exception as e:
            print(f"分析模型文件失败: {str(e)}")
            return {}
    
    def save_check_info(self, data: Any, filename: str) -> str:
        """保存预检测信息到文件"""
        os.makedirs("check", exist_ok=True)
        filepath = os.path.join("check", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                f.write(str(data))
        
        return filepath
    
    def validate_model_file(self, model_type: str, filename: str, use_cache: bool = True) -> Dict:
        """
        验证模型文件是否存在
        
        Args:
            model_type: 模型类型 (checkpoints, loras, vae等)
            filename: 文件名
            use_cache: 是否使用缓存
            
        Returns:
            验证结果
        """
        result = {
            "exists": False,
            "model_type": model_type,
            "filename": filename,
            "error": None
        }
        
        try:
            # 使用缓存或从API获取模型文件列表
            if use_cache and model_type in self._model_files_cache:
                model_files = self._model_files_cache[model_type]
            else:
                model_files = self.api.get_model_files(model_type)
            
            # 检查文件是否存在
            if filename in model_files:
                result["exists"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def validate_workflow(self, prompt: Dict, use_cache: bool = True) -> Dict:
        """
        全面验证工作流的有效性
        
        Args:
            prompt: 工作流数据
            use_cache: 是否使用缓存
            
        Returns:
            包含验证结果的字典
        """
        result = {
            "valid": True,
            "issues_count": 0,
            "structure_issues": [],
            "parameter_issues": [],
            "model_issues": [],
            "workflow_analysis": {}
        }
        
        # 1. 结构验证（节点连接）
        try:
            structure_issues = self.validate_prompt(prompt, use_cache)
            if any(len(issues) > 0 for issues in structure_issues.values()):
                result["valid"] = False
                
                # 统计并添加结构问题
                for issue_type, issues in structure_issues.items():
                    if issues:
                        result["structure_issues"].extend([
                            {"type": issue_type, "message": message}
                            for message in issues
                        ])
                        result["issues_count"] += len(issues)
        except Exception as e:
            result["structure_issues"].append({
                "type": "validation_error",
                "message": f"验证结构时出错: {str(e)}"
            })
            result["valid"] = False
            result["issues_count"] += 1
        
        # 2. 分析工作流（包括参数验证）
        try:
            workflow_analysis = self.analyze_workflow(prompt, use_cache)
            result["workflow_analysis"] = workflow_analysis
            
            # 添加参数问题
            if "parameter_issues" in workflow_analysis and workflow_analysis["parameter_issues"]:
                result["parameter_issues"] = workflow_analysis["parameter_issues"]
                result["issues_count"] += len(workflow_analysis["parameter_issues"])
                result["valid"] = False
                
            # 检查是否有输出节点
            if not workflow_analysis.get("outputs"):
                result["structure_issues"].append({
                    "type": "no_output_nodes",
                    "message": "工作流中没有输出节点（如SaveImage或Preview）"
                })
                result["issues_count"] += 1
                result["valid"] = False
        except Exception as e:
            result["structure_issues"].append({
                "type": "analysis_error",
                "message": f"分析工作流时出错: {str(e)}"
            })
            result["valid"] = False
            result["issues_count"] += 1
        
        # 3. 检查模型文件
        try:
            for node_id, node_type in result["workflow_analysis"].get("inputs", {}).items():
                node_data = prompt.get(node_id, {})
                
                # 检查CheckpointLoader类型节点
                if "CheckpointLoader" in node_type and "inputs" in node_data:
                    if "ckpt_name" in node_data["inputs"]:
                        checkpoint_name = node_data["inputs"]["ckpt_name"]
                        model_check = self.validate_model_file("checkpoints", checkpoint_name, use_cache)
                        
                        if not model_check["exists"]:
                            result["model_issues"].append({
                                "node_id": node_id,
                                "node_type": node_type,
                                "model_type": "checkpoints",
                                "filename": checkpoint_name,
                                "message": f"模型文件 '{checkpoint_name}' 不存在"
                            })
                            result["issues_count"] += 1
                            result["valid"] = False
                
                # 检查LoraLoader类型节点
                if "LoraLoader" in node_type and "inputs" in node_data:
                    if "lora_name" in node_data["inputs"]:
                        lora_name = node_data["inputs"]["lora_name"]
                        model_check = self.validate_model_file("loras", lora_name, use_cache)
                        
                        if not model_check["exists"]:
                            result["model_issues"].append({
                                "node_id": node_id,
                                "node_type": node_type,
                                "model_type": "loras",
                                "filename": lora_name,
                                "message": f"LoRA文件 '{lora_name}' 不存在"
                            })
                            result["issues_count"] += 1
                            result["valid"] = False
                
                # 检查VAELoader类型节点
                if "VAELoader" in node_type and "inputs" in node_data:
                    if "vae_name" in node_data["inputs"]:
                        vae_name = node_data["inputs"]["vae_name"]
                        model_check = self.validate_model_file("vae", vae_name, use_cache)
                        
                        if not model_check["exists"]:
                            result["model_issues"].append({
                                "node_id": node_id,
                                "node_type": node_type,
                                "model_type": "vae",
                                "filename": vae_name,
                                "message": f"VAE文件 '{vae_name}' 不存在"
                            })
                            result["issues_count"] += 1
                            result["valid"] = False
                            
        except Exception as e:
            result["model_issues"].append({
                "type": "model_validation_error",
                "message": f"验证模型文件时出错: {str(e)}"
            })
            result["valid"] = False
            result["issues_count"] += 1
        
        return result 