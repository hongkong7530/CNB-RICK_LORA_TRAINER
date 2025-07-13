<template>
  <transition :name="animation ? 'modal-backdrop' : ''">
    <div v-if="modelValue" class="modal-overlay" :class="{ 'no-backdrop': noBackdrop }" @click="closeOnBackdrop ? close() : null">
      <transition :name="animation ? 'modal' : ''">
        <div 
          class="modal-wrapper mac-card" 
          :class="{ 
            'modal-fullscreen': isFullscreen,
            'no-header': !hasHeader
          }" 
          :style="modalStyle"
          @click.stop
          ref="modalRef"
        >
          <!-- 标题模式 -->
          <div v-if="title && (!tabs || tabs.length === 0)" class="modal-header">
            <h3 class="modal-title">{{ title }}</h3>
            <div class="modal-header-actions">
              <button v-if="fullscreenToggle" class="action-btn" @click="toggleFullscreen" title="切换全屏">
                <ArrowsPointingInIcon v-if="isFullscreen" class="action-icon" />
                <ArrowsPointingOutIcon v-else class="action-icon" />
              </button>
              <button class="close-btn" @click="close" title="关闭">
                <XMarkIcon class="close-icon" />
              </button>
            </div>
          </div>
          
          <!-- 标签页模式 -->
          <div v-else-if="tabs && tabs.length > 0" class="modal-header with-tabs">
            <div class="modal-tabs">
              <div 
                v-for="(tab, index) in tabs" 
                :key="index"
                class="modal-tab"
                :class="{ active: activeTabIndex === index }"
                @click="setActiveTab(index)"
              >
                <component v-if="tab.icon" :is="tab.icon" class="tab-icon" />
                <span>{{ tab.title }}</span>
              </div>
            </div>
            <div class="modal-header-actions">
              <button v-if="fullscreenToggle" class="action-btn" @click="toggleFullscreen" title="切换全屏">
                <ArrowsPointingInIcon v-if="isFullscreen" class="action-icon" />
                <ArrowsPointingOutIcon v-else class="action-icon" />
              </button>
              <button class="close-btn" @click="close" title="关闭">
                <XMarkIcon class="close-icon" />
              </button>
            </div>
          </div>
          
          <!-- 无标题模式下的浮动关闭按钮 -->
          <button v-if="!hasHeader" class="floating-close-btn" @click="close" title="关闭">
            <XMarkIcon class="floating-close-icon" />
          </button>
          
          <div class="modal-body" :style="bodyStyle">
            <div v-if="loading" class="modal-loading-overlay">
              <div class="loading-spinner"></div>
            </div>
            <slot name="body"></slot>
          </div>
          
          <div v-if="showFooter" class="modal-footer">
            <slot name="footer">
              <button class="mac-btn" @click="close">{{ cancelText }}</button>
              <button class="mac-btn primary" @click="$emit('confirm')">{{ confirmText }}</button>
            </slot>
          </div>
        </div>
      </transition>
    </div>
  </transition>
</template>

<script>
import { XMarkIcon, ArrowsPointingInIcon, ArrowsPointingOutIcon } from '@heroicons/vue/24/outline'
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

export default {
  name: 'BaseModal',
  components: {
    XMarkIcon,
    ArrowsPointingInIcon,
    ArrowsPointingOutIcon
  },
  props: {
    modelValue: Boolean,
    title: String,
    width: {
      type: [String, Number],
      default: '650px'
    },
    height: {
      type: [String, Number],
      default: null
    },
    maxHeight: {
      type: [String, Number],
      default: '85vh'
    },
    showFooter: {
      type: Boolean,
      default: true
    },
    loading: {
      type: Boolean,
      default: false
    },
    cancelText: {
      type: String,
      default: '取消'
    },
    confirmText: {
      type: String,
      default: '确认'
    },
    closeOnBackdrop: {
      type: Boolean,
      default: true
    },
    noBackdrop: {
      type: Boolean,
      default: false
    },
    fullscreen: {
      type: Boolean,
      default: false
    },
    fullscreenToggle: {
      type: Boolean,
      default: false
    },
    animation: {
      type: Boolean,
      default: true
    },
    bodyPadding: {
      type: [String, Number],
      default: null
    },
    zIndex: {
      type: Number,
      default: 1000
    },
    // 标签页配置，格式为[{title: '标签1', icon: Component}, {title: '标签2', icon: Component}]
    tabs: {
      type: Array,
      default: () => []
    },
    // 默认激活的标签页索引
    defaultActiveTab: {
      type: Number,
      default: 0
    },
    // 是否阻止ESC键关闭，对于嵌套需要ESC关闭的组件如ImageViewer很有用
    preventKeydownClose: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'confirm', 'fullscreen-change', 'update:fullscreen', 'tab-change'],
  setup(props, { emit }) {
    const modalRef = ref(null)
    const isFullscreen = ref(props.fullscreen)
    const activeTabIndex = ref(props.defaultActiveTab)
    
    // 计算是否有标题区域
    const hasHeader = computed(() => {
      return (props.title && props.title.trim() !== '') || (props.tabs && props.tabs.length > 0)
    })
    
    // 监听props.fullscreen变化
    watch(() => props.fullscreen, (newVal) => {
      isFullscreen.value = newVal
    })
    
    // 监听props.defaultActiveTab变化
    watch(() => props.defaultActiveTab, (newVal) => {
      activeTabIndex.value = newVal
    })
    
    // 设置当前活动的标签页
    const setActiveTab = (index) => {
      activeTabIndex.value = index
      emit('tab-change', index)
    }
    
    // 计算模态框样式
    const modalStyle = computed(() => {
      const style = {
        zIndex: props.zIndex
      }
      
      // 处理自定义宽度
      if (props.width && !isFullscreen.value) {
        if (typeof props.width === 'number') {
          style.width = `${props.width}vw`
        } else {
          style.width = props.width
        }
      }
      
      // 处理自定义高度
      if (props.height && !isFullscreen.value) {
        if (typeof props.height === 'number') {
          style.height = `${props.height}vh`
        } else {
          style.height = props.height
        }
      }
      
      // 处理最大高度
      if (props.maxHeight && !isFullscreen.value) {
        if (typeof props.maxHeight === 'number') {
          style.maxHeight = `${props.maxHeight}vh`
        } else {
          style.maxHeight = props.maxHeight
        }
      }
      
      return style
    })
    
    // 计算模态框内容样式
    const bodyStyle = computed(() => {
      const style = {}
      
      if (props.bodyPadding !== null) {
        style.padding = typeof props.bodyPadding === 'number' 
          ? `${props.bodyPadding}px` 
          : props.bodyPadding
      }
      
      return style
    })
    
    // 关闭模态框
    const close = () => {
      emit('update:modelValue', false)
    }
    
    // 切换全屏模式
    const toggleFullscreen = () => {
      isFullscreen.value = !isFullscreen.value
      emit('fullscreen-change', isFullscreen.value)
      emit('update:fullscreen', isFullscreen.value)
      
      // 延迟执行resize事件，确保DOM更新后触发resize
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'))
      }, 100)
    }
    
    // 监听键盘事件
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && !props.preventKeydownClose) {
        close()
      } else if (event.key === 'F11' && props.fullscreenToggle) {
        // 按F11键切换全屏
        event.preventDefault()
        toggleFullscreen()
      }
    }
    
    // 组件挂载时添加键盘事件监听
    onMounted(() => {
      document.addEventListener('keydown', handleKeyDown)
      
      // 如果初始状态为全屏，触发resize事件
      if (isFullscreen.value) {
        setTimeout(() => {
          window.dispatchEvent(new Event('resize'))
        }, 100)
      }
    })
    
    // 组件卸载时移除事件监听
    onUnmounted(() => {
      document.removeEventListener('keydown', handleKeyDown)
    })
    
    return {
      close,
      modalRef,
      modalStyle,
      bodyStyle,
      isFullscreen,
      toggleFullscreen,
      activeTabIndex,
      setActiveTab,
      hasHeader
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--background-mask);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  transition: var(--theme-transition);
}

.no-backdrop {
  background: transparent;
  backdrop-filter: none;
}

.modal-wrapper {
  max-width: 90vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  background: var(--background-secondary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  position: relative;
  transition: all 0.3s ease;
}

/* 无标题模式 */
.modal-wrapper.no-header {
  border-radius: var(--radius-lg);
  overflow: visible;
}

/* 浮动关闭按钮 */
.floating-close-btn {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary-color);
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s ease;
  padding: 0;
  color: var(--text-primary-inverse);
}

.floating-close-btn:hover {
  background: color-mix(in srgb, var(--primary-color) 80%, black);
  transform: scale(1.1);
  box-shadow: 0 3px 12px color-mix(in srgb, var(--primary-color) 25%, transparent);
}

.floating-close-btn:active {
  transform: scale(0.95);
}

.floating-close-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2.5;
}

/* 全屏模式 */
.modal-fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  max-width: 100vw !important;
  max-height: 100vh !important;
  border-radius: 0 !important;
  z-index: 1100 !important;
}

.modal-header {
  border-bottom: 1px solid var(--border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  transition: var(--theme-transition);
}

/* 标签页模式的头部样式 */
.modal-header.with-tabs {
  padding: 0;
  border-bottom: none;
}

.modal-tabs {
  display: flex;
  flex: 1;
  overflow-x: auto;
  scrollbar-width: none; /* Firefox */
}

.modal-tabs::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Edge */
}

.modal-tab {
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  transition: all 0.2s ease;
  color: var(--text-secondary);
}

.modal-tab:hover {
  background-color: var(--background-hover);
  color: var(--text-primary);
}

.modal-tab.active {
  border-bottom-color: var(--primary-color);
  color: var(--primary-color);
  font-weight: 500;
}

.tab-icon {
  width: 16px;
  height: 16px;
}

.modal-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
}

.modal-body {
  overflow-y: auto;
  flex: 1;
  max-height: calc(85vh - 120px); /* 减去头部和底部的高度 */
  position: relative;
}

.modal-fullscreen .modal-body {
  max-height: calc(100vh - 120px);
}

.modal-footer {
  padding: var(--spacing-4) var(--spacing-6);
  border-top: 1px solid var(--border-color-light);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
  transition: var(--theme-transition);
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.close-btn, .action-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  transition: all var(--transition-speed);
}

.close-btn:hover, .action-btn:hover {
  background: var(--background-tertiary);
  color: var(--text-primary);
}

.action-btn:hover {
  transform: scale(1.1);
}

.close-icon, .action-icon {
  width: 20px;
  height: 20px;
}

/* 加载状态 */
.modal-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--background-overlay-heavy);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  backdrop-filter: blur(4px);
  transition: var(--theme-transition);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 动画 */
.modal-backdrop-enter-active,
.modal-backdrop-leave-active {
  transition: opacity var(--transition-speed);
}

.modal-backdrop-enter-from,
.modal-backdrop-leave-to {
  opacity: 0;
}

.modal-enter-active,
.modal-leave-active {
  transition: all var(--transition-speed);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .modal-wrapper {
    width: 95vw !important;
  }
}
</style> 