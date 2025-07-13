#!/usr/bin/env python3
"""
参数同步检查脚本 - 比较前端期望与后端配置的差异
"""

import json
import sys
import os
import re

# 前端参数定义（从useLoraParams.js提取）
FRONTEND_PARAMETERS = {
    # 基础配置
    'model_train_type': 'flux-lora',
    'pretrained_model_name_or_path': '',
    'flux_model_path': '',
    'sd_model_path': '',
    'sdxl_model_path': '',
    'vae': '',
    'sd_vae': '',
    'sdxl_vae': '',
    'ae': '',
    'clip_l': '',
    't5xxl': '',
    'v2': False,
    'train_t5xxl': False,
    
    # 训练配置
    'train_data_dir': './input',
    'output_dir': './output',
    'output_name': 'rlt',
    'resolution': '768,768',
    'enable_bucket': True,
    'min_bucket_reso': 256,
    'max_bucket_reso': 1024,
    'bucket_reso_steps': 64,
    'bucket_no_upscale': True,
    'train_batch_size': 1,
    'max_train_epochs': 10,
    'save_every_n_epochs': 2,
    'save_model_as': 'safetensors',
    'save_precision': 'fp16',
    
    # 学习率相关
    'learning_rate': 0.0001,
    'unet_lr': 0.0001,
    'text_encoder_lr': 0.00001,
    'lr_scheduler': 'cosine_with_restarts',
    'lr_warmup_steps': 0,
    'lr_scheduler_num_cycles': 1,
    
    # 网络配置
    'network_module': 'networks.lora_flux',
    'network_dim': 32,
    'network_alpha': 32,
    'network_train_unet_only': False,
    'network_train_text_encoder_only': False,
    
    # 优化器配置
    'optimizer_type': 'AdamW8bit',
    'optimizer_args': {},
    'lr_scheduler_args': {},
    
    # 高级训练参数
    'gradient_checkpointing': True,
    'gradient_accumulation_steps': 1,
    'mixed_precision': 'bf16',
    'full_fp16': False,
    'full_bf16': False,
    'noise_offset': 0,
    'prior_loss_weight': 1,
    'loss_type': 'l2',
    'guidance_scale': 1,
    
    # FLUX专用参数
    'timestep_sampling': 'sigmoid',
    'sigmoid_scale': 1,
    'model_prediction_type': 'raw',
    'discrete_flow_shift': 1,
    'fp8_base': True,
    'sdpa': True,
    'xformers': False,
    
    # 内存优化
    'lowram': False,
    'cache_latents': True,
    'cache_latents_to_disk': True,
    'cache_text_encoder_outputs': True,
    'cache_text_encoder_outputs_to_disk': True,
    'persistent_data_loader_workers': True,
    
    # 文本处理
    'caption_extension': '.txt',
    'shuffle_caption': False,
    'keep_tokens': 0,
    'max_token_length': 255,
    'clip_skip': 2,
    'seed': 1337,
    
    # 日志配置
    'log_with': 'tensorboard',
    'logging_dir': './logs',
    
    # 重复训练
    'repeat_num': 12,
    
    # 预览图生成
    'generate_preview': True,
    'use_image_tags': True,
    'max_image_tags': 1,
    'positive_prompts': 'masterpiece, best quality, 1girl, solo',
    'negative_prompts': '(worst quality, low quality:1.4), nsfw',
    'sample_width': 768,
    'sample_height': 1024,
    'sample_cfg': 7,
    'sample_steps': 24,
    'sample_seed': 1337,
    'sample_sampler': 'euler',
    'sample_every_n_epochs': 2,
    
    # LyCORIS高级网络模块
    'lycoris_preset': None,
    'conv_dim': None,
    'conv_alpha': None,
    'decompose_both': False,
    'train_norm': False,
    'network_dropout': 0.0,
    'rank_dropout': 0.0,
    'module_dropout': 0.0,
    
    # 高级优化器参数
    'd_coef': 1.0,
    'prodigy_beta3': None,
    'prodigy_decouple': True,
    'prodigy_use_bias_correction': True,
    'prodigy_safeguard_warmup': True,
    
    # 高级噪声控制
    'min_snr_gamma': None,
    'scale_weight_norms': None,
    'caption_dropout_rate': 0.0,
    'caption_dropout_every_n_epochs': 0,
    'caption_tag_dropout_rate': 0.0,
    'multires_noise_iterations': 0,
    'multires_noise_discount': 0.0,
    'ip_noise_gamma': None,
    'ip_noise_gamma_random_strength': False,
    
    # FLUX高级参数
    'flow_weighting_scheme': 'sigma_sqrt',
    'logit_mean': 0.0,
    'logit_std': 1.0,
    'mode_scale': 1.29,
    'apply_t5_attn_mask': True,
    't5xxl_max_token_length': 512,
    
    # 块学习率控制
    'block_lr_zero_threshold': None,
    'down_lr_weight': None,
    'mid_lr_weight': None,
    'up_lr_weight': None,
    'block_dims': None,
    'block_alphas': None,
    
    # 内存优化
    'vae_batch_size': 0,
    'no_half_vae': False,
    'fp8_base_unet': False,
    
    # 数据增强
    'color_aug': False,
    'flip_aug': False,
    'random_crop': False,
    'arb_max_train_resolution': None,
}

def check_parameter_sync():
    """检查参数同步状态"""
    print("=" * 60)
    print("RLT参数同步检查")
    print("=" * 60)
    
    # 导入后端配置
    sys.path.append('/workspace/RLT/backend')
    try:
        from app.config import Config
        backend_config = Config.LORA_TRAINING_CONFIG
    except ImportError as e:
        print(f"❌ 无法导入后端配置: {e}")
        return
    
    # 比较参数
    missing_in_backend = []
    extra_in_backend = []
    type_mismatches = []
    value_mismatches = []
    
    # 检查前端参数是否在后端存在
    for param, frontend_value in FRONTEND_PARAMETERS.items():
        if param not in backend_config:
            missing_in_backend.append(param)
        else:
            backend_value = backend_config[param]
            # 检查类型匹配
            if type(frontend_value) != type(backend_value):
                type_mismatches.append((param, type(frontend_value).__name__, type(backend_value).__name__))
            # 检查默认值匹配（忽略None和空字符串的差异）
            elif frontend_value != backend_value and not (frontend_value in [None, ''] and backend_value in [None, '']):
                value_mismatches.append((param, frontend_value, backend_value))
    
    # 检查后端是否有前端没有的参数
    for param in backend_config:
        if param not in FRONTEND_PARAMETERS:
            extra_in_backend.append(param)
    
    # 输出结果
    print(f"前端参数总数: {len(FRONTEND_PARAMETERS)}")
    print(f"后端参数总数: {len(backend_config)}")
    print()
    
    if missing_in_backend:
        print(f"❌ 后端缺失参数 ({len(missing_in_backend)}个):")
        for param in missing_in_backend:
            value = FRONTEND_PARAMETERS[param]
            print(f"  '{param}': {repr(value)},")
        print()
    
    if extra_in_backend:
        print(f"⚠️  后端额外参数 ({len(extra_in_backend)}个):")
        for param in extra_in_backend:
            print(f"  {param}: {backend_config[param]}")
        print()
    
    if type_mismatches:
        print(f"⚠️  类型不匹配 ({len(type_mismatches)}个):")
        for param, frontend_type, backend_type in type_mismatches:
            print(f"  {param}: 前端={frontend_type}, 后端={backend_type}")
        print()
    
    if value_mismatches:
        print(f"⚠️  默认值不匹配 ({len(value_mismatches)}个):")
        for param, frontend_value, backend_value in value_mismatches:
            print(f"  {param}: 前端={repr(frontend_value)}, 后端={repr(backend_value)}")
        print()
    
    # 总结
    total_issues = len(missing_in_backend) + len(type_mismatches) + len(value_mismatches)
    if total_issues == 0:
        print("✅ 前后端参数完全同步!")
    else:
        print(f"🔥 发现 {total_issues} 个同步问题需要修复")
    
    return {
        'missing_in_backend': missing_in_backend,
        'extra_in_backend': extra_in_backend,
        'type_mismatches': type_mismatches,
        'value_mismatches': value_mismatches
    }

if __name__ == "__main__":
    check_parameter_sync()