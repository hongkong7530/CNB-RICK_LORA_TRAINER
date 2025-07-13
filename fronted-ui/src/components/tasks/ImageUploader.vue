<template>
  <div class="uploader-container">
    <!-- 拖拽上传区域 -->
    <div 
      class="upload-zone"
      :class="{ 
        'is-dragover': isDragover,
        'is-disabled': disabled || isUploading
      }"
      @dragenter.prevent="handleDragEnter"
      @dragleave.prevent="handleDragLeave"
      @dragover.prevent
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <div class="upload-content">
        <CloudArrowUpIcon class="upload-icon" />
        <p class="upload-text">
          拖拽文件到此处或
          <span class="upload-link">点击上传</span>
        </p>
        <p class="upload-hint">
          支持 jpg、png、webp 格式，单次最多可上传 50 张图片
        </p>
      </div>
    </div>

    <!-- 上传进度 -->
    <div v-if="isUploading" class="upload-progress-section">
      <div class="progress-header">
        <span class="progress-title">正在上传 {{ currentBatch }}/{{ totalBatches }} 批次</span>
        <span class="progress-stats">{{ uploadedCount }}/{{ totalFiles }} 张图片</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${uploadProgress}%` }"></div>
      </div>
      <div class="progress-details">
        <span class="progress-text">{{ uploadProgress.toFixed(1) }}%</span>
        <span v-if="uploadSpeed > 0" class="upload-speed">{{ formatUploadSpeed(uploadSpeed) }}</span>
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-if="fileList.length" class="file-list">
      <div 
        v-for="(file, index) in fileList" 
        :key="index"
        class="file-item"
        :class="{ 
          'upload-success': file.uploadStatus === 'success',
          'upload-error': file.uploadStatus === 'error',
          'upload-uploading': file.uploadStatus === 'uploading'
        }"
      >
        <!-- 文件预览 -->
        <div class="file-preview">
          <img :src="file.preview" :alt="file.name">
          <!-- 上传状态覆盖层 -->
          <div v-if="file.uploadStatus" class="status-overlay">
            <CheckIcon v-if="file.uploadStatus === 'success'" class="status-icon success" />
            <ExclamationTriangleIcon v-else-if="file.uploadStatus === 'error'" class="status-icon error" />
            <div v-else-if="file.uploadStatus === 'uploading'" class="uploading-spinner"></div>
          </div>
        </div>
        
        <!-- 文件信息 -->
        <div class="file-info">
          <span class="file-name text-ellipsis" :title="file.name">
            {{ file.name }}
          </span>
          <span class="file-size">{{ formatFileSize(file.size) }}</span>
          <span v-if="file.errorMessage" class="error-message">{{ file.errorMessage }}</span>
        </div>
        
        <!-- 操作按钮 -->
        <div class="file-actions">
          <!-- 重试按钮 -->
          <button 
            v-if="file.uploadStatus === 'error'" 
            class="retry-btn"
            @click="retryFile(index)"
            :disabled="isUploading"
            title="重新上传"
          >
            <ArrowPathIcon class="btn-icon" />
          </button>
          <!-- 删除按钮 -->
          <button 
            class="remove-btn"
            @click="removeFile(index)"
            :disabled="isUploading && file.uploadStatus === 'uploading'"
          >
            <XMarkIcon class="btn-icon" />
          </button>
        </div>
      </div>
    </div>

    <!-- 上传操作区域 -->
    <div v-if="fileList.length && !isUploading" class="upload-actions">
      <div class="file-summary">
        <span class="file-count">已选择 {{ fileList.length }} 个文件</span>
        <span v-if="failedFiles.length" class="failed-count">{{ failedFiles.length }} 个失败</span>
      </div>
      <div class="action-buttons">
        <button 
          v-if="failedFiles.length" 
          class="mac-btn secondary"
          @click="retryFailedFiles"
          :disabled="isUploading"
        >
          重试失败文件
        </button>
        <button 
          class="mac-btn primary"
          @click="startUpload"
          :disabled="isUploading || !pendingFiles.length"
        >
          {{ pendingFiles.length ? `上传 ${pendingFiles.length} 个文件` : '所有文件已上传' }}
        </button>
      </div>
    </div>

    <!-- 隐藏的文件输入框 -->
    <input
      ref="fileInput"
      type="file"
      multiple
      accept="image/*"
      class="hidden-input"
      @change="handleFileSelect"
    >
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { CloudArrowUpIcon, XMarkIcon, CheckIcon, ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'
import { tasksApi } from '@/api/tasks'
import message from '@/utils/message'

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['upload-complete', 'upload-progress', 'upload-error'])

// 状态
const isDragover = ref(false)
const fileList = ref([])
const fileInput = ref(null)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadedCount = ref(0)
const currentBatch = ref(0)
const totalBatches = ref(0)
const totalFiles = ref(0)
const uploadSpeed = ref(0)
const uploadStartTime = ref(0)

// 批量上传配置
const BATCH_SIZE = 5
const MAX_RETRY_ATTEMPTS = 3

// 计算属性
const pendingFiles = computed(() => 
  fileList.value.filter(file => !file.uploadStatus || file.uploadStatus === 'pending')
)

const failedFiles = computed(() => 
  fileList.value.filter(file => file.uploadStatus === 'error')
)

const successFiles = computed(() => 
  fileList.value.filter(file => file.uploadStatus === 'success')
)

// 触发文件选择
const triggerFileInput = () => {
  if (props.disabled || isUploading.value) return
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  addFiles(files)
  e.target.value = '' // 重置input
}

// 处理拖拽
const handleDragEnter = () => {
  if (props.disabled || isUploading.value) return
  isDragover.value = true
}

const handleDragLeave = () => {
  isDragover.value = false
}

const handleDrop = (e) => {
  if (props.disabled || isUploading.value) return
  isDragover.value = false
  const files = Array.from(e.dataTransfer.files)
  addFiles(files)
}

// 添加文件
const addFiles = (files) => {
  // 检查文件数量限制
  if (files.length + fileList.value.length > 50) {
    message.warning('最多只能上传50张图片')
    return
  }

  // 过滤图片文件
  const imageFiles = files.filter(file => {
    const isImage = file.type.startsWith('image/')
    const isValidSize = file.size <= 50 * 1024 * 1024 // 50MB 限制
    
    if (!isImage) {
      console.warn(`跳过非图片文件: ${file.name}`)
    }
    if (!isValidSize) {
      console.warn(`文件过大: ${file.name}`)
      message.warning(`文件 ${file.name} 超过50MB限制`)
    }
    
    return isImage && isValidSize
  })
  
  // 创建预览
  const newFiles = imageFiles.map(file => {
    try {
      const preview = URL.createObjectURL(file)
      return {
        file,
        name: file.name,
        size: file.size,
        preview,
        uploadStatus: 'pending',
        retryCount: 0,
        errorMessage: null
      }
    } catch (error) {
      console.error(`创建预览失败: ${file.name}`, error)
      return null
    }
  }).filter(Boolean) // 过滤掉创建预览失败的文件
  
  fileList.value.push(...newFiles)
}

// 移除文件
const removeFile = (index) => {
  const file = fileList.value[index]
  if (file?.preview) {
    try {
      URL.revokeObjectURL(file.preview)
    } catch (error) {
      console.error('清理预览失败:', error)
    }
  }
  fileList.value.splice(index, 1)
}

// 重试单个文件
const retryFile = async (index) => {
  const file = fileList.value[index]
  if (!file || file.retryCount >= MAX_RETRY_ATTEMPTS) {
    message.warning('文件重试次数已达上限')
    return
  }

  file.uploadStatus = 'pending'
  file.errorMessage = null
  await uploadSingleFile(file)
}

// 重试失败文件
const retryFailedFiles = async () => {
  const failed = failedFiles.value
  if (!failed.length) return

  // 重置失败文件状态
  failed.forEach(file => {
    if (file.retryCount < MAX_RETRY_ATTEMPTS) {
      file.uploadStatus = 'pending'
      file.errorMessage = null
    }
  })

  await startUpload()
}

// 开始上传
const startUpload = async () => {
  const filesToUpload = pendingFiles.value
  if (!filesToUpload.length) {
    message.info('没有需要上传的文件')
    return
  }

  isUploading.value = true
  uploadStartTime.value = Date.now()
  uploadedCount.value = successFiles.value.length
  totalFiles.value = fileList.value.length
  
  // 分批处理
  const batches = []
  for (let i = 0; i < filesToUpload.length; i += BATCH_SIZE) {
    batches.push(filesToUpload.slice(i, i + BATCH_SIZE))
  }
  
  totalBatches.value = batches.length
  currentBatch.value = 0

  try {
    for (let i = 0; i < batches.length; i++) {
      currentBatch.value = i + 1
      await uploadBatch(batches[i])
      
      // 更新进度
      updateProgress()
    }

    // 上传完成
    const successCount = successFiles.value.length
    const failedCount = failedFiles.value.length
    
    if (failedCount === 0) {
      message.success(`成功上传 ${successCount} 个文件`)
      emit('upload-complete', { success: true, uploaded: successCount, failed: 0 })
    } else {
      message.warning(`上传完成：成功 ${successCount} 个，失败 ${failedCount} 个`)
      emit('upload-complete', { success: false, uploaded: successCount, failed: failedCount })
    }
    
  } catch (error) {
    console.error('上传过程出错:', error)
    message.error('上传过程中出现错误')
    emit('upload-error', error)
  } finally {
    isUploading.value = false
    currentBatch.value = 0
    uploadProgress.value = 0
  }
}

// 上传单批文件
const uploadBatch = async (batch) => {
  const formData = new FormData()
  batch.forEach(fileItem => {
    formData.append('files', fileItem.file)
    fileItem.uploadStatus = 'uploading'
  })

  try {
    const result = await tasksApi.uploadImages(props.taskId, formData)
    
    // 标记成功
    batch.forEach(fileItem => {
      fileItem.uploadStatus = 'success'
      uploadedCount.value++
    })
    
  } catch (error) {
    console.error('批次上传失败:', error)
    
    // 如果是整批失败，尝试单个文件上传
    for (const fileItem of batch) {
      await uploadSingleFile(fileItem)
    }
  }
}

// 上传单个文件
const uploadSingleFile = async (fileItem) => {
  if (fileItem.retryCount >= MAX_RETRY_ATTEMPTS) {
    fileItem.uploadStatus = 'error'
    fileItem.errorMessage = '重试次数已达上限'
    return
  }

  const formData = new FormData()
  formData.append('files', fileItem.file)
  fileItem.uploadStatus = 'uploading'
  fileItem.retryCount++

  try {
    await tasksApi.uploadImages(props.taskId, formData)
    fileItem.uploadStatus = 'success'
    fileItem.errorMessage = null
    uploadedCount.value++
  } catch (error) {
    console.error(`文件 ${fileItem.name} 上传失败:`, error)
    fileItem.uploadStatus = 'error'
    fileItem.errorMessage = getErrorMessage(error)
  }
}

// 更新上传进度
const updateProgress = () => {
  const completed = successFiles.value.length
  const total = totalFiles.value
  
  if (total > 0) {
    uploadProgress.value = (completed / total) * 100
    
    // 计算上传速度
    const elapsed = (Date.now() - uploadStartTime.value) / 1000
    if (elapsed > 0) {
      uploadSpeed.value = completed / elapsed
    }
  }
  
  emit('upload-progress', {
    progress: uploadProgress.value,
    uploaded: completed,
    total: total,
    speed: uploadSpeed.value
  })
}

// 获取错误消息
const getErrorMessage = (error) => {
  if (error.response?.data?.msg) {
    return error.response.data.msg
  }
  if (error.message) {
    return error.message
  }
  return '上传失败'
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return ''
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

// 格式化上传速度
const formatUploadSpeed = (filesPerSecond) => {
  if (filesPerSecond < 1) {
    return `${(filesPerSecond * 60).toFixed(1)} 文件/分钟`
  }
  return `${filesPerSecond.toFixed(1)} 文件/秒`
}

// 组件卸载时清理预览URL
onBeforeUnmount(() => {
  fileList.value.forEach(file => {
    try {
      if (file?.preview) {
        URL.revokeObjectURL(file.preview)
      }
    } catch (error) {
      console.error('清理预览失败:', error)
    }
  })
})

// 暴露方法给父组件
defineExpose({
  startUpload,
  getFileList: () => fileList.value,
  getUploadStats: () => ({
    total: fileList.value.length,
    uploaded: successFiles.value.length,
    failed: failedFiles.value.length,
    pending: pendingFiles.value.length
  })
})
</script>

<style scoped>
.uploader-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-zone {
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 32px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-zone:hover:not(.is-disabled) {
  border-color: var(--primary-color);
}

.upload-zone.is-dragover {
  border-color: var(--primary-color);
  background: rgba(var(--primary-color-rgb), 0.05);
}

.upload-zone.is-disabled {
  cursor: not-allowed;
  opacity: 0.7;
  background: var(--background-secondary);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
}

.upload-icon {
  width: 48px;
  height: 48px;
  color: var(--text-secondary);
}

.upload-text {
  margin: 0;
  color: var(--text-primary);
}

.upload-link {
  color: var(--primary-color);
  text-decoration: underline;
}

.upload-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

/* 上传进度区域 */
.upload-progress-section {
  padding: 16px;
  background: var(--background-secondary);
  border-radius: 8px;
  border-left: 3px solid var(--primary-color);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-title {
  font-weight: 500;
  color: var(--text-primary);
}

.progress-stats {
  font-size: 14px;
  color: var(--text-secondary);
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: var(--background-tertiary);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), var(--success-color));
  transition: width 0.3s ease;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--primary-color);
}

.upload-speed {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 文件列表 */
.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: var(--background-tertiary);
  border-radius: 6px;
  transition: all 0.3s ease;
  position: relative;
}

.file-item.upload-success {
  background: rgba(var(--success-color-rgb), 0.1);
  border-left: 3px solid var(--success-color);
}

.file-item.upload-error {
  background: rgba(var(--danger-color-rgb), 0.1);
  border-left: 3px solid var(--danger-color);
}

.file-item.upload-uploading {
  background: rgba(var(--primary-color-rgb), 0.1);
  border-left: 3px solid var(--primary-color);
}

.file-preview {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
}

.file-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.status-icon {
  width: 20px;
  height: 20px;
}

.status-icon.success {
  color: var(--success-color);
}

.status-icon.error {
  color: var(--danger-color);
}

.uploading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-size: 14px;
  color: var(--text-primary);
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary);
}

.error-message {
  font-size: 11px;
  color: var(--danger-color);
}

.file-actions {
  display: flex;
  gap: 4px;
}

.retry-btn, .remove-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.retry-btn:hover {
  background: var(--background-secondary);
  color: var(--primary-color);
}

.remove-btn:hover {
  background: var(--background-secondary);
  color: var(--danger-color);
}

.retry-btn:disabled, .remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  width: 14px;
  height: 14px;
}

/* 上传操作区域 */
.upload-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--background-secondary);
  border-radius: 6px;
}

.file-summary {
  display: flex;
  gap: 12px;
  font-size: 14px;
}

.file-count {
  color: var(--text-primary);
}

.failed-count {
  color: var(--danger-color);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.mac-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mac-btn.primary {
  background: var(--primary-color);
  color: white;
}

.mac-btn.primary:hover:not(:disabled) {
  background: var(--primary-color-dark);
}

.mac-btn.secondary {
  background: var(--background-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.mac-btn.secondary:hover:not(:disabled) {
  background: var(--background-secondary);
}

.mac-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hidden-input {
  display: none;
}

/* 滚动条样式 */
.file-list::-webkit-scrollbar {
  width: 6px;
}

.file-list::-webkit-scrollbar-track {
  background: transparent;
}

.file-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.file-list::-webkit-scrollbar-thumb:hover {
  background: var(--border-color-dark);
}

/* 文字省略 */
.text-ellipsis {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>