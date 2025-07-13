from flask import Blueprint, current_app, request, jsonify, Response, stream_with_context
from flask_sock import Sock
import paramiko
import json
import os
from ...services.asset_service import AssetService
from ...services.terminal_service import TerminalService
from ...utils.logger import setup_logger
from ...utils.response import success_json, error_json, exception_handler, response_template
from werkzeug.utils import secure_filename
from ...utils.ssh import SSHRealTimeClient
from ...config import config
import time

logger = setup_logger('terminal')
terminal_bp = Blueprint('terminal', __name__)
sock = Sock()
active_sessions = {}

@sock.route('/api/v1/terminal/<int:asset_id>')
def terminal(ws, asset_id):
    """WebSocket终端处理函数"""
    logger.info(f"新的终端连接请求，资产ID: {asset_id}")
    
    # 获取资产信息
    asset = AssetService.get_asset(asset_id)
    if not asset:
        error_msg = f'资产不存在: {asset_id}'
        logger.error(error_msg)
        ws.send(json.dumps({
            'type': 'error',
            'data': error_msg
        }))
        return

    # 初始化会话ID和SSH客户端
    session_id = None
    ssh = None
    
    # 准备SSH连接参数
    try:
        connect_params = {
            'hostname': asset.ip,
            'port': asset.ssh_port,
            'username': asset.ssh_username,
            'timeout': 10
        }

        if asset.ssh_auth_type == 'PASSWORD':
            if not asset.ssh_password:
                raise ValueError("密码认证方式下密码不能为空")
            connect_params['password'] = asset.ssh_password
        else:
            if not asset.ssh_key_path:
                raise ValueError("密钥认证方式下密钥路径不能为空")
            connect_params['key_filename'] = asset.ssh_key_path
            
        # 创建SSH客户端
        ssh = SSHRealTimeClient(**connect_params)
        
    except Exception as e:
        error_msg = f'SSH参数错误: {str(e)}'
        logger.error(error_msg)
        ws.send(json.dumps({
            'type': 'error',
            'data': error_msg
        }))
        return

    try:
        # 连接到SSH服务器
        if not ssh.connect():
            ws.send(json.dumps({
                'type': 'error',
                'data': '无法连接到SSH服务器'
            }))
            return
            
        # 设置WebSocket
        ssh.set_ws(ws)
        
        # 开始读取SSH输出
        ssh.start_reading()
        
        # 存储会话
        session_id = f"{asset_id}_{int(time.time())}"
        active_sessions[session_id] = ssh
        
        # 发送连接成功消息
        ws.send(json.dumps({
            'type': 'data',
            'data': f'已连接到 {asset.ip}\r\n'
        }))
        
        # 处理WebSocket消息
        while True:
            message = json.loads(ws.receive())
            
            if message['type'] == 'data':
                # 发送数据到SSH
                if not ssh.write(message['data']):
                    break
            elif message['type'] == 'resize':
                # 调整终端大小
                cols = message['data']['cols']
                rows = message['data']['rows']
                ssh.resize_pty(cols, rows)
                
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
    finally:
        # 清理连接
        if session_id and session_id in active_sessions:
            del active_sessions[session_id]
        if ssh:
            ssh.close()

@terminal_bp.route('/files/list/<int:asset_id>', methods=['GET'])
@exception_handler
def list_remote_files(asset_id):
    """列出远程目录文件"""
    remote_path = request.args.get('path', '/')
    
    files = TerminalService.list_remote_directory(asset_id, remote_path)
    return success_json(files)

@terminal_bp.route('/files/upload/<int:asset_id>', methods=['POST'])
@exception_handler
def upload_to_remote(asset_id):
    """上传文件到远程服务器"""
    data = request.json
    file_id = data.get('file_id')
    remote_path = data.get('remote_path', '/')
    
    if not file_id:
        return error_json(4001, "文件ID不能为空")
    
    success, message = TerminalService.upload_to_remote(asset_id, file_id, remote_path)
    
    if success:
        return success_json(None, message)
    else:
        return error_json(4002, message)

@terminal_bp.route('/files/download/<int:asset_id>', methods=['POST'])
@exception_handler
def download_from_remote(asset_id):
    """从远程服务器下载文件"""
    data = request.json
    remote_path = data.get('remote_path')
    
    if not remote_path:
        return error_json(4003, "远程文件路径不能为空")
    
    success, file_info, message = TerminalService.download_from_remote(asset_id, remote_path)
    
    if success:
        return success_json(file_info, message)
    else:
        return error_json(4004, message)

@terminal_bp.route('/files/stream-download/<int:asset_id>', methods=['POST'])
def stream_download_from_remote(asset_id):
    """从远程服务器流式下载文件，直接返回响应流"""
    try:
        data = request.json
        remote_path = data.get('remote_path')
        
        if not remote_path:
            return error_json(4003, "远程文件路径不能为空")
        
        success, file_stream, file_info, message = TerminalService.stream_download_from_remote(asset_id, remote_path)
        
        if not success:
            return error_json(4004, message)
        
        # 设置响应头
        filename = file_info.get('filename', 'download')
        headers = {
            'Content-Disposition': f'attachment; filename="{secure_filename(filename)}"',
            'Content-Type': file_info.get('mime_type', 'application/octet-stream')
        }
        
        # 返回流式响应
        return Response(
            stream_with_context(file_stream),
            headers=headers
        )
    except Exception as e:
        logger.error(f"流式下载文件失败: {str(e)}")
        return error_json(5000, f"流式下载文件失败: {str(e)}")

@terminal_bp.route('/files/stream-upload/<int:asset_id>', methods=['POST'])
def stream_upload_to_remote(asset_id):
    """将请求流直接上传到远程服务器"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return error_json(4001, "没有上传文件")
            
        file = request.files['file']
        if file.filename == '':
            return error_json(4001, "没有选择文件")
        
        # 获取远程路径
        remote_path = request.form.get('remote_path', '/')
        if not remote_path.endswith('/'):
            remote_path = remote_path + '/'
        
        # 构建完整的远程文件路径
        filename = secure_filename(file.filename)
        remote_file_path = os.path.join(remote_path, filename)
        
        # 上传文件流
        success, message = TerminalService.stream_upload_to_remote(
            asset_id=asset_id,
            remote_path=remote_file_path,
            file_obj=file
        )
        
        if success:
            return success_json(None, message)
        else:
            return error_json(4002, message)
    except Exception as e:
        logger.error(f"流式上传文件失败: {str(e)}")
        return error_json(5000, f"流式上传文件失败: {str(e)}")

@terminal_bp.route('/files/delete/<int:asset_id>', methods=['POST'])
@exception_handler
def delete_remote_file(asset_id):
    """删除远程服务器上的文件或目录"""
    try:
        remote_path = request.json.get('remote_path')
        
        if not remote_path:
            return error_json(4003, "远程文件路径不能为空")
        
        TerminalService.delete_remote_file(
            asset_id=asset_id,
            remote_path=remote_path,
        )
        return success_json(None, "删除成功")
    except Exception as e:
        logger.error(f"删除远程文件或目录失败: {str(e)}")
        return error_json(5000, f"删除远程文件或目录失败: {str(e)}")

@terminal_bp.route('/files/browse/<int:asset_id>', methods=['GET'])
@exception_handler
def browse_remote_directory(asset_id):
    """
    浏览远程目录，提供更详细的文件信息和导航功能
    """
    try:
        # 获取请求参数
        remote_path = request.args.get('path', '/')
        sort_by = request.args.get('sort_by', 'name')  # 排序字段：name, size, modified_time
        sort_order = request.args.get('sort_order', 'asc')  # 排序顺序：asc, desc
        
        # 获取文件列表
        files = TerminalService.list_remote_directory(asset_id, remote_path)
        
        # 如果目录不存在或无法访问，返回空列表
        if not files:
            return success_json({
                'path': remote_path,
                'parent_path': os.path.dirname(remote_path) if remote_path != '/' else None,
                'files': [],
                'directories': [],
                'total_files': 0,
                'total_directories': 0
            })
        
        # 分离文件和目录
        directories = [f for f in files if f.get('is_dir')]
        regular_files = [f for f in files if not f.get('is_dir')]
        
        # 排序
        def sort_key(item):
            if sort_by == 'size':
                return item.get('size', 0)
            elif sort_by == 'modified_time':
                return item.get('modified_time', '')
            else:
                return item.get('name', '').lower()
        
        directories.sort(key=sort_key, reverse=(sort_order.lower() == 'desc'))
        regular_files.sort(key=sort_key, reverse=(sort_order.lower() == 'desc'))
        
        # 计算父目录路径
        parent_path = os.path.dirname(remote_path) if remote_path != '/' else None
        
        # 构建响应
        response_data = {
            'path': remote_path,
            'parent_path': parent_path,
            'directories': directories,
            'files': regular_files,
            'total_directories': len(directories),
            'total_files': len(regular_files)
        }
        
        return success_json(response_data)
    except Exception as e:
        logger.error(f"浏览远程目录失败: {str(e)}")
        return error_json(4005, f"浏览远程目录失败: {str(e)}")

@terminal_bp.route('/files/rename/<int:asset_id>', methods=['POST'])
@exception_handler
def rename_remote_file(asset_id):
    """重命名远程服务器上的文件或目录"""
    try:
        data = request.json
        old_path = data.get('old_path')
        new_name = data.get('new_name')
        
        if not old_path:
            return error_json(4006, "原文件路径不能为空")
        
        if not new_name:
            return error_json(4007, "新文件名不能为空")
            
        # 调用服务层函数执行重命名操作
        success, message = TerminalService.rename_remote_file(
            asset_id=asset_id,
            old_path=old_path,
            new_name=new_name
        )
        
        if success:
            return success_json(None, message)
        else:
            return error_json(4008, message)
    except Exception as e:
        logger.error(f"重命名远程文件或目录失败: {str(e)}")
        return error_json(5000, f"重命名远程文件或目录失败: {str(e)}")

@terminal_bp.route('/files/move/<int:asset_id>', methods=['POST'])
@exception_handler
def move_remote_files(asset_id):
    """移动远程服务器上的一个或多个文件或目录到目标目录"""
    try:
        data = request.json
        source_paths = data.get('source_paths', [])
        target_dir = data.get('target_dir')
        
        if not source_paths:
            return error_json(4009, "源文件路径列表不能为空")
        
        if not target_dir:
            return error_json(4010, "目标目录不能为空")
            
        # 如果传入的是单个文件路径字符串，转换为列表
        if isinstance(source_paths, str):
            source_paths = [source_paths]
            
        # 调用服务层函数执行移动操作
        success, results = TerminalService.move_remote_files(
            asset_id=asset_id,
            source_paths=source_paths,
            target_dir=target_dir
        )
        
        if success:
            return success_json(results, results.get('message', '移动成功'))
        else:
            return error_json(4011, results.get('message', '移动失败'))
    except Exception as e:
        logger.error(f"移动远程文件或目录失败: {str(e)}")
        return error_json(5000, f"移动远程文件或目录失败: {str(e)}")