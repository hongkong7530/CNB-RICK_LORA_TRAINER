from flask import Blueprint
from .tasks import tasks_bp
from .assets import assets_bp
from .settings import settings_bp
from .terminal import terminal_bp
from .common import common_bp
from .upload import upload_bp

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# 注册路由
api_v1.register_blueprint(tasks_bp, url_prefix='/tasks')
api_v1.register_blueprint(assets_bp, url_prefix='/assets')
api_v1.register_blueprint(settings_bp, url_prefix='/settings')
api_v1.register_blueprint(terminal_bp, url_prefix='/terminal')
api_v1.register_blueprint(upload_bp, url_prefix='/upload')
api_v1.register_blueprint(common_bp, url_prefix='/common')