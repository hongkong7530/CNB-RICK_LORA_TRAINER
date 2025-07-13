from flask import Blueprint, request, jsonify, send_from_directory
from ...services.upload_service import UploadService
from ...config import config
import os

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/files', methods=['POST'])
def upload_file():
    """上传文件接口"""
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
        
    # 获取文件描述
    description = request.form.get('description', '')
    
    # 保存文件
    result = UploadService.save_file(file, description)
    if result:
        return jsonify({'message': '文件上传成功', 'file': result}), 201
    else:
        return jsonify({'error': '文件上传失败'}), 500

@upload_bp.route('/files', methods=['GET'])
def get_files():
    """获取所有文件列表"""
    files = UploadService.get_all_files()
    return jsonify({'files': files})

@upload_bp.route('/files/<int:file_id>', methods=['GET'])
def get_file(file_id):
    """获取单个文件信息"""
    file = UploadService.get_file_by_id(file_id)
    if file:
        return jsonify({'file': file})
    return jsonify({'error': '文件不存在'}), 404

@upload_bp.route('/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除文件"""
    result = UploadService.delete_file(file_id)
    if result:
        return jsonify({'message': '文件删除成功'})
    return jsonify({'error': '文件删除失败'}), 404

@upload_bp.route('/files/<int:file_id>/download', methods=['GET'])
def download_file(file_id):
    """下载文件"""
    file = UploadService.get_file_by_id(file_id)
    if not file:
        return jsonify({'error': '文件不存在'}), 404
        
    # 获取文件路径
    file_dir = os.path.dirname(os.path.join(config.PROJECT_ROOT, file['storage_path']))
    filename = os.path.basename(file['storage_path'])
    
    # 设置下载文件名为原始文件名
    download_name = file['filename']
    
    return send_from_directory(
        file_dir, 
        filename, 
        as_attachment=True,
        download_name=download_name
    )

def init_app(app):
    """注册蓝图"""
    app.register_blueprint(upload_bp, url_prefix=f'{config.API_V1_PREFIX}/upload') 