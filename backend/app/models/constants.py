"""
常量定义
"""

# 常用训练参数，用户可以在任务级别配置这些参数
COMMON_TRAINING_PARAMS = {
    'max_train_epochs': '最大训练轮次',
    'train_batch_size': '批量大小',
    'network_dim': '网络维度 (Dim)',
    'network_alpha': '网络Alpha值',
    'learning_rate': '基础学习率',
    'unet_lr': 'Unet学习率',
    'text_encoder_lr': '文本编码器学习率',
    'resolution': '分辨率',
    'lr_scheduler': '学习率调度器',
    'lr_warmup_steps': '预热步数',
    'lr_scheduler_num_cycles': '学习率循环次数',
    'save_every_n_epochs': '每N轮保存一次',
    'sample_every_n_epochs': '每N轮采样一次',
    'clip_skip': 'CLIP跳过层数',
    'seed': '随机种子',
    'mixed_precision': '混合精度',
    'optimizer_type': '优化器类型',
    'repeat_num': '单张图片重复次数',
} 

# 常用标记参数，用户可以在任务级别配置这些参数
COMMON_MARK_PARAMS = {
    'resolution': '图像分辨率',
    'ratio': '图像比例',
    'max_tokens': '最大标记令牌数',
    'min_confidence': '最小置信度',
    'trigger_words': '触发词',
    'auto_crop': '自动裁剪'
}

# Flux-Lora训练特有参数
FLUX_LORA_PARAMS = {
    'model_train_type': '训练模型类型',
    'pretrained_model_name_or_path': '预训练模型路径',
    'ae': 'AutoEncoder模型路径',
    'clip_l': 'CLIP-L模型路径',
    't5xxl': 'T5XXL模型路径',
    'timestep_sampling': '时间步采样方法',
    'sigmoid_scale': 'Sigmoid缩放系数',
    'model_prediction_type': '模型预测类型',
    'discrete_flow_shift': '离散流偏移',
    'loss_type': '损失函数类型',
    'guidance_scale': '引导缩放系数',
    'prior_loss_weight': '先验损失权重',
    'enable_bucket': '启用分桶',
    'min_bucket_reso': '最小桶分辨率',
    'max_bucket_reso': '最大桶分辨率',
    'bucket_reso_steps': '桶分辨率步长',
    'bucket_no_upscale': '桶不上采样',
    'network_module': '网络模块',
    'network_train_unet_only': '仅训练UNet',
    'network_train_text_encoder_only': '仅训练文本编码器',
    'fp8_base': '使用FP8基础模型',
    'sdpa': '使用SDPA',
    'lowram': '低内存模式',
    'cache_latents': '缓存潜变量',
    'cache_latents_to_disk': '潜变量缓存到磁盘',
    'cache_text_encoder_outputs': '缓存文本编码器输出',
    'cache_text_encoder_outputs_to_disk': '文本编码器输出缓存到磁盘',
    'persistent_data_loader_workers': '持久化数据加载器工作线程',
    'gradient_checkpointing': '梯度检查点',
    'gradient_accumulation_steps': '梯度累积步数',
} 

# 域名访问模式配置
DOMAIN_ACCESS_CONFIG = {
    # 域名访问模式
    'PORT_ACCESS_MODES': {
        'DIRECT': '直连模式',  # 直接使用IP:PORT访问
        'DOMAIN': '域名模式',  # 使用域名方式访问
    },
    
    # SSH域名后缀，例如：mq1xrkw51rq0vj8w.ssh.x-gpu.com
    'SSH_DOMAIN_SUFFIX': '.ssh.x-gpu.com',
    
    # 服务容器域名格式，例如：mq1xrkw51rq0vj8w-80.container.x-gpu.com
    # 格式为：{hostname}-{port}.container.x-gpu.com
    'CONTAINER_DOMAIN_FORMAT': '{hostname}-{port}.container.x-gpu.com',
    
    # 容器域名后缀
    'CONTAINER_DOMAIN_SUFFIX': '.container.x-gpu.com',
    
    # 默认协议前缀，可以是http或https
    'DEFAULT_PROTOCOL': 'https://'
} 