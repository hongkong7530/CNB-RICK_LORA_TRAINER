<template>
  <div class="file-uploader">
    <div
      class="upload-area"
      :class="{ 'is-dragover': isDragOver, 'has-file': !!selectedFile }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInput"
        type="file"
        class="file-input"
        @change="handleFileChange"
        :accept="accept"
      />
      
      <div v-if="!selectedFile" class="upload-placeholder">
        <DocumentPlusIcon class="upload-icon" />
        <div class="upload-text">
          <p>点击或拖拽文件到此处上传</p>
          <p class="upload-hint">{{ acceptHint }}</p>
        </div>
      </div>
      
      <div v-else class="selected-file">
        <DocumentIcon class="file-icon" />
        <div class="file-info">
          <div class="file-name">{{ selectedFile.name }}</div>
          <div class="file-meta">{{ formatFileSize(selectedFile.size) }}</div>
        </div>
        <button type="button" class="remove-btn" @click.stop="removeFile">
          <XMarkIcon class="remove-icon" />
        </button>
      </div>
    </div>
    
    <div v-if="isUploading" class="upload-progress">
      <div class="progress-bar">
        <div class="progress-value" :style="{ width: `${uploadProgress}%` }"></div>
      </div>
      <div class="progress-text">{{ uploadProgress }}%</div>
    </div>
    
    <div class="upload-actions" v-if="selectedFile && !isUploading && !autoUpload">
      <button 
        type="button" 
        class="mac-btn primary" 
        @click="upload"
      >
        上传文件
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { DocumentPlusIcon, DocumentIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { uploadApi } from '@/api/upload'
import message from '@/utils/message'

const props = defineProps({
  accept: {
    type: String,
    default: '*'
  },
  autoUpload: {
    type: Boolean,
    default: false
  },
  description: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['file-selected', 'upload-success', 'upload-error', 'upload-progress', 'file-removed'])

const fileInput = ref(null)
const selectedFile = ref(null)
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)

// 计算接受的文件类型提示
const acceptHint = computed(() => {
  if (props.accept === '*') return '支持所有文件类型'
  
  const types = props.accept.split(',').map(type => {
    return type.trim().replace('.', '').toUpperCase()
  })
  
  return `支持的文件类型: ${types.join(', ')}`
})

// 触发文件选择
const triggerFileInput = () => {
  if (!isUploading.value) {
    fileInput.value.click()
  }
}

// 处理文件选择
const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    emit('file-selected', file)
    
    if (props.autoUpload) {
      upload()
    }
  }
}

// 处理拖拽
const handleDragOver = () => {
  if (!isUploading.value) {
    isDragOver.value = true
  }
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event) => {
  if (isUploading.value) return
  
  isDragOver.value = false
  const file = event.dataTransfer.files[0]
  if (file) {
    selectedFile.value = file
    emit('file-selected', file)
    
    if (props.autoUpload) {
      upload()
    }
  }
}

// 移除已选文件
const removeFile = () => {
  if (isUploading.value) return
  
  selectedFile.value = null
  fileInput.value.value = '' // 清空input
  emit('file-removed')
}

// 上传文件
const upload = async () => {
  if (!selectedFile.value || isUploading.value) return
  
  try {
    isUploading.value = true
    uploadProgress.value = 0
    
    // 创建一个模拟进度的函数
    const simulateProgress = () => {
      const interval = setInterval(() => {
        if (uploadProgress.value < 90) {
          uploadProgress.value += 5
          emit('upload-progress', uploadProgress.value)
        } else {
          clearInterval(interval)
        }
      }, 200)
      
      return interval
    }
    
    const progressInterval = simulateProgress()
    
    const result = await uploadApi.uploadFile(selectedFile.value, props.description)
    
    // 清除进度模拟
    clearInterval(progressInterval)
    uploadProgress.value = 100
    emit('upload-progress', 100)
    
    // 延迟一点以显示100%进度
    setTimeout(() => {
      isUploading.value = false
      emit('upload-success', result.file)
      message.success('文件上传成功')
    }, 300)
    
  } catch (error) {
    isUploading.value = false
    uploadProgress.value = 0
    emit('upload-error', error)
    message.error('文件上传失败')
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`
}

// 暴露方法
defineExpose({
  upload,
  removeFile,
  reset: removeFile
})
</script>

<style scoped>
.file-uploader {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upload-area {
  position: relative;
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-area:hover {
  border-color: var(--primary-color);
  background-color: var(--background-tertiary);
}

.is-dragover {
  border-color: var(--primary-color);
  background-color: var(--background-tertiary);
}

.has-file {
  border-style: solid;
  border-color: var(--border-color-light);
}

.file-input {
  display: none;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  text-align: center;
}

.upload-icon {
  width: 48px;
  height: 48px;
  color: var(--text-tertiary);
}

.upload-text {
  font-size: 14px;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.selected-file {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.file-icon {
  width: 32px;
  height: 32px;
  color: var(--primary-color);
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.remove-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: var(--background-tertiary);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  color: var(--danger-color);
  background: color-mix(in srgb, var(--danger-color) 10%, transparent);
}

.remove-icon {
  width: 16px;
  height: 16px;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background-color: var(--background-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.progress-value {
  height: 100%;
  background-color: var(--primary-color);
  transition: width 0.2s ease;
}

.progress-text {
  font-size: 12px;
  color: var(--text-tertiary);
  min-width: 36px;
  text-align: right;
}

.upload-actions {
  display: flex;
  justify-content: flex-end;
}
</style> 