<template>
  <div 
    v-if="modelValue"
    class="image-viewer-overlay"
    @click.self="handleClose"
    @keydown.stop
  >
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="image-info">
        <span class="image-name">{{ getImageName(currentImage) }}</span>
        <span class="image-index">{{ currentIndex + 1 }}/{{ images.length }}</span>
      </div>
      <div class="actions">
        <button class="tool-btn" @click="handleZoom('out')" title="缩小">
          <MinusIcon class="btn-icon" />
        </button>
        <button class="tool-btn" @click="handleZoom('in')" title="放大">
          <PlusIcon class="btn-icon" />
        </button>
        <button class="tool-btn" @click="handleRotate" title="旋转">
          <ArrowPathIcon class="btn-icon" />
        </button>
        <button class="tool-btn" @click="handleClose" title="关闭">
          <XMarkIcon class="btn-icon" />
        </button>
      </div>
    </div>

    <!-- 导航按钮 -->
    <button 
      v-if="hasPrev"
      class="nav-btn prev"
      @click="showPrev"
      title="上一张 (←)"
    >
      <ChevronLeftIcon class="nav-icon" />
    </button>
    <button 
      v-if="hasNext"
      class="nav-btn next"
      @click="showNext"
      title="下一张 (→)"
    >
      <ChevronRightIcon class="nav-icon" />
    </button>

    <!-- 图片容器 -->
    <div 
      class="image-container"
      @mousedown="startDrag"
      @mousemove="onDrag"
      @mouseup="stopDrag"
      @mouseleave="stopDrag"
      @wheel="handleWheel"
    >
      <img 
        :src="currentImage"
        :alt="getImageName(currentImage)"
        :style="{
          transform: `translate3d(${translateX}px, ${translateY}px, 0) 
                     scale(${scale}) 
                     rotate(${rotation}deg)`,
          cursor: isDragging ? 'grabbing' : 'grab'
        }"
        @dragstart.prevent
      >
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  XMarkIcon,
  PlusIcon,
  MinusIcon,
  ArrowPathIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: Boolean,
  image: {
    type: String,
    default: ''
  },
  images: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'update:image'])

// 状态
const scale = ref(1)
const rotation = ref(0)
const isDragging = ref(false)
const startX = ref(0)
const startY = ref(0)
const translateX = ref(0)
const translateY = ref(0)
const lastTranslateX = ref(0)
const lastTranslateY = ref(0)

// 从路径中获取图片名称
const getImageName = (imagePath) => {
  if (!imagePath) return ''
  return imagePath.split('/').pop()
}

// 当前图片索引
const currentIndex = computed(() => {
  console.log("需要显示的图片",props.image)
  console.log("数组中的图片",props.images)
  return props.images.indexOf(props.image)
})

// 当前显示的图片
const currentImage = computed(() => {
  return props.images[currentIndex.value] || props.image
})

// 导航状态
const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < props.images.length - 1)

// 监听显示状态
watch(() => props.modelValue, (val) => {
  if (val) {
    // 重置状态
    scale.value = 1
    rotation.value = 0
    translateX.value = 0
    translateY.value = 0
    // 禁止body滚动
    document.body.style.overflow = 'hidden'
  } else {
    // 恢复body滚动
    document.body.style.overflow = ''
  }
})

// 关闭预览
const handleClose = () => {
  emit('update:modelValue', false)
}

// 缩放控制
const handleZoom = (type) => {
  const step = 0.25
  if (type === 'in' && scale.value < 3) {
    scale.value += step
  } else if (type === 'out' && scale.value > 0.5) {
    scale.value -= step
  }
}

// 鼠标滚轮缩放
const handleWheel = (e) => {
  e.preventDefault()
  const delta = e.deltaY
  if (delta < 0) {
    handleZoom('in')
  } else {
    handleZoom('out')
  }
}

// 旋转控制
const handleRotate = () => {
  rotation.value = (rotation.value + 90) % 360
}

// 拖动控制
const startDrag = (e) => {
  e.preventDefault()
  isDragging.value = true
  startX.value = e.clientX
  startY.value = e.clientY
  lastTranslateX.value = translateX.value
  lastTranslateY.value = translateY.value
}

const onDrag = (e) => {
  if (!isDragging.value) return
  
  const dx = e.clientX - startX.value
  const dy = e.clientY - startY.value
  
  // 计算新的位置
  translateX.value = lastTranslateX.value + dx
  translateY.value = lastTranslateY.value + dy
}

const stopDrag = () => {
  isDragging.value = false
  // 保存最后的位置
  lastTranslateX.value = translateX.value
  lastTranslateY.value = translateY.value
}

// 重置变换
const resetTransform = () => {
  scale.value = 1
  rotation.value = 0
  translateX.value = 0
  translateY.value = 0
  lastTranslateX.value = 0
  lastTranslateY.value = 0
}

// 导航控制
const showPrev = () => {
  if (hasPrev.value) {
    resetTransform()
    const prevImage = props.images[currentIndex.value - 1]
    emit('update:image', prevImage)
  }
}

const showNext = () => {
  if (hasNext.value) {
    resetTransform()
    const nextImage = props.images[currentIndex.value + 1]
    emit('update:image', nextImage)
  }
}

// 键盘事件处理
const handleKeydown = (e) => {
  if (!props.modelValue) return
  
  switch (e.key) {
    case 'ArrowLeft':
      showPrev()
      break
    case 'ArrowRight':
      showNext()
      break
    case 'Escape':
      e.stopPropagation()
      handleClose()
      break
  }
}

// 监听键盘事件
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.image-viewer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toolbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.5), transparent);
  color: white;
  z-index: 1;
}

.image-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.image-name {
  font-size: 14px;
  font-weight: 500;
}

.image-index {
  font-size: 12px;
  opacity: 0.8;
}

.actions {
  display: flex;
  gap: 8px;
}

.tool-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tool-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.nav-btn {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 2;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.nav-btn.prev {
  left: 20px;
}

.nav-btn.next {
  right: 20px;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.image-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.image-container img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
  transition: transform 0.1s linear;
  user-select: none;
  will-change: transform;
}
</style> 