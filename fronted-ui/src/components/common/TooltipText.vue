<template>
  <span class="tooltip-trigger" @mouseenter="showTooltip" @mouseleave="hideTooltip">?</span>
  <Teleport to="body">
    <div v-if="isVisible" 
         ref="tooltipContainer"
         class="tooltip-container" 
         :style="tooltipStyle"
         @mouseenter="keepTooltip" 
         @mouseleave="hideTooltip">
      <div class="tooltip-content">
        <slot></slot>
      </div>
      <div class="tooltip-arrow" :style="arrowStyle"></div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onUnmounted, onMounted, nextTick } from 'vue';

const props = defineProps({
  width: {
    type: String,
    default: '320px'
  },
  delay: {
    type: Number,
    default: 100
  }
});

const isVisible = ref(false);
const triggerElement = ref(null);
const tooltipContainer = ref(null);
const position = ref({ x: 0, y: 0 });
const tooltipTimeout = ref(null);
const arrowPosition = ref(null);

// 计算工具提示的样式
const tooltipStyle = computed(() => {
  return {
    left: `${position.value.x}px`,
    top: `${position.value.y}px`,
    maxWidth: props.width
  };
});

// 计算箭头的样式
const arrowStyle = computed(() => {
  if (!arrowPosition.value) return {};
  return {
    left: `${arrowPosition.value}px`
  };
});

// 显示工具提示
const showTooltip = (event) => {
  // 获取触发元素
  triggerElement.value = event.currentTarget;
  
  // 设置延迟显示
  tooltipTimeout.value = setTimeout(() => {
    isVisible.value = true;
    
    // 等待下一个渲染周期后计算位置
    nextTick(() => {
      updatePosition();
    });
  }, props.delay);
};

// 隐藏工具提示
const hideTooltip = () => {
  if (tooltipTimeout.value) {
    clearTimeout(tooltipTimeout.value);
    tooltipTimeout.value = null;
  }
  isVisible.value = false;
};

// 保持工具提示显示（鼠标移到工具提示上时）
const keepTooltip = () => {
  if (tooltipTimeout.value) {
    clearTimeout(tooltipTimeout.value);
    tooltipTimeout.value = null;
  }
};

// 更新工具提示的位置
const updatePosition = () => {
  if (!triggerElement.value || !tooltipContainer.value) return;
  
  const rect = triggerElement.value.getBoundingClientRect();
  const tooltipElement = tooltipContainer.value;
  
  const tooltipRect = tooltipElement.getBoundingClientRect();
  
  // 保存原始触发元素中心点
  const triggerCenterX = rect.left + (rect.width / 2);
  
  // 默认将工具提示显示在触发元素上方
  let x = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
  let y = rect.top - tooltipRect.height - 10;
  
  // 检查是否超出视口边界
  if (x < 10) x = 10;
  if (x + tooltipRect.width > window.innerWidth - 10) {
    x = window.innerWidth - tooltipRect.width - 10;
  }
  
  // 如果上方空间不足，则显示在下方
  const isBottom = y < 10;
  if (isBottom) {
    y = rect.bottom + 10;
    tooltipElement.classList.add('tooltip-bottom');
  } else {
    tooltipElement.classList.remove('tooltip-bottom');
  }
  
  // 计算箭头位置：触发元素中心相对于新位置的偏移
  arrowPosition.value = triggerCenterX - x;
  
  // 确保箭头不会太靠近边缘
  const minArrowMargin = 15;
  if (arrowPosition.value < minArrowMargin) {
    arrowPosition.value = minArrowMargin;
  } else if (arrowPosition.value > tooltipRect.width - minArrowMargin) {
    arrowPosition.value = tooltipRect.width - minArrowMargin;
  }
  
  position.value = { x: x + window.scrollX, y: y + window.scrollY };
};

// 组件挂载时添加resize事件监听器
onMounted(() => {
  window.addEventListener('resize', handleResize);
});

// 处理窗口大小变化
const handleResize = () => {
  if (isVisible.value) {
    updatePosition();
  }
};

// 组件卸载时清理
onUnmounted(() => {
  if (tooltipTimeout.value) {
    clearTimeout(tooltipTimeout.value);
  }
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.tooltip-trigger {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: var(--border-color);
  color: var(--text-tertiary);
  font-size: 10px;
  margin-left: 4px;
  cursor: help;
}

.tooltip-container {
  position: absolute;
  z-index: 9999;
  pointer-events: auto;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
}

.tooltip-content {
  background-color: var(--background-tertiary);
  color: var(--text-primary);
  text-align: left;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: normal;
  line-height: 1.5;
  white-space: normal;
  border: 1px solid var(--border-color);
}

.tooltip-arrow {
  position: absolute;
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid var(--background-tertiary);
  transform: translateX(-50%);
}

.tooltip-bottom .tooltip-arrow {
  border-top: none;
  border-bottom: 6px solid var(--background-tertiary);
  bottom: auto;
  top: -6px;
}
</style> 