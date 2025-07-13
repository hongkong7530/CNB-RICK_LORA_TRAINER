<template>
  <div 
    class="image-grid-container"
    :class="{ 'drag-over': isDragging }"
    @dragenter.prevent="handleDragEnter"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
    ref="gridContainer"
  >
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <LoadingSpinner />
      <span>加载中...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!images?.length" class="empty-state">
      <PhotoIcon class="empty-icon" />
      <span>暂无图片</span>
      <p v-if="canDragUpload" class="drag-hint">拖拽图片到此处上传</p>
      <p v-else class="drag-hint status-hint">当前状态不允许上传图片</p>
    </div>

    <!-- 图片网格 -->
    <div v-else>
      <!-- 批量操作区域与图片网格 -->
      <div class="image-grid">
        <div 
          v-for="image in images" 
          :key="image.id"
          class="image-item"
          :class="{ 'selected': selectedImages.includes(image.id) }"
        >
          <!-- 图片容器 -->
          <div class="image-container">
            <!-- 多选框 -->
            <label 
              class="select-checkbox"
              @click.stop
              title="选择图片"
            >
              <input 
                type="checkbox" 
                :checked="selectedImages.includes(image.id)"
                @change="toggleSelectImage(image.id)"
              />
              <span class="checkbox-custom"></span>
            </label>
            
            <!-- 图片分辨率显示 -->
            <div 
              class="image-resolution" 
              v-if="image.width && image.height"
            >
              {{ image.width }}×{{ image.height }}
            </div>
            
            <!-- 删除按钮 -->
            <button 
              v-if="canDelete"
              class="delete-btn"
              @click.stop="handleDelete(image)"
              title="删除"
            >
              <TrashIcon class="btn-icon" />
            </button>
            
            <!-- 图片 -->
            <img 
              :src="getImageUrl(image)" 
              :alt="image.filename"
              @click="handlePreview(getImageUrl(image))"
              @load="handleImageLoad($event, image)"
            >
          </div>
          
          <!-- 图片信息 -->
          <div class="image-info">
            <span class="image-name text-ellipsis" :title="image.filename">
              {{ image.filename }}
            </span>
            
            <!-- 打标文本（只在MARKED及之后的状态显示） -->
            <div v-if="showMarkedText" class="marked-text-container">
              <div 
                class="marked-text" 
                v-html="highlightMarkedText(getMarkedTextContent(image.filename))"
                @mouseenter="showFullTextTooltip($event, image.filename)"
                @mouseleave="hideTooltipWithDelay"
              ></div>
              <div class="text-actions">
                <button 
                  class="text-toggle" 
                  @click.stop="copyMarkedText(image.filename)"
                  title="复制提示词"
                >
                  复制
                </button>
                <button
                  v-if="canEdit"
                  class="text-edit"
                  @click="startEditText(image.filename)"
                >
                  编辑
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 拖拽上传提示覆盖层 -->
    <div v-if="isDragging" class="drag-overlay">
      <div class="drag-overlay-content">
        <template v-if="canDragUpload">
          <UploadIcon class="upload-icon" />
          <span>释放鼠标上传图片</span>
        </template>
        <template v-else>
          <XMarkIcon class="upload-icon error-icon" />
          <span>当前状态不可上传图片</span>
        </template>
      </div>
    </div>
    
    <!-- 使用封装的TextTooltip组件 -->
    <TextTooltip
      v-model="showFullTextTooltipContent"
      :trigger-element="tooltipTriggerElement"
      :content="highlightedFullTextContent"
      :translation="fullTextTranslation"
      :is-translating="isTooltipTranslating"
      :hide-delay="300"
      ref="textTooltipRef"
    />
    
    <!-- 文本编辑模态框 -->
    <BaseModal
      v-model="showEditModal"
      :title="`编辑打标文本: ${currentEditingFilename}`"
      :loading="isEditing"
      @confirm="handleEditConfirm"
    >
      <template #body>
        <div class="edit-text-container">
          <!-- 使用自定义高亮编辑组件 -->
          <HighlightEditableDiv
            v-model="editingTextContent"
            :highlightChars="[',', '，']"
            highlightColor="#ff3333" 
            maxHeight="150px"
            placeholder="请输入打标文本"
          />
          
          <!-- 翻译结果显示区域 -->
          <div class="translation-container" v-if="translationConfig.enabled">
            <div class="translation-header">
              <span class="translation-title">中文翻译参考：</span>
              <div v-if="isTranslating" class="translation-loading">
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
              </div>
            </div>
            <div class="translation-content" v-html="translatedText"></div>
          </div>
        </div>
      </template>
    </BaseModal>
    
    <!-- 批量编辑模态框 -->
    <BaseModal
      v-model="showBatchEditModal"
      title="批量编辑打标文本"
      :loading="isBatchEditing"
      @confirm="handleBatchEditConfirm"
    >
      <template #body>
        <div class="batch-edit-container">
          <div class="batch-edit-info">
            已选择 {{ selectedImages.length }} 张图片进行批量编辑
          </div>
          
          <div class="edit-type-selector">
            <div class="edit-type-label">编辑类型：</div>
            <div class="edit-type-options">
              <label class="edit-type-option">
                <input type="radio" v-model="batchEditType" value="prefix" />
                <span>添加前缀</span>
              </label>
              <label class="edit-type-option">
                <input type="radio" v-model="batchEditType" value="suffix" />
                <span>添加后缀</span>
              </label>
              <label class="edit-type-option">
                <input type="radio" v-model="batchEditType" value="replace" />
                <span>替换文本</span>
              </label>
              <label class="edit-type-option">
                <input type="radio" v-model="batchEditType" value="remove" />
                <span>删除文本</span>
              </label>
            </div>
          </div>
          
          <!-- 统一的输入区域 -->
          <div class="batch-edit-unified-inputs">
            <!-- 主输入框 -->
            <div class="batch-edit-input">
              <label>{{ getBatchEditMainLabel }}</label>
              <HighlightEditableDiv
                v-model="batchEditText"
                :highlightChars="[',', '，']"
                highlightColor="#ff3333"
                maxHeight="60px"
                :placeholder="getBatchEditMainPlaceholder"
              />
            </div>
            
            <!-- 替换模式下的第二个输入框 -->
            <div v-if="batchEditType === 'replace'" class="batch-edit-input">
              <label>替换为</label>
              <HighlightEditableDiv
                v-model="batchEditReplaceText"
                :highlightChars="[',', '，']"
                highlightColor="#ff3333"
                maxHeight="60px"
                placeholder="请输入要替换的文本"
              />
            </div>
          </div>
          
          <div class="preview-section" v-if="batchEditPreview">
            <div class="preview-label">预览效果：</div>
            <div class="preview-content" v-html="highlightMarkedText(batchEditPreview)"></div>
          </div>
        </div>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
/* eslint-disable */
import { computed, ref, watch, onUnmounted } from 'vue'
import { PhotoIcon, TrashIcon, XMarkIcon, CloudArrowUpIcon as UploadIcon } from '@heroicons/vue/24/outline'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import BaseModal from '@/components/common/Modal.vue'
import HighlightEditableDiv from '@/components/common/HighlightEditableDiv.vue'
import TextTooltip from '@/components/common/PromptTooltip.vue'
import message from '@/utils/message'
import { highlightMarkedText } from '@/utils/textFormatters'
import { getTranslation, translationConfig } from '@/utils/translationCache'

const props = defineProps({
  images: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  status: {
    type: String,
    default: 'NEW'
  },
  markedTexts: {
    type: Object,
    default: () => ({})
  },
  taskId: {
    type: [Number, String],
    default: ''
  }
})

const emit = defineEmits([
  'delete', 
  'preview', 
  'update:markedText', 
  'batch-delete', 
  'batch-update-marked-text',
  'selection-change',
  'upload-files'
])

const gridContainer = ref(null) // 添加网格容器引用
const textTooltipRef = ref(null) // 添加对TextTooltip的引用

// 图片分辨率缓存
const imageResolutionCache = new Map()

// 是否可以删除图片
const canDelete = computed(() => {
  return props.status === 'NEW'
})

// 是否可以通过拖拽上传图片
const canDragUpload = computed(() => {
  return props.status === 'NEW'
})

// 是否可以编辑打标文本
const canEdit = computed(() => {
  return ['MARKED', 'TRAINING', 'COMPLETED'].includes(props.status)
})

// 是否显示打标文本
const showMarkedText = computed(() => {
  return ['MARKED', 'TRAINING', 'COMPLETED'].includes(props.status)
})

// 拖放相关状态
const isDragging = ref(false)
const dragCounter = ref(0) // 添加计数器跟踪拖拽事件

// 处理拖拽进入事件
const handleDragEnter = (event) => {
  event.preventDefault()
  
  dragCounter.value++
  
  // 只要有拖拽动作就显示提示，不需要检查是否都是图片
  isDragging.value = true
}

// 处理拖拽悬停事件
const handleDragOver = (event) => {
  event.preventDefault()
  
  // 只有在可上传状态下才允许放置
  event.dataTransfer.dropEffect = canDragUpload.value ? 'copy' : 'none'
}

// 处理拖拽离开事件
const handleDragLeave = (event) => {
  event.preventDefault()
  
  // 减少计数器
  dragCounter.value--
  
  // 只有当计数器为0时才认为真正离开了容器
  if (dragCounter.value <= 0) {
    isDragging.value = false
    dragCounter.value = 0 // 重置计数器，防止负值
  }
}

// 处理拖拽放下事件
const handleDrop = (event) => {
  event.preventDefault()
  dragCounter.value = 0
  isDragging.value = false
  
  if (!canDragUpload.value) {
    message.warning('当前状态不允许上传图片')
    return
  }
  
  if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
    // 过滤图片文件
    const imageFiles = Array.from(event.dataTransfer.files).filter(file => {
      const isImage = file.type.startsWith('image/')
      if (!isImage) {
        console.warn(`跳过非图片文件: ${file.name}`)
      }
      return isImage
    })
    
    if (imageFiles.length > 0) {
      emit('upload-files', imageFiles)
    } else {
      message.warning('未发现有效的图片文件')
    }
  }
}

// 处理预览
const handlePreview = (imageUrl) => {
  console.log("显示图片", imageUrl)
  emit('preview', 'task', imageUrl)
}

// 处理删除
const handleDelete = (image) => {
  if (confirm(`确定要删除图片 "${image.filename}" 吗？`)) {
    emit('delete', image.id)
  }
}

// 文本编辑相关
const showEditModal = ref(false)
const currentEditingFilename = ref('')
const editingTextContent = ref('')
const isEditing = ref(false)
const translatedText = ref('') // 添加翻译文本
const isTranslating = ref(false) // 添加翻译中状态

// 翻译当前编辑的文本
const translateEditingText = async () => {
  // 如果翻译功能被禁用，直接返回
  if (!translationConfig.value.enabled) {
    translatedText.value = ''
    return
  }
  
  if (!editingTextContent.value) {
    translatedText.value = ''
    return
  }
  
  try {
    isTranslating.value = true
    // 使用全局翻译缓存服务
    const { text, isError } = await getTranslation(editingTextContent.value, 'zh', 'en')
    
    if (!isError) {
      // 应用高亮处理到翻译结果
      translatedText.value = highlightMarkedText(text)
    } else {
      translatedText.value = text // 错误信息
    }
  } catch (error) {
    console.error('翻译失败:', error)
    translatedText.value = '翻译服务异常'
  } finally {
    isTranslating.value = false
  }
}

// 获取打标文本内容
const getMarkedTextContent = (filename) => {
  // 直接匹配文件名
  if (props.markedTexts[filename]) {
    return props.markedTexts[filename];
  }
  
  // 如果直接匹配不到，尝试从相对路径中匹配
  const relativePaths = Object.keys(props.markedTexts);
  const matchingPath = relativePaths.find(path => {
    // 从路径中提取文件名
    const pathFilename = path.split('/').pop();
    return pathFilename === filename;
  });
  
  return matchingPath ? props.markedTexts[matchingPath] : '';
}

// 获取图片URL
const getImageUrl = (image) => {
  // 如果没有markedTexts或者状态不是MARKED及之后，使用原始URL
  if (!props.markedTexts || Object.keys(props.markedTexts).length === 0 || 
      !['MARKED', 'TRAINING', 'COMPLETED'].includes(props.status)) {
    return image.preview_url;
  }
  
  // 查找匹配的相对路径
  const relativePaths = Object.keys(props.markedTexts);
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
}

// 开始编辑文本
const startEditText = async (filename) => {
  console.log("开始编辑文本",filename)
  currentEditingFilename.value = filename
  
  // 获取对应的打标文本内容
  editingTextContent.value = getMarkedTextContent(filename)
  
  showEditModal.value = true
  
  // 翻译当前文本
  await translateEditingText()
}

// 监听编辑内容变化，自动更新翻译
watch(editingTextContent, async (newValue) => {
  if (!newValue) {
    translatedText.value = ''
    return
  }
  
  // 使用防抖函数处理翻译请求
  if (translationDebounceTimer) clearTimeout(translationDebounceTimer)
  translationDebounceTimer = setTimeout(async () => {
    await translateEditingText()
  }, 500)
})

// 防抖计时器
let translationDebounceTimer = null

// 确认编辑
const handleEditConfirm = () => {
  if (!currentEditingFilename.value) return;
  emit('update:markedText', {
    filename: currentEditingFilename.value,
    content: editingTextContent.value
  })
  
  showEditModal.value = false
}

// 多选相关
const selectedImages = ref([])

// 切换选择图片
const toggleSelectImage = (imageId) => {
  const index = selectedImages.value.indexOf(imageId)
  if (index === -1) {
    selectedImages.value.push(imageId)
  } else {
    selectedImages.value.splice(index, 1)
  }
  
  // 发送选择变化事件
  emit('selection-change', selectedImages.value.length)
}

// 清除选择
const clearSelection = () => {
  selectedImages.value = []
  emit('selection-change', 0)
}

// 全选图片
const selectAllImages = () => {
  if (!props.images || props.images.length === 0) return
  
  // 获取所有图片ID
  const allImageIds = props.images.map(img => img.id)
  
  // 设置为选中状态
  selectedImages.value = [...allImageIds]
  
  // 发送选择变化事件
  emit('selection-change', selectedImages.value.length)
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedImages.value.length === 0) {
    message.warning('请先选择要删除的图片')
    return
  }
  
  if (confirm(`确定要删除选中的 ${selectedImages.value.length} 张图片吗？`)) {
    // 只发射事件通知父组件，让父组件处理API调用
    emit('batch-delete', [...selectedImages.value])
    // 清除选择
    selectedImages.value = []
    emit('selection-change', 0)
  }
}

// 批量编辑相关
const showBatchEditModal = ref(false)
const isBatchEditing = ref(false)
const batchEditType = ref('prefix')
const batchEditText = ref('') // 统一的主输入框文本
const batchEditReplaceText = ref('') // 替换模式下的第二个输入框
const batchEditPreview = ref('')

// 获取批量编辑主输入框的标签
const getBatchEditMainLabel = computed(() => {
  switch (batchEditType.value) {
    case 'prefix': return '添加前缀';
    case 'suffix': return '添加后缀';
    case 'replace': return '查找文本';
    case 'remove': return '删除文本';
    default: return '输入文本';
  }
})

// 获取批量编辑主输入框的占位符
const getBatchEditMainPlaceholder = computed(() => {
  switch (batchEditType.value) {
    case 'prefix': return '请输入要添加的前缀';
    case 'suffix': return '请输入要添加的后缀';
    case 'replace': return '请输入要查找的文本';
    case 'remove': return '请输入要删除的文本';
    default: return '请输入文本';
  }
})

// 批量编辑防抖计时器
let batchEditDebounceTimer = null

// 监听批量编辑类型变化，重置相关字段
watch(batchEditType, (newType, oldType) => {
  // 如果类型变了，清空输入框
  if (newType !== oldType) {
    batchEditText.value = ''
    batchEditReplaceText.value = ''
  }
  
  // 更新预览
      updateBatchEditPreview()
})

// 监听批量编辑输入内容变化，更新预览
watch([batchEditText, batchEditReplaceText], () => {
  // 使用防抖函数延迟更新预览
  if (batchEditDebounceTimer) clearTimeout(batchEditDebounceTimer)
  batchEditDebounceTimer = setTimeout(() => {
    updateBatchEditPreview()
  }, 300)
}, { deep: true })

// 监听批量编辑模态框显示状态变化
watch(showBatchEditModal, (newValue) => {
  if (newValue) {
    // 当模态框打开时，重置输入并立即更新预览
    batchEditText.value = ''
    batchEditReplaceText.value = ''
    updateBatchEditPreview()
  }
})

// 更新批量编辑预览
const updateBatchEditPreview = () => {
  if (selectedImages.value.length === 0) return
  
  // 获取第一个选中图片的打标文本作为预览
  const firstSelectedImage = props.images.find(img => img.id === selectedImages.value[0])
  if (!firstSelectedImage) return
  
  // 获取原始文本，考虑相对路径情况
  const originalText = getMarkedTextContent(firstSelectedImage.filename) || '无打标文本'
  
  let newText = originalText
  
  if (batchEditType.value === 'prefix') {
    newText = batchEditText.value + originalText
  } else if (batchEditType.value === 'suffix') {
    newText = originalText + batchEditText.value
  } else if (batchEditType.value === 'replace') {
    if (!batchEditText.value) {
      newText = originalText
    } else {
      newText = originalText.replaceAll(batchEditText.value, batchEditReplaceText.value || '')
    }
  } else if (batchEditType.value === 'remove') {
    if (!batchEditText.value) {
      newText = originalText
    } else {
      newText = originalText.replaceAll(batchEditText.value, '')
    }
  }
  
  batchEditPreview.value = newText
}

// 批量编辑确认
const handleBatchEditConfirm = async () => {
  if (selectedImages.value.length === 0) {
    message.warning('请先选择要编辑的图片')
    return
  }
  
  try {
    isBatchEditing.value = true
    
    // 构建需要更新的文本映射
    const updateData = {}
    
    // 获取选中的图片ID对应的图片对象
    const selectedImageObjects = props.images.filter(img => selectedImages.value.includes(img.id))
    
    // 遍历处理每个选中的图片
    for (const image of selectedImageObjects) {
      // 查找匹配的相对路径
      let targetFilename = image.filename;
      const relativePaths = Object.keys(props.markedTexts);
      const matchingPath = relativePaths.find(path => {
        const pathFilename = path.split('/').pop();
        return pathFilename === image.filename;
      });
      
      // 如果找到匹配的路径，使用该路径作为文件名
      if (matchingPath) {
        targetFilename = matchingPath;
      }
      
      // 获取原始文本
      const originalText = getMarkedTextContent(image.filename);
      
      // 根据编辑类型修改文本
      let newText = originalText
      
      if (batchEditType.value === 'prefix') {
        newText = batchEditText.value + originalText
      } else if (batchEditType.value === 'suffix') {
        newText = originalText + batchEditText.value
      } else if (batchEditType.value === 'replace' && batchEditText.value) {
        newText = originalText.replaceAll(batchEditText.value, batchEditReplaceText.value)
      } else if (batchEditType.value === 'remove' && batchEditText.value) {
        newText = originalText.replaceAll(batchEditText.value, '')
      }
      
      // 只有当文本有变化时才添加到更新列表
      if (newText !== originalText) {
        updateData[targetFilename] = newText
      }
    }
    
    // 如果没有需要更新的内容，提示并返回
    if (Object.keys(updateData).length === 0) {
      message.warning('没有文本需要更新')
      showBatchEditModal.value = false
      return
    }
    
    // 发送批量更新事件
    emit('batch-update-marked-text', updateData)
    
    // 清空编辑状态
    resetBatchEdit()
    showBatchEditModal.value = false
    
  } finally {
    isBatchEditing.value = false
  }
}

// 重置批量编辑状态
const resetBatchEdit = () => {
  batchEditText.value = ''
  batchEditReplaceText.value = ''
  batchEditPreview.value = ''
}

// 暴露方法给父组件
defineExpose({
  clearSelection,
  handleBatchDelete,
  getSelectedImages: () => props.images.filter(img => selectedImages.value.includes(img.id)),
  selectAllImages,
  showBatchEditModal
})


// 清理计时器
onUnmounted(() => {
  if (translationDebounceTimer) {
    clearTimeout(translationDebounceTimer)
  }
  
  if (batchEditDebounceTimer) {
    clearTimeout(batchEditDebounceTimer)
  }
})

// 浮动提示词框相关
const showFullTextTooltipContent = ref(false)
const tooltipTriggerElement = ref(null) // 触发元素的DOM引用
const fullTextContent = ref('')
const highlightedFullTextContent = ref('') // 添加高亮后的内容引用
const fullTextTranslation = ref('')
const isTooltipTranslating = ref(false) // 翻译加载状态
let lastHoveredFilename = null // 记录最后悬停的文件名

// 显示完整提示词的浮动框
const showFullTextTooltip = (event, filename) => {
  // 如果翻译功能被禁用，不需要处理翻译
  const shouldTranslate = translationConfig.value.enabled
  
  // 如果是相同文件，不重新触发处理，直接保持显示状态
  if (showFullTextTooltipContent.value && filename === lastHoveredFilename) {
    // 如果已经显示且文件名相同，只需更新触发元素位置
    tooltipTriggerElement.value = event.target
    // 确保不会自动隐藏
    if (textTooltipRef.value) {
      textTooltipRef.value.cancelHideTimer()
    }
    return
  }
  
  // 记录当前文件名
  lastHoveredFilename = filename
  
  // 如果当前有显示的提示框，先隐藏当前的，再显示新的
  if (showFullTextTooltipContent.value) {
    // 立即隐藏当前提示框
    showFullTextTooltipContent.value = false
    
    // 清除任何可能的隐藏计时器
    if (textTooltipRef.value) {
      textTooltipRef.value.cancelHideTimer()
    }
  }
  
  // 直接处理内容显示，无需延迟
  processTooltipContent(event, filename, shouldTranslate)
}

// 处理提示词内容并显示提示框
const processTooltipContent = async (event, filename, shouldTranslate = true) => {
  if (!gridContainer.value) return // 确保网格容器存在
  
  // 保存触发元素引用
  tooltipTriggerElement.value = event.target
  
  // 获取完整的提示词内容
  fullTextContent.value = getMarkedTextContent(filename)
  
  // 高亮提示词内容
  highlightedFullTextContent.value = highlightMarkedText(fullTextContent.value)
  
  // 显示提示词框
  showFullTextTooltipContent.value = true

  // 如果有内容且应该翻译，则尝试获取翻译
  if (fullTextContent.value && shouldTranslate) {
    isTooltipTranslating.value = true
    // 使用全局翻译缓存服务
    const { text } = await getTranslation(fullTextContent.value, 'zh', 'en')
    fullTextTranslation.value = highlightMarkedText(text)
    isTooltipTranslating.value = false
  } else {
    fullTextTranslation.value = ''
  }
}

// 延迟隐藏浮动框
const hideTooltipWithDelay = () => {
  // 记录要隐藏的是哪个文件的提示框
  const hidingFilename = lastHoveredFilename
  
  // 启动隐藏计时器
  if (textTooltipRef.value) {
    textTooltipRef.value.startHideTimer()
    
    // 设置一个短暂的延迟，检查是否在这段时间内触发了新的提示框
    setTimeout(() => {
      // 如果当前显示的文件名与要隐藏的文件名不同，说明用户已经移动到了新的元素
      // 这种情况下应该取消隐藏计时器，保持新的提示框显示
      if (showFullTextTooltipContent.value && lastHoveredFilename !== hidingFilename) {
        textTooltipRef.value.cancelHideTimer()
      }
    }, 50)
  }
}

// 复制提示词内容
const copyMarkedText = (filename) => {
  const text = getMarkedTextContent(filename)
  if (text) {
    navigator.clipboard.writeText(text)
      .then(() => message.success('提示词已复制到剪贴板'))
      .catch(err => {
        console.error('无法复制文本: ', err)
        message.error('复制失败，请手动复制')
      })
  } else {
    message.warning('没有可复制的提示词')
  }
}

// 处理图片加载事件，获取图片的实际尺寸
const handleImageLoad = (event, image) => {
  // 如果已经有宽高信息，则跳过
  if (image.width && image.height) return
  
  const img = event.target
  if (img.naturalWidth && img.naturalHeight) {
    // 设置图片宽高属性
    image.width = img.naturalWidth
    image.height = img.naturalHeight
    
    // 缓存分辨率信息
    imageResolutionCache.set(image.id, {
      width: img.naturalWidth,
      height: img.naturalHeight
    })
  }
}

// 监听图片列表变化，恢复分辨率信息
watch(() => props.images, (newImages) => {
  if (!newImages || newImages.length === 0) return
  // 遍历图片列表，从缓存中恢复分辨率信息
  newImages.forEach(image => {
    // 如果图片已有分辨率信息，则跳过
    if (image.width && image.height) return
    
    // 从缓存中获取分辨率信息
    const cachedResolution = imageResolutionCache.get(image.id)
    if (cachedResolution) {
      image.width = cachedResolution.width
      image.height = cachedResolution.height
    }
  })
}, { immediate: true, deep: true })
</script>

<style scoped>
.image-grid-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 1px;  /* 防止阴影被裁剪 */
  position: relative;
  transition: all 0.3s ease;
}

.image-grid-container.drag-over {
  background-color: rgba(0, 122, 255, 0.05);
  border: 2px dashed rgba(0, 122, 255, 0.3);
  border-radius: 8px;
}

.drag-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(var(--background-secondary-rgb), 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  border-radius: 8px;
  animation: fadeIn 0.3s ease;
  pointer-events: none; /* 防止覆盖层捕获事件 */
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.drag-overlay-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background-color: var(--background-secondary);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.upload-icon {
  width: 48px;
  height: 48px;
  color: var(--primary-color);
  margin-bottom: 16px;
}

.error-icon {
  color: #dc2626 !important;
  animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
}

@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}

.drag-hint {
  margin-top: 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

.status-hint {
  color: #dc2626;
  font-weight: 500;
}

.loading-state,
.empty-state {
  height: 100%;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.empty-icon {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  padding: 4px;
}

.image-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background: var(--background-secondary);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.image-item.selected {
  box-shadow: 0 0 0 2px var(--primary-color), var(--shadow-md);
}

.image-container {
  position: relative;
  width: 100%;
}

/* 多选框样式 */
.select-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 28px;
  height: 28px;
  z-index: 2;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.image-item:hover .select-checkbox,
.image-item.selected .select-checkbox {
  opacity: 1;
}

.select-checkbox input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-custom {
  position: absolute;
  top: 0;
  left: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(var(--background-secondary-rgb), 0.9);
  border: 2px solid rgba(var(--background-secondary-rgb), 0.9);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-custom::after {
  content: '';
  position: absolute;
  display: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--primary-color);
}

.select-checkbox input:checked ~ .checkbox-custom {
  background: var(--background-secondary);
  border-color: var(--primary-color);
}

.select-checkbox input:checked ~ .checkbox-custom::after {
  display: block;
}

.delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(var(--background-secondary-rgb), 0.9);
  color: #dc2626;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2;
  opacity: 0;
  transition: opacity 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.image-container:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: var(--background-secondary);
  transform: scale(1.05);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.image-container img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  cursor: pointer;
  display: block;
}

.image-info {
  padding: 8px;
  background: var(--background-secondary);
}

.image-name {
  font-size: 13px;
  color: var(--text-primary);
  margin-bottom: 4px;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 打标文本样式 */
.marked-text-container {
  margin-top: 8px;
  border-top: 1px solid var(--border-color-light);
  padding-top: 8px;
}

.marked-text {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
  background: var(--background-tertiary);
  padding: 0 6px;
  border-radius: 4px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  text-overflow: ellipsis;
  cursor: pointer;
}

.text-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
}

.text-toggle, .text-edit {
  font-size: 11px;
  color: var(--primary-color);
  background: transparent;
  border: none;
  padding: 2px 4px;
  cursor: pointer;
  border-radius: 2px;
}

.text-toggle:hover, .text-edit:hover {
  background: color-mix(in srgb, var(--primary-color) 10%, transparent);
}

/* 编辑模态框样式 */
.edit-text-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 批量编辑模态框样式 */
.batch-edit-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.batch-edit-info {
  padding: 8px 12px;
  background: var(--background-tertiary);
  border-radius: 4px;
  font-size: 14px;
  color: var(--text-secondary);
}

.edit-type-selector {
  display: flex;
  align-items: center;
  gap: 16px;
}

.edit-type-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
}

.edit-type-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.edit-type-option {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.edit-type-option input {
  margin: 0;
}

.edit-type-option span {
  font-size: 14px;
  color: var(--text-primary);
}

.batch-edit-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.batch-edit-input label {
  font-size: 14px;
  color: var(--text-secondary);
}

.batch-edit-inputs {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-section {
  margin-top: 8px;
  padding: 12px;
  background: var(--background-tertiary);
  border-radius: 4px;
}

.preview-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.preview-content {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-secondary);
  white-space: pre-wrap;
  max-height: 100px;
  overflow-y: auto;
}

/* 翻译相关样式 */
.translation-container,
.translation-section {
  margin-top: 12px;
  padding: 10px;
  background-color: #f8f9ff;
  border-radius: 6px;
  border: 1px solid #e6ebff;
}

.translation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.translation-title {
  font-size: 13px;
  font-weight: 500;
  color: #5264cc;
}

.translation-loading {
  display: flex;
  align-items: center;
  gap: 4px;
}

.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #5264cc;
  animation: loading-dot 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes loading-dot {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.translation-content {
  font-size: 13px;
  line-height: 1.5;
  color: #333;
  background-color: var(--background-secondary);
  padding: 8px;
  border-radius: 4px;
  white-space: pre-wrap;
  max-height: 100px;
  overflow-y: auto;
  border: 1px solid #eaeaea;
}

/* 自定义文本样式 */
:deep(.red-comma) {
  color: #ff3333;
  font-weight: bold;
}

/* 滚动条样式 */
.image-grid-container::-webkit-scrollbar {
  width: 8px;
}

.image-grid-container::-webkit-scrollbar-track {
  background: transparent;
}

.image-grid-container::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.image-grid-container::-webkit-scrollbar-thumb:hover {
  background: var(--border-color-dark);
}

.error-icon {
  color: #dc2626;
}

.image-resolution {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: var(--text-primary-inverse);
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  z-index: 2;
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
</style> 