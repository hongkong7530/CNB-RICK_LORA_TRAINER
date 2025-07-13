import os
import subprocess
import signal
import time
from ..utils.logger import setup_logger

logger = setup_logger('nginx_manager')

class NginxManager:
    def __init__(self, config_path=None):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.config_path = config_path or os.path.join(self.project_root, 'nginx.conf')
        self.pid_file = os.path.join(self.project_root, 'nginx.pid')
        
    def _prepare_config(self):
        """准备nginx配置文件，更新PID文件路径"""
        try:
            # 检查主配置文件是否存在
            if not os.path.exists(self.config_path):
                logger.error(f"nginx配置文件不存在: {self.config_path}")
                return False
                
            # 读取配置内容
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # 检查是否需要更新PID路径
            if '/run/nginx.pid' in config_content:
                # 更新配置中的PID文件路径
                updated_content = config_content.replace(
                    'pid /run/nginx.pid;',
                    f'pid {self.pid_file};'
                )
                
                # 写回配置文件
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                    
                logger.info(f"已更新nginx配置文件中的PID路径: {self.config_path}")
            
            logger.info(f"使用nginx主配置文件: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"准备nginx配置文件失败: {e}")
            return False
    
    def start(self):
        """启动nginx"""
        if self.is_running():
            logger.info("nginx已经在运行中")
            return True
            
        if not self._prepare_config():
            return False
            
        try:
            # 测试配置文件
            result = subprocess.run(
                ['nginx', '-t', '-c', self.config_path],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"nginx配置文件测试失败: {result.stderr}")
                return False
            
            # 启动nginx
            result = subprocess.run(
                ['nginx', '-c', self.config_path],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"nginx启动失败: {result.stderr}")
                return False
                
            logger.info("nginx启动成功")
            return True
        except Exception as e:
            logger.error(f"启动nginx时发生错误: {e}")
            return False
    
    def stop(self):
        """停止nginx"""
        if not self.is_running():
            logger.info("nginx未在运行")
            return True
            
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                
                # 等待进程结束
                for _ in range(10):
                    if not self.is_running():
                        break
                    time.sleep(0.5)
                    
                if self.is_running():
                    logger.warning("优雅停止失败，强制终止nginx")
                    os.kill(pid, signal.SIGKILL)
                    
            logger.info("nginx停止成功")
            return True
        except Exception as e:
            logger.error(f"停止nginx时发生错误: {e}")
            return False
    
    def is_running(self):
        """检查nginx是否在运行"""
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)  # 检查进程是否存在
                return True
        except (OSError, ValueError):
            # 清理无效的pid文件
            if os.path.exists(self.pid_file):
                try:
                    os.unlink(self.pid_file)
                except:
                    pass
        return False
    
    def reload(self):
        """重新加载nginx配置"""
        if not self.is_running():
            return self.start()
            
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGHUP)
                logger.info("nginx配置重新加载成功")
                return True
        except Exception as e:
            logger.error(f"重新加载nginx配置失败: {e}")
            return False