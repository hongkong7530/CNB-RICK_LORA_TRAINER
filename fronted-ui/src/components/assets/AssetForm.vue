<template>
  <BaseModal 
    :modelValue="modelValue"
    @update:modelValue="$emit('update:modelValue', $event)"
    :title="isEditing ? '编辑资产' : '新建资产'"
  >
    <template #body>
      <form @submit.prevent="handleSubmit" class="asset-form">
        <div class="form-section">
          <h3 class="section-title">基本信息</h3>
          <div class="form-item">
            <label>资产名称</label>
            <input 
              v-model="assetForm.name" 
              class="mac-input"
              :class="{ 'is-error': formErrors.name }"
              @blur="validateField('name', assetForm.name)"
              :disabled="isLocalResource || isEditing"
            >
            <span class="error-message" v-if="formErrors.name">{{ formErrors.name }}</span>
          </div>
          
          <!-- 添加资产启用状态开关 -->
          <div class="form-item">
            <div class="config-switch-container">
              <label>启用资产</label>
              <switch-button v-model="assetForm.enabled" />
            </div>
            <div v-if="!assetForm.enabled" class="disabled-note">
              <InformationCircleIcon class="info-icon" />
              <span>禁用后，该资产将不会被用于训练或标记任务</span>
            </div>
          </div>
          
          <!-- 非本地资源才显示基本信息字段 -->
          <template v-if="!isLocalResource">
            <div class="form-row">
              <div class="form-item">
                <label>IP地址</label>
                <input 
                  v-model="assetForm.ip" 
                  class="mac-input"
                  :class="{ 'is-error': formErrors.ip }"
                  @blur="parseAndValidateIp"
                  placeholder="IP地址或域名，也可粘贴SSH连接字符串"
                >
                <span class="error-message" v-if="formErrors.ip">{{ formErrors.ip }}</span>
              </div>
              <div class="form-item">
                <label>SSH端口</label>
                <input 
                  v-model="assetForm.ssh_port" 
                  type="number" 
                  class="mac-input"
                  :class="{ 'is-error': formErrors.ssh_port }"
                  @blur="validateField('ssh_port', assetForm.ssh_port)"
                >
                <span class="error-message" v-if="formErrors.ssh_port">{{ formErrors.ssh_port }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-item">
                <label>SSH用户名</label>
                <input 
                  v-model="assetForm.ssh_username" 
                  class="mac-input"
                  :class="{ 'is-error': formErrors.ssh_username }"
                  @blur="validateField('ssh_username', assetForm.ssh_username)"
                >
                <span class="error-message" v-if="formErrors.ssh_username">{{ formErrors.ssh_username }}</span>
              </div>
              <div class="form-item">
                <label>认证方式</label>
                <select 
                  v-model="assetForm.ssh_auth_type" 
                  class="mac-input"
                >
                  <option value="KEY">SSH密钥</option>
                  <option value="PASSWORD">密码</option>
                </select>
              </div>
            </div>
            
            <!-- 根据认证方式显示不同的输入框 -->
            <div class="form-item ssh-auth-input">
              <template v-if="assetForm.ssh_auth_type === 'PASSWORD'">
                <label>SSH密码</label>
                <div class="input-with-button">
                  <input 
                    v-model="assetForm.ssh_password"
                    type="password"
                    class="mac-input"
                    :class="{ 'is-error': formErrors.ssh_password }"
                    @blur="validateField('ssh_password', assetForm.ssh_password)"
                  >
                  <button 
                    class="mac-btn verify-ssh-btn" 
                    :disabled="isVerifyingSsh"
                    @click="verifySshConnection"
                  >
                    <CheckCircleIcon class="btn-icon" v-if="!isVerifyingSsh" />
                    <span class="loading-spinner" v-else></span>
                    {{ isVerifyingSsh ? '验证中...' : '验证连接' }}
                  </button>
                </div>
                <span class="error-message" v-if="formErrors.ssh_password">{{ formErrors.ssh_password }}</span>
              </template>
              
              <template v-else>
                <label>SSH密钥路径</label>
                <div class="input-with-button">
                  <input 
                    v-model="assetForm.ssh_key_path"
                    class="mac-input"
                    :class="{ 'is-error': formErrors.ssh_key_path }"
                    @blur="validateField('ssh_key_path', assetForm.ssh_key_path)"
                  >
                  <button 
                    class="mac-btn verify-ssh-btn" 
                    :disabled="isVerifyingSsh"
                    @click="verifySshConnection"
                  >
                    <CheckCircleIcon class="btn-icon" v-if="!isVerifyingSsh" />
                    <span class="loading-spinner" v-else></span>
                    {{ isVerifyingSsh ? '验证中...' : '验证连接' }}
                  </button>
                </div>
                <span class="error-message" v-if="formErrors.ssh_key_path">{{ formErrors.ssh_key_path }}</span>
              </template>
            </div>
          </template>
          
          <div v-else class="local-resource-note">
            本地系统资产无需配置连接信息，可直接配置服务能力
          </div>
        </div>

        <div class="form-section">
          <div class="section-header">
            <h3 class="section-title">Lora训练能力</h3>
            <switch-button v-model="assetForm.lora_training.enabled" />
          </div>
          <div v-show="assetForm.lora_training.enabled" class="capability-form">
            <div class="form-item">
              <div class="config-switch-container">
                <label>使用全局配置</label>
                <switch-button v-model="assetForm.lora_training.use_global_config" />
              </div>
              <div v-if="assetForm.lora_training.use_global_config" class="global-config-note">
                <InformationCircleIcon class="info-icon" />
                <span>已启用全局配置，以下字段将显示全局值（不可编辑）</span>
              </div>
            </div>
            
            <div class="form-item">
              <label>服务端口</label>
              <input 
                v-model="assetForm.lora_training.port" 
                type="number" 
                class="mac-input"
                :class="{ 'is-error': formErrors.lora_port }"
                @blur="validateCapabilityField('lora_training', 'port')"
              >
              <span class="error-message" v-if="formErrors.lora_port">{{ formErrors.lora_port }}</span>
            </div>
            
            <div v-if="!assetForm.lora_training.use_global_config">
            <div class="form-item">
                <label>Headers配置</label>
                <KeyValueConfig
                  v-model="assetForm.lora_training.headers"
                  keyPlaceholder="Header名称"
                  valuePlaceholder="Header值"
                  addButtonText="添加"
                  keyRequiredMessage="请输入Header名称"
                />
            </div>
              
            <div class="form-item">
              <label>训练参数配置</label>
                <div class="training-params-form">
                  <div class="params-header">
                    <span>模型训练参数配置</span>
                    <button 
                      type="button" 
                      class="mac-btn small show-params-btn" 
                      @click="toggleShowAllParams"
                    >
                      {{ showAllParams ? '隐藏更多参数' : '显示更多参数' }}
                    </button>
                  </div>
                  
                  <LoraTrainingParams
                    v-model="trainingParams"
                    :disabled="false"
                    layout="asset"
                    :showAllParams="showAllParams"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="form-section">
          <div class="section-header">
            <h3 class="section-title">AI引擎能力</h3>
            <switch-button v-model="assetForm.ai_engine.enabled" />
          </div>
          <div v-show="assetForm.ai_engine.enabled" class="capability-form">
            <div class="form-item">
              <div class="config-switch-container">
                <label>使用全局配置</label>
                <switch-button v-model="assetForm.ai_engine.use_global_config" />
              </div>
              <div v-if="assetForm.ai_engine.use_global_config" class="global-config-note">
                <InformationCircleIcon class="info-icon" />
                <span>已启用全局配置，以下字段将显示全局值（不可编辑）</span>
              </div>
            </div>
            
            <!-- 单独一行的服务端口 -->
            <div class="form-item">
              <label>服务端口</label>
              <input 
                v-model="assetForm.ai_engine.port" 
                type="number" 
                class="mac-input"
                :class="{ 'is-error': formErrors.ai_port }"
                @blur="validateCapabilityField('ai_engine', 'port')"
              >
              <span class="error-message" v-if="formErrors.ai_port">{{ formErrors.ai_port }}</span>
            </div>
            
            <div v-if="!assetForm.ai_engine.use_global_config">
              <!-- 单独一行的Headers配置 -->
              <div class="form-item">
                <label>Headers配置</label>
                <KeyValueConfig
                  v-model="assetForm.ai_engine.headers"
                  keyPlaceholder="Header名称"
                  valuePlaceholder="Header值"
                  addButtonText="添加"
                  keyRequiredMessage="请输入Header名称"
                />
              </div>
              
              <!-- 两列布局的超时和重试次数 -->
              <div class="form-row">
                <div class="form-item">
                  <label>超时时间（秒）</label>
                  <input 
                    v-model="assetForm.ai_engine.timeout" 
                    type="number" 
                    class="mac-input"
                  >
                </div>
                <div class="form-item">
                  <label>最大重试次数</label>
                  <input 
                    v-model="assetForm.ai_engine.max_retries" 
                    type="number" 
                    class="mac-input"
                  >
                </div>
              </div>
              
              <!-- 单独一行的重试间隔 -->
              <div class="form-item">
                <label>重试间隔（秒）</label>
                <input 
                  v-model="assetForm.ai_engine.retry_interval" 
                  type="number" 
                  class="mac-input"
                >
              </div>
            </div>
          </div>
        </div>
      </form>
    </template>
    <template #footer>
      <button class="mac-btn" @click="close">取消</button>
      <button 
        type="submit" 
        class="mac-btn primary" 
        :disabled="isSubmitting"
        @click="handleSubmit"
      >
        {{ isSubmitting ? '提交中...' : '确认' }}
      </button>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, defineEmits, defineProps, computed, watch, reactive } from 'vue'
import BaseModal from '@/components/common/Modal.vue'
import SwitchButton from '@/components/common/SwitchButton.vue'
import KeyValueConfig from '@/components/common/KeyValueConfig.vue'
import LoraTrainingParams from '@/components/common/LoraTrainingParams.vue'
import { assetApi } from '@/api/asset'
import message from '@/utils/message'
import { CheckCircleIcon, InformationCircleIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  asset: {
    type: Object,
    default: () => null
  },
  isEditing: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit-success'])

// 弹窗显示控制
const close = () => {
  emit('update:modelValue', false)
}

// 表单状态
const assetForm = ref({
  name: '',
  ip: '',
  ssh_port: 22,
  ssh_username: '',
  ssh_key_path: '',
  lora_training: {
    enabled: false,
    port: 28000,
    params: {},
    headers: {
      "Authorization": "",
      "Content-Type": "application/json"
    },
    use_global_config: true,
    verified: false
  },
  ai_engine: {
    enabled: false,
    port: 8188,
    headers: {
      "Authorization": "",
      "Content-Type": "application/json"
    },
    timeout: 300,
    max_retries: 3,
    retry_interval: 5,
    use_global_config: true,
    verified: false
  },
  ssh_auth_type: 'KEY',
  ssh_password: '',
  enabled: true
})

// 表单错误信息
const formErrors = ref({})

// 提交中状态
const isSubmitting = ref(false)

// SSH验证状态
const isVerifyingSsh = ref(false)

// 添加训练参数状态
const showAllParams = ref(false)
const trainingParams = ref({
  model_train_type: '',
  pretrained_model_name_or_path: '',
  ae: '',
  clip_l: '',
  t5xxl: '',
  timestep_sampling: '',
  sigmoid_scale: '',
  model_prediction_type: '',
  discrete_flow_shift: '',
  loss_type: '',
  guidance_scale: '',
  train_data_dir: '',
  prior_loss_weight: '',
  resolution: '',
  enable_bucket: '',
  min_bucket_reso: '',
  max_bucket_reso: '',
  bucket_reso_steps: '',
  bucket_no_upscale: '',
  output_name: '',
  output_dir: '',
  save_model_as: '',
  save_precision: '',
  save_every_n_epochs: '',
  max_train_epochs: '',
  train_batch_size: '',
  gradient_checkpointing: '',
  gradient_accumulation_steps: '',
  network_train_unet_only: '',
  network_train_text_encoder_only: '',
  learning_rate: '',
  unet_lr: '',
  text_encoder_lr: '',
  lr_scheduler: '',
  lr_warmup_steps: '',
  lr_scheduler_num_cycles: '',
  optimizer_type: '',
  network_module: '',
  network_dim: '',
  network_alpha: '',
  sample_prompts: '',
  sample_sampler: '',
  sample_every_n_epochs: '',
  log_with: '',
  logging_dir: '',
  caption_extension: '',
  shuffle_caption: '',
  keep_tokens: '',
  max_token_length: '',
  seed: '',
  clip_skip: '',
  mixed_precision: '',
  full_fp16: '',
  full_bf16: '',
  fp8_base: '',
  sdpa: '',
  lowram: '',
  cache_latents: '',
  cache_latents_to_disk: '',
  cache_text_encoder_outputs: '',
  cache_text_encoder_outputs_to_disk: '',
  persistent_data_loader_workers: ''
})

// 切换显示所有参数
const toggleShowAllParams = () => {
  showAllParams.value = !showAllParams.value
}

// 重置表单
const resetForm = () => {
  assetForm.value = {
    name: '',
    ip: '',
    ssh_port: 22,
    ssh_username: '',
    ssh_auth_type: 'KEY',
    ssh_password: '',
    ssh_key_path: '',
    lora_training: {
      enabled: false,
      port: 28000,
      params: {},
      headers: {
        "Authorization": "",
        "Content-Type": "application/json"
      },
      use_global_config: true,
      verified: false
    },
    ai_engine: {
      enabled: false,
      port: 8188,
      headers: {
        "Authorization": "",
        "Content-Type": "application/json"
      },
      timeout: 300,
      max_retries: 3,
      retry_interval: 5,
      use_global_config: true,
      verified: false
    },
    enabled: true
  }
  formErrors.value = {}
}

// 监听asset属性变化，初始化表单
watch(() => props.asset, (newValue) => {
  if (newValue) {
    // 深拷贝资产数据并确保认证相关字段存在
    const assetData = {
      ...JSON.parse(JSON.stringify(newValue)),
      ssh_auth_type: newValue.ssh_auth_type || (newValue.ssh_password ? 'PASSWORD' : 'KEY'),
      ssh_password: newValue.ssh_password || '',
      ssh_key_path: newValue.ssh_key_path || ''
    }
    
    // 处理lora_training的参数
    if (assetData.lora_training) {
      // 将params对象的值赋给trainingParams
      if (assetData.lora_training.params) {
        // 确保params是对象类型
        const params = assetData.lora_training.params;
        
        // 将params对象的值赋给trainingParams
        Object.keys(params).forEach(key => {
          if (key in trainingParams.value) {
            trainingParams.value[key] = params[key]
          }
        })
      }
      
      // 确保use_global_config存在
      assetData.lora_training.use_global_config = assetData.lora_training.use_global_config ?? true
    }
    
    // 处理ai_engine的字段
    if (assetData.ai_engine) {
      // 确保use_global_config存在
      assetData.ai_engine.use_global_config = assetData.ai_engine.use_global_config ?? true
    }
    
    assetForm.value = assetData
  } else {
    resetForm()
    // 清空训练参数
    Object.keys(trainingParams.value).forEach(key => {
      trainingParams.value[key] = ''
    })
  }
}, { immediate: true })

// 监听trainingParams的变化，更新assetForm.lora_training.params
watch(trainingParams, (newParams) => {
  // 过滤掉空值
  const filteredParams = {}
  Object.keys(newParams).forEach(key => {
    if (newParams[key] !== '' && newParams[key] !== null && newParams[key] !== undefined) {
      // 处理布尔值
      if (newParams[key] === 'true') {
        filteredParams[key] = true
      } else if (newParams[key] === 'false') {
        filteredParams[key] = false
      } else {
        filteredParams[key] = newParams[key]
      }
    }
  })
  
  // 直接更新params对象
  assetForm.value.lora_training.params = filteredParams
}, { deep: true })

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入资产名称' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符' }
  ],
  ip: [
    { required: true, message: '请输入IP地址或域名' },
    { 
      validator: (value) => {
        // IP地址格式验证
        const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
        // 域名格式验证（简化版，支持二级域名和顶级域名）
        const domainPattern = /^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
        // 本地主机名验证
        const localhostPattern = /^localhost$/i;
        
        return ipPattern.test(value) || domainPattern.test(value) || localhostPattern.test(value);
      },
      message: 'IP地址或域名格式不正确'
    }
  ],
  ssh_port: [
    { required: true, message: '请输入SSH端口' },
    { type: 'number', min: 1, max: 65535, message: '端口范围为 1-65535' }
  ],
  ssh_username: [
    { required: true, message: '请输入SSH用户名' }
  ],
  ssh_password: [
    { required: true, message: '请输入SSH密码', when: (form) => form.ssh_auth_type === 'PASSWORD' }
  ],
  ssh_key_path: [
    { required: true, message: '请输入SSH密钥路径', when: (form) => form.ssh_auth_type === 'KEY' }
  ]
}

// 判断是否为本地资源
const isLocalResource = computed(() => {
  return assetForm.value.name === "本地系统"
})

// 验证单个字段
const validateField = (field, value) => {
  const rules = formRules[field]
  if (!rules) return true

  for (const rule of rules) {
    if (rule.when && !rule.when(assetForm.value)) {
      continue
    }
    if (rule.required && !value) {
      formErrors.value[field] = rule.message
      return false
    }
    if (rule.min && value.length < rule.min) {
      formErrors.value[field] = rule.message
      return false
    }
    if (rule.max && value.length > rule.max) {
      formErrors.value[field] = rule.message
      return false
    }
    if (rule.pattern && !rule.pattern.test(value)) {
      formErrors.value[field] = rule.message
      return false
    }
    if (rule.validator && !rule.validator(value)) {
      formErrors.value[field] = rule.message
      return false
    }
    if (rule.type === 'number') {
      const num = Number(value)
      if (isNaN(num) || num < rule.min || num > rule.max) {
        formErrors.value[field] = rule.message
        return false
      }
    }
  }
  delete formErrors.value[field]
  return true
}

// 解析SSH连接字符串并自动填充相关字段
const parseAndValidateIp = () => {
  const input = assetForm.value.ip.trim()
  
  // 检查是否是SSH连接字符串
  if (input.startsWith('ssh ')) {
    
    // 用于提取端口的正则表达式
    const portRegex = /-p\s+(\d+)/i
    const portMatch = input.match(portRegex)
    
    // 提取端口（如果有）
    if (portMatch && portMatch[1]) {
      assetForm.value.ssh_port = parseInt(portMatch[1], 10)
    }
    
    // 提取用户名和主机
    const userHostRegex = /(\w+)@([\w.-]+\.\w+(?:\.\w+)*)/i
    const userHostMatch = input.match(userHostRegex)
    
    if (userHostMatch) {
      // 提取用户名
      if (userHostMatch[1]) {
        assetForm.value.ssh_username = userHostMatch[1]
      }
      
      // 提取主机/域名
      if (userHostMatch[2]) {
        assetForm.value.ip = userHostMatch[2]
      }
      
      message.success('已自动填充SSH连接信息')
    } else {
      message.warning('无法解析SSH连接字符串中的用户名和主机')
    }
  }
  
  // 无论是否是SSH连接字符串，都验证IP字段
  return validateField('ip', assetForm.value.ip)
}

// 验证能力字段
const validateCapabilityField = (capability, field) => {
  const value = assetForm.value[capability][field]
  const errorKey = `${capability.split('_')[0]}_${field}`
  
  // 如果能力被启用并且不使用全局配置，验证字段
  if (assetForm.value[capability].enabled && !assetForm.value[capability].use_global_config) {
    if (!value || (typeof value === 'string' && !value.trim())) {
      formErrors.value[errorKey] = `请输入${field === 'port' ? '服务端口' : '必填项'}`
      return false
    }
    
    if (field === 'port') {
      const port = Number(value)
      if (isNaN(port) || port < 1 || port > 65535) {
        formErrors.value[errorKey] = '端口范围为 1-65535'
        return false
      }
    }
  }
  
  delete formErrors.value[errorKey]
  return true
}

// 验证整个表单
const validateForm = () => {
  let isValid = true
  formErrors.value = {}

  // 验证基本字段
  Object.keys(formRules).forEach(field => {
    const rules = formRules[field]
    if (!rules) return

    // 如果是本地资源，只验证名称字段
    if (isLocalResource.value && field !== 'name') {
      return
    }

    for (const rule of rules) {
      // 检查条件验证规则
      if (rule.when && !rule.when(assetForm.value)) {
        continue
      }

      if (!validateField(field, assetForm.value[field])) {
        isValid = false
        break
      }
    }
  })

  // 验证 Lora 训练能力
  if (assetForm.value.lora_training.enabled && !assetForm.value.lora_training.use_global_config) {
    if (!validateCapabilityField('lora_training', 'port')) isValid = false
  }

  // 验证 AI 引擎能力
  if (assetForm.value.ai_engine.enabled && !assetForm.value.ai_engine.use_global_config) {
    if (!validateCapabilityField('ai_engine', 'port')) isValid = false
  }

  return isValid
}

// SSH连接验证方法
const verifySshConnection = async () => {
  // 验证必要字段
  if (!validateField('ip', assetForm.value.ip) || 
      !validateField('ssh_port', assetForm.value.ssh_port) ||
      !validateField('ssh_username', assetForm.value.ssh_username)) {
    return
  }

  if (assetForm.value.ssh_auth_type === 'PASSWORD' && 
      !validateField('ssh_password', assetForm.value.ssh_password)) {
    return
  }

  if (assetForm.value.ssh_auth_type === 'KEY' && 
      !validateField('ssh_key_path', assetForm.value.ssh_key_path)) {
    return
  }

  try {
    isVerifyingSsh.value = true
    
    // 构建验证数据
    const verifyData = {
      ip: assetForm.value.ip,
      ssh_port: assetForm.value.ssh_port,
      ssh_username: assetForm.value.ssh_username,
      ssh_auth_type: assetForm.value.ssh_auth_type,
      ssh_password: assetForm.value.ssh_password,
      ssh_key_path: assetForm.value.ssh_key_path
    }

    // 调用API验证SSH连接
    await assetApi.verifySshConnection(verifyData)
    message.success('SSH连接验证成功')
  } catch (error) {
    message.error(error.message || 'SSH连接验证失败')
  } finally {
    isVerifyingSsh.value = false
  }
}

// 表单提交
const handleSubmit = async () => {
  if (!validateForm()) return
  
  try {
    isSubmitting.value = true
    
    // 构建提交的数据对象
    const submitData = {
      name: assetForm.value.name,
      enabled: assetForm.value.enabled,
      lora_training: {
        enabled: assetForm.value.lora_training.enabled,
        use_global_config: assetForm.value.lora_training.use_global_config,
        port: parseInt(assetForm.value.lora_training.port),
        headers: assetForm.value.lora_training.headers,
        params: assetForm.value.lora_training.params
      },
      ai_engine: {
        enabled: assetForm.value.ai_engine.enabled,
        use_global_config: assetForm.value.ai_engine.use_global_config,
        port: parseInt(assetForm.value.ai_engine.port),
        headers: assetForm.value.ai_engine.headers,
        params: assetForm.value.ai_engine.params
      }
    }
    
    // 非本地资源添加SSH连接信息
    if (!isLocalResource.value) {
      submitData.ip = assetForm.value.ip
      submitData.ssh_port = parseInt(assetForm.value.ssh_port)
      submitData.ssh_username = assetForm.value.ssh_username
      submitData.ssh_auth_type = assetForm.value.ssh_auth_type
      
      if (assetForm.value.ssh_auth_type === 'KEY') {
        submitData.ssh_key_path = assetForm.value.ssh_key_path
      } else {
        submitData.ssh_password = assetForm.value.ssh_password
      }
    }
    
    let result
    if (props.isEditing) {
      result = await assetApi.updateAsset(props.asset.id, submitData)
      message.success('资产更新成功')
    } else {
      result = await assetApi.createAsset(submitData)
      message.success('资产创建成功')
    }
    
    emit('submit-success', result)
    emit('update:modelValue', false)
  } catch (error) {
    message.error(error.message || '提交失败')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
/* 表单样式 */
.asset-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 4px;
}

/* 本地资源提示样式 */
.local-resource-note {
  padding: 12px;
  background-color: var(--status-info-bg);
  border-radius: 6px;
  color: var(--info-color);
  font-size: 14px;
  margin-top: 8px;
  border-left: 3px solid var(--info-color);
  line-height: 1.5;
  transition: var(--theme-transition);
}

/* 表单区块 */
.form-section {
  background: var(--form-section-bg);
  border-radius: 8px;
  padding: 20px;
  transition: var(--theme-transition);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  transition: var(--theme-transition);
}

/* 表单项 */
.form-item {
  margin-bottom: 16px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  display: block;
  font-size: 13px;
  color: var(--form-label-text);
  margin-bottom: 6px;
  transition: var(--theme-transition);
}

/* 输入框样式 */
.mac-input {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid var(--input-border);
  background: var(--input-bg);
  color: var(--input-text);
  font-size: 14px;
  transition: var(--theme-transition);
}

.mac-input:focus {
  outline: none;
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 10%, transparent);
}

/* 错误状态 */
.mac-input.is-error {
  border-color: var(--form-error-border);
  background: var(--form-error-bg);
}

.mac-input.is-error:focus {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--danger-color) 10%, transparent);
}

/* 错误提示文字 */
.error-message {
  display: block;
  color: var(--form-error-text);
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.5;
  transition: var(--theme-transition);
}

/* 表单行布局 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

/* 文本域样式 */
.mac-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--input-border);
  background: var(--input-bg);
  color: var(--input-text);
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: var(--theme-transition);
}

.mac-textarea:focus {
  outline: none;
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 10%, transparent);
}

.mac-textarea.is-error {
  border-color: var(--form-error-border);
  background: var(--form-error-bg);
}

/* 能力区块头部 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

/* 能力表单区域 */
.capability-form {
  background: var(--background-secondary);
  border-radius: 6px;
  padding: 16px;
  margin-top: 12px;
  transition: var(--theme-transition);
}

/* 响应式调整 */
@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .form-section {
    padding: 16px;
  }
}

/* 表单验证提示动画 */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.is-error {
  animation: shake 0.3s ease-in-out;
}

/* 占位符文本样式 */
.mac-input::placeholder,
.mac-textarea::placeholder {
  color: #A1A1AA;
}

/* 禁用状态样式 */
.mac-input:disabled,
.mac-textarea:disabled {
  background: #F3F4F6;
  cursor: not-allowed;
}

.mac-input[type="password"] {
  font-family: monospace;
  letter-spacing: 0.2em;
}

select.mac-input {
  padding-right: 30px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236B7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px;
  appearance: none;
  cursor: pointer;
}

select.mac-input:focus {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23007AFF'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
}

.input-with-button {
  display: flex;
  gap: 8px;
}

.input-with-button .mac-input {
  flex: 1;
}

.verify-ssh-btn {
  padding: 0 12px;
  background: var(--status-info-bg);
  color: var(--info-color);
  border: none;
  border-radius: 6px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition: var(--theme-transition);
}

.verify-ssh-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--info-color) 20%, transparent);
}

.verify-ssh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 按钮样式 */
.mac-btn {
  height: 36px;
  padding: 0 16px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--background-secondary);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: var(--theme-transition);
}

.mac-btn:hover {
  background: var(--background-tertiary);
}

.mac-btn.primary {
  background: var(--primary-color);
  color: var(--text-primary-inverse);
  border: none;
}

.mac-btn.primary:hover {
  background: color-mix(in srgb, var(--primary-color) 80%, black);
}

.mac-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* 加载动画 */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--info-color);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.note-text {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 10px 12px;
  background-color: var(--status-warning-bg);
  border-radius: 6px;
  color: var(--warning-color);
  font-size: 13px;
  line-height: 1.5;
  transition: var(--theme-transition);
}

.info-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--warning-color);
  transition: var(--theme-transition);
}

.config-switch-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--background-quaternary);
  border-radius: 6px;
  transition: var(--theme-transition);
}

.global-config-note {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 10px 12px;
  background-color: var(--status-info-bg);
  border-radius: 6px;
  color: var(--info-color);
  font-size: 13px;
  line-height: 1.5;
  transition: var(--theme-transition);
}

.training-params-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 16px;
  background: var(--background-tertiary);
  transition: var(--theme-transition);
}

.params-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.params-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px dashed var(--border-color);
  padding-top: 16px;
}

.params-section:first-child {
  border-top: none;
  padding-top: 0;
}

.params-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0;
  transition: var(--theme-transition);
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 4px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-item label {
  font-size: 12px;
  color: var(--form-label-text);
  transition: var(--theme-transition);
}

.show-params-btn {
  background: var(--status-info-bg);
  color: var(--info-color);
  border: none;
  height: 28px;
  padding: 0 12px;
  font-size: 12px;
  transition: var(--theme-transition);
}

.show-params-btn:hover {
  background: color-mix(in srgb, var(--info-color) 20%, transparent);
}

.param-item-group {
  display: flex;
  gap: 12px;
  grid-column: span 2;
}

.param-item-half {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-item-half label {
  font-size: 12px;
  color: var(--form-label-text);
  transition: var(--theme-transition);
}

.param-item-full {
  grid-column: span 2;
}

/* 确保输入框在移动设备上垂直对齐 */
@media (max-width: 768px) {
  .param-item-group {
    flex-direction: column;
    grid-column: span 1;
    gap: 16px;
  }
  
  .param-item-full {
    grid-column: span 1;
  }
  
  .params-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

.param-item input:hover,
.param-item select:hover,
.param-item-half input:hover,
.param-item-half select:hover {
  border-color: var(--input-hover-border);
}

.param-item input:focus,
.param-item select:focus,
.param-item-half input:focus,
.param-item-half select:focus {
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 10%, transparent);
}

.param-item-half input::-webkit-outer-spin-button,
.param-item-half input::-webkit-inner-spin-button,
.param-item input::-webkit-outer-spin-button,
.param-item input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.param-item-half input[type=number],
.param-item input[type=number] {
  -moz-appearance: textfield;
}

.params-subsection {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-color);
  grid-column: span 2;
}

.params-subsection-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
  transition: var(--theme-transition);
}

.mac-textarea {
  width: 100%;
  min-height: 80px;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--input-border);
  background: var(--input-bg);
  color: var(--input-text);
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: var(--theme-transition);
}

.mac-textarea:focus {
  outline: none;
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 10%, transparent);
}

.mac-textarea.is-error {
  border-color: var(--form-error-border);
  background: var(--form-error-bg);
}

.mac-textarea:disabled {
  background: var(--input-disabled-bg);
  cursor: not-allowed;
}

.param-name {
  font-size: 11px;
  color: var(--text-tertiary);
  opacity: 0.8;
  font-weight: normal;
  margin-left: 4px;
  transition: var(--theme-transition);
}

.disabled-note {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background-color: var(--status-warning-bg);
  color: var(--warning-color);
  border-radius: 6px;
  font-size: 13px;
  transition: var(--theme-transition);
}

.disabled-note .info-icon {
  width: 16px;
  height: 16px;
  color: var(--warning-color);
}
</style> 