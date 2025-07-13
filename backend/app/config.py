import os
from typing import Dict, List, Any

class Config:
    # 基础配置
    PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
    LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
    UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')
    MARKED_DIR = os.path.join(DATA_DIR, 'marked')
    OUTPUT_DIR = os.path.join(DATA_DIR, 'output')

    REMOTE_DATA_DIR = "/workspace/rlt_lora"
    REMOTE_UPLOAD_DIR = f'{REMOTE_DATA_DIR}/uploads'
    REMOTE_MARKED_DIR = f'{REMOTE_DATA_DIR}/marked'
    REMOTE_OUTPUT_DIR = f'{REMOTE_DATA_DIR}/output'

    # 确保必要的目录存在
    for dir_path in [DATA_DIR, LOGS_DIR, UPLOAD_DIR, MARKED_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    # 文件路径
    CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(PROJECT_ROOT, 'app.db'))
    print("DATABASE_URL:", DATABASE_URL)
    
    # 应用固定配置
    APP_CONFIG = {
        'max_concurrent_tasks': 2,
        'max_file_size': 10 * 1024 * 1024  # 10MB
    }
    
    # API配置
    API_V1_PREFIX = '/api/v1'
    
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_ENV', 'dev') == 'dev'
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 训练配置
    TRAINING_TIMEOUT = 60 * 60 * 24  # 24 hours
    MAX_RETRY_COUNT = 3
    
    # 上传文件配置
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp','json','zip','rar','7z'}  # 允许的文件类型
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 最大文件大小 (500MB)
    
    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # 系统配置
    SYSTEM_CONFIG = {
        'scheduling_minute': 5,  # 调度间隔（分钟）
        'mark_pan_dir': os.path.join(DATA_DIR, 'mark_pan'),  # 标记中间目录
        'lora_pan_upload_dir': os.path.join(DATA_DIR, 'lora_pan'),  # Lora上传中间目录
        'mark_poll_interval': 5,  # 标记轮询间隔（秒）
    }
    
    # 打标全局配置
    MARK_CONFIG = {
        'auto_crop': True,  # 是否自动裁剪图片
        'crop_ratio': '1:1',  # 默认裁剪比例
        'available_crop_ratios':['1:1', '3:2', '4:3', '2:3', '16:9', '9:16'],
        'min_confidence': 0.6,  # 自动标签最小置信度
        'max_tags': 300,  # 最大标签数量
        'trigger_words': '',  # 触发词
        'mark_algorithm': 'wd-v1-4-convnext-tagger-v2',  # 默认打标算法
        'available_algorithms': [  # 可用的打标算法列表
            'wd-vit-tagger-v3',
            'wd-swinv2-tagger-v3',
            'wd-convnext-tagger-v3',
            'wd-v1-4-moat-tagger-v2',
            'wd-v1-4-convnextv2-tagger-v2',
            'wd-v1-4-convnext-tagger-v2',
            'wd-v1-4-convnext-tagger',
            'wd-v1-4-vit-tagger-v2',
            'wd-v1-4-swinv2-tagger-v2',
            'wd-v1-4-vit-tagger',
            'joycaption2'
        ]
    }
    
    # 请求头全局配置
    HEADERS_CONFIG = {
        # Lora训练引擎请求头
        'lora_training': {
            'Content-Type': 'application/json',
            'Authorization': '',
            'User-Agent': 'LoraTrainingClient/1.0',
            'Accept': 'application/json',
            'X-API-KEY': '',
            'Connection': 'keep-alive'
        },
        # AI引擎请求头
        'ai_engine': {
            'Content-Type': 'application/json',
            'Authorization': '',
            'User-Agent': 'AIEngineClient/1.0',
            'Accept': 'application/json',
            'X-API-KEY': '',
            'Connection': 'keep-alive'
        }
    }
    
    # Lora训练全局配置
    LORA_TRAINING_CONFIG = {
        'model_train_type': 'flux-lora',
        'train_data_dir':'./input', #任务独立设置
        'output_dir': './output',   #任务独立设置
        'output_name':'rlt',   #任务独立设置
        'v2':False, # 是否使用v2模型
        'train_t5xxl':False, # 是否训练t5xxl模型
        'pretrained_model_name_or_path': '',
        'flux_model_path':'L:/ComfyUI-aki-v1.6/ComfyUI/models/unet/flux/flux1-dev-fp8.safetensors',
        'sd_model_path':'L:/ComfyUI-aki-v1.6/ComfyUI/models/checkpoints/SD1.5/majicMIX realistic 麦橘写实_v7.safetensors',
        'sdxl_model_path':'L:/ComfyUI-aki-v1.6/ComfyUI/models/checkpoints/SDXL/LEOSAM HelloWorld 新世界 _ SDXL大模型_v7.0.safetensors',
        'vae':'',
        'sd_vae':'L:/ComfyUI-aki-v1.6/ComfyUI/models/vae/vae-ft-mse-840000-ema-pruned.safetensors',
        'sdxl_vae':'L:/ComfyUI-aki-v1.6/ComfyUI/models/vae/sdxl_vae_fp16fix.safetensors',
        'ae': 'L:/ComfyUI-aki-v1.6/ComfyUI/models/vae/ae.sft',
        'clip_l': 'L:/ComfyUI-aki-v1.6/ComfyUI/models/clip/clip_l.safetensors',
        't5xxl': 'L:/ComfyUI-aki-v1.6/ComfyUI/models/clip/t5xxl_fp8_e4m3fn.safetensors',
        'timestep_sampling': 'sigmoid',
        'sigmoid_scale': 1,
        'model_prediction_type': 'raw',
        'discrete_flow_shift': 1,
        'loss_type': 'l2',
        'noise_offset': 0,
        'guidance_scale': 1,
        'prior_loss_weight': 1,
        'resolution': '768,768',
        'enable_bucket': True,
        'min_bucket_reso': 256,
        'max_bucket_reso': 1024,
        'bucket_reso_steps': 64,
        'bucket_no_upscale': True,
        'save_model_as': 'safetensors',
        'save_precision': 'fp16',
        'save_every_n_epochs': 2,
        'max_train_epochs': 10,
        'train_batch_size': 1,
        'gradient_checkpointing': False,
        'gradient_accumulation_steps': 0,
        'network_train_unet_only': False,
        'network_train_text_encoder_only': False,
        'learning_rate': 0.0001,
        'unet_lr': 0.0001,
        'text_encoder_lr': 0.00001,
        'lr_scheduler': 'cosine_with_restarts',
        'lr_warmup_steps': 0,
        'lr_scheduler_num_cycles': 1,
        'optimizer_type': 'AdamW8bit',
        'network_module': 'networks.lora_flux',
        'network_dim': 32,
        'network_alpha': 32,
        'log_with': 'tensorboard',
        'logging_dir': './logs',
        'caption_extension': '.txt',
        'shuffle_caption': False,
        'keep_tokens': 0,
        'max_token_length': 255,
        'seed': 1337,
        'clip_skip': 2,
        'mixed_precision': 'bf16',
        'full_fp16': False,
        'full_bf16': False,
        'fp8_base': True,
        'sdpa': True,
        'xformers' :False,
        'lowram': False,
        'cache_latents': True,
        'cache_latents_to_disk': True,
        'cache_text_encoder_outputs': True,
        'cache_text_encoder_outputs_to_disk': True,
        'persistent_data_loader_workers': True,
        'repeat_num':12,
        
        # 预览图生成参数（兼容旧版本）
        'generate_preview':True,            #是否生成预览图
        'use_image_tags': True,           # 是否使用图片标签生成预览图
        'max_image_tags': 1,               # 最多采用图片提示词数量
        'positive_prompts': 'masterpiece, best quality, 1girl, solo',
        'negative_prompts': '(worst quality, low quality:1.4),(depth of field, blurry:1.2),(greyscale, monochrome:1.1),3D face,cropped,lowres,text,(nsfw:1.3),(worst quality:2),(low quality:2),(normal quality:2),normal quality,((grayscale)),skin spots,acnes,skin blemishes,age spot,(ugly:1.331),(duplicate:1.331),(morbid:1.21),(mutilated:1.21),(tranny:1.331),mutated hands,(poorly drawn hands:1.5),blurry,(bad anatomy:1.21),(bad proportions:1.331),extra limbs,(disfigured:1.331),(missing arms:1.331),(extra legs:1.331),(fused fingers:1.61051),(too many fingers:1.61051),(unclear eyes:1.331),lowers,bad hands,missing fingers,extra digit,bad hands,missing fingers,(((extra arms and legs)))',
        'sample_width': 768,
        'sample_height': 1024,
        'sample_cfg': 7,
        'sample_steps': 24,
        'sample_seed': 1337,
        'sample_sampler': 'euler',
        'sample_every_n_epochs': 2,
    }
    
    # AI引擎配置
    AI_ENGINE_CONFIG = {
        'api_url': 'http://127.0.0.1:8188/api/predict',
        'timeout': 300,  # 请求超时时间（秒）
        'max_retries': 3,  # 最大重试次数
        'retry_interval': 5  # 重试间隔（秒）
    }

config = Config() 