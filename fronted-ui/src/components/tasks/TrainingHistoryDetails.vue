<template>
  <div class="training-history-details">
    <div class="tabs-header">
      <div 
        v-for="(tab, index) in tabs" 
        :key="index" 
        class="tab" 
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <component :is="tab.icon" class="tab-icon" />
        {{ tab.name }}
      </div>
    </div>
    
    <div class="tabs-content">
      <!-- 参数配置标签页 -->
      <div v-if="activeTab === 'parameters'" class="tab-pane parameters-tab">
        <div class="config-section status-section">
          <div class="section-header">
            <h3>训练状态</h3>
            <div class="status-badge" :class="getStatusClass(historyRecord.status)">
              {{ getStatusText(historyRecord.status) }}
            </div>
          </div>
          
          <div class="status-card">
            <div class="time-info">
              <div class="info-item">
                <div class="info-icon start-time">
                  <CalendarIcon />
                </div>
                <div class="info-content">
                  <div class="label">开始时间</div>
                  <div class="value">{{ formatDateTime(historyRecord.start_time) }}</div>
                </div>
              </div>
              
              <div class="info-item">
                <div class="info-icon end-time">
                  <CalendarIcon />
                </div>
                <div class="info-content">
                  <div class="label">结束时间</div>
                  <div class="value">{{ formatDateTime(historyRecord.end_time) || '未结束' }}</div>
                </div>
              </div>
              
              <div class="info-item" v-if="trainingDuration">
                <div class="info-icon duration">
                  <ClockIcon />
                </div>
                <div class="info-content">
                  <div class="label">训练时长</div>
                  <div class="value">{{ trainingDuration }}</div>
                </div>
              </div>
              
              <!-- 添加打标资产信息 -->
              <div class="info-item" v-if="historyRecord.marking_asset_id">
                <div class="info-icon marking">
                  <TagIcon />
                </div>
                <div class="info-content">
                  <div class="label">打标资产</div>
                  <div class="value">{{ historyRecord.marking_asset_name || `ID: ${historyRecord.marking_asset_id}` }}</div>
                </div>
              </div>
              
              <!-- 添加训练资产信息 -->
              <div class="info-item" v-if="historyRecord.training_asset_id">
                <div class="info-icon training">
                  <CpuChipIcon />
                </div>
                <div class="info-content">
                  <div class="label">训练资产</div>
                  <div class="value">{{ historyRecord.training_asset_name || `ID: ${historyRecord.training_asset_id}` }}</div>
                </div>
              </div>
            </div>
            
            <div class="description-container" v-if="historyRecord.description">
              <div class="description-header">
                <DocumentTextIcon class="description-icon" />
                <span>训练描述</span>
              </div>
              <div class="description">
                {{ historyRecord.description }}
              </div>
            </div>
          </div>
        </div>

        <div class="config-section">
          <div class="section-header">
            <h3>打标配置</h3>
            <div class="config-badge">
              <TagIcon class="config-badge-icon" />
              标记参数
            </div>
          </div>
          
          <div class="config-grid">
            <template v-if="historyRecord.mark_config">
              <div 
                v-for="(value, key) in filteredMarkConfig" 
                :key="`mark-${key}`" 
                class="config-item"
              >
                <div class="config-label-container">
                  <div class="config-label">{{ formatConfigKey(key) }}</div>
                  <div class="param-name">{{ key }}</div>
                </div>
                <div class="config-value" :class="getValueTypeIndicator(value)">
                  {{ formatConfigValue(value, key) }}
                </div>
              </div>
            </template>
            <div v-else class="no-config">
              <DocumentIcon class="empty-icon" />
              <span>无打标配置数据</span>
            </div>
          </div>
        </div>

        <div class="config-section">
          <div class="section-header">
            <h3>训练配置</h3>
            <div class="config-badge training">
              <CpuChipIcon class="config-badge-icon" />
              训练参数
            </div>
          </div>
          
          <div v-if="historyRecord.training_config">
            <template v-for="(section, sectionIndex) in paramSections" :key="`section-${sectionIndex}`">
              <div v-if="hasParamsInSection(section)" class="config-category">
                <div class="category-header">
                  <div class="category-title">
                    <component :is="getCategoryIcon(section.id)" class="category-icon" />
                    {{ section.title }}
                  </div>
                  <div class="category-divider"></div>
                </div>
                
                <div class="config-grid">
                  <div 
                    v-for="(param, paramKey) in getParamsInSection(section)" 
                    :key="`param-${paramKey}`" 
                    class="config-item"
                  >
                    <div class="config-label-container">
                      <div class="config-label">{{ param.label || formatConfigKey(paramKey) }}</div>
                      <div class="param-name">{{ paramKey }}</div>
                    </div>
                    <div class="config-value" :class="getValueTypeIndicator(param.value)">
                      {{ formatConfigValue(param.value, paramKey) }}
                    </div>
                  </div>
                </div>
              </div>
            </template>
            
            <div class="view-more-container" v-if="hasMoreTrainingConfigs">
              <button class="view-more-btn" @click="showAllTrainingConfigs = !showAllTrainingConfigs">
                <ChevronDownIcon v-if="!showAllTrainingConfigs" class="view-more-icon" />
                <ChevronUpIcon v-else class="view-more-icon" />
                {{ showAllTrainingConfigs ? '收起参数' : '查看全部参数' }}
              </button>
            </div>
          </div>
          <div v-else class="no-config">
            <DocumentIcon class="empty-icon" />
            <span>无训练配置数据</span>
          </div>
        </div>
      </div>

      <!-- 训练结果标签页 -->
      <div v-if="activeTab === 'results'" class="tab-pane results-tab">
        <TrainingDetails 
          v-if="isTrainingResultsAvailable"
          :taskId="historyRecord.task_id" 
          :taskName="taskName"
          :isTraining="historyRecord.status === 'TRAINING'"
          :historyRecordId="historyRecord.id"
          :refreshInterval="0"
          @preview-image="handlePreviewImage"
        />
        <div v-else class="no-results">
          <ChartBarIcon class="empty-icon" />
          <div class="empty-text">无训练结果数据</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import TrainingDetails from '@/components/tasks/TrainingDetails.vue';
import { getStatusText, getStatusClass } from '@/utils/taskStatus';
import { PARAM_SECTIONS } from '@/composables/useLoraParams';
import { 
  DocumentTextIcon, 
  ClockIcon, 
  CalendarIcon, 
  TagIcon,
  CpuChipIcon,
  ChartBarIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentIcon,
  ClipboardDocumentListIcon,
  CogIcon,
  ServerIcon,
  AdjustmentsHorizontalIcon,
  PhotoIcon,
  ArchiveBoxIcon,
  CircleStackIcon,
  DocumentDuplicateIcon,
  CommandLineIcon
} from '@heroicons/vue/24/outline';

const props = defineProps({
  historyRecord: {
    type: Object,
    required: true
  },
  taskName: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['preview-image']);

// 过滤打标配置参数
const filteredMarkConfig = computed(() => {
  if (!props.historyRecord.mark_config) return {};
  
  const result = {};
  for (const [key, value] of Object.entries(props.historyRecord.mark_config)) {
    if (key !== 'available_algorithms' && key !== 'available_crop_ratios') {
      result[key] = value;
    }
  }
  return result;
});

// 标签页配置
const tabs = [
  { id: 'parameters', name: '训练参数', icon: ClipboardDocumentListIcon },
  { id: 'results', name: '训练结果', icon: ChartBarIcon }
];

const activeTab = ref('parameters');

// 控制训练参数显示
const showAllTrainingConfigs = ref(false);
const MAX_VISIBLE_CONFIGS = 12;

// 获取参数定义
const paramSections = computed(() => {
  return PARAM_SECTIONS;
});

// 获取分类图标
const getCategoryIcon = (sectionId) => {
  const iconMap = {
    'basic': CogIcon,
    'training': ClipboardDocumentListIcon,
    'advanced': AdjustmentsHorizontalIcon,
    'preview': PhotoIcon,
    'bucket': ArchiveBoxIcon,
    'precision': CircleStackIcon,
    'memory': ServerIcon,
    'text_processing': DocumentDuplicateIcon,
    'full_precision': CommandLineIcon
  };
  
  return iconMap[sectionId] || CogIcon;
};

// 检查部分是否有参数
const hasParamsInSection = (section) => {
  if (!props.historyRecord.training_config) return false;
  
  // 如果是子部分且父部分不显示，则不显示
  if (section.subsection && section.parent && !showAllTrainingConfigs.value) {
    return false;
  }
  
  // 检查该部分是否有任何参数存在于训练配置中
  return section.params.some(param => 
    props.historyRecord.training_config[param.name] !== undefined
  );
};

// 获取部分中的参数
const getParamsInSection = (section) => {
  if (!props.historyRecord.training_config) return {};
  
  const result = {};
  section.params.forEach(param => {
    const value = props.historyRecord.training_config[param.name];
    if (value !== undefined) {
      result[param.name] = {
        label: param.label,
        value: value
      };
    }
  });
  
  return result;
};


// 是否有更多配置项可显示
const hasMoreTrainingConfigs = computed(() => {
  if (!props.historyRecord.training_config) return false;
  return Object.keys(props.historyRecord.training_config).length > MAX_VISIBLE_CONFIGS;
});

// 训练时长计算
const trainingDuration = computed(() => {
  if (!props.historyRecord.start_time || !props.historyRecord.end_time) return null;
  
  const start = new Date(props.historyRecord.start_time);
  const end = new Date(props.historyRecord.end_time);
  const durationMs = end - start;
  
  // 转换为可读格式
  const seconds = Math.floor((durationMs / 1000) % 60);
  const minutes = Math.floor((durationMs / (1000 * 60)) % 60);
  const hours = Math.floor((durationMs / (1000 * 60 * 60)) % 24);
  
  const parts = [];
  if (hours > 0) parts.push(`${hours}小时`);
  if (minutes > 0) parts.push(`${minutes}分钟`);
  if (seconds > 0 || parts.length === 0) parts.push(`${seconds}秒`);
  
  return parts.join(' ');
});

// 检查是否有训练结果数据
const isTrainingResultsAvailable = computed(() => {
  return props.historyRecord && (
    (props.historyRecord.training_results && props.historyRecord.training_results.models) || 
    props.historyRecord.loss_data
  );
});

// 格式化配置键名
const formatConfigKey = (key) => {
  // 特殊处理某些键名
  const specialKeys = {
    'crop_ratios': '裁剪比例',
    'crop_min_size': '最小裁剪尺寸',
    'crop_max_size': '最大裁剪尺寸',
    'crop_method': '裁剪方法',
    'min_bucket_reso': '最小桶分辨率',
    'max_bucket_reso': '最大桶分辨率',
    'auto_crop': '自动裁剪',
    'default_crop_ratio': '裁剪比例',
    'max_tags': '最大标签数',
    'trigger_words': '触发词',
  };
  
  if (specialKeys[key]) {
    return specialKeys[key];
  }
  
  // 一般处理：将下划线替换为空格，每个单词首字母大写
  return key.replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// 格式化配置值
const formatConfigValue = (value, key = '') => {
  if (value === true || value === 'true') return '是';
  if (value === false || value === 'false') return '否';
  if (value === null || value === undefined) return '无';
  
  
  // 处理学习率等小数值的格式化
  if (typeof value === 'number' && value < 0.01) {
    return value.toExponential(4);
  }
  
  // 处理特殊参数的格式化
  if (typeof value === 'string') {
    // 处理预训练模型路径，只显示文件名
    if (value.includes('/') || value.includes('\\')) {
      const parts = value.split(/[/\\]/);
      return parts[parts.length - 1];
    }
    
    // 处理分辨率
    if (/^\d+,\d+$/.test(value)) {
      const [width, height] = value.split(',');
      return `${width}×${height}`;
    }
  }
  
  
  return value.toString();
};

// 获取参数值的类型标识
const getValueTypeIndicator = (value) => {
  if (value === true || value === 'true' || value === false || value === 'false') {
    return 'boolean';
  }
  if (Array.isArray(value)) {
    return 'array';
  }
  if (typeof value === 'number' || !isNaN(Number(value))) {
    return 'number';
  }
  if (typeof value === 'string' && (value.startsWith('./') || value.includes('/'))) {
    return 'path';
  }
  if (typeof value === 'object' && value !== null) {
    return 'object';
  }
  return 'text';
};

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '';
  
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
};

// 处理预览图片
const handlePreviewImage = (source, imageUrl, allImages) => {
  emit('preview-image', source, imageUrl, allImages);
};
</script>

<style scoped>
.training-history-details {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  --section-gap: 24px;
}

.tabs-header {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 20px;
  background-color: var(--background-secondary);
  border-radius: 8px 8px 0 0;
}

.tab {
  padding: 12px 20px;
  cursor: pointer;
  font-weight: 500;
  color: var(--text-secondary);
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-icon {
  width: 16px;
  height: 16px;
}

.tab.active {
  color: var(--primary-color);
  border-bottom: 2px solid var(--primary-color);
  background-color: var(--background-primary);
}

.tab:hover:not(.active) {
  color: var(--text-primary);
  background-color: var(--background-hover);
}

.tabs-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 4px;
}

.tab-pane {
  height: 100%;
}

.results-tab {
  height: 100%;
  overflow: hidden;
}

.parameters-tab {
  padding: 0 16px 24px;
}

.config-section {
  margin-bottom: var(--section-gap);
  animation: fade-in 0.3s ease;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 16px;
  margin: 0;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-badge {
  display: flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  background-color: rgba(59, 130, 246, 0.1);
  color: rgb(59, 130, 246);
  gap: 4px;
}

.config-badge.training {
  background-color: rgba(16, 185, 129, 0.1);
  color: rgb(16, 185, 129);
}

.config-badge-icon {
  width: 14px;
  height: 14px;
}

.status-card {
  background-color: var(--background-secondary);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 20px;
  transition: all 0.3s ease;
  animation: card-appear 0.5s ease-out;
}

.status-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

@keyframes card-appear {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.time-info {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 180px;
  animation: fade-in 0.5s ease-out;
  animation-fill-mode: both;
}

.info-item:nth-child(1) { animation-delay: 0.1s; }
.info-item:nth-child(2) { animation-delay: 0.2s; }
.info-item:nth-child(3) { animation-delay: 0.3s; }
.info-item:nth-child(4) { animation-delay: 0.4s; }
.info-item:nth-child(5) { animation-delay: 0.5s; }

.info-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--background-tertiary), var(--background-hover));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.info-icon.start-time {
  background: linear-gradient(135deg, var(--status-info-bg), color-mix(in srgb, var(--info-color) 20%, transparent));
  transition: var(--theme-transition);
}

.info-icon.start-time svg {
  color: var(--info-color);
  transition: var(--theme-transition);
}

.info-icon.end-time {
  background: linear-gradient(135deg, var(--status-success-bg), color-mix(in srgb, var(--success-color) 20%, transparent));
  transition: var(--theme-transition);
}

.info-icon.end-time svg {
  color: var(--success-color);
  transition: var(--theme-transition);
}

.info-icon.duration {
  background: linear-gradient(135deg, var(--status-warning-bg), color-mix(in srgb, var(--warning-color) 20%, transparent));
  transition: var(--theme-transition);
}

.info-icon.duration svg {
  color: var(--warning-color);
  transition: var(--theme-transition);
}

.info-icon.marking {
  background: linear-gradient(135deg, color-mix(in srgb, var(--primary-color) 10%, transparent), color-mix(in srgb, var(--primary-color) 20%, transparent));
  transition: var(--theme-transition);
}

.info-icon.marking svg {
  color: var(--primary-color);
  transition: var(--theme-transition);
}

.info-icon.training {
  background: linear-gradient(135deg, var(--status-error-bg), color-mix(in srgb, var(--danger-color) 20%, transparent));
  transition: var(--theme-transition);
}

.info-icon.training svg {
  color: var(--danger-color);
  transition: var(--theme-transition);
}

.info-item:hover .info-icon {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
}

.info-icon svg {
  width: 18px;
  height: 18px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-weight: 500;
}

.value {
  font-size: 14px;
  color: var(--text-primary);
}

.description-container {
  background-color: var(--background-tertiary);
  border-radius: 8px;
  padding: 16px;
}

.description-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-secondary);
}

.description-icon {
  width: 16px;
  height: 16px;
}

.description {
  white-space: pre-line;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}

.config-item {
  display: flex;
  flex-direction: column;
  background-color: var(--background-secondary);
  padding: 12px 16px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.config-item:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.config-label-container {
  margin-bottom: 6px;
}

.config-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.param-name {
  font-size: 11px;
  color: var(--text-tertiary);
  font-weight: normal;
  font-family: var(--font-mono);
  opacity: 0.7;
  margin-top: 2px;
}

.config-value {
  font-family: var(--font-mono);
  font-size: 14px;
  overflow-wrap: break-word;
  word-break: break-word;
  color: var(--text-primary);
  background-color: var(--background-tertiary);
  padding: 6px 10px;
  border-radius: 4px;
  position: relative;
  display: flex;
  align-items: center;
}

.config-value::before {
  content: '';
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  flex-shrink: 0;
  background-color: var(--text-secondary);
  opacity: 0.5;
}

.config-value.boolean {
  background-color: rgba(16, 185, 129, 0.1);
}

.config-value.boolean::before {
  background-color: #10b981; /* 绿色 */
}

.config-value.number {
  background-color: rgba(59, 130, 246, 0.1);
}

.config-value.number::before {
  background-color: #3b82f6; /* 蓝色 */
}

.config-value.path {
  background-color: rgba(139, 92, 246, 0.1);
}

.config-value.path::before {
  background-color: #8b5cf6; /* 紫色 */
}

.config-value.text {
  background-color: rgba(245, 158, 11, 0.1);
}

.config-value.text::before {
  background-color: #f59e0b; /* 橙色 */
}

.config-value.array::before {
  background-color: #ec4899; /* 粉色 */
}

.config-value.object::before {
  background-color: #14b8a6; /* 青色 */
}

.config-value.array, .config-value.object {
  background-color: rgba(236, 72, 153, 0.1);
  white-space: pre-wrap;
  line-height: 1.4;
}

.no-config, .no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: var(--text-secondary);
  background-color: var(--background-secondary);
  border-radius: 8px;
  grid-column: 1 / -1;
}

.empty-icon {
  width: 40px;
  height: 40px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-text {
  font-size: 16px;
}

.status-badge {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 14px;
}

.view-more-container {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.view-more-btn {
  background-color: var(--background-tertiary);
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.view-more-btn:hover {
  background-color: var(--background-hover);
  transform: translateY(-2px);
}

.view-more-icon {
  width: 16px;
  height: 16px;
}

/* 状态颜色 */
.status-badge.completed {
  background-color: rgba(34, 197, 94, 0.1);
  color: rgb(34, 197, 94);
}

.status-badge.error {
  background-color: rgba(239, 68, 68, 0.1);
  color: rgb(239, 68, 68);
}

.status-badge.training {
  background-color: rgba(59, 130, 246, 0.1);
  color: rgb(59, 130, 246);
}

@media (max-width: 768px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
  
  .time-info {
    justify-content: flex-start;
    gap: 20px;
  }
  
  .info-item {
    min-width: 100%;
    max-width: 100%;
  }
}

.config-category {
  margin-bottom: 24px;
  animation: fade-in 0.3s ease;
  background-color: var(--background-secondary);
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.config-category:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.category-header {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
}

.category-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--primary-color);
  margin-right: 12px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}

.category-divider {
  flex-grow: 1;
  height: 1px;
  background: linear-gradient(to right, var(--border-color), transparent);
}

.category-icon {
  width: 18px;
  height: 18px;
  opacity: 0.8;
}
</style> 