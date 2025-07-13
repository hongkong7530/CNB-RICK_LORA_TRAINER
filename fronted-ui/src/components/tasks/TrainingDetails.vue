<template>
  <div class="training-details">
    <div class="details-header">
      <h3 class="details-title">任务 - {{ taskName }}</h3>
      <div class="header-info" v-if="trainingProgress">
        <div class="progress-info">
          <span class="progress-label">训练进度:</span>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
          <span class="progress-text">{{ progressPercent }}%</span>
        </div>
        <div class="step-info">
          <span>步数: {{ trainingProgress.current_step }}/{{ trainingProgress.total_steps }}</span>
          <span>轮数: {{ trainingProgress.max_epochs }}</span>
        </div>
      </div>
    </div>

    <div class="details-content">
      <!-- 左侧Loss曲线区域 -->
      <div class="loss-section">
        <TrainingLossChart :loss-data="lossData" :is-loading="isLoadingLoss" :is-training="isTraining" height="100%" />
      </div>

      <!-- 右侧模型预览和列表 -->
      <div class="models-section">
        <!-- 大图预览区域 -->
        <div class="model-preview-area">
          <h4 class="section-title">模型预览</h4>
          <div class="model-large-preview">
            <!-- 添加左上角图片计数器 -->
            <div class="image-counter" v-if="hasMultiplePreviewImages">
              {{ currentImageIndex + 1 }}/{{ totalPreviewImages }}
            </div>

            <!-- 修改图片预览区域，增加一个可点击层 -->
            <div class="preview-image-container" v-if="selectedModel && currentPreviewImage"
              @click="openImagePreview(currentPreviewImage.path)">
              <img :src="currentPreviewImage.path" alt="模型预览" class="large-preview-image" />
            </div>
            <div v-else class="no-preview-large">
              <div class="empty-icon">🖼️</div>
              <div class="empty-text">{{ selectedModel ? '无预览图' : '请选择模型查看预览' }}</div>
            </div>

            <!-- 添加左右切换按钮，完全阻止事件冒泡 -->
            <div class="image-navigation" v-if="hasMultiplePreviewImages" @click.stop>
              <button class="nav-btn prev-btn" @click.stop="prevImage()" :disabled="currentImageIndex === 0">
                <ChevronLeftIcon class="nav-icon" />
              </button>
              <button class="nav-btn next-btn" @click.stop="nextImage()"
                :disabled="currentImageIndex >= totalPreviewImages - 1">
                <ChevronRightIcon class="nav-icon" />
              </button>
            </div>

            <div v-if="selectedModel" class="selected-model-info">
              <div class="model-info-left">
                <div class="model-name" :title="selectedModel.name">{{ selectedModel.name }}</div>
                <div class="model-meta">
                  <span class="model-size">{{ formatFileSize(selectedModel.size) }}</span>
                  <span class="model-date">{{ formatDate(selectedModel.modified_time) }}</span>
                </div>

                <!-- 添加提示词在下载条内 -->
                <div class="prompt-display" v-if="currentPreviewImage && currentPreviewImage.prompt">
                  <div class="prompt-content" :title="currentPreviewImage.prompt">
                    {{ currentPreviewImage.prompt }}
                  </div>
                </div>
              </div>
              <button class="download-btn" @click="downloadModel(selectedModel)">
                <ArrowDownTrayIcon class="download-icon" />
                下载
              </button>
            </div>
          </div>
        </div>

        <!-- 模型列表 -->
        <div class="models-list-container">
          <h4 class="section-title">训练模型 ({{ models.length }})</h4>
          <div v-if="isLoadingModels" class="loading-placeholder">加载中...</div>
          <div v-else-if="models.length === 0 && !hasLossData" class="empty-placeholder">
            <div class="empty-icon">📦</div>
            <div class="empty-text">暂无训练模型</div>
            <div class="empty-desc" v-if="isTraining">训练进行中，模型将在训练过程中保存</div>
          </div>
          <div v-else-if="models.length > 0" class="models-thumbnails" ref="thumbnailsContainer">
            <div v-for="(model, index) in models" :key="index" class="model-thumbnail"
              :class="{ active: selectedModel && selectedModel.path === model.path }" @click="selectModel(model)">
              <div class="thumbnail-preview">
                <img v-if="getPreviewImage(model)" :src="getPreviewImage(model)" alt="模型缩略图" />
                <div v-else class="no-preview-thumbnail">无预览</div>
              </div>
              <div class="thumbnail-name" :title="model.name">{{ model.name }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { tasksApi } from '@/api/tasks'
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowDownTrayIcon
} from '@heroicons/vue/24/outline'
import TrainingLossChart from '@/components/common/TrainingLossChart.vue'

const props = defineProps({
  taskId: {
    type: [Number, String],
    required: true
  },
  taskName: {
    type: String,
    default: ''
  },
  isTraining: {
    type: Boolean,
    default: false
  },
  refreshInterval: {
    type: Number,
    default: 10000 // 默认10秒刷新一次
  },
  task: {
    type: Object,
    default: () => ({})
  },
  // 添加历史记录ID属性，用于加载特定训练历史的数据
  historyRecordId: {
    type: [Number, String],
    default: null
  }
})

// 添加自定义事件
const emit = defineEmits(['preview-image', 'model-images-change'])

// 状态变量
const models = ref([])
const lossData = ref([])
const trainingProgress = ref(null)
const isLoadingModels = ref(false)
const isLoadingLoss = ref(false)
const refreshTimer = ref(null)
const selectedModel = ref(null)
const isComponentMounted = ref(false) // 添加组件挂载状态标志
const thumbnailsContainer = ref(null) // 添加缩略图容器引用
const currentImageIndex = ref(0) // 添加当前图片索引

// 计算属性
const hasLossData = computed(() => lossData.value && lossData.value.length > 0)

// 计算训练进度百分比
const progressPercent = computed(() => {
  if (!trainingProgress.value || !trainingProgress.value.total_steps) return 0

  const percent = Math.floor((trainingProgress.value.current_step / trainingProgress.value.total_steps) * 100)
  return Math.min(100, Math.max(0, percent)) // 确保百分比在0-100之间
})

// 获取预览图片
const getPreviewImage = (model) => {
  if (!model) return null

  if (model.preview_images && model.preview_images.length > 0) {
    return model.preview_images[0].path
  }

  return null
}

// 当前显示的预览图
const currentPreviewImage = computed(() => {
  if (!selectedModel.value ||
    !selectedModel.value.preview_images ||
    selectedModel.value.preview_images.length === 0) {
    return null
  }

  // 使用范围安全的索引，避免在计算属性中修改状态
  const safeIndex = Math.min(currentImageIndex.value, selectedModel.value.preview_images.length - 1)

  return selectedModel.value.preview_images[safeIndex]
})

// 总预览图数量
const totalPreviewImages = computed(() => {
  if (!selectedModel.value || !selectedModel.value.preview_images) {
    return 0
  }
  return selectedModel.value.preview_images.length
})

// 是否有多张预览图
const hasMultiplePreviewImages = computed(() => {
  return totalPreviewImages.value > 1
})

// 下一张预览图
const nextImage = () => {
  if (currentImageIndex.value < totalPreviewImages.value - 1) {
    currentImageIndex.value++
  }
}

// 上一张预览图
const prevImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
  }
}

// 修改计算模型的所有预览图片数组
const modelPreviewImages = computed(() => {
  return models.value
    .flatMap(model => {
      if (model.preview_images && model.preview_images.length > 0) {
        return model.preview_images.map(img => img.path)
      }
      return []
    })
})

// 修改获取训练结果方法，支持历史记录
const fetchTrainingResults = async (isTimer = false) => {
  if (!props.taskId || !isComponentMounted.value) return

  try {
    isLoadingModels.value = models.value.length === 0 && !isTimer // 只在首次加载时显示加载状态
    let data

    // 如果提供了historyRecordId，从历史记录中获取训练结果
    if (props.historyRecordId) {
      const historyData = await tasksApi.getTrainingHistoryDetails(props.historyRecordId)
      if (historyData && historyData.training_results) {
        data = historyData.training_results
      }
    } else {
      data = await tasksApi.getTrainingResults(props.taskId)
    }

    // 检查组件是否仍然挂载
    if (!isComponentMounted.value) return

    if (data && data.models) {
      if (models.value.length === 0) {
        // 首次加载直接赋值
        models.value = data.models
      } else {
        // 更新现有模型或添加新模型
        data.models.forEach(newModel => {
          const existingModelIndex = models.value.findIndex(m => m.path === newModel.path)
          if (existingModelIndex >= 0) {
            // 更新现有模型，保留选中状态
            const isSelected = selectedModel.value && selectedModel.value.path === models.value[existingModelIndex].path
            models.value[existingModelIndex] = newModel
            if (isSelected) {
              selectedModel.value = newModel
            }
          } else {
            // 添加新模型
            models.value.push(newModel)
          }
        })
      }

      // 如果没有选中模型，默认选择第一个有预览图的模型
      if (!selectedModel.value && models.value.length > 0) {
        const modelWithPreview = models.value.find(model =>
          model.preview_images && model.preview_images.length > 0
        ) || models.value[0]
        selectedModel.value = modelWithPreview
      }
    }
  } catch (error) {
    console.error('获取训练结果失败:', error)
  } finally {
    isLoadingModels.value = false
  }
}

// 修改获取训练Loss数据方法，支持历史记录
const fetchTrainingLoss = async () => {
  if (!props.taskId || !isComponentMounted.value) return
  try {
    isLoadingLoss.value = lossData.value.length === 0
    let data

    // 如果提供了historyRecordId，从历史记录中获取Loss数据
    if (props.historyRecordId) {
      const historyData = await tasksApi.getTrainingHistoryDetails(props.historyRecordId)
      if (historyData && historyData.loss_data) {
        data = historyData.loss_data
      }
    } else {
      data = await tasksApi.getTrainingLoss(props.taskId)
    }

    // 检查组件是否仍然挂载
    if (!isComponentMounted.value) return

    if (data && data.series) {
      // 合并数据而不是直接替换，避免闪烁
      if (lossData.value.length === 0) {
        // 首次加载直接赋值
        lossData.value = data.series
      } else {
        // 后续更新使用合并策略
        data.series.forEach(newSeries => {
          const existingSeries = lossData.value.find(s => s.step === newSeries.step)
          if (!existingSeries) {
            // 添加新系列
            lossData.value.push(newSeries)
          }
        })
      }
      
      // 更新训练进度
      if (data.training_progress) {
        trainingProgress.value = data.training_progress
      }
    }
  } catch (error) {
    console.error('获取训练Loss数据失败:', error)
  } finally {
    isLoadingLoss.value = false
  }
}

// 选择模型
const selectModel = (model) => {
  selectedModel.value = model
  currentImageIndex.value = 0
}

// 下载模型
const downloadModel = (model) => {
  if (!model || !model.path) return

  const downloadUrl = model.path
  window.open(downloadUrl, '_blank')
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'

  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }

  return `${bytes.toFixed(2)} ${units[i]}`
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''

  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// 修改自动刷新逻辑，在历史记录模式下不自动刷新
const startAutoRefresh = () => {
  stopAutoRefresh() // 先停止可能存在的定时器

  // 只在非历史记录模式下且正在训练时启动自动刷新
  if (props.isTraining && !props.historyRecordId && props.refreshInterval > 0) {
    refreshTimer.value = setInterval(() => {
      // 确保组件仍然挂载
      if (isComponentMounted.value) {
        fetchTrainingLoss()
        fetchTrainingResults(true)
      } else {
        // 如果组件已卸载，停止刷新
        stopAutoRefresh()
      }
    }, props.refreshInterval)
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 监听训练状态变化
watch(() => props.isTraining, (newVal) => {
  if (newVal) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

// 监听taskId变化
watch(() => props.taskId, () => {
  fetchTrainingResults()
  fetchTrainingLoss()
})

// 监听鼠标滚轮事件实现横向滚动
const handleThumbnailsScroll = (event) => {
  if (!thumbnailsContainer.value) return

  // 阻止默认的垂直滚动
  event.preventDefault()

  // 根据滚轮方向确定滚动方向和距离
  const scrollAmount = event.deltaY || event.deltaX
  thumbnailsContainer.value.scrollLeft += scrollAmount
}

// 修改图片预览方法
const openImagePreview = (imagePath) => {
  if (!imagePath) return

  // 如果是当前选中的模型，获取所有预览图发送给父组件
  if (selectedModel.value && selectedModel.value.preview_images) {
    const allImages = selectedModel.value.preview_images.map(img => img.path)

    // 多图预览，发送当前图片和所有图片列表
    emit('preview-image', 'train', imagePath, allImages)
  }
}

// 添加对modelPreviewImages变化的监听，向父组件发送更新
watch(modelPreviewImages, (images) => {
  emit('model-images-change', images)
}, { immediate: true })

// 组件挂载时
onMounted(async () => {
  isComponentMounted.value = true // 设置组件已挂载标志

  // 先获取数据
  await Promise.all([
    fetchTrainingResults(),
    fetchTrainingLoss()
  ])

  // 如果是训练中状态，启动自动刷新
  if (props.isTraining) {
    startAutoRefresh()
  }

  // 添加滚轮事件监听，确保DOM元素存在
  if (thumbnailsContainer.value && document.body.contains(thumbnailsContainer.value)) {
    thumbnailsContainer.value.addEventListener('wheel', handleThumbnailsScroll, { passive: false })
  }
})

// 组件卸载时
onUnmounted(() => {
  isComponentMounted.value = false // 设置组件已卸载标志
  stopAutoRefresh()

  // 移除滚轮事件监听
  if (thumbnailsContainer.value) {
    try {
      thumbnailsContainer.value.removeEventListener('wheel', handleThumbnailsScroll)
    } catch (error) {
      console.error('移除滚轮事件监听失败:', error)
    }
  }
})
</script>

<style scoped>
.training-details {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  /* 添加overflow: hidden防止内容溢出 */
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.details-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.progress-bar {
  width: 150px;
  height: 8px;
  background-color: var(--background-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
}

.step-info {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--text-secondary);
  max-height: calc(100% - 60px);
  /* 减去标题区域的高度 */
}

.details-content {
  flex: 1;
  display: flex;
  gap: 24px;
  overflow: hidden;
  min-height: 0;
  /* 修改min-height为0，允许内容区域收缩 */
}

/* 左侧Loss曲线区域 */
.loss-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* 右侧模型区域 */
.models-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
  overflow: hidden;
}

.model-preview-area {
  flex: 0 1 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.model-large-preview {
  height: 400px;
  background-color: var(--background-tertiary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.preview-image-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.large-preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.selected-model-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background-color: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  border-radius: 0 0 8px 8px;
  display: flex;
  align-items: flex-start;
  /* 改为顶部对齐 */
  justify-content: space-between;
  z-index: 3;
}

.model-info-left {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.model-name {
  font-size: 14px;
  font-weight: 500;
  color: white;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.download-btn {
  width: auto;
  /* 改为自适应宽度 */
  padding: 6px 12px;
  border: none;
  background-color: var(--primary-color);
  color: white;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: background-color 0.2s;
  flex-shrink: 0;
  /* 防止按钮被压缩 */
}

.download-btn:hover {
  background-color: var(--primary-color-dark);
}

.download-icon {
  width: 16px;
  height: 16px;
}

.models-list-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  /* 添加overflow: hidden */
}

.models-thumbnails {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 4px;
  padding-bottom: 12px;
  flex-wrap: nowrap;
}

.model-thumbnail {
  flex: 0 0 150px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: var(--background-secondary);
  aspect-ratio: 1 / 1;
  display: flex;
  flex-direction: column;
  max-height: 150px;
  /* 添加最大高度限制 */
}

.model-thumbnail.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

.model-thumbnail:hover {
  transform: translateY(-2px);
}

.thumbnail-preview {
  height: 150px;
  background-color: var(--background-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex: 1;
}

.thumbnail-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-name {
  padding: 8px;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-secondary);
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 16px 0;
}

.no-preview-large {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  color: var(--text-secondary);
}

.no-preview-thumbnail {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 12px;
  color: var(--text-secondary);
}

.loading-placeholder,
.empty-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--background-secondary);
  border-radius: 8px;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
}

.empty-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 8px;
}

/* 响应式布局 */
@media (max-width: 992px) {
  .details-content {
    flex-direction: column;
  }

  .loss-section,
  .models-section {
    width: 100%;
  }
}

.image-navigation {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  z-index: 5;
  /* 提高导航层的z-index */
  pointer-events: none;
  /* 导航容器不接收事件 */
}

.nav-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.5);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  transition: all 0.2s;
  z-index: 10;
  /* 提高按钮的z-index */
  pointer-events: all;
  /* 确保按钮可点击 */
}

.nav-btn:hover {
  background-color: rgba(0, 0, 0, 0.7);
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.image-counter {
  position: absolute;
  top: 12px;
  left: 12px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 14px;
  z-index: 2;
}

.prompt-display {
  margin-top: 8px;
}

.prompt-content {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  line-height: 1.4;
  /* 显示两行，隐藏多余内容 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  max-height: 2.8em;
  /* 两行的高度 */
  white-space: normal;
}
</style>