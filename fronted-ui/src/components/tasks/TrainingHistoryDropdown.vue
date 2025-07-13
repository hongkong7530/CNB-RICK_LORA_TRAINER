<template>
  <Teleport to="body">
    <div 
      v-if="visible" 
      class="history-dropdown"
      :style="position"
    >
      <div class="dropdown-header">
        <h4>训练历史记录</h4>
      </div>

      <div v-if="loading" class="history-loading">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>
      
      <div v-else-if="!records.length" class="history-empty">
        <ClipboardDocumentIcon class="empty-icon" />
        <span>暂无训练历史</span>
      </div>
      
      <div v-else class="history-list">
        <div 
          v-for="record in records" 
          :key="record.id"
          class="history-item" 
          @click="$emit('select', record)"
        >
          <div class="history-icon" :class="getStatusClass(record.status)">
            <component :is="getStatusIcon(record.status)" class="status-icon" />
          </div>
          
          <div class="history-content">
            <div class="history-item-header">
              <div class="history-date">{{ formatShortDate(record.start_time) }}</div>
              <div class="history-status-badge" :class="getStatusClass(record.status)">
                {{ getStatusText(record.status) }}
              </div>
            </div>
            
            <div class="history-details">
              <div class="history-duration" v-if="record.end_time">
                <ClockIcon class="detail-icon" />
                {{ getHistoryDuration(record) }}
              </div>
              <div class="history-models" v-if="getModelCount(record)">
                <CubeIcon class="detail-icon" />
                {{ getModelCount(record) }} 个模型
              </div>
              <div class="history-model-type" v-if="record.training_config?.model_train_type">
                <DocumentIcon class="detail-icon" :class="getModelTypeClass(record.training_config.model_train_type)" />
                <span :class="getModelTypeClass(record.training_config.model_train_type)">
                  {{ getModelTypeLabel(record.training_config.model_train_type) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';
import { 
  ClockIcon, 
  CubeIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  ClipboardDocumentIcon,
  PauseCircleIcon,
  PlayCircleIcon,
  DocumentIcon
} from '@heroicons/vue/24/outline';
import { getStatusText, getStatusClass } from '@/utils/taskStatus';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  records: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  position: {
    type: Object,
    default: () => ({
      top: '0px',
      left: '0px',
      zIndex: '1100'
    })
  }
});

const emit = defineEmits(['select']);

// 根据状态获取对应图标
const getStatusIcon = (status) => {
  const iconMap = {
    'COMPLETED': CheckCircleIcon,
    'ERROR': ExclamationCircleIcon,
    'TRAINING': ArrowPathIcon,
    'STOPPED': PauseCircleIcon,
    'PENDING': PlayCircleIcon
  };
  
  return iconMap[status] || ClipboardDocumentIcon;
};

// 格式化短日期
const formatShortDate = (dateStr) => {
  if (!dateStr) return '';
  
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};

// 获取历史记录的训练时长
const getHistoryDuration = (record) => {
  if (!record.start_time || !record.end_time) return '进行中';
  
  const start = new Date(record.start_time);
  const end = new Date(record.end_time);
  const duration = end - start;
  
  const minutes = Math.floor((duration / 1000 / 60) % 60);
  const hours = Math.floor((duration / 1000 / 60 / 60));
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`;
  } else {
    return `${minutes}分钟`;
  }
};

// 获取模型数量
const getModelCount = (record) => {
  if (record.training_results && record.training_results.models) {
    return record.training_results.models.length;
  }
  return 0;
};

// 获取模型类型标签
const getModelTypeLabel = (modelTrainType) => {
  const typeMap = {
    'flux-lora': 'FLUX',
    'sd-lora': 'SD1.5',
    'sdxl-lora': 'SDXL'
  };
  
  return typeMap[modelTrainType] || modelTrainType;
};

// 获取模型类型类
const getModelTypeClass = (modelTrainType) => {
  const typeMap = {
    'flux-lora': 'model-type-flux',
    'sd-lora': 'model-type-sd',
    'sdxl-lora': 'model-type-sdxl'
  };
  
  return typeMap[modelTrainType] || '';
};
</script>

<style scoped>
.history-dropdown {
  position: fixed;
  min-width: 320px;
  max-width: 380px;
  background-color: var(--background-primary);
  border-radius: 12px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.15);
  max-height: 480px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
  animation: dropdown-fade-in 0.2s ease;
}

@keyframes dropdown-fade-in {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--background-secondary);
}

.dropdown-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.history-list {
  overflow-y: auto;
  max-height: 400px;
  padding: 8px 0;
}

.history-item {
  padding: 12px 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid var(--border-color-light);
  position: relative;
  overflow: hidden;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item:hover {
  background-color: var(--background-hover);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.history-item:hover::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 4px;
  background-color: var(--primary-color);
}

.history-item:hover .history-date {
  color: var(--primary-color);
}

.history-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--background-tertiary);
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.history-icon.completed {
  background-color: rgba(34, 197, 94, 0.15);
  color: rgb(34, 197, 94);
}

.history-icon.error {
  background-color: rgba(239, 68, 68, 0.15);
  color: rgb(239, 68, 68);
}

.history-icon.training {
  background-color: rgba(59, 130, 246, 0.15);
  color: rgb(59, 130, 246);
}

.status-icon {
  width: 18px;
  height: 18px;
}

.history-content {
  flex: 1;
  min-width: 0;
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-date {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  transition: color 0.2s ease;
}

.history-status-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.history-details {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
}

.history-duration, .history-models {
  display: flex;
  align-items: center;
  gap: 4px;
}

.detail-icon {
  width: 14px;
  height: 14px;
  opacity: 0.7;
}

.detail-icon.model-type-flux,
.detail-icon.model-type-sd,
.detail-icon.model-type-sdxl {
  opacity: 1;
}

.history-loading, .history-empty {
  padding: 32px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.empty-icon {
  width: 32px;
  height: 32px;
  opacity: 0.6;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 自定义文本样式 */
:deep(.red-comma) {
  color: #ff3333;
  font-weight: bold;
}

/* 模型类型样式 */
.model-type-flux {
  color: #0A84FF;
  font-weight: 500;
}

.model-type-sd {
  color: #30D158;
  font-weight: 500;
}

.model-type-sdxl {
  color: #FF9F0A;
  font-weight: 500;
}

/* 滚动条样式 */
</style> 