<template>
  <Teleport to="body">
    <Transition name="tooltip-fade">
      <div 
        v-if="modelValue" 
        class="text-tooltip"
        ref="tooltipRef"
        :style="computedTooltipStyle"
        @mouseenter="onMouseEnter"
        @mouseleave="onMouseLeave"
      >
        <div class="tooltip-arrow"></div>
        <div class="tooltip-content">
          <div class="tooltip-section">
            <div class="tooltip-title">
              {{ title }}：
              <button v-if="content" class="tooltip-action-btn" @click="copyContent">
                <span class="tooltip-action-icon">📋</span>复制
              </button>
            </div>
            <div class="tooltip-text" v-html="content"></div>
          </div>
          <div class="tooltip-section" v-if="translationEnabled">
            <div class="tooltip-title">
              {{ translationTitle }}：
              <span v-if="isTranslating" class="tooltip-loading">
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
              </span>
              <button 
                v-if="translation" 
                class="tooltip-action-btn" 
                @click="copyTranslation"
              >
                <span class="tooltip-action-icon">📋</span>复制
              </button>
            </div>
            <div 
              v-if="translation || isTranslating" 
              class="tooltip-text" 
              v-html="translation || '加载中...'"
            ></div>
            <div v-else class="tooltip-text tooltip-empty">暂无翻译</div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
/* eslint-disable */
import { ref, defineProps, defineEmits, watch, onUnmounted, computed, nextTick } from 'vue'
import message from '@/utils/message'
import { stripHtml } from '@/utils/textFormatters'
import { translationConfig } from '@/utils/translationCache'

const props = defineProps({
  // 控制组件显示与隐藏
  modelValue: {
    type: Boolean,
    default: false
  },
  // 触发元素（DOM元素）
  triggerElement: {
    type: [HTMLElement, Object],
    default: null
  },
  // 自定义样式（会与计算的样式合并）
  customStyle: {
    type: Object,
    default: () => ({})
  },
  // 最大宽度
  maxWidth: {
    type: Number,
    default: 500
  },
  // 估计高度
  estimatedHeight: {
    type: Number,
    default: 300
  },
  // 标题
  title: {
    type: String,
    default: '提示词'
  },
  // 内容
  content: {
    type: String,
    default: ''
  },
  // 翻译标题
  translationTitle: {
    type: String,
    default: '翻译'
  },
  // 翻译内容
  translation: {
    type: String,
    default: ''
  },
  // 是否正在翻译
  isTranslating: {
    type: Boolean,
    default: false
  },
  // 延迟隐藏时间（毫秒）
  hideDelay: {
    type: Number,
    default: 300
  }
})

const emit = defineEmits(['update:modelValue', 'copy'])

const tooltipRef = ref(null)
let hideTimer = null
let isHoveringTooltip = false // 跟踪鼠标是否在提示框上

// 计算属性：是否启用翻译功能
const translationEnabled = computed(() => translationConfig.value.enabled)

// 计算提示框样式，包括位置
const computedTooltipStyle = computed(() => {
  // 如果没有触发元素，返回默认样式
  if (!props.triggerElement) {
    return {
      ...props.customStyle,
      maxWidth: `${props.maxWidth}px`,
      width: `${props.maxWidth}px`,
    }
  }
  
  return calculatePosition()
})

// 获取实际提示框高度（如果可用）
const getTooltipHeight = () => {
  if (tooltipRef.value) {
    return tooltipRef.value.offsetHeight
  }
  return props.estimatedHeight
}

// 获取元素的位置信息
const getElementRect = (element) => {
  if (!element) return null
  
  try {
    return element.getBoundingClientRect()
  } catch (e) {
    console.error('获取元素位置失败:', e)
    return null
  }
}

// 计算提示框位置
const calculatePosition = () => {
  // 获取触发元素和卡片元素的位置
  const triggerRect = getElementRect(props.triggerElement)
  
  if (!triggerRect) return {
    ...props.customStyle,
    maxWidth: `${props.maxWidth}px`,
    width: `${props.maxWidth}px`,
  }
  
  // 使用卡片元素位置（如果有）或触发元素位置
  const refRect = triggerRect
  
  // 获取窗口尺寸
  const windowWidth = window.innerWidth
  const windowHeight = window.innerHeight
  const scrollY = window.scrollY
  const scrollX = window.scrollX
  
  // 设置提示框的尺寸
  const maxWidth = props.maxWidth
  const tooltipHeight = getTooltipHeight()
  
  // 初始位置计算（默认在元素下方）
  let top = triggerRect.bottom + scrollY + 10 // 元素底部 + 间距
  let left = refRect.left + scrollX // 与卡片左对齐
  let arrowPosition = '20px' // 箭头默认位置
  let arrowTop = '-8px' // 箭头在顶部
  let arrowBottom = 'auto' // 箭头底部位置（默认不设置）
  let arrowTransform = 'translateY(50%) rotate(45deg)' // 默认箭头变换
  
  // 检查是否有足够的向下空间
  const hasEnoughSpaceBelow = (windowHeight - triggerRect.bottom) > (tooltipHeight + 20)
  
  // 如果下方空间不足，则将提示框显示在元素上方
  if (!hasEnoughSpaceBelow) {
    top = triggerRect.top + scrollY - tooltipHeight - 10 // 使用实际高度
    arrowTop = 'auto' // 箭头不在顶部
    arrowBottom = '-8px' // 箭头在底部
    arrowPosition = '20px' // 重置箭头水平位置
    arrowTransform = 'translateY(-50%) rotate(225deg)' // 旋转箭头指向下方
  }
  
  // 检查左侧对齐是否会导致提示框超出右侧边界
  if (left + maxWidth > windowWidth + scrollX - 20) {
    // 如果卡片宽度大于提示框，则右对齐
    if (refRect.width >= maxWidth) {
      left = refRect.right + scrollX - maxWidth // 右对齐
      arrowPosition = `${maxWidth - 40}px` // 箭头位于右侧
    } 
    // 否则居中对齐或左移
    else {
      // 计算居中位置
      const centerLeft = refRect.left + (refRect.width - maxWidth) / 2 + scrollX
      
      // 如果居中会超出左侧，则左对齐屏幕边缘
      if (centerLeft < scrollX + 20) {
        left = scrollX + 20
        // 计算箭头位置，使其指向卡片中心
        const arrowLeft = Math.max(20, refRect.left + refRect.width / 2 - left - 8)
        arrowPosition = `${arrowLeft}px`
      }
      // 如果居中不会超出左侧，则居中对齐
      else {
        left = centerLeft
        arrowPosition = `${maxWidth / 2 - 8}px` // 箭头居中
      }
    }
  }
  
  // 检查左对齐是否会导致提示框超出左侧边界
  if (left < scrollX + 20) {
    left = scrollX + 20 // 保持左边距
    // 计算箭头位置，使其指向卡片中心
    const arrowLeft = Math.max(20, refRect.left + refRect.width / 2 - left - 8)
    arrowPosition = `${arrowLeft}px`
  }
  
  // 返回计算后的样式
  return {
    ...props.customStyle,
    top: `${top}px`,
    left: `${left}px`,
    maxWidth: `${maxWidth}px`,
    width: `${maxWidth}px`, // 固定宽度
    '--arrow-left': arrowPosition,
    '--arrow-top': arrowTop,
    '--arrow-bottom': arrowBottom,
    '--arrow-transform': arrowTransform,
  }
}


// 鼠标进入提示框
const onMouseEnter = () => {
  isHoveringTooltip = true
  cancelHideTimer()
}

// 鼠标离开提示框
const onMouseLeave = () => {
  isHoveringTooltip = false
  startHideTimer()
}

// 取消隐藏计时器
const cancelHideTimer = () => {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
}

// 开始隐藏计时器
const startHideTimer = () => {
  // 如果已经有计时器正在运行，不再创建新的
  if (hideTimer) return
  
  hideTimer = setTimeout(() => {
    emit('update:modelValue', false)
  }, props.hideDelay)
}

// 复制提示词内容
const copyContent = () => {
  if (props.content) {
    const textContent = stripHtml(props.content)
    navigator.clipboard.writeText(textContent)
      .then(() => {
        message.success('提示词已复制到剪贴板')
        emit('copy', { type: 'content', text: textContent })
      })
      .catch(err => {
        console.error('无法复制文本: ', err)
        message.error('复制失败，请手动复制')
      })
  }
}

// 复制翻译内容
const copyTranslation = () => {
  if (props.translation) {
    const textContent = stripHtml(props.translation)
    navigator.clipboard.writeText(textContent)
      .then(() => {
        message.success('翻译已复制到剪贴板')
        emit('copy', { type: 'translation', text: textContent })
      })
      .catch(err => {
        console.error('无法复制文本: ', err)
        message.error('复制失败，请手动复制')
      })
  }
}

// 监听显示状态变化
watch(() => props.modelValue, (newValue) => {
  // 当提示框隐藏时，清理计时器
  if (!newValue && hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
})

// 组件销毁时清理计时器
onUnmounted(() => {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
})

// 暴露方法给父组件
defineExpose({
  cancelHideTimer,
  startHideTimer
})
</script>

<style scoped>
/* 提示框样式 */
.text-tooltip {
  position: fixed;
  z-index: 9999;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 12px;
  pointer-events: auto;
  border: 1px solid var(--border-color, #e0e0e0);
}

/* 提示框动画 */
.tooltip-fade-enter-active {
  animation: tooltip-fade-in 0.2s ease-in-out;
}

.tooltip-fade-leave-active {
  animation: tooltip-fade-out 0.2s ease-in-out;
}

@keyframes tooltip-fade-in {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes tooltip-fade-out {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(-5px); }
}

.tooltip-arrow {
  position: absolute;
  top: var(--arrow-top, -8px);
  bottom: var(--arrow-bottom, auto);
  left: var(--arrow-left, 20px);
  width: 16px;
  height: 8px;
  overflow: hidden;
}

.tooltip-arrow::after {
  content: '';
  position: absolute;
  width: 12px;
  height: 12px;
  background: white;
  border: 1px solid var(--border-color, #e0e0e0);
  transform: var(--arrow-transform, translateY(50%) rotate(45deg));
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tooltip-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tooltip-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary, #333);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tooltip-text {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-secondary, #666);
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  background-color: var(--background-tertiary, #f5f5f5);
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.tooltip-loading {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: 6px;
}

.tooltip-loading .loading-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background-color: var(--text-secondary, #666);
  animation: tooltip-loading-dot 1.4s infinite ease-in-out both;
}

.tooltip-loading .loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.tooltip-loading .loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes tooltip-loading-dot {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.tooltip-empty {
  color: var(--text-disabled, #999);
  font-style: italic;
}

.tooltip-action-btn {
  background: transparent;
  border: none;
  font-size: 12px;
  color: var(--primary-color, #1890ff);
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tooltip-action-btn:hover {
  background-color: rgba(0, 122, 255, 0.1);
}

.tooltip-action-icon {
  font-size: 12px;
}
</style> 