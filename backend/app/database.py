from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .config import config
from .utils.logger import setup_logger

# 设置日志记录器
logger = setup_logger('database')

# 创建数据库引擎
# 如果是SQLite，添加check_same_thread=False参数
if config.DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        config.DATABASE_URL,
        connect_args={"check_same_thread": False}  # 允许多线程访问SQLite连接
    )
    logger.info("SQLite数据库已配置为多线程模式")
else:
    engine = create_engine(config.DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

@contextmanager
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    # 导入所有模型以确保它们被注册
    from .models import task  # noqa
    from .models import training  # noqa
    from .models import asset  # noqa
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    # 初始化本地资产
    try:
        from .services.local_asset_service import LocalAssetService
        logger.info("正在初始化本地资产...")
        local_asset = LocalAssetService.init_local_asset()
        if local_asset:
            logger.info(f"本地资产初始化成功: ID={local_asset.id}, 名称={local_asset.name}")
        else:
            logger.warning("本地资产初始化失败")
        
        # 初始化系统设置
        from .services.config_service import ConfigService
        ConfigService.init_settings()
    except Exception as e:
        logger.error(f"初始化本地资产时出错: {str(e)}", exc_info=True) 