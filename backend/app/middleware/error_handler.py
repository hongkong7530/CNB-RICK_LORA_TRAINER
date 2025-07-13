from flask import jsonify
from werkzeug.exceptions import HTTPException
from ..utils.logger import setup_logger

logger = setup_logger('error_handler')

class ErrorHandler:
    @staticmethod
    def init_app(app):
        @app.errorhandler(Exception)
        def handle_exception(e):
            """处理所有异常"""
            if isinstance(e, HTTPException):
                response = {
                    'error': e.name,
                    'message': e.description,
                    'status_code': e.code
                }
                return jsonify(response), e.code
            
            # 处理其他异常
            logger.exception('Unhandled Exception')
            response = {
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500
            }
            return jsonify(response), 500

class ValidationError(Exception):
    """验证错误"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class NotFoundError(Exception):
    """资源不存在错误"""
    def __init__(self, message="Resource not found"):
        self.message = message
        super().__init__(self.message)

class ServiceError(Exception):
    """服务错误"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message) 