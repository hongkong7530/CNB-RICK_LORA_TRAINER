import os
import uuid
from typing import Dict, List, Optional, Tuple, Any, Iterator, BinaryIO, Callable
from ..models.asset import Asset as AssetModel
from ..models.upload_file import UploadFile
from ..database import get_db
from ..utils.logger import setup_logger
from ..utils.ssh import SSHClientTool, create_ssh_client_from_asset, connection_manager, SshFileInfo
from ..utils.file_handler import calculate_md5
from ..config import config
from ..services.upload_service import UploadService
import paramiko
import socket

logger = setup_logger('terminal_service')

class TerminalService:
    @staticmethod
    def get_asset_connection_params(asset_id: int) -> Dict[str, Any]:
        """获取资产连接参数"""
        with get_db() as db:
            asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
            if not asset:
                raise ValueError(f"资产不存在: {asset_id}")
            
            # 构建连接参数
            params = {
                'hostname': asset.ip,
                'port': asset.ssh_port,
                'username': asset.ssh_username
            }
            
            # 根据认证类型设置认证参数
            if asset.ssh_auth_type == 'PASSWORD':
                params['password'] = asset.ssh_password
            else:
                params['key_path'] = asset.ssh_key_path
                
            return params
    
    @staticmethod
    def list_remote_directory(asset_id: int, remote_path: str) -> List[Dict]:
        """
        列出远程目录内容
        
        Args:
            asset_id: 资产ID
            remote_path: 远程目录路径
            
        Returns:
            List[Dict]: 文件列表
        """
        try:
            # 直接查询资产
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    logger.error(f"资产不存在: {asset_id}")
                    return []
            
            # 使用create_ssh_client_from_asset创建SSH客户端工具
            ssh_client = create_ssh_client_from_asset(asset)
            
            # 列出目录
            success, file_list, message = ssh_client.list_directory(remote_path)
            
            if not success:
                logger.error(f"列出目录失败: {message}")
                return []
            
            # 转换为字典列表
            result = []
            for file_info in file_list:
                result.append({
                    'name': file_info.name,
                    'path': file_info.path,
                    'size': file_info.size,
                    'is_dir': file_info.is_dir,
                    'permissions': file_info.permissions,
                    'modified_time': file_info.modified_time
                })
            
            return result
        except Exception as e:
            logger.error(f"列出远程目录失败: {str(e)}")
            return []
    
    @staticmethod
    def upload_to_remote(asset_id: int, file_id: int, remote_path: str) -> Tuple[bool, str]:
        """
        上传文件到远程服务器
        
        Args:
            asset_id: 资产ID
            file_id: 上传文件ID
            remote_path: 远程目录路径
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 直接查询资产
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    return False, f"资产不存在: {asset_id}"
            
            # 使用create_ssh_client_from_asset创建SSH客户端工具
            ssh_client = create_ssh_client_from_asset(asset)
            
            # 获取文件信息
            file_info = UploadService.get_file_by_id(file_id)
            if not file_info:
                return False, f"文件不存在: {file_id}"
            
            # 构建本地文件路径
            local_path = os.path.join(config.PROJECT_ROOT, file_info['storage_path'])
            
            # 构建远程文件路径
            remote_file_path = os.path.join(remote_path, file_info['filename'])
            
            # 上传文件
            success, message = ssh_client.upload_file(
                local_path=local_path,
                remote_path=remote_file_path
            )
            
            if success:
                logger.info(f"文件上传到远程服务器成功: {file_info['filename']} -> {remote_file_path}")
            else:
                logger.error(f"文件上传到远程服务器失败: {message}")
                
            return success, message
        except Exception as e:
            logger.error(f"上传文件到远程服务器失败: {str(e)}")
            return False, f"上传文件失败: {str(e)}"
    
    @staticmethod
    def download_from_remote(asset_id: int, remote_path: str) -> Tuple[bool, Dict, str]:
        """
        从远程服务器下载文件
        
        Args:
            asset_id: 资产ID
            remote_path: 远程文件路径
            
        Returns:
            Tuple[bool, Dict, str]: (成功标志, 文件信息, 消息)
        """
        try:
            # 直接查询资产
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    return False, {}, f"资产不存在: {asset_id}"
            
            # 使用create_ssh_client_from_asset创建SSH客户端工具
            ssh_client = create_ssh_client_from_asset(asset)
            
            # 生成唯一文件名
            filename = os.path.basename(remote_path)
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            timestamp = str(int(uuid.uuid1().time_low))  # 生成短时间戳
            filename_without_extension = filename.rsplit('.', 1)[0] if '.' in filename else filename
            unique_filename = f"{filename_without_extension}_{timestamp}.{file_extension}" if file_extension else f"{filename_without_extension}_{timestamp}"
            
            # 构建本地存储路径
            relative_path = os.path.join('uploads', unique_filename)
            file_path = os.path.join(config.UPLOAD_DIR, unique_filename)
            
            # 确保上传目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 下载文件
            success, message = ssh_client.download_file(
                remote_path=remote_path,
                local_path=file_path
            )
            
            if not success:
                return False, {}, message
            
            # 获取文件大小
            file_size = os.path.getsize(file_path) / 1024  # 转换为KB
            
            # 计算MD5
            md5 = calculate_md5(file_path)
            
            # 创建文件记录
            with get_db() as db:
                upload_file = UploadFile(
                    filename=filename,
                    storage_path=relative_path,
                    file_type=file_extension,
                    file_size=file_size,
                    mime_type='application/octet-stream',
                    md5=md5,
                    description=f"从资产 {asset_id} 下载的文件"
                )
                db.add(upload_file)
                db.commit()
                db.refresh(upload_file)
                
                logger.info(f"远程文件下载成功: {filename}, ID: {upload_file.id}")
                return True, upload_file.to_dict(), "文件下载成功"
                
        except Exception as e:
            logger.error(f"从远程服务器下载文件失败: {str(e)}")
            return False, {}, f"下载文件失败: {str(e)}"
    
    @staticmethod
    def stream_download_from_remote(asset_id: int, remote_path: str) -> Tuple[bool, Iterator[bytes], Dict, str]:
        """
        从远程服务器流式下载文件，直接返回文件流而不保存到本地
        
        Args:
            asset_id: 资产ID
            remote_path: 远程文件路径
            
        Returns:
            Tuple[bool, Iterator[bytes], Dict, str]: (成功标志, 文件流迭代器, 文件信息, 消息)
        """
        try:
            # 直接查询资产
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    return False, iter([]), {}, f"资产不存在: {asset_id}"
            
            # 使用create_ssh_client_from_asset创建SSH客户端工具
            ssh_client = create_ssh_client_from_asset(asset)
            
            # 创建文件流
            success, file_stream, file_info, message = ssh_client.stream_download_file(
                remote_path=remote_path
            )
            
            if not success:
                logger.error(f"创建文件流失败: {message}")
                return False, iter([]), {}, message
            
            logger.info(f"成功创建远程文件流: {remote_path}")
            return True, file_stream, file_info, "文件流创建成功"
            
        except Exception as e:
            logger.error(f"流式下载文件失败: {str(e)}")
            return False, iter([]), {}, f"流式下载文件失败: {str(e)}"
            
    @staticmethod
    def stream_upload_to_remote(
        asset_id: int, 
        remote_path: str, 
        file_obj: BinaryIO,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """
        将文件流直接上传到远程服务器
        
        Args:
            asset_id: 资产ID
            remote_path: 远程文件路径
            file_obj: 文件对象或类文件对象
            progress_callback: 进度回调函数，接收已上传字节数和总字节数
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 直接查询资产
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    return False, f"资产不存在: {asset_id}"
            
            # 使用create_ssh_client_from_asset创建SSH客户端工具
            ssh_client = create_ssh_client_from_asset(asset)
            
            # 上传文件流
            success, message = ssh_client.stream_upload_file(
                remote_path=remote_path,
                file_obj=file_obj,
                progress_callback=progress_callback
            )
            
            if success:
                logger.info(f"文件流上传成功: {remote_path}")
            else:
                logger.error(f"文件流上传失败: {message}")
                
            return success, message
            
        except Exception as e:
            logger.error(f"流式上传文件失败: {str(e)}")
            return False, f"流式上传文件失败: {str(e)}"
            
    @staticmethod
    def delete_remote_file(
        asset_id: int,
        remote_path: str
    ) -> Tuple[bool, str]:
        """
        删除远程服务器上的文件或目录
        
        Args:
            asset_id: 资产ID
            remote_path: 远程文件或目录路径
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 直接查询资产
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    return False, f"资产不存在: {asset_id}"
            
            # 使用create_ssh_client_from_asset创建SSH客户端工具
            ssh_client = create_ssh_client_from_asset(asset)
            
            # 删除文件或目录
            return ssh_client.delete_remote_file(remote_path)
        except Exception as e:
            logger.error(f"删除远程文件失败: {str(e)}")
            return False, f"删除远程文件失败: {str(e)}"
            
    @staticmethod
    def rename_remote_file(
        asset_id: int,
        old_path: str,
        new_name: str
    ) -> Tuple[bool, str]:
        """
        重命名远程服务器上的文件或目录
        
        Args:
            asset_id: 资产ID
            old_path: 原文件路径
            new_name: 新文件名（不是完整路径）
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 直接查询资产
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    return False, f"资产不存在: {asset_id}"
            
            # 使用create_ssh_client_from_asset创建SSH客户端工具
            ssh_client = create_ssh_client_from_asset(asset)
            
            # 获取目录和文件名
            parent_dir = os.path.dirname(old_path)
            if not parent_dir.endswith('/'):
                parent_dir += '/'
                
            # 构建新路径（保持在同一目录）
            new_path = os.path.join(parent_dir, new_name).replace('\\', '/')
            
            # 执行重命名操作
            success, message = ssh_client.rename_remote_file(
                old_path=old_path,
                new_path=new_path
            )
            
            if success:
                logger.info(f"文件重命名成功: {old_path} -> {new_path}")
            else:
                logger.error(f"文件重命名失败: {message}")
                
            return success, message
        except Exception as e:
            logger.error(f"重命名远程文件失败: {str(e)}")
            return False, f"重命名远程文件失败: {str(e)}"
            
    @staticmethod
    def move_remote_files(
        asset_id: int,
        source_paths: List[str],
        target_dir: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        移动远程服务器上的多个文件或目录到目标目录
        
        Args:
            asset_id: 资产ID
            source_paths: 源文件路径列表
            target_dir: 目标目录路径
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (成功标志, 操作结果)
        """
        try:
            # 直接查询资产
            with get_db() as db:
                asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    return False, {
                        'success_count': 0,
                        'failed_count': len(source_paths),
                        'total_count': len(source_paths),
                        'message': f"资产不存在: {asset_id}",
                        'details': []
                    }
            
            # 使用create_ssh_client_from_asset创建SSH客户端工具
            ssh_client = create_ssh_client_from_asset(asset)
            
            # 保存每个文件的移动结果
            results = {
                'success_count': 0,
                'failed_count': 0,
                'total_count': len(source_paths),
                'details': []
            }
            
            # 处理每个文件
            for source_path in source_paths:
                # 执行移动操作
                success, message = ssh_client.move_remote_file(
                    source_path=source_path,
                    target_dir=target_dir
                )
                
                # 记录结果
                file_result = {
                    'source_path': source_path,
                    'success': success,
                    'message': message
                }
                results['details'].append(file_result)
                
                # 更新计数
                if success:
                    results['success_count'] += 1
                    logger.info(f"文件移动成功: {source_path} -> {target_dir}")
                else:
                    results['failed_count'] += 1
                    logger.error(f"文件移动失败: {message}")
            
            # 总体操作是否成功取决于是否有文件成功移动
            overall_success = results['success_count'] > 0
            
            # 添加总结信息
            if overall_success:
                results['message'] = f"成功移动 {results['success_count']}/{results['total_count']} 个文件"
            else:
                results['message'] = "所有文件移动失败"
                
            return overall_success, results
            
        except Exception as e:
            logger.error(f"移动远程文件失败: {str(e)}")
            return False, {
                'success_count': 0,
                'failed_count': len(source_paths),
                'total_count': len(source_paths),
                'message': f"移动远程文件失败: {str(e)}",
                'details': []
            }
            
    @staticmethod
    def verify_ssh_connection(
        hostname: str,
        port: int,
        username: str,
        auth_type: str = 'PASSWORD',
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        timeout: int = 10
    ) -> Tuple[bool, str]:
        """
        验证SSH连接并将成功的连接加入到连接管理器
        
        Args:
            hostname: 主机地址
            port: SSH端口
            username: SSH用户名
            auth_type: 认证类型，'PASSWORD'或'KEY'
            password: SSH密码（认证类型为PASSWORD时使用）
            key_path: SSH密钥路径（认证类型为KEY时使用）
            timeout: 超时时间（秒）
        
        Returns:
            Tuple[bool, str]: (连接是否成功, 消息)
        """
        try:
            # 首先检查网络连通性
            logger.debug(f"检查网络连通性: {hostname}:{port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            try:
                sock.connect((hostname, int(port)))
                logger.debug(f"网络连通性检查通过: {hostname}:{port}")
            except socket.timeout:
                logger.error(f"连接超时: {hostname}:{port}")
                return False, f"网络连接超时，无法连接到 {hostname}:{port}"
            except ConnectionRefusedError:
                logger.error(f"连接被拒绝: {hostname}:{port}")
                return False, f"连接被拒绝，目标服务器 {hostname}:{port} 未开放SSH服务"
            except socket.gaierror:
                logger.error(f"无法解析主机名: {hostname}")
                return False, f"无法解析主机名 {hostname}，请检查主机名或IP地址是否正确"
            except Exception as e:
                logger.error(f"网络连通性检查失败: {hostname}:{port}, 错误: {str(e)}")
                return False, f"网络连接问题: {str(e)}"
            finally:
                sock.close()
            
            # 准备连接参数
            connect_params = {
                'hostname': hostname,
                'port': int(port),
                'username': username,
                'timeout': timeout
            }
            
            # 根据认证类型设置认证参数
            if auth_type == 'PASSWORD':
                if not password:
                    return False, "密码认证方式下必须提供密码"
                connect_params['password'] = password
            else:
                if not key_path:
                    return False, "密钥认证方式下必须提供密钥路径"
                connect_params['key_filename'] = key_path
                
            logger.debug(f"尝试SSH连接: {hostname}:{port}")
            
            # 使用连接管理器获取或创建连接
            ssh = connection_manager.get_connection(**connect_params)
            
            # 执行简单命令测试连接
            stdin, stdout, stderr = ssh.exec_command('echo "SSH connection test"')
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error = stderr.read().decode().strip()
                return False, f"SSH命令执行失败: {error}"
                
            logger.info(f"SSH连接成功: {hostname}:{port}")
            return True, "SSH连接验证成功"
            
        except paramiko.AuthenticationException as e:
            return False, "SSH认证失败，请检查用户名和密码/密钥"
            
        except paramiko.SSHException as e:
            logger.error(f"SSH连接异常: {str(e)}")
            return False, f"SSH连接异常: {str(e)}"
            
        except Exception as e:
            logger.error(f"SSH连接失败: {str(e)}")
            return False, f"SSH连接失败: {str(e)}"
            
    @staticmethod
    def verify_asset_ssh_connection(asset: Any) -> Tuple[bool, str]:
        """
        验证资产的SSH连接
        
        Args:
            asset: 资产对象（需包含SSH连接相关字段）
            
        Returns:
            Tuple[bool, str]: (连接是否成功, 消息)
        """
        try:
            # 从资产对象创建SSH客户端工具
            ssh_client = create_ssh_client_from_asset(asset)
            
            # 执行简单命令测试连接
            result = ssh_client.execute_command('echo "SSH connection test"')
            
            if result.returncode != 0:
                return False, f"SSH命令执行失败: {result.stderr}"
                
            logger.info(f"SSH连接成功: {asset.ip}:{asset.ssh_port}")
            return True, "SSH连接验证成功"
            
        except paramiko.AuthenticationException as e:
            return False, "SSH认证失败，请检查用户名和密码/密钥"
            
        except paramiko.SSHException as e:
            logger.error(f"SSH连接异常: {str(e)}")
            return False, f"SSH连接异常: {str(e)}"
            
        except Exception as e:
            logger.error(f"验证资产SSH连接失败: {str(e)}")
            return False, f"验证资产SSH连接失败: {str(e)}"