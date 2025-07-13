import socket
import platform
import os
from ..utils.logger import setup_logger

logger = setup_logger('common')

def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 使用谷歌DNS服务器地址，不需要真的连接
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"获取本地IP地址失败: {str(e)}")
        return "127.0.0.1"

def get_system_info():
    """获取系统信息"""
    system = platform.system()
    if system == "Windows":
        username = os.environ.get("USERNAME", "Administrator")
        return {
            "is_windows": True,
            "username": username
        }
    else:  # Linux/Darwin
        username = os.environ.get("USER", "root")
        return {
            "is_windows": False,
            "username": username
        }

def copy_attributes(source, target, attributes=None, ignore=None):
    """
    将源对象的属性拷贝到目标对象
    
    Args:
        source: 源对象
        target: 目标对象
        attributes: 要拷贝的属性列表，如果为None则拷贝所有属性
        ignore: 要忽略的属性列表
        
    Returns:
        拷贝后的目标对象
    """
    if ignore is None:
        ignore = []
    
    # 如果没有指定属性列表，则获取源对象的所有属性
    if attributes is None:
        if hasattr(source, '__dict__'):
            attributes = source.__dict__.keys()
        elif hasattr(source, '__slots__'):
            attributes = source.__slots__
        elif isinstance(source, dict):
            attributes = source.keys()
        else:
            attributes = [attr for attr in dir(source) if not attr.startswith('_')]
    
    # 拷贝属性
    for attr in attributes:
        # 跳过被忽略的属性
        if attr in ignore:
            continue
            
        # 获取源对象的属性值
        if isinstance(source, dict):
            if attr in source:
                value = source[attr]
            else:
                continue
        else:
            if hasattr(source, attr):
                value = getattr(source, attr)
            else:
                continue
        
        # 设置目标对象的属性值
        if isinstance(target, dict):
            target[attr] = value
        else:
            setattr(target, attr, value)
    
    return target

def generate_domain_url(hostname: str, port: int) -> tuple[str, int]:
    """
    根据主机名和端口生成域名URL
    
    Args:
        hostname: 主机名（SSH域名）
        port: 服务端口
        
    Returns:
        tuple[str, int]: 生成的域名URL和端口，如果无法解析则返回None
    """
    from ..models.constants import DOMAIN_ACCESS_CONFIG
    
    try:
        # 检查是否是SSH域名格式
        if DOMAIN_ACCESS_CONFIG['SSH_DOMAIN_SUFFIX'] in hostname:
            # 提取主机名部分（移除SSH域名后缀）
            base_hostname = hostname.replace(DOMAIN_ACCESS_CONFIG['SSH_DOMAIN_SUFFIX'], '')
            
            # 根据域名格式模板生成容器访问域名
            container_domain = DOMAIN_ACCESS_CONFIG['CONTAINER_DOMAIN_FORMAT'].format(
                hostname=base_hostname,
                port=port
            )
            
            # 添加协议前缀
            full_url = f"{DOMAIN_ACCESS_CONFIG['DEFAULT_PROTOCOL']}{container_domain}"
            
            # 根据协议确定返回端口
            return_port = 443 if DOMAIN_ACCESS_CONFIG['DEFAULT_PROTOCOL'].startswith('https') else 80
            
            return full_url, return_port
        
        return None
    except Exception as e:
        import logging
        logging.error(f"生成域名URL失败: {str(e)}")
        return None