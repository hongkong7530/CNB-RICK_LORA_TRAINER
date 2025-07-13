from flask import Flask, send_from_directory, send_file
from flask_cors import CORS
from .config import config
from .api.v1 import api_v1
from .utils.logger import setup_logger
from .middleware.error_handler import ErrorHandler
from .database import init_db
from .api.v1.terminal import sock  # 确保导入 sock
from .services.config_service import ConfigService  # 添加这行
from .services.task_services.scheduler_service import SchedulerService
from .utils.json_encoder import CustomJSONEncoder
from .utils.ssh import close_ssh_connection_pool
import os
import atexit

logger = setup_logger('main')

def create_app():
    """创建 Flask 应用"""
    logger.info("开始创建Flask应用...")
    app = Flask(__name__)
    
    # 基础配置
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
    # 注册自定义 JSON 编码器
    app.json_encoder = CustomJSONEncoder
    
    # 初始化数据库
    init_db()
    
    # 启用CORS
    CORS(app)
    
    # 注册错误处理
    ErrorHandler.init_app(app)
    
    # 注册 API 路由
    app.register_blueprint(api_v1)
    
    # 注册请求前处理器
    @app.before_request
    def before_request():
        # TODO: 添加认证和请求日志
        pass
    
    # 注册请求后处理器
    @app.after_request
    def after_request(response):
        # TODO: 添加响应日志
        return response
    
    # 注册 WebSocket 扩展
    sock.init_app(app)
    
    # 注册静态文件路由，用于访问data目录下的任意文件
    @app.route('/data/<path:filepath>')
    def serve_data_files(filepath):
        """处理data目录下的文件访问，包括上传的图片和打标后的文本等"""
        # 构建完整的文件路径
        full_path = os.path.join(config.DATA_DIR, filepath)
        directory, filename = os.path.split(full_path)
        
        # 检查目录是否存在
        if not os.path.exists(directory):
            logger.error(f"Directory not found: {directory}")
            return "Directory not found", 404
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            return "File not found", 404
            
        return send_from_directory(directory, filename)
    
    # 初始化任务服务和调度器
    SchedulerService.init_scheduler()
    logger.info("任务服务已启动")
    
    # 注册应用关闭处理函数
    atexit.register(close_ssh_connection_pool)
    logger.info("注册了SSH连接池关闭函数")
    
    # 定义Vue前端静态文件目录
    dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dist')
    logger.info(f"Vue前端静态文件目录: {dist_dir}")

    # 提供静态文件
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_vue_app(path):
        # 如果路径以 /api 开头，不处理（因为已经有API路由处理了）
        if path.startswith('api/'):
            return "Not found", 404
            
        # 尝试直接提供静态文件
        if path and os.path.exists(os.path.join(dist_dir, path)):
            return send_from_directory(dist_dir, path)
            
        # 否则返回index.html（SPA应用的入口点）
        try:
            return send_file(os.path.join(dist_dir, 'index.html'))
        except Exception as e:
            logger.error(f"Error serving Vue app: {str(e)}")
            return f"Error serving Vue app: {str(e)}", 500
    
    return app

app = create_app() 