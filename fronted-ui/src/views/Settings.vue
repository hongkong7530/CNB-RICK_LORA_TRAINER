<template>
  <div class="page-container">
    <!-- 固定顶部 -->
    <div class="page-header">
      <div class="header-row">
        <h2 class="page-title">系统设置</h2>
        <div class="settings-actions">
          <button 
            type="button" 
            class="mac-btn primary"
            :disabled="isSubmitting"
            @click="handleSubmit"
          >
            {{ isSubmitting ? '保存中...' : '保存设置' }}
          </button>
        </div>
      </div>
      
      <PageTabs
        v-model:activeTab="activeTab"
        :tabs="tabs"
        tabStyle="default"
      />
    </div>
        
    <!-- 可滚动内容区域 -->
    <div class="page-content">
      <!-- 系统配置 -->
      <div v-if="activeTab === 'system'" class="mac-card settings-card">
        <h3 class="section-title">系统配置</h3>
        
        <div class="form-row">
          <div class="form-group">
            <label>
              <div class="label-text">标记轮询间隔(分钟)</div>
            </label>
            <input 
              v-model.number="form.mark_poll_interval"
              type="number"
              class="mac-input"
              min="1"
              max="60"
            >
          </div>
          
          <div class="form-group">
            <label>
              <div class="label-text">调度间隔(分钟)</div>
            </label>
            <input 
              v-model.number="form.scheduling_minute"
              type="number"
              class="mac-input"
              min="1"
              max="60"
            >
          </div>
        </div>
        
        <div class="form-group">
          <label>
            <div class="label-text">标记文件目录</div>
          </label>
          <input 
            v-model="form.mark_pan_dir"
            class="mac-input"
            placeholder="请输入标记文件目录路径"
          >
        </div>
        
        <div class="form-group">
          <label>
            <div class="label-text">Lora上传目录</div>
          </label>
          <input 
            v-model="form.lora_pan_upload_dir"
            class="mac-input"
            placeholder="请输入Lora上传目录路径"
          >
        </div>
        
        <div class="form-group">
          <label>
            <div class="label-text">标记工作流文件</div>
          </label>
          <div class="workflow-file-container">
            <div v-if="form.mark_workflow_api" class="workflow-file-info">
              <div class="workflow-file-path">{{ form.mark_workflow_api }}</div>
              <div class="workflow-file-actions">
                <button 
                  v-if="uploadedWorkflowFile"
                  type="button" 
                  class="workflow-action-btn"
                  @click="downloadWorkflowFile"
                  title="下载文件"
                >
                  <ArrowDownTrayIcon class="action-icon" />
                </button>
                <button 
                  type="button" 
                  class="workflow-action-btn delete"
                  @click="clearWorkflowFile"
                  title="移除文件"
                >
                  <XMarkIcon class="action-icon" />
                </button>
              </div>
            </div>
            <FileUploader
              v-else
              ref="workflowUploaderRef"
              accept=".json"
              :auto-upload="true"
              description="标记工作流配置文件"
              @upload-success="handleWorkflowUploadSuccess"
            />
          </div>
        </div>
      </div>

      <!-- 标记配置 -->
      <div v-if="activeTab === 'mark'" class="mac-card settings-card">
        <h3 class="section-title">标记配置</h3>
        
        <div class="form-row">
          <div class="form-group toggle-group">
            <div class="toggle-label">自动裁剪</div>
            <SwitchButton v-model="form.mark_config.auto_crop" />
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>
              <div class="label-text">最小置信度</div>
            </label>
            <input 
              v-model.number="form.mark_config.min_confidence"
              type="number"
              class="mac-input"
              min="0"
              max="1"
              step="0.1"
            >
          </div>
          
          <div class="form-group">
            <label>
              <div class="label-text">最大标签数</div>
            </label>
            <input 
              v-model.number="form.mark_config.max_tags"
              type="number"
              class="mac-input"
              min="1"
            >
          </div>
          
          <div class="form-group">
            <label>
              <div class="label-text">默认裁剪比例</div>
            </label>
            <select v-model="form.mark_config.crop_ratio" class="mac-input">
              <option v-for="ratio in form.mark_config.available_crop_ratios" :key="ratio" :value="ratio">
                {{ ratio }}
              </option>
            </select>
          </div>
        </div>
        
        <div class="form-group">
          <label>
            <div class="label-text">打标算法</div>
          </label>
          <select v-model="form.mark_config.mark_algorithm" class="mac-input">
            <option v-for="algorithm in form.mark_config.available_algorithms" :key="algorithm" :value="algorithm">
              {{ algorithm }}
            </option>
          </select>
        </div>
      </div>

      <!-- AI引擎配置 -->
      <div v-if="activeTab === 'ai'" class="mac-card settings-card">
        <h3 class="section-title">AI引擎配置</h3>
        
        <div class="form-row">
          <div class="form-group">
            <label>
              <div class="label-text">超时时间(秒)</div>
            </label>
            <input 
              v-model.number="form.ai_engine_config.timeout"
              type="number"
              class="mac-input"
              min="1"
            >
          </div>
          
          <div class="form-group">
            <label>
              <div class="label-text">最大重试次数</div>
            </label>
            <input 
              v-model.number="form.ai_engine_config.max_retries"
              type="number"
              class="mac-input"
              min="0"
            >
          </div>
          
          <div class="form-group">
            <label>
              <div class="label-text">重试间隔(秒)</div>
            </label>
            <input 
              v-model.number="form.ai_engine_config.retry_interval"
              type="number"
              class="mac-input"
              min="1"
            >
          </div>
        </div>
        
        <h4 class="subsection-title">请求头配置</h4>
        <KeyValueConfig
          v-model="form.ai_engine_headers"
          keyPlaceholder="Header名称"
          valuePlaceholder="Header值"
          addButtonText="添加"
        />
      </div>

      <!-- 翻译配置 -->
      <div v-if="activeTab === 'translate'" class="mac-card settings-card">
        <h3 class="section-title">翻译配置</h3>
        
        <!-- 全局翻译开关 -->
        <div class="form-row">
          <div class="form-group toggle-group">
            <div class="toggle-label">启用翻译功能</div>
            <SwitchButton v-model="form.translate_config.enabled" />
          </div>
        </div>
        
        <!-- 翻译服务选择 -->
        <div class="form-row">
          <div class="form-group">
            <label>
              <div class="label-text">翻译服务提供商</div>
            </label>
            <select v-model="form.translate_config.provider" class="mac-input">
              <option value="baidu">百度翻译</option>
              <option value="google">谷歌翻译（免费）</option>
            </select>
          </div>
        </div>
        
        <!-- 百度翻译配置 -->
        <div v-if="form.translate_config.provider === 'baidu'" class="provider-config">
          <h4 class="subsection-title">百度翻译配置</h4>
          <div class="form-row">
            <div class="form-group toggle-group">
              <div class="toggle-label">启用百度翻译</div>
              <SwitchButton v-model="form.baidu_translate_config.enabled" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>
                <div class="label-text">百度翻译APP ID</div>
              </label>
              <input 
                v-model="form.baidu_translate_config.app_id"
                type="text"
                class="mac-input"
                placeholder="请输入百度翻译APP ID"
                :disabled="!form.baidu_translate_config.enabled"
              >
            </div>
            
            <div class="form-group">
              <label>
                <div class="label-text">百度翻译密钥</div>
              </label>
              <input 
                v-model="form.baidu_translate_config.secret_key"
                type="text"
                class="mac-input"
                placeholder="请输入百度翻译密钥"
                :disabled="!form.baidu_translate_config.enabled"
              >
            </div>
          </div>
          <p class="simple-note">使用百度翻译API，需要在百度翻译开放平台申请APP ID和密钥。</p>
        </div>
        
        <!-- 谷歌翻译配置 -->
        <div v-if="form.translate_config.provider === 'google'" class="provider-config">
          <h4 class="subsection-title">谷歌翻译配置</h4>
          <div class="form-row">
            <div class="form-group toggle-group">
              <div class="toggle-label">启用谷歌翻译</div>
              <SwitchButton v-model="form.google_translate_config.enabled" />
            </div>
          </div>
          <p class="simple-note">使用免费的谷歌翻译服务，无需API密钥，但可能受到访问限制。</p>
        </div>
        
        <!-- 通用语言配置 -->
        <div class="form-row">
          <div class="form-group">
            <label>
              <div class="label-text">默认源语言</div>
            </label>
            <select v-model="form.translate_config.default_from" class="mac-input">
              <option v-for="option in languageOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>
              <div class="label-text">默认目标语言</div>
            </label>
            <select v-model="form.translate_config.default_to" class="mac-input">
              <option v-for="option in languageOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>
        
        <!-- 翻译测试 -->
        <h4 class="subsection-title">翻译测试</h4>
        <div class="translate-test-container">
          <div class="translate-input-area">
            <textarea 
              v-model="testTranslateText" 
              class="mac-textarea" 
              placeholder="请输入要翻译的文本"
              rows="4"
            ></textarea>
          </div>
          
          <div class="translate-actions">
            <button 
              type="button" 
              class="mac-btn" 
              @click="testTranslate"
              :disabled="isTranslating || !testTranslateText"
            >
              {{ isTranslating ? '翻译中...' : '测试翻译' }}
            </button>
          </div>
          
          <div class="translate-result-area" v-if="testTranslateResult">
            <div class="translate-result-title">翻译结果：</div>
            <div class="translate-result-content">{{ testTranslateResult }}</div>
          </div>
        </div>
      </div>

      <!-- Lora训练配置 -->
      <div v-if="activeTab === 'lora'" class="mac-card settings-card">
        <h3 class="section-title">Lora训练配置</h3>
        
        <LoraTrainingParams
          v-model="form.lora_training_config"
          :disabled="false"
          layout="settings"
          :showAllParams="true"
          ref="loraTrainingParamsRef"
        />
        
        <h4 class="subsection-title">请求头配置</h4>
        <KeyValueConfig
          v-model="form.lora_training_headers"
          keyPlaceholder="Header名称"
          valuePlaceholder="Header值"
          addButtonText="添加"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { 
  ArrowDownTrayIcon, 
  XMarkIcon 
} from '@heroicons/vue/24/outline'
import { settingsApi } from '@/api/settings'
import { uploadApi } from '@/api/upload'
import { commonApi } from '@/api/common'
import message from '@/utils/message'
import FileUploader from '@/components/common/FileUploader.vue'
import KeyValueConfig from '@/components/common/KeyValueConfig.vue'
import LoraTrainingParams from '@/components/common/LoraTrainingParams.vue'
import SwitchButton from '@/components/common/SwitchButton.vue'
import PageTabs from '@/components/common/PageTabs.vue'
import { useRouter, useRoute } from 'vue-router'
import { translationConfig, updateTranslationConfig } from '@/utils/translationCache'

const router = useRouter()
const route = useRoute()

// 标签页定义
const tabs = [
  { key: 'system', label: '系统配置' },
  { key: 'mark', label: '标记配置' },
  { key: 'ai', label: 'AI引擎配置' },
  { key: 'translate', label: '翻译配置' },
  { key: 'lora', label: 'Lora训练配置' }
]
const activeTab = ref('system')

// 根据路由设置当前Tab
const setTabFromRoute = () => {
  // 如果当前路由不是设置页面，则不处理
  if (!route.path.startsWith('/settings')) {
    return
  }
  
  // 从路由元数据中获取tab参数
  const tabParam = route.params.tab || route.meta.tab
  
  if (tabParam && tabs.some(tab => tab.key === tabParam)) {
    activeTab.value = tabParam
  } else if (route.path === '/settings') {
    // 如果直接访问/settings路径，重定向到默认tab
    router.replace('/settings/system')
  } else {
    // 尝试从路径中提取tab名称
    const pathSegments = route.path.split('/')
    const lastSegment = pathSegments[pathSegments.length - 1]
    
    if (tabs.some(tab => tab.key === lastSegment)) {
      activeTab.value = lastSegment
    } else {
      // 如果无法匹配任何已知tab，设置为默认tab
      activeTab.value = 'system'
    }
  }
}

// 监听activeTab变化，更新路由
watch(activeTab, (newTab) => {
  // 只有在设置页面时才更新路由
  if (route.path.startsWith('/settings') && route.params.tab !== newTab) {
    router.push(`/settings/${newTab}`);
  }
})

// 监听路由变化，更新当前Tab
watch(() => route.path, () => {
  // 只有当路径以/settings开头时才更新标签页
  if (route.path.startsWith('/settings')) {
    setTabFromRoute()
  }
}, { immediate: true })

// 表单数据
const form = ref({
  // 系统配置
  mark_pan_dir: '',
  lora_pan_upload_dir: '',
  scheduling_minute: 5,
  mark_poll_interval: 5,
  mark_workflow_api: '',
  
  // 标记配置
  mark_config: {
    auto_crop: true,
    available_crop_ratios: ['1:1', '3:2', '4:3', '2:3', '16:9', '9:16'],
    crop_ratio: '1:1',
    max_tags: 20,
    min_confidence: 0.6,
    mark_algorithm: 'wd-v1-4-convnext-tagger-v2',
    available_algorithms: [
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
  },
  
  // AI引擎配置
  ai_engine_config: {
    max_retries: 3,
    retry_interval: 5,
    timeout: 300
  },
  ai_engine_headers: {},
  
  // 翻译配置
  translate_config: {
    enabled: true,
    provider: 'baidu',
    default_from: 'auto',
    default_to: 'zh'
  },
  
  // 百度翻译配置
  baidu_translate_config: {
    enabled: true,
    app_id: '20250327002316619',
    secret_key: '67qaSQg_WdfWqQFvx7ml',
    api_url: 'https://fanyi-api.baidu.com/api/trans/vip/translate',
    default_from: 'auto',
    default_to: 'zh'
  },
  
  // 谷歌翻译配置
  google_translate_config: {
    enabled: true,
    api_url: 'https://translate.googleapis.com/translate_a/single',
    default_from: 'auto',
    default_to: 'zh'
  },
  
  // Lora训练配置
  lora_training_config: {
    model_train_type: 'flux-lora',
    pretrained_model_name_or_path: '',
    ae: '',
    clip_l: '',
    t5xxl: '',
    output_dir: '',
    resolution: '512,512',
    timestep_sampling: 'sigmoid',
    sigmoid_scale: 1,
    model_prediction_type: 'raw',
    discrete_flow_shift: 1,
    loss_type: 'l2',
    guidance_scale: 1,
    prior_loss_weight: 1,
    learning_rate: 0.0001,
    unet_lr: 0.0005,
    text_encoder_lr: 0.00001,
    max_train_epochs: 10,
    train_batch_size: 1,
    gradient_checkpointing: true,
    gradient_accumulation_steps: 1,
    network_train_unet_only: false,
    network_train_text_encoder_only: false,
    network_dim: 64,
    network_alpha: 32,
    lr_warmup_steps: 0,
    lr_scheduler_num_cycles: 1,
    optimizer_type: 'AdamW8bit',
    lr_scheduler: 'cosine_with_restarts',
    mixed_precision: 'bf16',
    full_fp16: false,
    full_bf16: false,
    fp8_base: true,
    sdpa: true,
    save_precision: 'fp16',
    save_model_as: 'safetensors',
    save_every_n_epochs: 2,
    sample_every_n_epochs: 2,
    network_module: 'networks.lora_flux',
    clip_skip: 2,
    seed: 1337,
    enable_bucket: true,
    bucket_no_upscale: true,
    min_bucket_reso: 256,
    max_bucket_reso: 1024,
    bucket_reso_steps: 64,
    cache_latents: true,
    cache_latents_to_disk: true,
    cache_text_encoder_outputs: true,
    cache_text_encoder_outputs_to_disk: true,
    persistent_data_loader_workers: true,
    lowram: false,
    sample_prompts: '(masterpiece, best quality:1.2), 1girl, solo, --n lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,signature, watermark, username, blurry,  --w 512  --h 768  --l 7  --s 24  --d 1337',
    sample_sampler: 'euler_a',
    log_with: 'tensorboard',
    logging_dir: './logs',
    caption_extension: '.txt',
    shuffle_caption: false,
    keep_tokens: 0,
    max_token_length: 255,
    v2: false,
    train_t5xxl: false
  },
  lora_training_headers: {}
})

const isSubmitting = ref(false)

const workflowUploaderRef = ref(null)
const uploadedWorkflowFile = ref(null)

// 翻译相关
const testTranslateText = ref('love you')
const testTranslateResult = ref('')
const isTranslating = ref(false)

// 支持的语言列表
const languageOptions = [
  { value: 'auto', label: '自动检测' },
  { value: 'zh', label: '中文' },
  { value: 'en', label: '英文' },
  { value: 'yue', label: '粤语' },
  { value: 'wyw', label: '文言文' },
  { value: 'jp', label: '日语' },
  { value: 'kor', label: '韩语' },
  { value: 'fra', label: '法语' },
  { value: 'spa', label: '西班牙语' },
  { value: 'th', label: '泰语' },
  { value: 'ara', label: '阿拉伯语' },
  { value: 'ru', label: '俄语' },
  { value: 'pt', label: '葡萄牙语' },
  { value: 'de', label: '德语' },
  { value: 'it', label: '意大利语' },
  { value: 'nl', label: '荷兰语' },
  { value: 'pl', label: '波兰语' }
]

// 添加对LoraTrainingParams组件的引用
const loraTrainingParamsRef = ref(null);

// 获取设置
const fetchSettings = async () => {
  try {
    const data = await settingsApi.getSettings()
    form.value = data
    
    // 同步翻译配置到translationCache模块
    updateTranslationConfig({
      enabled: form.value.translate_config?.enabled || false,
      provider: form.value.translate_config?.provider || 'baidu',
      app_id: form.value.baidu_translate_config?.app_id || '',
      secret_key: form.value.baidu_translate_config?.secret_key || '',
      default_from: form.value.translate_config?.default_from || 'auto',
      default_to: form.value.translate_config?.default_to || 'zh'
    })
    
    // 如果存在工作流路径，尝试获取文件信息
    if (form.value.mark_workflow_api && form.value.mark_workflow_api.includes('uploads/')) {
      try {
        // 从路径中提取文件ID，假设格式为 uploads/{id}.{ext}
        const filePathMatch = form.value.mark_workflow_api.match(/uploads\/(\d+)\..+/)
        if (filePathMatch && filePathMatch[1]) {
          const fileId = parseInt(filePathMatch[1])
          const fileResponse = await uploadApi.getFile(fileId)
          if (fileResponse && fileResponse.file) {
            uploadedWorkflowFile.value = fileResponse.file
          }
        }
      } catch (err) {
        console.error('获取工作流文件信息失败', err)
      }
    }
  } catch (error) {
    message.error('获取设置失败')
  }
}

// 提交设置
const handleSubmit = async () => {
  try {
    isSubmitting.value = true
    await settingsApi.updateSettings(form.value)
    
    // 更新翻译配置到translationCache模块
    updateTranslationConfig({
      enabled: form.value.translate_config?.enabled || false,
      provider: form.value.translate_config?.provider || 'baidu',
      app_id: form.value.baidu_translate_config?.app_id || '',
      secret_key: form.value.baidu_translate_config?.secret_key || '',
      default_from: form.value.translate_config?.default_from || 'auto',
      default_to: form.value.translate_config?.default_to || 'zh'
    })
    
    // 重置Lora训练参数的修改状态
    if (loraTrainingParamsRef.value) {
      loraTrainingParamsRef.value.resetChangedState();
    }
    
    message.success('设置已保存')
  } catch (error) {
    console.log('保存设置失败',error)
    message.error('保存设置失败')
  } finally {
    isSubmitting.value = false
  }
}

// 处理工作流文件上传成功
const handleWorkflowUploadSuccess = (file) => {
  form.value.mark_workflow_api = file.storage_path
  uploadedWorkflowFile.value = file
}

// 下载工作流文件
const downloadWorkflowFile = () => {
  if (uploadedWorkflowFile.value) {
    const downloadUrl = uploadApi.getDownloadUrl(uploadedWorkflowFile.value.id)
    window.open(downloadUrl, '_blank')
  }
}

// 清除工作流文件
const clearWorkflowFile = () => {
  form.value.mark_workflow_api = ''
  uploadedWorkflowFile.value = null
}

// 测试翻译
const testTranslate = async () => {
  if (!testTranslateText.value) {
    message.warning('请输入要测试的文本')
    return
  }
  
  // 检查翻译功能是否启用
  if (!form.value.translate_config.enabled) {
    message.warning('翻译功能已禁用，请先启用')
    return
  }
  
  // 检查具体的翻译服务是否可用
  const provider = form.value.translate_config.provider
  if (provider === 'baidu') {
    if (!form.value.baidu_translate_config.enabled) {
      message.warning('百度翻译功能未启用，请先启用')
      return
    }
    if (!form.value.baidu_translate_config.app_id || !form.value.baidu_translate_config.secret_key) {
      message.warning('百度翻译配置不完整，请先配置APP ID和密钥')
      return
    }
  } else if (provider === 'google') {
    if (!form.value.google_translate_config.enabled) {
      message.warning('谷歌翻译功能未启用，请先启用')
      return
    }
  }
  
  try {
    isTranslating.value = true
    const resp = await commonApi.translateText(
      testTranslateText.value,
      form.value.translate_config.default_to,
      form.value.translate_config.default_from,
      provider
    )
    
    if (resp && resp.result) {
      testTranslateResult.value = resp.result
      const providerName = provider === 'baidu' ? '百度翻译' : '谷歌翻译'
      message.success(`${providerName}测试成功`)
    } else {
      testTranslateResult.value = '翻译失败'
      message.error('翻译失败：' + (resp.message || resp.error || '未知错误'))
    }
  } catch (error) {
    console.error('翻译测试失败:', error)
    testTranslateResult.value = '翻译服务异常'
    message.error('翻译服务异常')
  } finally {
    isTranslating.value = false
  }
}

onMounted(() => {
  fetchSettings()
  setTabFromRoute() // 初始加载时设置Tab
})
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: var(--background-primary);
  padding: 20px 20px 0;
  border-bottom: 1px solid var(--border-color, #E5E7EB);
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.settings-actions {
  display: flex;
  gap: 8px;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.settings-card {
  margin-bottom: 20px;
  padding: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--text-primary);
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin: 24px 0 16px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color-light);
  padding-bottom: 8px;
}

/* 改为统一的网格布局 */
.form-row, .config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 0;
}

.form-group label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

/* 开关组样式调整 */
.toggle-group {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.toggle-label {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 工作流文件样式优化 */
.workflow-file-container {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  overflow: hidden;
}

.workflow-file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background-color: var(--background-tertiary);
}

.workflow-file-path {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.workflow-file-actions {
  display: flex;
  gap: 4px;
}

.workflow-action-btn {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.workflow-action-btn:hover {
  background-color: var(--background-secondary);
  color: var(--primary-color);
}

.workflow-action-btn.delete:hover {
  color: var(--danger-color);
}

.action-icon {
  width: 16px;
  height: 16px;
}

.param-name {
  font-size: 11px;
  color: var(--text-secondary);
  opacity: 0.8;
  font-weight: normal;
  margin-left: 4px;
}

.config-group-wide {
  grid-column: 1 / -1;
}

.mac-textarea {
  width: 100%;
  min-height: 80px;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--background-secondary);
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: all 0.2s ease;
}

.mac-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.1);
}

.mac-textarea:disabled {
  background: var(--background-tertiary);
  cursor: not-allowed;
}

.params-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color-light);
}

.params-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

/* 响应式设计优化 */
@media (max-width: 768px) {
  .form-row, .config-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .settings-card {
    padding: 16px;
  }
  
  .section-title {
    margin-bottom: 20px;
  }
}

.label-text {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: normal;
}

/* 翻译测试样式 */
.translate-test-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 20px;
}

.translate-input-area {
  flex: 1;
}

.translate-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.translate-result-area {
  background: var(--background-tertiary);
  padding: 16px;
  border-radius: 6px;
  margin-top: 16px;
}

.translate-result-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.translate-result-content {
  font-size: 14px;
  color: var(--text-secondary);
}

@media (max-width: 640px) {
  .page-container {
    padding: 0;
  }
  
  .page-header {
    padding: 16px 16px 0;
  }
  
  .page-content {
    padding: 16px;
  }
}

/* 翻译提供商配置样式 */
.provider-config {
  margin-top: 20px;
  padding: 16px;
  background: var(--background-tertiary);
  border-radius: 8px;
  border: 1px solid var(--border-color-light);
}

.simple-note {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 12px;
  line-height: 1.5;
}

.info-icon {
  font-size: 16px;
  color: var(--info-color);
}
</style> 