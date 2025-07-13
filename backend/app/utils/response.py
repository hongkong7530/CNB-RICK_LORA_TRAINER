"""
响应格式工具模块
统一API响应格式为 {code, data, msg} 结构
"""
from typing import Any, Dict, Optional, Union, List, Tuple, TypeVar, Callable
from flask import jsonify, Response, current_app
import traceback
import logging

# 创建logger
logger = logging.getLogger(__name__)

# 类型定义
T = TypeVar('T')
DataType = Optional[Union[Dict, List, Any]]
ResponseType = Tuple[Response, int]

def api_response(code: int = 0, 
                 data: DataType = None, 
                 msg: str = "成功") -> Dict:
    """
    生成统一的API响应格式
    
    参数:
        code: 状态码，0表示成功，非0表示各种错误
        data: 响应数据
        msg: 状态消息
        
    返回:
        符合统一格式的响应字典
    """
    response = {
        "code": code,
        "data": data if data is not None else {},
        "msg": msg
    }
    return response


def success(data: DataType = None, msg: str = "成功") -> Dict:
    """成功响应字典"""
    return api_response(0, data, msg)


def error(code: int = 500, msg: str = "操作失败", data: DataType = None) -> Dict:
    """错误响应字典"""
    return api_response(code, data, msg)


def json_response(code: int = 0, 
                 data: DataType = None, 
                 msg: str = "成功",
                 status: int = 200) -> ResponseType:
    """
    生成统一的API JSON响应对象
    
    参数:
        code: 业务码，0表示成功，非0表示各种错误
        data: 响应数据
        msg: 状态消息
        status: HTTP状态码
        
    返回:
        Flask响应对象
    """
    response_data = api_response(code, data, msg)
    return jsonify(response_data), status


def success_json(data: DataType = None, 
                msg: str = "成功", 
                status: int = 200) -> ResponseType:
    """
    生成成功的JSON响应对象
    
    参数:
        data: 响应数据
        msg: 状态消息
        status: HTTP状态码 (默认200)
        
    返回:
        Flask响应对象
    """
    return json_response(0, data, msg, status)


def error_json(code: int = 500, 
              msg: str = "操作失败", 
              data: DataType = None,
              status: int = None) -> ResponseType:
    """
    生成错误的JSON响应对象
    
    参数:
        code: 业务错误码
        msg: 错误消息
        data: 额外数据
        status: HTTP状态码 (默认根据code自动判断)
        
    返回:
        Flask响应对象
    """
    # 如果未指定消息，尝试从错误码定义中获取
    if msg == "操作失败" and code in ERROR_CODES:
        msg = ERROR_CODES[code]
        
    # 如果未指定HTTP状态码，根据业务码自动选择
    if status is None:
        if code >= 1000:  # 业务错误码
            status = 400  # 默认业务错误返回400
        else:  # HTTP错误码
            status = code if 400 <= code < 600 else 500
            
    # 记录错误日志（5xx错误）
    if status >= 500:
        logger.error(f"服务器错误: code={code}, msg={msg}")
            
    return json_response(code, data, msg, status)


def exception_handler(func: Callable[..., T]) -> Callable[..., Union[T, ResponseType]]:
    """
    异常处理装饰器，捕获函数执行中的异常并返回标准错误响应
    
    使用示例:
    
    @exception_handler
    def my_api_function():
        # 可能抛出异常的代码
        return success_json(...)
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            # 参数验证错误
            logger.warning(f"参数验证错误: {str(e)}")
            return error_json(400, str(e))
        except Exception as e:
            # 服务器内部错误
            error_id = generate_error_id()
            logger.error(f"未处理异常 [{error_id}]: {str(e)}", exc_info=True)
            
            if current_app.debug:
                # 开发环境返回详细错误
                return error_json(500, f"服务器错误: {str(e)}", {
                    "error_id": error_id,
                    "traceback": traceback.format_exc()
                })
            else:
                # 生产环境返回简化错误
                return error_json(500, f"服务器错误，请联系管理员。错误ID: {error_id}")
    
    # 保留原函数名和文档
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def generate_error_id() -> str:
    """生成唯一的错误ID，用于日志跟踪"""
    import uuid
    import time
    return f"{int(time.time())}-{str(uuid.uuid4())[:8]}"


def response_template(template_name: str, **kwargs) -> ResponseType:
    """
    使用预定义模板生成响应
    
    参数:
        template_name: 模板名称
        **kwargs: 模板参数
        
    返回:
        Flask响应对象
    """
    templates = {
        "created": lambda **kw: success_json(
            kw.get("data"), 
            kw.get("msg", "创建成功"), 
            201
        ),
        "updated": lambda **kw: success_json(
            kw.get("data"), 
            kw.get("msg", "更新成功")
        ),
        "deleted": lambda **kw: success_json(
            None, 
            kw.get("msg", "删除成功")
        ),
        "not_found": lambda **kw: error_json(
            kw.get("code", 404), 
            kw.get("msg", "资源不存在"),
            kw.get("data")
        ),
        "bad_request": lambda **kw: error_json(
            kw.get("code", 400), 
            kw.get("msg", "请求参数错误"),
            kw.get("data")
        ),
        "unauthorized": lambda **kw: error_json(
            kw.get("code", 401), 
            kw.get("msg", "未授权访问"),
            kw.get("data"),
            401
        ),
        "forbidden": lambda **kw: error_json(
            kw.get("code", 403), 
            kw.get("msg", "禁止访问"),
            kw.get("data"),
            403
        ),
    }
    
    if template_name not in templates:
        raise ValueError(f"未知的响应模板: {template_name}")
        
    return templates[template_name](**kwargs)


def get_error_message(code: int) -> str:
    """获取错误码对应的默认错误消息"""
    return ERROR_CODES.get(code, "未知错误")


# 常见错误码定义
ERROR_CODES = {
    # 通用错误
    400: "请求参数错误", 
    401: "未授权访问",
    403: "禁止访问",
    404: "资源不存在",
    405: "方法不允许",
    500: "服务器内部错误",
    
    # 业务错误码
    # 1xxx: 任务相关错误
    1001: "任务不存在",
    1002: "任务状态不允许此操作",
    1003: "创建任务失败",
    1004: "更新任务失败",
    1005: "删除任务失败",
    1006: "获取任务失败",
    
    # 2xxx: 资产相关错误
    2001: "创建资产失败",
    2002: "资产不存在或更新失败",
    2003: "删除资产失败",
    2004: "标记资产不可用",
    2005: "训练资产不可用",
    2006: "标记请求失败",
    2007: "标记过程异常",
    2008: "验证资产能力失败",
    
    # 3xxx: 文件操作错误
    3001: "文件上传失败",
    3002: "文件删除失败",
    
    # 4xxx: 系统设置相关错误
    4001: "更新配置失败",
    4002: "获取配置失败",
    
    # 5xxx: 训练相关错误
    5001: "启动训练失败",
    5002: "停止训练失败",
    5003: "获取训练状态失败"
} 