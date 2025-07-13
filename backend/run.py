import os
import sys
import signal
import atexit

# 添加项目根目录到 Python 路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from app.main import app
from app.config import config
from app.utils.nginx_manager import NginxManager

# 初始化nginx管理器
nginx_manager = NginxManager()
cleanup_executed = False

def cleanup_on_exit():
    """程序退出时的清理函数"""
    global cleanup_executed
    if cleanup_executed:
        return
    cleanup_executed = True
    
    print("正在停止nginx...")
    nginx_manager.stop()
    print("程序已退出")

def signal_handler(signum, frame):
    """信号处理函数"""
    print(f"\n收到信号 {signum}，正在停止服务...")
    cleanup_on_exit()
    sys.exit(0)

if __name__ == '__main__':
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 注册退出处理器
    atexit.register(cleanup_on_exit)
    
    # 启动nginx
    print("正在启动nginx...")
    if nginx_manager.start():
        print("nginx启动成功，前端服务地址: http://localhost:4059")
    else:
        print("nginx启动失败，将仅启动后端服务")
    
    # 启动Flask应用
    print(f"正在启动Flask应用，后端服务地址: http://{config.HOST}:{config.PORT}")
    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            use_reloader=config.DEBUG,
            threaded=True
        )
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_on_exit() 