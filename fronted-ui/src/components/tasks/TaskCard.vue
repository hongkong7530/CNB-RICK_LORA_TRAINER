<template>
  <div 
    class="task-card mac-card" 
    :class="{ 'is-selected': selected }"
  >
    <!-- 卡片头部 -->
    <div class="task-card-header">
      <div class="task-title">
        <component :is="getStatusIcon(task.status)" class="status-icon" />
        <span class="task-name text-ellipsis">{{ task.name }}</span>
      </div>
      <div class="task-status-badge" :class="getStatusClass(task.status)">
        {{ getStatusText(task.status) }}
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="task-card-content">
      <!-- 图片预览网格 -->
      <div class="preview-section" v-if="task.images?.length">
        <!-- 主预览图 -->
        <div class="main-preview">
          <img 
            :src="task.images[0].preview_url" 
            :alt="task.images[0].filename"
            class="preview-image"
          >
        </div>
        <!-- 缩略图列表 -->
        <div class="thumbnail-list" v-if="task.images.length > 1">
          <div 
            v-for="(image, index) in thumbnailImages" 
            :key="index"
            class="thumbnail-item"
          >
            <img :src="image.preview_url" :alt="image.filename">
          </div>
          <div v-if="task.images.length > 4" class="thumbnail-more">
            <span>+{{ task.images.length - 4 }}</span>
          </div>
        </div>
      </div>
      <div v-else class="preview-empty">
        <PhotoIcon class="empty-icon" />
        暂无图片
      </div>

      <!-- 任务信息 -->
      <div class="task-info">
        <div class="info-item">
          <ClockIcon class="info-icon" />
          <span>{{ formatDate(task.created_at) }}</span>
        </div>
        <div class="info-item">
          <PhotoIcon class="info-icon" />
          <span>{{ task.images?.length || 0 }} 张图片</span>
        </div>
      </div>
    </div>

    <!-- 进度条 -->
    <div v-if="showProgress" class="task-progress">
      <div class="progress-bar" :style="{ width: `${task.progress || 0}%` }" />
    </div>

    <!-- 操作按钮组 -->
    <div class="task-actions">
      <button 
        class="mac-btn small view-btn"
        @click.stop="$router.push(`/tasks/${task.id}`)"
      >
        <EyeIcon class="btn-icon" />
        <span>查看</span>
      </button>
      <button 
        :disabled="!canDelete"
        :title="getDeleteButtonTitle"
        class="mac-btn small delete-btn"
        @click.stop="handleDelete"
      >
        <TrashIcon class="btn-icon" />
        <span>删除</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  ClockIcon, 
  PhotoIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon as PendingIcon,
  ArrowPathIcon,
  TagIcon,
  XCircleIcon,
  EyeIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'
import { formatDate } from '@/utils/datetime'

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  selected: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['delete'])

// 是否可以删除
const canDelete = computed(() => {
  return ['NEW', 'ERROR'].includes(props.task.status)
})

// 删除按钮提示文本
const getDeleteButtonTitle = computed(() => {
  if (canDelete.value) {
    return '删除任务'
  }
  const statusText = getStatusText(props.task.status)
  return `${statusText}状态的任务不能删除`
})

// 处理删除
const handleDelete = (e) => {
  e.stopPropagation()
  if (!canDelete.value) return
  if (confirm(`确定要删除任务 "${props.task.name}" 吗？`)) {
    emit('delete', props.task.id)
  }
}

// 获取状态图标
const getStatusIcon = (status) => {
  const iconMap = {
    'NEW': PendingIcon,
    'MARKING': TagIcon,
    'MARKED': CheckCircleIcon,
    'TRAINING': ArrowPathIcon,
    'COMPLETED': CheckCircleIcon,
    'ERROR': XCircleIcon
  }
  return iconMap[status] || ExclamationCircleIcon
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'NEW': '新建',
    'MARKING': '标记中',
    'MARKED': '已标记',
    'TRAINING': '训练中',
    'COMPLETED': '已完成',
    'ERROR': '错误'
  }
  return statusMap[status] || status
}

// 获取状态样式类
const getStatusClass = (status) => {
  const statusClassMap = {
    'NEW': 'new',
    'MARKING': 'marking',
    'MARKED': 'marked',
    'TRAINING': 'training',
    'COMPLETED': 'completed',
    'ERROR': 'error'
  }
  return statusClassMap[status] || ''
}

// 预览图片列表
const thumbnailImages = computed(() => {
  return (props.task.images || []).slice(1, 4) // 从第二张开始取3张
})

// 是否显示进度条
const showProgress = computed(() => {
  return ['MARKING', 'TRAINING'].includes(props.task.status)
})
</script>

<style scoped>
.task-card {
  height: 320px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: var(--background-primary);
}

.task-card:hover {
  transform: translateY(-2px);
}

.task-card.is-selected {
  border: 2px solid var(--primary-color);
}

.task-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-icon {
  width: 20px;
  height: 20px;
}

.task-name {
  font-weight: 500;
  font-size: 15px;
}

.task-status-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

/* 状态样式 */
.task-status-badge.new {
  background: #F0F9FF;
  color: #0369A1;
}

.task-status-badge.marking {
  background: #FFF7ED;
  color: #C2410C;
}

.task-status-badge.marked {
  background: #F0FDF4;
  color: #166534;
}

.task-status-badge.training {
  background: #EEF2FF;
  color: #4338CA;
}

.task-status-badge.completed {
  background: #ECFDF5;
  color: #047857;
}

.task-status-badge.error {
  background: #FEF2F2;
  color: #B91C1C;
}

.task-card-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 160px;
}

.main-preview {
  flex: 1;
  border-radius: 6px;
  overflow: hidden;
}

.thumbnail-list {
  display: flex;
  gap: 8px;
  height: 48px;
}

.thumbnail-item {
  position: relative;
  width: 48px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
}

.preview-image,
.thumbnail-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-more {
  width: 48px;
  height: 48px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  color: var(--text-primary-inverse);
  border-radius: 4px;
  font-size: 12px;
}

.preview-empty {
  height: 160px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--background-tertiary);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 14px;
  gap: 8px;
}

.empty-icon {
  width: 32px;
  height: 32px;
  color: var(--text-tertiary);
}

.task-info {
  display: flex;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.info-icon {
  width: 16px;
  height: 16px;
}

.task-progress {
  height: 4px;
  background: var(--background-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.3s ease;
}

.task-actions {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--border-color-light);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.mac-btn.small {
  padding: 6px 12px;
  font-size: 13px;
}

.view-btn {
  background: var(--primary-color);
  color: var(--text-primary-inverse);
  border: none;
}

.view-btn:hover {
  background: color-mix(in srgb, var(--primary-color) 90%, black);
}

.delete-btn {
  color: var(--danger-color);
  border: 1px solid var(--danger-color);
  background: transparent;
}

.delete-btn:hover:not(:disabled) {
  background: var(--danger-color);
  color: var(--text-primary-inverse);
}

.delete-btn:disabled {
  color: var(--text-tertiary);
  border-color: var(--border-color);
  background: var(--background-secondary);
  cursor: not-allowed;
}

.delete-btn:disabled .btn-icon {
  opacity: 0.5;
}

.btn-icon {
  width: 14px;
  height: 14px;
}
</style> 