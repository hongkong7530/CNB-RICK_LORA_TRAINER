<template>
  <div class="task-detail">
    <!-- 顶部操作栏 -->
    <div class="action-bar mac-card">
      <div class="left-section">
        <h2 class="task-title">{{ task?.name }}</h2>
        <div class="task-status-badge" :class="getStatusClass(task?.status)">
          {{ getStatusText(task?.status) }}
        </div>
      </div>

      <!-- 中间状态栏 -->
      <div class="center-section" v-if="task">
        <div class="status-timeline">
          <TaskStatus :task="task" :compact="true" />
        </div>
      </div>

      <div class="right-section">
        <!-- 修改历史记录按钮部分 -->
        <div v-if="canViewTrainingHistory" class="history-dropdown-container">
          <button class="mac-btn info" @click="toggleHistoryDropdown" ref="historyBtn">
            <ClockIcon class="btn-icon" />
            训练历史
          </button>

          <!-- 使用新组件 -->
          <TrainingHistoryDropdown :visible="showHistoryDropdown" :records="trainingHistory" :loading="isLoadingHistory"
            :position="historyDropdownPosition" @select="openHistoryDetails" />
        </div>

        <button v-if="canViewTrainingDetails" class="mac-btn info" @click="showTrainingDetailsModal = true">
          <ChartBarIcon class="btn-icon" />
          训练详情
        </button>
        <button v-if="canViewMarkingProgress" class="mac-btn info" @click="showMarkingProgressModal = true">
          <ChartBarIcon class="btn-icon" />
          标记进度
        </button>
        <button v-if="canSubmitMarking" class="mac-btn primary" :disabled="isLoading" @click="handleSubmitMarking">
          <TagIcon class="btn-icon" />
          提交标记
        </button>
        <button v-if="canStartTraining" class="mac-btn primary" :disabled="isLoading" @click="handleStartTraining">
          <PlayIcon class="btn-icon" />
          开始训练
        </button>
        <button v-if="canStop" class="mac-btn error" :disabled="isLoading" @click="handleStop">
          <StopIcon class="btn-icon" />
          终止任务
        </button>
        <button v-if="canRestart" class="mac-btn warning" :disabled="isLoading" @click="handleRestart">
          <ArrowPathIcon class="btn-icon" />
          重启任务
        </button>
        <button v-if="canCancel" class="mac-btn secondary" :disabled="isLoading" @click="handleCancel">
          <XMarkIcon class="btn-icon" />
          取消任务
        </button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-area">
      <!-- 左侧图片区域 -->
      <div class="images-section mac-card">
        <div class="section-header">
          <h3>
            训练图片
            <span class="image-count" v-if="task?.images?.length > 0">
              ({{ task.images.length }} 张)
            </span>
          </h3>
          <div class="header-actions">
            <!-- 批量操作按钮组，只有当有选中图片时显示 -->
            <template v-if="selectedImagesCount > 0">
              <div class="selected-count">已选择 {{ selectedImagesCount }} 张图片</div>
              <button class="mac-btn danger" @click="handleBatchDelete" title="批量删除">
                <TrashIcon class="btn-icon" />
                删除所选
              </button>
              <button class="mac-btn" @click="showBatchEditModal()" title="批量编辑文本" v-if="canEditMarkedText">
                <PencilIcon class="btn-icon" />
                批量编辑
              </button>
              <button class="mac-btn secondary" @click="clearImageSelection" title="取消选择">
                <XMarkIcon class="btn-icon" />
                取消选择
              </button>
              <div class="action-divider"></div>
            </template>
            <!-- 全选按钮 -->
            <template v-if="task?.images?.length > 0">
              <button class="mac-btn secondary" @click="toggleSelectAllImages" title="全选/取消全选">
                <input type="checkbox" :checked="isAllImagesSelected" class="select-all-checkbox" />
                <span>{{ isAllImagesSelected ? '取消全选' : '全选' }}</span>
              </button>
              <div class="action-divider"></div>
            </template>
            <button class="mac-btn" @click="showUploader" :title="uploadButtonTitle">
              <PlusIcon class="btn-icon" />
              上传图片
            </button>
          </div>
        </div>

        <!-- 图片网格 -->
        <ImageGrid ref="imageGridRef" :images="task?.images" :loading="isLoading" :status="task?.status"
          :marked-texts="markedTexts" :task-id="taskId" @delete="handleDeleteImage" @preview="handlePreview"
          @update:marked-text="handleUpdateMarkedText" @batch-delete="handleBatchDeleteImages"
          @batch-update-marked-text="handleBatchUpdateMarkedTexts" @selection-change="handleSelectionChange"
          @upload-files="handleDragUpload" />
      </div>

      <!-- 右侧信息区域 -->
      <div class="info-section">
        <!-- 基本信息卡片 -->
        <div class="mac-card">
          <h3>基本信息</h3>
          <div class="info-grid">
            <div class="info-row">
              <div class="info-item">
                <span class="label">创建时间</span>
                <span>{{ formatDate(task?.created_at) }}</span>
              </div>
              <div class="info-item">
                <span class="label">图片数量</span>
                <span>{{ task?.images?.length || 0 }} 张</span>
              </div>
            </div>
            <div class="info-row">
              <div class="info-item">
                <span class="label">标记资产</span>
                <div class="asset-info" v-if="task?.marking_asset">
                  <div class="asset-details">
                    <div class="asset-name">{{ task.marking_asset.name }}</div>
                    <div class="asset-ip">({{ task.marking_asset.ip }})</div>
                  </div>
                </div>
                <span v-else class="no-asset">暂无</span>
              </div>
              <div class="info-item">
                <span class="label">训练资产</span>
                <div class="asset-info" v-if="task?.training_asset">
                  <div class="asset-details">
                    <div class="asset-name">{{ task.training_asset.name }}</div>
                    <div class="asset-ip">({{ task.training_asset.ip }})</div>
                  </div>
                </div>
                <span v-else class="no-asset">暂无</span>
              </div>
            </div>
            <div class="info-row">
              <div class="info-item full-width training-steps">
                <span class="label">预估训练步数</span>
                <div class="training-steps-info">
                  <div class="steps-value">{{ estimatedTrainingSteps }}</div>
                  <div class="steps-formula">图片数量({{ task?.images?.length || 0 }}) × 重复次数({{ getRepeatNum }}) × 训练轮次({{
                    getMaxTrainEpochs }}) ÷ 批次大小({{ getTrainBatchSize }})</div>
                </div>
              </div>
            </div>
            <div class="info-item full-width">
              <span class="label">描述</span>
              <p class="description">{{ task?.description || '暂无描述' }}</p>
            </div>
          </div>
        </div>

        <!-- 任务配置卡片 -->
        <TaskConfigCard v-if="task" :task-id="taskId" :can-edit="canEditConfig" @config-changed="handleConfigChange" />
      </div>
    </div>

    <!-- 图片上传模态框 -->
    <BaseModal 
      v-model="showUploadModal" 
      title="上传训练图片" 
      :loading="false"
      :showFooter="false"
      :width="60"
    >
      <template #body>
        <ImageUploader 
          ref="uploaderRef" 
          :task-id="taskId" 
          @upload-complete="handleUploadComplete"
          @upload-progress="handleUploadProgress"
          @upload-error="handleUploadError"
        />
      </template>
    </BaseModal>

    <!-- 图片预览模态框 -->
    <ImageViewer v-model="showPreview" v-model:image="selectedImage"
      :images="previewSource === 'task' ? getTaskImagesUrls() : trainingModelImages" />

    <!-- 训练详情模态框 -->
    <BaseModal v-model="showTrainingDetailsModal" :width="70" :loading="false" :showFooter="false"
      :preventKeydownClose="showPreview">
      <template #body>
        <TrainingDetails :taskId="taskId" :taskName="task?.name || ''" :isTraining="task?.status === 'TRAINING'"
          @preview-image="handlePreview" @model-images-change="updateTrainingModelImages" />
      </template>
    </BaseModal>

    <!-- 标记进度模态框 -->
    <BaseModal v-model="showMarkingProgressModal" :width="70" :loading="false" :showFooter="false"
      :preventKeydownClose="showPreview">
      <template #body>
        <MarkingProgressDetails :taskId="taskId" :taskName="task?.name || ''" />
      </template>
    </BaseModal>

    <!-- 训练历史详情模态框 -->
    <BaseModal v-model="showHistoryDetailsModal" :width="70" :loading="false" :showFooter="false"
      :preventKeydownClose="showPreview">
      <template #body>
        <TrainingHistoryDetails v-if="selectedHistoryRecord" :historyRecord="selectedHistoryRecord"
          :taskName="task?.name || ''" @preview-image="handlePreview" />
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
/* eslint-disable */
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  TagIcon,
  PlayIcon,
  PlusIcon,
  XMarkIcon,
  ArrowPathIcon,
  StopIcon,
  TrashIcon,
  PencilIcon,
  ChartBarIcon,
  InformationCircleIcon,
  ClockIcon
} from '@heroicons/vue/24/outline'
import { tasksApi } from '@/api/tasks'
import { settingsApi } from '@/api/settings'
import { formatDate } from '@/utils/datetime'
import message from '@/utils/message'
import { emitter } from '@/utils/eventBus'
import ImageGrid from '@/components/tasks/ImageGrid.vue'
import ImageUploader from '@/components/tasks/ImageUploader.vue'
import ImageViewer from '@/components/tasks/ImageViewer.vue'
import BaseModal from '@/components/common/Modal.vue'
import TaskStatus from '@/components/tasks/TaskStatus.vue'
import TaskConfigCard from '@/components/tasks/TaskConfigCard.vue'
import TrainingDetails from '@/components/tasks/TrainingDetails.vue'
import MarkingProgressDetails from '@/components/tasks/MarkingProgressDetails.vue'
import TrainingHistoryDetails from '@/components/tasks/TrainingHistoryDetails.vue'
import TrainingHistoryDropdown from '@/components/tasks/TrainingHistoryDropdown.vue'
import {
  getStatusText,
  getStatusClass,
  isTaskActive as checkTaskActive,
  statusDetailColorMap
} from '@/utils/taskStatus'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.id)

// 状态
const task = ref(null)
const isLoading = ref(false)
const showUploadModal = ref(false)
const showPreview = ref(false)
const selectedImage = ref(null)
const uploaderRef = ref(null)
const refreshTimer = ref(null)
const REFRESH_INTERVAL = 5000 // 5秒刷新一次
const statusUpdating = ref(false) // 添加状态更新标志
const markedTexts = ref({}) // 打标文本数据
const localConfig = ref(null) // 本地缓存的配置数据

// 图片网格引用和批量操作相关
const imageGridRef = ref(null)
const selectedImagesCount = ref(0)

// 训练详情相关
const showTrainingDetailsModal = ref(false)
const showMarkingProgressModal = ref(false)

// 图片预览相关
const previewSource = ref('task') // 'task' 或 'training'
const trainingModelImages = ref([]) // 训练模型预览图片数组

// 计算预估训练步数
const estimatedTrainingSteps = computed(() => {
  if (!task.value?.images?.length) return '0';

  const imageCount = task.value.images.length;

  // 如果没有配置，返回计算中
  if (!trainingConfigData.value && !localConfig.value?.training_config) {
    return '计算中...';
  }

  // 获取训练参数
  const repeat_num = getTrainingConfigParam('repeat_num', 1);
  const max_train_epochs = getTrainingConfigParam('max_train_epochs', 10);
  const train_batch_size = getTrainingConfigParam('train_batch_size', 1);
  
  // 计算步数
  let steps = Math.floor(imageCount * repeat_num * max_train_epochs / train_batch_size);

  // 如果是奇数，加1
  return (steps + (steps % 2)).toLocaleString();
});

// 获取训练配置参数的通用函数
const getTrainingConfigParam = (paramName, defaultValue) => {
  const useGlobalConfig = localConfig.value?.use_global_training_config === true;
  // 使用全局训练配置变量代替task.value.settings.training_config
  const settingConfig = trainingConfigData.value;
  const trainingConfig = useGlobalConfig ?
    settingConfig :
    localConfig.value?.training_config || settingConfig;
  return trainingConfig?.[paramName] || settingConfig?.[paramName] || defaultValue;
};

// 获取训练配置中的重复次数
const getRepeatNum = computed(() => getTrainingConfigParam('repeat_num', 1));

// 获取训练配置中的最大训练轮次
const getMaxTrainEpochs = computed(() => getTrainingConfigParam('max_train_epochs', 10));

// 获取训练配置中的批次大小
const getTrainBatchSize = computed(() => getTrainingConfigParam('train_batch_size', 1));

// 计算是否可以查看训练详情
const canViewTrainingDetails = computed(() => {
  return ['TRAINING', 'COMPLETED'].includes(task.value?.status)
})

// 计算是否可以查看标记进度
const canViewMarkingProgress = computed(() => {
  return ['MARKING', 'MARKED', 'TRAINING', 'COMPLETED'].includes(task.value?.status)
})

// 历史记录相关
const showHistoryDropdown = ref(false);
const showHistoryDetailsModal = ref(false);
const historyBtn = ref(null);
const trainingHistory = ref([]);
const isLoadingHistory = ref(false);
const selectedHistoryRecord = ref(null);
const historyDropdownPosition = ref({
  top: '0px',
  left: '0px',
  zIndex: '1100'
});

// 计算是否可以查看训练历史
const canViewTrainingHistory = computed(() => {
  return taskId.value && task.value;
});

// 添加全局训练配置变量
const trainingConfigData = ref(null);

// 获取任务详情
const fetchTask = async () => {
  if (!taskId.value) return // 添加ID判断，防止无ID时请求

  try {
    isLoading.value = true
    const data = await tasksApi.getTaskById(taskId.value)
    if (data) {
      task.value = data
      // 如果任务状态是MARKED或之后，获取打标文本
      if (['MARKED', 'TRAINING', 'COMPLETED'].includes(data.status)) {
        await fetchMarkedTexts()
      }
      // 获取训练设置配置
      await fetchTrainingSettings()

      // 根据任务状态决定是否需要继续自动刷新
      if (needsAutoRefresh.value) {
        startAutoRefresh()
      } else {
        stopAutoRefresh()
      }
    } else {
      message.error('任务不存在')
      router.push('/tasks')
    }
  } catch (error) {
    message.error('获取任务详情失败')
    router.push('/tasks')
  } finally {
    isLoading.value = false
  }
}

// 获取打标文本
const fetchMarkedTexts = async () => {
  if (!taskId.value) return

  try {
    const data = await tasksApi.getMarkedTexts(taskId.value)
    if (data) {
      markedTexts.value = data
    }
  } catch (error) {
    console.error('获取打标文本失败', error)
    message.error('获取打标文本失败')
  }
}

// 只更新任务状态
const updateTaskStatus = async () => {
  if (!taskId.value || !task.value) return

  try {
    statusUpdating.value = true
    const statusData = await tasksApi.getTaskStatus(taskId.value)

    if (statusData) {
      // 只更新状态相关字段，而不替换整个task对象
      if (task.value.status !== statusData.status) {
        task.value.status = statusData.status
        task.value.status_history = statusData.status_history

        // 如果状态变为完成或错误，获取完整任务信息
        if (['COMPLETED', 'ERROR', 'MARKED'].includes(statusData.status)) {
          await fetchTask()
        }
      }

      // 根据任务状态决定是否需要继续自动刷新
      if (!needsAutoRefresh.value) {
        stopAutoRefresh()
      }
    }
  } catch (error) {
    console.error('更新任务状态失败', error)
  } finally {
    statusUpdating.value = false
  }
}

// 监听任务ID变化，立即获取对应任务详情
watch(taskId, (newId, oldId) => {
  // 仅当ID真实变化且有效时执行
  if (newId && newId !== oldId) {
    fetchTask()
  }
})

// 监听任务状态变化
watch(() => task.value?.status, (newStatus, oldStatus) => {
  if (newStatus !== oldStatus) {
    // 如果状态变为MARKED或之后，获取打标文本
    if (['MARKED', 'TRAINING', 'COMPLETED'].includes(newStatus) &&
      !['MARKED', 'TRAINING', 'COMPLETED'].includes(oldStatus)) {
      fetchMarkedTexts()
    }
    if (needsAutoRefresh.value) {
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  }
})

// 状态相关的计算属性
const canUploadImages = computed(() => {
  return task.value?.status === 'NEW'
})

const canSubmitMarking = computed(() => {
  return task.value?.status === 'NEW' && task.value?.images?.length > 0
})

const canStartTraining = computed(() => {
  return task.value?.status === 'MARKED' && !task.value?.auto_training
})

// 计算是否可以重启
const canRestart = computed(() => {
  return task.value?.status === 'ERROR' || task.value?.status === 'COMPLETED'
})

// 计算是否可以取消
const canCancel = computed(() => {
  return ['SUBMITTED', 'MARKED'].includes(task.value?.status)
})

// 计算是否可以停止任务
const canStop = computed(() => {
  return ['MARKING', 'TRAINING'].includes(task.value?.status)
})

// 上传按钮提示文本
const uploadButtonTitle = computed(() => {
  if (canUploadImages.value) {
    return '上传训练图片'
  }
  return `${getStatusText(task.value?.status)}状态不能上传图片`
})

// 显示上传器
const showUploader = () => {
  if (!canUploadImages.value) {
    message.warning(`${getStatusText(task.value?.status)}状态不能上传图片`)
    return
  }
  showUploadModal.value = true
}

// 上传完成处理
const handleUploadComplete = async (result) => {
  if (result.success) {
    message.success(`成功上传 ${result.uploaded} 个文件`)
    showUploadModal.value = false
  } else {
    if (result.uploaded > 0) {
      message.warning(`部分上传成功：成功 ${result.uploaded} 个，失败 ${result.failed} 个`)
    } else {
      message.error('所有文件上传失败')
    }
  }
  // 刷新任务数据
  await fetchTask()
}

// 上传进度处理
const handleUploadProgress = (progressData) => {
  // 可以在这里处理进度更新，例如显示全局进度条
  console.log('上传进度:', progressData)
}

// 上传错误处理
const handleUploadError = (error) => {
  console.error('上传错误:', error)
  message.error('上传过程中出现错误')
}

// 处理图片删除
const handleDeleteImage = async (imageId) => {
  try {
    await tasksApi.deleteImage(taskId.value, imageId)
    message.success('删除成功')
    fetchTask()
  } catch (error) {
    message.error('删除失败')
  }
}

// 处理图片预览
const handlePreview = (source, imageUrl) => {
  previewSource.value = source
  selectedImage.value = imageUrl
  showPreview.value = true
}

// 开始标记
const handleSubmitMarking = async () => {
  try {
    isLoading.value = true
    console.log('开始提交打标任务:', taskId.value)
    const response = await tasksApi.startMarking(taskId.value)
    console.log('打标任务响应成功:', response)

    message.success('标记任务已提交')
    task.value = response

    // 触发全局事件，通知TaskList组件刷新
    emitter.emit('task-status-changed', taskId.value)
  } catch (error) {
    console.error('打标任务失败:', error)
    console.error('错误类型:', error.constructor.name)
    console.error('错误消息:', error.message)
    console.error('完整错误对象:', error)
    message.error(error.message || '提交标记任务失败')
  } finally {
    isLoading.value = false
  }
}

// 开始训练
const handleStartTraining = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.startTraining(taskId.value)
    message.success('开始训练')
    task.value = response

    // 触发全局事件，通知TaskList组件刷新
    emitter.emit('task-status-changed', taskId.value)
  } catch (error) {
    // message.error(error)
  } finally {
    isLoading.value = false
  }
}

// 处理重启
const handleRestart = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.restartTask(taskId.value)
    message.success('任务已重启')
    task.value = response

    // 重启任务后立即完整获取任务信息
    await fetchTask()

    // 触发全局事件，通知TaskList组件刷新
    emitter.emit('task-status-changed', taskId.value)
  } catch (error) {
    // message.error(error)
  } finally {
    isLoading.value = false
  }
}

// 处理取消
const handleCancel = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.cancelTask(taskId.value)
    message.success('任务已取消')
    task.value = response

    // 触发全局事件，通知TaskList组件刷新
    emitter.emit('task-status-changed', taskId.value)
  } catch (error) {
    // message.error(error)
  } finally {
    isLoading.value = false
  }
}

// 处理停止任务
const handleStop = async () => {
  try {
    isLoading.value = true
    const response = await tasksApi.stopTask(taskId.value)
    message.success('任务已终止')
    task.value = response

    // 终止任务后立即完整获取任务信息
    await fetchTask()

    // 触发全局事件，通知TaskList组件刷新
    emitter.emit('task-status-changed', taskId.value)
  } catch (error) {
    message.error('终止任务失败')
  } finally {
    isLoading.value = false
  }
}

// 是否需要自动刷新
const needsAutoRefresh = computed(() => {
  return checkTaskActive(task.value?.status)
})

// 开始自动刷新
const startAutoRefresh = () => {
  stopAutoRefresh() // 先清除可能存在的定时器
  if (needsAutoRefresh.value) {
    refreshTimer.value = setInterval(async () => {
      if (!isLoading.value && !statusUpdating.value) { // 避免重复请求
        await updateTaskStatus() // 使用轻量级更新函数代替完整获取
      }
    }, REFRESH_INTERVAL)
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 处理更新打标文本
const handleUpdateMarkedText = async ({ filename, content }) => {
  if (!taskId.value || !filename) return

  try {
    isLoading.value = true
    await tasksApi.updateMarkedText(taskId.value, filename, content)

    // 更新本地缓存
    markedTexts.value[filename] = content

    message.success('打标文本更新成功')
  } catch (error) {
    console.error('更新打标文本失败', error)
    message.error('更新打标文本失败')
  } finally {
    isLoading.value = false
  }
}

// 添加可以编辑配置的计算属性
const canEditConfig = computed(() => {
  return ['NEW'].includes(task.value?.status);
});

// 处理批量删除图片
const handleBatchDeleteImages = async (imageIds) => {
  if (!imageIds || imageIds.length === 0) return

  try {
    isLoading.value = true
    await tasksApi.batchDeleteImages(taskId.value, imageIds)
    message.success(`成功删除 ${imageIds.length} 张图片`)
    await fetchTask() // 重新获取任务信息，刷新图片列表
  } catch (error) {
    console.error('批量删除图片失败:', error)
    message.error('批量删除图片失败')
  } finally {
    isLoading.value = false
  }
}

// 处理批量更新打标文本
const handleBatchUpdateMarkedTexts = async (updateData) => {
  if (!updateData || Object.keys(updateData).length === 0) return

  try {
    isLoading.value = true
    await tasksApi.batchUpdateMarkedTexts(taskId.value, updateData)
    message.success('批量更新打标文本成功')

    // 更新本地打标文本数据
    Object.entries(updateData).forEach(([filename, content]) => {
      markedTexts.value[filename] = content
    })
  } catch (error) {
    message.error('批量更新打标文本失败')
  } finally {
    isLoading.value = false
  }
}

// 处理图片选择变化
const handleSelectionChange = (count) => {
  selectedImagesCount.value = count
}

// 清除图片选择
const clearImageSelection = () => {
  if (imageGridRef.value) {
    imageGridRef.value.clearSelection()
  }
}

// 判断是否可以编辑打标文本
const canEditMarkedText = computed(() => {
  return ['MARKED', 'TRAINING', 'COMPLETED'].includes(task.value?.status)
})

// 处理批量删除
const handleBatchDelete = () => {
  if (imageGridRef.value) {
    // 只触发图片网格组件内部的批量删除逻辑
    imageGridRef.value.handleBatchDelete()
  }
}

// 处理拖拽上传图片
const handleDragUpload = async (files) => {
  if (!canUploadImages.value) {
    message.warning(`${getStatusText(task.value?.status)}状态不能上传图片`)
    return
  }

  if (!files || files.length === 0) return

  try {
    isLoading.value = true
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    await tasksApi.uploadImages(taskId.value, formData)
    message.success(`成功上传 ${files.length} 张图片`)
    await fetchTask() // 刷新任务数据
  } catch (error) {
    console.error('拖拽上传图片失败:', error)
    message.error('图片上传失败')
  } finally {
    isLoading.value = false
  }
}

// 全选相关计算属性
const isAllImagesSelected = computed(() => {
  if (!task.value?.images || task.value.images.length === 0) return false
  return selectedImagesCount.value === task.value.images.length
})

// 全选/取消全选
const toggleSelectAllImages = () => {
  if (!task.value?.images || task.value.images.length === 0) return

  if (isAllImagesSelected.value) {
    // 取消全选
    clearImageSelection()
  } else {
    // 全选
    if (imageGridRef.value) {
      imageGridRef.value.selectAllImages()
    }
  }
}

// 处理批量编辑模态框显示
const showBatchEditModal = () => {
  if (imageGridRef.value) {
    imageGridRef.value.showBatchEditModal = true
  }
}

// 处理训练模型图片变化
const updateTrainingModelImages = (images) => {
  trainingModelImages.value = images // 这些已经是图片路径的数组
}

// 获取任务图片的URL数组
const getTaskImagesUrls = () => {
  if (!task.value?.images || task.value.images.length === 0) return []
  
  // 如果是已标记状态，使用markedTexts中的key作为图片路径
  if (['MARKED', 'TRAINING', 'COMPLETED'].includes(task.value?.status) && 
      markedTexts.value && Object.keys(markedTexts.value).length > 0) {
    
    return task.value.images.map(image => {
      // 查找匹配的相对路径
      const relativePaths = Object.keys(markedTexts.value);
      const matchingPath = relativePaths.find(path => {
        // 从路径中提取文件名
        const pathFilename = path.split('/').pop();
        return pathFilename === image.filename;
      });
      
      // 如果找到匹配的路径，直接使用该路径作为图片URL
      if (matchingPath) {
        // 确保路径是图片格式，将所有后缀改为.png
        const pathWithoutExt = matchingPath.substring(0, matchingPath.lastIndexOf('.'));
        return pathWithoutExt + '.png';
      }
      
      // 如果没有找到匹配的路径，返回原始URL
      return image.preview_url;
    });
  }
  
  // 否则使用原始URL
  return task.value.images.map(image => image.preview_url)
}

// 获取训练历史
const fetchTrainingHistory = async () => {
  if (!taskId.value) return;

  try {
    isLoadingHistory.value = true;
    const data = await tasksApi.getTaskTrainingHistory(taskId.value);
    console.log("历史记录", data)
    if (data) {
      trainingHistory.value = data;
    }
  } catch (error) {
    console.error('获取训练历史失败:', error);
    message.error('获取训练历史失败');
  } finally {
    isLoadingHistory.value = false;
  }
};

// 切换历史记录下拉菜单
const toggleHistoryDropdown = async () => {
  showHistoryDropdown.value = !showHistoryDropdown.value;

  if (showHistoryDropdown.value) {
    // 加载历史数据
    if (trainingHistory.value.length === 0) {
      await fetchTrainingHistory();
    }

    // 计算下拉菜单位置
    nextTick(() => {
      updateHistoryDropdownPosition();
      document.addEventListener('click', handleClickOutside);
    });
  } else {
    document.removeEventListener('click', handleClickOutside);
  }
};

// 更新历史下拉菜单位置
const updateHistoryDropdownPosition = () => {
  if (!historyBtn.value) return;

  const btnRect = historyBtn.value.getBoundingClientRect();

  historyDropdownPosition.value = {
    top: `${btnRect.bottom + window.scrollY + 8}px`,
    left: `${btnRect.right - 280 + window.scrollX}px`, // 右对齐，假设下拉菜单宽度为280px
    zIndex: '1100' // 确保足够高的z-index值
  };
};

// 修改点击外部区域关闭下拉菜单处理函数
const handleClickOutside = (event) => {
  if (historyBtn.value && !historyBtn.value.contains(event.target) &&
    !event.target.closest('.history-dropdown')) {
    showHistoryDropdown.value = false;
    document.removeEventListener('click', handleClickOutside);
  }
};

// 打开历史详情模态框
const openHistoryDetails = (record) => {
  selectedHistoryRecord.value = record;
  showHistoryDetailsModal.value = true;
  showHistoryDropdown.value = false;
  document.removeEventListener('click', handleClickOutside);
};

// 监听窗口大小变化，更新下拉菜单位置
const handleResize = () => {
  if (showHistoryDropdown.value) {
    updateHistoryDropdownPosition();
  }
};

// 初始化
onMounted(() => {
  if (taskId.value) {
    fetchTask()
    startAutoRefresh()
  }
  window.addEventListener('resize', handleResize);
})

// 清理
onUnmounted(() => {
  stopAutoRefresh()
  document.removeEventListener('click', handleClickOutside);
  window.removeEventListener('resize', handleResize);
})

// 处理配置变更
const handleConfigChange = (newConfig) => {
  // 将配置卡片传来的配置同步到本地配置
  if (!localConfig.value) localConfig.value = {};
  console.log("更新配置", newConfig)
  // 只关注训练配置，因为打标配置不影响步数计算
  localConfig.value = newConfig;
};

// 添加从settings接口获取训练配置的方法
const fetchTrainingSettings = async () => {
  if (!taskId.value) return;

  try {
    const trainingConfig = await settingsApi.getTaskTrainingConfig(taskId.value);
    if (trainingConfig) {
      // 直接保存到全局变量
      trainingConfigData.value = trainingConfig;
    }
  } catch (error) {
    console.error('获取训练设置失败:', error);
  }
};
</script>

<style scoped>
.task-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
  /* 修改为hidden，防止整个页面滚动 */
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0px 16px;
  flex-shrink: 0;
  height: auto;
  /* 调整为自适应高度 */
  min-height: 70px;
  /* 确保有足够高度显示状态图标和名称 */
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

/* 添加中间部分样式 */
.center-section {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 2;
  position: relative;
  padding: 5px 0;
  /* 增加上下内边距 */
}

.status-timeline {
  position: relative;
  cursor: pointer;
}

.task-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.right-section {
  display: flex;
  gap: 12px;
  flex: 1;
  justify-content: flex-end;
}

.content-area {
  display: grid;
  grid-template-columns: 3fr 1fr;
  /* 修改比例，从2:1改为3:1 */
  gap: 20px;
  flex: 1;
  overflow: hidden;
}

.images-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: auto;
  /* 修改为auto，允许左侧区域在需要时滚动 */
  height: 100%;
  /* 确保高度为100% */
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  display: flex;
  align-items: center;
}

.image-count {
  font-size: 14px;
  font-weight: normal;
  color: var(--text-secondary);
  margin-left: 6px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 280px;
  /* 减小最小宽度 */
  height: 100%;
  /* 确保高度为100% */
  overflow-y: auto;
  /* 允许右侧区域单独滚动 */
  padding-right: 6px;
  /* 为滚动条留出空间 */
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.info-row {
  display: flex;
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.info-item.full-width {
  flex-basis: 100%;
}

.info-item .label {
  font-size: 13px;
  color: var(--text-secondary);
}

.description {
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
  color: var(--text-primary);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.btn-icon.is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 状态徽章样式 */
.task-status-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.task-status-badge.new {
  background: v-bind('statusDetailColorMap.NEW.background');
  color: v-bind('statusDetailColorMap.NEW.color');
}

.task-status-badge.submitted {
  background: v-bind('statusDetailColorMap.SUBMITTED.background');
  color: v-bind('statusDetailColorMap.SUBMITTED.color');
}

.task-status-badge.marking {
  background: v-bind('statusDetailColorMap.MARKING.background');
  color: v-bind('statusDetailColorMap.MARKING.color');
}

.task-status-badge.marked {
  background: v-bind('statusDetailColorMap.MARKED.background');
  color: v-bind('statusDetailColorMap.MARKED.color');
}

.task-status-badge.training {
  background: v-bind('statusDetailColorMap.TRAINING.background');
  color: v-bind('statusDetailColorMap.TRAINING.color');
}

.task-status-badge.completed {
  background: v-bind('statusDetailColorMap.COMPLETED.background');
  color: v-bind('statusDetailColorMap.COMPLETED.color');
}

.task-status-badge.error {
  background: v-bind('statusDetailColorMap.ERROR.background');
  color: v-bind('statusDetailColorMap.ERROR.color');
}

.asset-info {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.asset-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.asset-name {
  font-weight: 500;
  word-break: break-word;
}

.asset-ip {
  font-size: 13px;
  color: var(--text-secondary);
}

.no-asset {
  font-size: 14px;
  color: var(--text-secondary);
  font-style: italic;
}

/* 预估训练步数样式 */
.training-steps {
  background-color: var(--background-tertiary);
  border-radius: var(--radius-md);
  padding: 10px 8px;
  transition: var(--theme-transition);
}

.training-steps-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.steps-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-color);
  transition: var(--theme-transition);
}

.steps-formula {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  transition: var(--theme-transition);
}

.mac-btn.error {
  background-color: var(--danger-color);
  color: var(--text-primary-inverse);
  transition: var(--theme-transition);
}

.mac-btn.error:hover {
  background-color: color-mix(in srgb, var(--danger-color) 80%, black);
  color: var(--text-primary-inverse);
  transform: translateY(-1px);
}

.mac-btn.warning {
  background-color: color-mix(in srgb, var(--warning-color) 15%, var(--background-secondary));
  color: var(--warning-color);
  border: 1px solid var(--warning-color);
  transition: var(--theme-transition);
}

.mac-btn.warning:hover {
  background-color: color-mix(in srgb, var(--warning-color) 25%, var(--background-secondary));
  color: var(--warning-color);
  transform: translateY(-1px);
}

.mac-btn.warning:disabled {
  background-color: var(--background-tertiary);
  color: var(--text-tertiary);
  border-color: var(--border-color);
  opacity: 0.5;
  cursor: not-allowed;
}

.task-status-badge.submitted {
  background: var(--status-info-bg);
  color: var(--info-color);
  border: 1px solid color-mix(in srgb, var(--info-color) 30%, transparent);
}

.mac-btn.secondary {
  background-color: var(--background-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  transition: var(--theme-transition);
}

.mac-btn.secondary:hover {
  background-color: var(--background-quaternary);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.mac-btn.secondary:disabled {
  background-color: var(--background-tertiary);
  color: var(--text-tertiary);
  border-color: var(--border-color);
  opacity: 0.5;
  cursor: not-allowed;
}

.mac-btn:not(:disabled):hover {
  background: var(--background-tertiary);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-divider {
  width: 1px;
  height: 24px;
  background-color: var(--border-color);
  margin: 0 8px;
}

.selected-count {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-right: 8px;
}

.mac-btn.danger {
  background-color: var(--error-bg);
  color: var(--error-color);
}

.mac-btn.danger:hover {
  background-color: var(--error-bg-hover);
  color: var(--error-color-hover);
}

/* 删除批量编辑模态框样式 */

.select-all-checkbox {
  margin-right: 6px;
  vertical-align: middle;
}

.mac-btn.info {
  background-color: var(--info-bg);
  color: var(--info-color);
}

.mac-btn.info:hover {
  background-color: var(--info-bg-hover);
  color: var(--info-color-hover);
}

.mac-btn.primary {
  background-color: var(--primary-color);
  color: var(--text-primary-inverse);
}

.mac-btn.primary:hover {
  background-color: var(--primary-color-hover);
  color: var(--text-primary-inverse);
}

.auto-training-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background-color: var(--info-bg);
  border-radius: 6px;
  color: var(--info-color);
  font-size: 14px;
  font-weight: 500;
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--info-color);
}

/* 历史记录下拉菜单相关样式 */
.history-dropdown-container {
  position: relative;
}

/* 移除其他不需要的样式 */
</style>