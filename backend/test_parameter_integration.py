#!/usr/bin/env python3
"""
前后端参数对接测试脚本
用于验证新增的LORA训练参数是否能够正确传递和处理
"""

import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.config_service import ConfigService
from app.services.task_services.training_service import TrainingService

def test_parameter_normalization():
    """测试参数类型规范化功能"""
    print("=" * 50)
    print("测试参数类型规范化功能")
    print("=" * 50)
    
    # 模拟前端发送的数据（字符串形式）
    frontend_data = {
        'gradient_checkpointing': 'true',
        'gradient_accumulation_steps': '1',
        'network_dim': '32',
        'network_alpha': '32',
        'learning_rate': '0.0001',
        'multires_noise_iterations': '6',
        'multires_noise_discount': '0.3',
        'lycoris_preset': 'LoCoN',
        'conv_dim': '32',
        'network_dropout': '0.1',
        'd_coef': '1.0',
        'flow_weighting_scheme': 'sigma_sqrt',
        't5xxl_max_token_length': '512',
        'apply_t5_attn_mask': 'true'
    }
    
    print("前端输入数据:")
    for key, value in frontend_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # 进行类型规范化
    normalized = ConfigService.normalize_config_types(frontend_data)
    
    print("\n规范化后数据:")
    for key, value in normalized.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # 验证结果
    assert normalized['gradient_checkpointing'] == True
    assert normalized['gradient_accumulation_steps'] == 1
    assert normalized['network_dim'] == 32
    assert normalized['learning_rate'] == 0.0001
    assert normalized['multires_noise_iterations'] == 6
    assert normalized['apply_t5_attn_mask'] == True
    
    print("\n✅ 参数类型规范化测试通过!")

def test_parameter_validation():
    """测试参数验证功能"""
    print("\n" + "=" * 50)
    print("测试参数验证功能")
    print("=" * 50)
    
    # 测试有效参数
    valid_config = {
        'network_dim': 64,
        'network_alpha': 32,
        'learning_rate': 0.001,
        'network_dropout': 0.1,
        'caption_dropout_rate': 0.05,
        'multires_noise_iterations': 6,
        'd_coef': 1.5
    }
    
    print("有效配置输入:")
    for key, value in valid_config.items():
        print(f"  {key}: {value}")
    
    validated = ConfigService.validate_training_config(valid_config)
    
    print("\n验证后配置:")
    for key, value in validated.items():
        print(f"  {key}: {value}")
    
    # 测试无效参数（超出范围）
    invalid_config = {
        'network_dim': 1000,  # 超出最大值
        'learning_rate': 0.00001,  # 小于最小值
        'network_dropout': 1.5,  # 超出范围
        'multires_noise_iterations': -1,  # 负值
    }
    
    print("\n无效配置输入:")
    for key, value in invalid_config.items():
        print(f"  {key}: {value}")
    
    validated_invalid = ConfigService.validate_training_config(invalid_config)
    
    print("\n验证并修正后:")
    for key, value in validated_invalid.items():
        print(f"  {key}: {value}")
    
    # 验证修正结果
    assert validated_invalid['network_dim'] == 512  # 应该被限制为最大值
    assert validated_invalid['learning_rate'] == 0.0001  # 应该被修正为最小值
    assert validated_invalid['network_dropout'] == 0.9  # 应该被限制为最大值
    assert validated_invalid['multires_noise_iterations'] == 0  # 应该被修正为最小值
    
    print("\n✅ 参数验证测试通过!")

def test_training_config_conversion():
    """测试训练配置转换功能"""
    print("\n" + "=" * 50)
    print("测试训练配置转换功能")
    print("=" * 50)
    
    # 模拟完整的训练配置
    full_config = {
        'model_train_type': 'flux-lora',
        'flux_model_path': '/path/to/flux/model.safetensors',
        'network_module': 'networks.lora_flux',
        'network_dim': 32,
        'network_alpha': 32,
        'learning_rate': 0.0001,
        'lycoris_preset': 'LoCoN',
        'conv_dim': 32,
        'conv_alpha': 32,
        'optimizer_type': 'Prodigy',
        'd_coef': 1.0,
        'multires_noise_iterations': 6,
        'multires_noise_discount': 0.3,
        'flow_weighting_scheme': 'sigma_sqrt',
        't5xxl_max_token_length': 512,
        'apply_t5_attn_mask': True,
        'color_aug': True,
        'flip_aug': False,
        'generate_preview': True,
        'use_image_tags': True,
        'repeat_num': 12
    }
    
    print("完整配置输入:")
    for key, value in full_config.items():
        print(f"  {key}: {value}")
    
    # 进行配置转换
    converted = TrainingService._convert_training_config(full_config)
    
    print("\n转换后配置:")
    for key, value in converted.items():
        print(f"  {key}: {value}")
    
    # 验证LyCORIS配置转换
    assert converted.get('network_module') == 'lycoris.kohya'
    assert 'lycoris_preset' not in converted  # 应该被移除
    assert converted.get('conv_dim') == 32  # 应该保留
    
    # 验证Prodigy优化器配置
    assert converted.get('optimizer_type') == 'Prodigy'
    assert converted.get('d_coef') == 1.0
    
    # 验证FLUX特定参数保留
    assert converted.get('flow_weighting_scheme') == 'sigma_sqrt'
    assert converted.get('t5xxl_max_token_length') == 512
    
    # 验证数据增强参数
    assert converted.get('color_aug') == True
    
    # 验证业务参数被移除
    assert 'use_image_tags' not in converted
    assert 'repeat_num' not in converted
    assert 'generate_preview' not in converted
    
    print("\n✅ 训练配置转换测试通过!")

def test_frontend_backend_defaults_consistency():
    """测试前后端默认值一致性"""
    print("\n" + "=" * 50)
    print("测试前后端默认值一致性")
    print("=" * 50)
    
    # 模拟从config.py获取的后端默认值
    from app.config import Config
    backend_defaults = Config.LORA_TRAINING_CONFIG
    
    # 关键参数的默认值检查
    critical_params = {
        'gradient_checkpointing': True,
        'gradient_accumulation_steps': 1,
        'network_dim': 32,
        'network_alpha': 32,
        'mixed_precision': 'bf16',
        'save_precision': 'fp16',
        'optimizer_type': 'AdamW8bit',
        'lr_scheduler': 'cosine_with_restarts'
    }
    
    print("检查关键参数默认值:")
    inconsistencies = []
    
    for param, expected_value in critical_params.items():
        backend_value = backend_defaults.get(param)
        if backend_value != expected_value:
            inconsistencies.append((param, expected_value, backend_value))
            print(f"  ❌ {param}: 期望 {expected_value}, 后端 {backend_value}")
        else:
            print(f"  ✅ {param}: {backend_value}")
    
    if inconsistencies:
        print(f"\n⚠️  发现 {len(inconsistencies)} 个默认值不一致!")
        for param, expected, actual in inconsistencies:
            print(f"    {param}: 期望 {expected}, 实际 {actual}")
    else:
        print("\n✅ 前后端默认值一致性检查通过!")

def main():
    """主测试函数"""
    print("🚀 开始前后端参数对接测试")
    print("=" * 60)
    
    try:
        # 运行所有测试
        test_parameter_normalization()
        test_parameter_validation()
        test_training_config_conversion()
        test_frontend_backend_defaults_consistency()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过! 前后端参数对接正常工作")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()