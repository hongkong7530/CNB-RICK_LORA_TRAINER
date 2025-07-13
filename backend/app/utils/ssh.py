import paramiko
import os
import stat
import io
import time
from typing import Tuple, Optional, NamedTuple, BinaryIO, List, Dict, Iterator, Callable
from ..config import config
from .logger import setup_logger
import paramiko
import threading
import select
import json

logger = setup_logger('ssh')

# 添加SSH连接缓存管理器
class SSHConnectionManager:
    """SSH连接缓存管理器，用于复用SSH连接"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
            return cls._instance
    
    def _init(self):
        self._connections = {}  # 存储SSH连接的字典
        self._last_used = {}    # 记录连接最后使用时间
        self._lock = threading.Lock()
        self._cleanup_interval = 300  # 清理间隔（秒）
        self._connection_timeout = 600  # 连接超时时间（秒）
        
        # 启动清理线程
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """启动定期清理过期连接的线程"""
        def cleanup_task():
            while True:
                time.sleep(self._cleanup_interval)
                self._cleanup_expired_connections()
        
        t = threading.Thread(target=cleanup_task)
        t.daemon = True
        t.start()
    
    def _cleanup_expired_connections(self):
        """清理过期的连接"""
        current_time = time.time()
        with self._lock:
            expired_keys = []
            for key, last_used in self._last_used.items():
                if current_time - last_used > self._connection_timeout:
                    expired_keys.append(key)
            
            for key in expired_keys:
                try:
                    logger.info(f"关闭过期连接: {key}")
                    self._connections[key].close()
                except Exception as e:
                    logger.error(f"关闭过期连接出错: {e}")
                finally:
                    del self._connections[key]
                    del self._last_used[key]
    
    def _get_connection_key(self, hostname, port, username, key_filename=None, password=None):
        """生成连接的唯一键"""
        auth_type = 'key' if key_filename else 'password'
        auth_value = key_filename if key_filename else '***'  # 不存储实际密码
        return f"{hostname}:{port}:{username}:{auth_type}:{auth_value}"
    
    def get_connection(self, hostname, port, username, key_filename=None, 
                      password=None, timeout=10):
        """获取SSH连接，如果缓存中存在则复用，否则创建新连接"""
        conn_key = self._get_connection_key(hostname, port, username, key_filename, password)
        
        with self._lock:
            # 检查是否有缓存的连接
            if conn_key in self._connections:
                ssh = self._connections[conn_key]
                try:
                    # 检查连接是否仍然活跃 - 改进检测方法
                    transport = ssh.get_transport()
                    if transport is None or not transport.is_active():
                        logger.warning(f"连接已失效 (transport inactive): {hostname}:{port}")
                        raise Exception("SSH transport not active")
                    
                    # 添加更可靠的检测：发送简单命令测试连接
                    try:
                        # 设置较短的超时时间，避免卡住
                        chan = transport.open_session()
                        chan.settimeout(3)
                        chan.exec_command('echo ping')
                        exit_status = chan.recv_exit_status()
                        chan.close()
                        if exit_status != 0:
                            raise Exception("SSH command test failed")
                    except Exception as cmd_err:
                        logger.warning(f"SSH连接测试失败: {hostname}:{port} - {str(cmd_err)}")
                        raise Exception(f"SSH connection test failed: {str(cmd_err)}")
                    
                    # 连接正常
                    logger.debug(f"复用SSH连接: {hostname}:{port}")
                    self._last_used[conn_key] = time.time()
                    return ssh
                except Exception as e:
                    logger.warning(f"缓存的连接已失效，将建立新连接: {str(e)}")
                    # 尝试关闭失效的连接
                    try:
                        ssh.close()
                    except:
                        pass
                    # 连接已失效，删除
                    del self._connections[conn_key]
                    del self._last_used[conn_key]
            
            # 创建新连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                connect_kwargs = {
                    'hostname': hostname,
                    'port': port,
                    'username': username,
                    'timeout': timeout,
                    'banner_timeout': 10,  # 设置banner超时
                    'auth_timeout': 15     # 设置认证超时
                }
                
                if password:
                    connect_kwargs['password'] = password
                elif key_filename:
                    connect_kwargs['key_filename'] = key_filename
                
                # 添加TCP连接保活选项
                connect_kwargs['disabled_algorithms'] = {'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512']}
                
                ssh.connect(**connect_kwargs)
                
                # 设置传输层keepalive
                if ssh.get_transport():
                    ssh.get_transport().set_keepalive(30)  # 每30秒发送一个keepalive包
                
                # 缓存连接
                self._connections[conn_key] = ssh
                self._last_used[conn_key] = time.time()
                logger.debug(f"创建新SSH连接: {hostname}:{port}")
                return ssh
            except Exception as e:
                logger.error(f"建立SSH连接失败: {str(e)}")
                try:
                    ssh.close()
                except:
                    pass
                raise
    
    def close_connection(self, hostname, port, username, key_filename=None, password=None):
        """关闭指定的连接"""
        conn_key = self._get_connection_key(hostname, port, username, key_filename, password)
        
        with self._lock:
            if conn_key in self._connections:
                try:
                    self._connections[conn_key].close()
                except Exception as e:
                    logger.error(f"关闭SSH连接出错: {e}")
                finally:
                    del self._connections[conn_key]
                    del self._last_used[conn_key]
                    logger.debug(f"已关闭SSH连接: {hostname}:{port}")
    
    def close_all_connections(self):
        """关闭所有连接"""
        with self._lock:
            for key, ssh in list(self._connections.items()):
                try:
                    ssh.close()
                except Exception as e:
                    logger.error(f"关闭SSH连接出错: {e}")
                finally:
                    del self._connections[key]
                    del self._last_used[key]
            logger.debug("已关闭所有SSH连接")

# 创建全局连接管理器实例
connection_manager = SSHConnectionManager()

class CommandResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str

class SshFileInfo(NamedTuple):
    name: str
    path: str
    size: int
    is_dir: bool
    permissions: str
    modified_time: str

class SSHRealTimeClient:
    """SSH客户端类，处理SSH连接和交互"""

    def __init__(self, hostname, port, username, password=None, key_filename=None, timeout=10):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.timeout = timeout
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.chan = None
        self.running = False
        self.ws = None
        self._keepalive_thread = None
        self._keepalive_interval = 30  # 30秒发送一次保活包

    def connect(self):
        """建立SSH连接"""
        try:
            connect_kwargs = {
                'hostname': self.hostname,
                'port': self.port,
                'username': self.username,
                'timeout': self.timeout,
                'banner_timeout': 10,
                'auth_timeout': 15,
                'disabled_algorithms': {'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512']}
            }

            if self.password:
                connect_kwargs['password'] = self.password
            elif self.key_filename:
                connect_kwargs['key_filename'] = self.key_filename

            self.client.connect(**connect_kwargs)
            
            # 设置传输层keepalive
            if self.client.get_transport():
                self.client.get_transport().set_keepalive(self._keepalive_interval)
            
            self.chan = self.client.invoke_shell(term='xterm')
            self.chan.settimeout(0.0)
            
            # 启动保活线程
            self._start_keepalive_thread()
            
            return True
        except Exception as e:
            logger.error(f"SSH连接失败: {str(e)}")
            return False
            
    def _start_keepalive_thread(self):
        """启动保活线程，定期发送数据包确保连接活跃"""
        def keepalive_task():
            while self.running:
                try:
                    # 如果连接不活跃，不继续发送
                    if not self.is_active():
                        break
                    
                    # 发送空命令保持连接活跃
                    if self.chan:
                        self.chan.send("\n")
                        logger.debug(f"发送SSH保活包: {self.hostname}:{self.port}")
                except Exception as e:
                    logger.warning(f"SSH保活失败: {str(e)}")
                    break
                    
                # 等待下一次发送
                time.sleep(self._keepalive_interval)
        
        # 停止旧线程（如果有）
        if self._keepalive_thread and self._keepalive_thread.is_alive():
            self.running = False
            self._keepalive_thread.join(2)
            
        # 启动新线程
        self.running = True
        self._keepalive_thread = threading.Thread(target=keepalive_task, daemon=True)
        self._keepalive_thread.start()
        
    def is_active(self):
        """检查SSH连接是否活跃"""
        try:
            transport = self.client.get_transport() if self.client else None
            if transport is None or not transport.is_active():
                return False
                
            # 检查终端通道
            if self.chan is None or self.chan.closed:
                return False
                
            return True
        except Exception:
            return False

    def set_ws(self, ws):
        """设置WebSocket连接"""
        self.ws = ws

    def resize_pty(self, cols, rows):
        """调整终端大小"""
        if self.chan:
            self.chan.resize_pty(width=cols, height=rows)

    def start_reading(self):
        """开始读取SSH输出"""
        self.running = True
        t = threading.Thread(target=self._read_output)
        t.daemon = True
        t.start()
        # 确保保活线程已启动
        if not self._keepalive_thread or not self._keepalive_thread.is_alive():
            self._start_keepalive_thread()

    def _read_output(self):
        """读取SSH输出并发送到WebSocket"""
        while self.running and self.chan:
            try:
                if not self.is_active():
                    logger.warning("SSH连接已断开，停止读取")
                    self.running = False
                    break
                    
                r, w, e = select.select([self.chan], [], [], 0.1)
                if self.chan in r:
                    data = self.chan.recv(1024)
                    if not data:
                        self.running = False
                        break
                    if self.ws:
                        self.ws.send(json.dumps({
                            'type': 'data',
                            'data': data.decode('utf-8', errors='replace')
                        }))
            except Exception as e:
                logger.error(f"读取SSH输出错误: {str(e)}")
                self.running = False
                break

    def write(self, data):
        """向SSH写入数据"""
        if not self.is_active():
            logger.error("SSH连接已断开，无法写入数据")
            return False
            
        if self.chan:
            try:
                self.chan.send(data)
            except Exception as e:
                logger.error(f"SSH写入错误: {str(e)}")
                return False
            return True
        return False

    def close(self):
        """关闭SSH连接"""
        self.running = False
        
        # 等待保活线程结束
        if self._keepalive_thread and self._keepalive_thread.is_alive():
            self._keepalive_thread.join(1)
            
        if self.chan:
            try:
                self.chan.close()
            except:
                pass
        try:
            self.client.close()
        except:
            pass

def close_ssh_connection_pool():
    """关闭所有SSH连接"""
    connection_manager.close_all_connections()



class SSHClientTool:
    """
    SSH客户端工具类，封装SSH连接和操作，避免重复传入连接信息
    """
    
    def __init__(self, hostname: str, port: int, username: str, 
                key_path: Optional[str] = None, password: Optional[str] = None, 
                timeout: int = 10):
        """
        初始化SSH客户端工具
        
        Args:
            hostname: 主机地址
            port: SSH端口
            username: SSH用户名
            key_path: SSH密钥路径（可选）
            password: SSH密码（可选）
            timeout: 超时时间（秒）
        """
        self.hostname = hostname
        self.port = port
        self.username = username
        self.key_path = key_path
        self.password = password
        self.timeout = timeout
    
    def get_connection(self):
        """
        获取SSH连接
        
        Returns:
            paramiko.SSHClient: SSH客户端对象
        """
        return connection_manager.get_connection(
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            key_filename=self.key_path,
            password=self.password,
            timeout=self.timeout
        )
    
    def execute_command(self, command: str) -> CommandResult:
        """
        执行SSH命令
        
        Args:
            command: 要执行的命令
        
        Returns:
            CommandResult: 包含返回码、标准输出和标准错误的元组
        """
        try:
            # 获取SSH连接
            ssh = self.get_connection()
            
            # 执行命令
            stdin, stdout, stderr = ssh.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            
            return CommandResult(
                returncode=exit_status,
                stdout=stdout.read().decode('utf-8').strip(),
                stderr=stderr.read().decode('utf-8').strip()
            )
            
        except Exception as e:
            logger.error(f"执行命令失败: {str(e)}")
            return CommandResult(
                returncode=1,
                stdout='',
                stderr=str(e)
            )
    
    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """
        上传文件到远程服务器
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
        
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 获取SSH连接
            ssh = self.get_connection()
            
            # 创建SFTP客户端
            sftp = ssh.open_sftp()
            
            # 上传文件
            sftp.put(local_path, remote_path)
            
            # 关闭SFTP会话（不关闭SSH连接）
            sftp.close()
            
            return True, f"文件上传成功: {remote_path}"
            
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return False, f"文件上传失败: {str(e)}"
    
    def download_file(self, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """
        从远程服务器下载文件
        
        Args:
            remote_path: 远程文件路径
            local_path: 本地文件路径
        
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 获取SSH连接
            ssh = self.get_connection()
            
            # 创建SFTP客户端
            sftp = ssh.open_sftp()
            
            # 下载文件
            sftp.get(remote_path, local_path)
            
            # 关闭SFTP会话（不关闭SSH连接）
            sftp.close()
            
            return True, f"文件下载成功: {local_path}"
            
        except Exception as e:
            logger.error(f"文件下载失败: {str(e)}")
            return False, f"文件下载失败: {str(e)}"
    
    def delete_remote_file(self, remote_path: str) -> Tuple[bool, str]:
        """
        删除远程服务器上的文件或目录
        
        Args:
            remote_path: 远程文件或目录路径
        
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 获取SSH连接
            ssh = self.get_connection()
            
            # 创建SFTP客户端
            sftp = ssh.open_sftp()
            
            # 检查文件/目录是否存在
            try:
                file_attr = sftp.stat(remote_path)
                is_dir = stat.S_ISDIR(file_attr.st_mode)
            except FileNotFoundError:
                sftp.close()
                return False, f"文件或目录不存在: {remote_path}"
            
            # 如果是目录
            if is_dir:
                # 如果是目录，递归删除
                try:
                    # 先删除目录中的所有文件
                    rm_cmd = f"rm -rf {remote_path}"
                    stdin, stdout, stderr = ssh.exec_command(rm_cmd)
                    exit_status = stdout.channel.recv_exit_status()
                    
                    if exit_status != 0:
                        sftp.close()
                        return False, f"删除目录失败: {stderr.read().decode('utf-8')}"
                except Exception as e:
                    sftp.close()
                    return False, f"删除目录失败: {str(e)}"
            else:
                # 如果是文件，直接删除
                try:
                    sftp.remove(remote_path)
                except Exception as e:
                    sftp.close()
                    return False, f"删除文件失败: {str(e)}"
            
            # 关闭SFTP会话（不关闭SSH连接）
            sftp.close()
            return True, f"删除成功: {remote_path}"
            
        except Exception as e:
            logger.error(f"删除远程文件失败: {str(e)}")
            return False, f"删除远程文件失败: {str(e)}"
    
    def list_directory(self, remote_path: str) -> Tuple[bool, List[SshFileInfo], str]:
        """
        列出远程目录内容
        
        Args:
            remote_path: 远程目录路径
        
        Returns:
            Tuple[bool, List[SshFileInfo], str]: (成功标志, 文件列表, 消息)
        """
        try:
            # 获取SSH连接
            ssh = self.get_connection()
            
            # 创建SFTP客户端
            sftp = ssh.open_sftp()
            
            # 获取目录列表
            file_list = []
            for attr in sftp.listdir_attr(remote_path):
                # 构建完整路径
                full_path = os.path.join(remote_path, attr.filename).replace('\\', '/')
                
                # 判断是否为目录
                is_dir = stat.S_ISDIR(attr.st_mode)
                
                # 获取权限字符串
                permission_str = ''
                permission_str += 'd' if is_dir else '-'
                permission_str += 'r' if attr.st_mode & stat.S_IRUSR else '-'
                permission_str += 'w' if attr.st_mode & stat.S_IWUSR else '-'
                permission_str += 'x' if attr.st_mode & stat.S_IXUSR else '-'
                permission_str += 'r' if attr.st_mode & stat.S_IRGRP else '-'
                permission_str += 'w' if attr.st_mode & stat.S_IWGRP else '-'
                permission_str += 'x' if attr.st_mode & stat.S_IXGRP else '-'
                permission_str += 'r' if attr.st_mode & stat.S_IROTH else '-'
                permission_str += 'w' if attr.st_mode & stat.S_IWOTH else '-'
                permission_str += 'x' if attr.st_mode & stat.S_IXOTH else '-'
                
                # 创建文件信息对象
                file_info = SshFileInfo(
                    name=attr.filename,
                    path=full_path,
                    size=attr.st_size,
                    is_dir=is_dir,
                    permissions=permission_str,
                    modified_time=str(attr.st_mtime)
                )
                
                file_list.append(file_info)
            
            # 关闭SFTP会话（不关闭SSH连接）
            sftp.close()
            
            return True, file_list, "目录列表获取成功"
            
        except Exception as e:
            logger.error(f"获取目录列表失败: {str(e)}")
            return False, [], f"获取目录列表失败: {str(e)}"
    
    def mkdir(self, remote_path: str, recursive: bool = True) -> Tuple[bool, str]:
        """
        创建远程目录
        
        Args:
            remote_path: 远程目录路径
            recursive: 是否递归创建父目录
        
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            if recursive:
                # 使用命令行创建目录（支持递归创建）
                cmd = f"mkdir -p {remote_path}"
                result = self.execute_command(cmd)
                
                if result.returncode != 0:
                    return False, f"创建目录失败: {result.stderr}"
            else:
                # 使用SFTP创建单层目录
                ssh = self.get_connection()
                sftp = ssh.open_sftp()
                
                try:
                    sftp.mkdir(remote_path)
                except Exception as e:
                    sftp.close()
                    return False, f"创建目录失败: {str(e)}"
                
                sftp.close()
            
            return True, f"目录创建成功: {remote_path}"
            
        except Exception as e:
            logger.error(f"创建远程目录失败: {str(e)}")
            return False, f"创建远程目录失败: {str(e)}"
    
    def copy_remote_file(self, source_path: str, target_path: str) -> Tuple[bool, str]:
        """
        在远程服务器上复制文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
        
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 使用cp命令复制文件
            cmd = f"cp -r {source_path} {target_path}"
            result = self.execute_command(cmd)
            
            if result.returncode != 0:
                return False, f"复制文件失败: {result.stderr}"
            
            return True, f"文件复制成功: {source_path} -> {target_path}"
            
        except Exception as e:
            logger.error(f"复制远程文件失败: {str(e)}")
            return False, f"复制远程文件失败: {str(e)}"
    
    def rename_remote_file(self, old_path: str, new_path: str) -> Tuple[bool, str]:
        """
        重命名远程服务器上的文件或目录
        
        Args:
            old_path: 原文件路径
            new_path: 新文件路径
        
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 获取SSH连接
            ssh = self.get_connection()
            sftp = ssh.open_sftp()
            
            # 检查原文件是否存在
            try:
                sftp.stat(old_path)
            except FileNotFoundError:
                sftp.close()
                return False, f"文件或目录不存在: {old_path}"
                
            # 执行重命名操作
            try:
                sftp.rename(old_path, new_path)
                sftp.close()
                return True, f"重命名成功: {old_path} -> {new_path}"
            except Exception as e:
                sftp.close()
                return False, f"重命名失败: {str(e)}"
                
        except Exception as e:
            logger.error(f"重命名远程文件失败: {str(e)}")
            return False, f"重命名远程文件失败: {str(e)}"
    
    def move_remote_file(self, source_path: str, target_dir: str) -> Tuple[bool, str]:
        """
        移动远程服务器上的文件或目录到目标目录
        
        Args:
            source_path: 源文件路径
            target_dir: 目标目录路径
        
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 获取SSH连接
            ssh = self.get_connection()
            sftp = ssh.open_sftp()
            
            # 检查源文件是否存在
            try:
                sftp.stat(source_path)
            except FileNotFoundError:
                sftp.close()
                return False, f"源文件或目录不存在: {source_path}"
            
            # 检查目标目录是否存在
            try:
                target_stat = sftp.stat(target_dir)
                if not stat.S_ISDIR(target_stat.st_mode):
                    sftp.close()
                    return False, f"目标路径不是目录: {target_dir}"
            except FileNotFoundError:
                sftp.close()
                return False, f"目标目录不存在: {target_dir}"
                
            # 获取文件名
            filename = os.path.basename(source_path)
            
            # 构建目标文件完整路径
            if not target_dir.endswith('/'):
                target_dir += '/'
            target_path = target_dir + filename
            
            # 执行移动操作
            try:
                sftp.rename(source_path, target_path)
                sftp.close()
                return True, f"移动成功: {source_path} -> {target_path}"
            except Exception as e:
                sftp.close()
                return False, f"移动失败: {str(e)}"
                
        except Exception as e:
            logger.error(f"移动远程文件失败: {str(e)}")
            return False, f"移动远程文件失败: {str(e)}"
    
    def stream_download_file(self, remote_path: str, chunk_size: int = 8192) -> Tuple[bool, Iterator[bytes], Dict, str]:
        """
        从远程服务器流式下载文件，直接返回文件流而不保存到本地
        
        Args:
            remote_path: 远程文件路径
            chunk_size: 每次读取的块大小
        
        Returns:
            Tuple[bool, Iterator[bytes], Dict, str]: (成功标志, 文件流迭代器, 文件信息, 消息)
        """
        try:
            # 获取SSH连接
            ssh = self.get_connection()
            
            # 创建SFTP客户端
            sftp = ssh.open_sftp()
            
            # 获取文件信息
            file_stat = sftp.stat(remote_path)
            file_size = file_stat.st_size
            filename = os.path.basename(remote_path)
            
            # 打开远程文件
            remote_file = sftp.open(remote_path, 'rb')
            
            # 创建文件信息
            file_info = {
                'filename': filename,
                'size': file_size,
                'mime_type': 'application/octet-stream'  # 默认MIME类型
            }
            
            # 注意：这里需要特殊处理，因为流式传输需要保持连接打开
            # 定义流迭代器 - 在迭代完成时关闭文件和SFTP会话，但不关闭SSH连接
            def file_stream():
                try:
                    while True:
                        data = remote_file.read(chunk_size)
                        if not data:
                            break
                        yield data
                finally:
                    remote_file.close()
                    sftp.close()
            
            return True, file_stream(), file_info, "文件流创建成功"
            
        except Exception as e:
            logger.error(f"创建文件流失败: {str(e)}")
            return False, iter([]), {}, f"创建文件流失败: {str(e)}"
    
    def stream_upload_file(self, remote_path: str, file_obj: BinaryIO, progress_callback: Optional[Callable[[int, int], None]] = None) -> Tuple[bool, str]:
        """
        将文件流直接上传到远程服务器
        
        Args:
            remote_path: 远程文件路径
            file_obj: 文件对象或类文件对象
            progress_callback: 进度回调函数，接收已上传字节数和总字节数
        
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 获取SSH连接
            ssh = self.get_connection()
            
            # 创建SFTP客户端
            sftp = ssh.open_sftp()
            
            # 创建远程文件
            with sftp.open(remote_path, 'wb') as remote_file:
                chunk_size = 8192
                uploaded_bytes = 0
                
                # 读取并写入数据
                while True:
                    data = file_obj.read(chunk_size)
                    if not data:
                        break
                        
                    remote_file.write(data)
                    uploaded_bytes += len(data)
                    
                    # 调用进度回调
                    if progress_callback:
                        try:
                            # 尝试获取文件总大小
                            total_size = file_obj.seek(0, io.SEEK_END)
                            file_obj.seek(uploaded_bytes)  # 重新定位到当前位置
                            progress_callback(uploaded_bytes, total_size)
                        except (AttributeError, IOError):
                            # 如果无法获取总大小，则只传递已上传大小
                            progress_callback(uploaded_bytes, -1)
            
            # 关闭SFTP会话（不关闭SSH连接）
            sftp.close()
            
            return True, f"文件流上传成功: {remote_path}"
            
        except Exception as e:
            logger.error(f"文件流上传失败: {str(e)}")
            return False, f"文件流上传失败: {str(e)}"
    
    def upload_directory(self, local_path: str, remote_path: str, recursive: bool = True) -> Tuple[bool, str, Dict]:
        """
        上传本地目录到远程服务器
        
        Args:
            local_path: 本地目录路径
            remote_path: 远程目录路径
            recursive: 是否递归上传子目录
        
        Returns:
            Tuple[bool, str, Dict]: (成功标志, 消息, 统计信息)
        """
        stats = {
            'added': 0,      # 新增文件数
            'updated': 0,    # 更新文件数
            'unchanged': 0,  # 未变更文件数
            'failed': 0      # 失败文件数
        }
        
        try:
            # 确保远程目录存在
            mkdir_result = self.mkdir(remote_path)
            if not mkdir_result[0]:
                return False, mkdir_result[1], stats
            
            # 获取SSH连接
            ssh = self.get_connection()
            sftp = ssh.open_sftp()
            
            if recursive:
                # 递归上传目录
                for root, dirs, files in os.walk(local_path):
                    # 计算当前目录相对路径
                    rel_path = os.path.relpath(root, local_path)
                    if rel_path == '.':
                        rel_path = ''
                    
                    # 创建远程目录
                    if rel_path:
                        remote_dir = os.path.join(remote_path, rel_path).replace('\\', '/')
                        try:
                            self.mkdir(remote_dir)
                        except Exception as e:
                            logger.error(f"创建远程目录失败: {remote_dir}, {str(e)}")
                            stats['failed'] += 1
                    
                    # 上传文件
                    for file in files:
                        local_file = os.path.join(root, file)
                        if rel_path:
                            remote_file = os.path.join(remote_path, rel_path, file).replace('\\', '/')
                        else:
                            remote_file = os.path.join(remote_path, file).replace('\\', '/')
                        
                        try:
                            # 检查远程文件是否存在
                            try:
                                remote_stat = sftp.stat(remote_file)
                                remote_size = remote_stat.st_size
                                local_size = os.path.getsize(local_file)
                                
                                # 如果大小不同，则更新文件
                                if remote_size != local_size:
                                    sftp.put(local_file, remote_file)
                                    stats['updated'] += 1
                                else:
                                    stats['unchanged'] += 1
                            except FileNotFoundError:
                                # 远程文件不存在，直接上传
                                sftp.put(local_file, remote_file)
                                stats['added'] += 1
                        except Exception as e:
                            logger.error(f"上传文件失败: {local_file} -> {remote_file}, {str(e)}")
                            stats['failed'] += 1
            else:
                # 非递归模式，只上传根目录下的文件
                for item in os.listdir(local_path):
                    local_item_path = os.path.join(local_path, item)
                    remote_item_path = os.path.join(remote_path, item).replace('\\', '/')
                    
                    # 只处理文件，跳过目录
                    if os.path.isfile(local_item_path):
                        try:
                            # 检查远程文件是否存在
                            try:
                                remote_stat = sftp.stat(remote_item_path)
                                remote_size = remote_stat.st_size
                                local_size = os.path.getsize(local_item_path)
                                
                                # 如果大小不同，则更新文件
                                if remote_size != local_size:
                                    sftp.put(local_item_path, remote_item_path)
                                    stats['updated'] += 1
                                else:
                                    stats['unchanged'] += 1
                            except FileNotFoundError:
                                # 远程文件不存在，直接上传
                                sftp.put(local_item_path, remote_item_path)
                                stats['added'] += 1
                        except Exception as e:
                            logger.error(f"上传文件失败: {local_item_path} -> {remote_item_path}, {str(e)}")
                            stats['failed'] += 1
            
            # 关闭SFTP会话
            sftp.close()
            
            summary = f"目录上传完成！新增:{stats['added']}, 更新:{stats['updated']}, 未变更:{stats['unchanged']}, 失败:{stats['failed']}"
            return True, summary, stats
            
        except Exception as e:
            logger.error(f"上传目录失败: {str(e)}")
            return False, f"上传目录失败: {str(e)}", stats
    
    def download_directory(self, remote_path: str, local_path: str, recursive: bool = True) -> Tuple[bool, str, Dict]:
        """
        从远程服务器下载目录
        
        Args:
            remote_path: 远程目录路径
            local_path: 本地目录路径
            recursive: 是否递归下载子目录
        
        Returns:
            Tuple[bool, str, Dict]: (成功标志, 消息, 统计信息)
        """
        stats = {
            'added': 0,      # 新增文件数
            'updated': 0,    # 更新文件数
            'unchanged': 0,  # 未变更文件数
            'failed': 0      # 失败文件数
        }
        
        try:
            # 确保本地目录存在
            os.makedirs(local_path, exist_ok=True)
            
            # 获取SSH连接
            ssh = self.get_connection()
            sftp = ssh.open_sftp()
            
            if recursive:
                # 递归下载目录
                def download_dir(sftp, remote_dir, local_dir):
                    try:
                        sftp.chdir(remote_dir)
                        os.makedirs(local_dir, exist_ok=True)
                        
                        for entry in sftp.listdir_attr():
                            remote_path = os.path.join(remote_dir, entry.filename).replace('\\', '/')
                            local_path = os.path.join(local_dir, entry.filename)
                            
                            if stat.S_ISDIR(entry.st_mode):
                                download_dir(sftp, remote_path, local_path)
                            else:
                                try:
                                    # 检查本地文件是否存在
                                    if os.path.exists(local_path):
                                        local_size = os.path.getsize(local_path)
                                        remote_size = entry.st_size
                                        
                                        # 如果大小不同，则更新文件
                                        if local_size != remote_size:
                                            sftp.get(remote_path, local_path)
                                            stats['updated'] += 1
                                        else:
                                            stats['unchanged'] += 1
                                    else:
                                        # 本地文件不存在，直接下载
                                        sftp.get(remote_path, local_path)
                                        stats['added'] += 1
                                except Exception as e:
                                    logger.error(f"下载文件失败: {remote_path} -> {local_path}, {str(e)}")
                                    stats['failed'] += 1
                    except Exception as e:
                        logger.error(f"下载目录失败: {remote_dir}, {str(e)}")
                        stats['failed'] += 1
                
                # 开始递归下载
                download_dir(sftp, remote_path, local_path)
            else:
                # 非递归模式，只下载根目录下的文件
                try:
                    # 列出远程目录中的文件和文件夹
                    for entry in sftp.listdir_attr(remote_path):
                        remote_item_path = os.path.join(remote_path, entry.filename).replace('\\', '/')
                        local_item_path = os.path.join(local_path, entry.filename)
                        
                        # 只处理文件，跳过目录
                        if not stat.S_ISDIR(entry.st_mode):
                            try:
                                # 检查本地文件是否存在
                                if os.path.exists(local_item_path):
                                    local_size = os.path.getsize(local_item_path)
                                    remote_size = entry.st_size
                                    
                                    # 如果大小不同，则更新文件
                                    if local_size != remote_size:
                                        sftp.get(remote_item_path, local_item_path)
                                        stats['updated'] += 1
                                    else:
                                        stats['unchanged'] += 1
                                else:
                                    # 本地文件不存在，直接下载
                                    sftp.get(remote_item_path, local_item_path)
                                    stats['added'] += 1
                            except Exception as e:
                                logger.error(f"下载文件失败: {remote_item_path} -> {local_item_path}, {str(e)}")
                                stats['failed'] += 1
                except Exception as e:
                    logger.error(f"列出远程目录失败: {remote_path}, {str(e)}")
                    stats['failed'] += 1
            
            # 关闭SFTP会话
            sftp.close()
            
            summary = f"目录下载完成！新增:{stats['added']}, 更新:{stats['updated']}, 未变更:{stats['unchanged']}, 失败:{stats['failed']}"
            return True, summary, stats
            
        except Exception as e:
            logger.error(f"下载目录失败: {str(e)}")
            return False, f"下载目录失败: {str(e)}", stats

    
    def close(self):
        """
        关闭SSH连接
        """
        try:
            connection_manager.close_connection(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                key_filename=self.key_path,
                password=self.password
            )
        except Exception as e:
            logger.error(f"关闭SSH连接失败: {str(e)}")

def create_ssh_client_from_asset(asset):
    """
    从资产对象创建SSH客户端工具
    
    Args:
        asset: 资产对象，需要包含ip、ssh_port、ssh_username、ssh_key_path、ssh_password属性
    
    Returns:
        SSHClientTool: SSH客户端工具对象
    """
    return SSHClientTool(
        hostname=asset.ip,
        port=asset.ssh_port,
        username=asset.ssh_username,
        key_path=asset.ssh_key_path,
        password=asset.ssh_password,
        timeout=30
    ) 