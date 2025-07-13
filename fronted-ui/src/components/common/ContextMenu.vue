<template>
  <Teleport to="body">
    <div 
      v-if="show" 
      class="context-menu"
      :style="{ top: top + 'px', left: left + 'px', zIndex }"
      @click.stop
      ref="menuRef"
    >
      <template v-for="(item, index) in menuItems" :key="index">
        <!-- 分割线 -->
        <div v-if="item.type === 'divider'" class="menu-divider"></div>
        
        <!-- 菜单项 -->
        <div 
          v-else
          class="menu-item"
          :class="{ 
            'disabled': item.disabled,
            [item.className]: item.className
          }"
          @click="handleItemClick(item)"
        >
          <component 
            v-if="item.icon" 
            :is="item.icon" 
            class="menu-icon"
          />
          <span class="menu-item-text">{{ item.label }}</span>
        </div>
      </template>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount,} from 'vue'

const props = defineProps({
  /**
   * 是否显示菜单
   */
  show: {
    type: Boolean,
    default: false
  },
  /**
   * 菜单顶部位置
   */
  top: {
    type: Number,
    default: 0
  },
  /**
   * 菜单左侧位置
   */
  left: {
    type: Number,
    default: 0
  },
  /**
   * 菜单项配置
   * [
   *   { 
   *     type: 'item', // 'item' 或 'divider'
   *     id: 'unique-id', // 用于识别菜单项
   *     label: '菜单项文本',
   *     icon: IconComponent, // 可选，菜单项图标
   *     disabled: false, // 可选，是否禁用
   *     className: 'custom-class', // 可选，自定义类名
   *     data: {} // 可选，传递给事件处理函数的数据
   *   },
   *   { type: 'divider' } // 分割线
   * ]
   */
  menuItems: {
    type: Array,
    default: () => []
  },
  /**
   * z-index层级
   */
  zIndex: {
    type: Number,
    default: 1000
  },
  /**
   * 点击外部是否自动关闭
   */
  closeOnOutsideClick: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:show', 'select', 'close'])

// 菜单DOM引用
const menuRef = ref(null)

// 处理菜单项点击
const handleItemClick = (item) => {
  if (item.disabled) return
  
  emit('select', {
    id: item.id,
    data: item.data
  })
  
  // 点击后自动关闭菜单
  closeMenu()
}

// 关闭菜单
const closeMenu = () => {
  emit('update:show', false)
  emit('close')
}

// 处理外部点击 - 使用全局点击处理器
const globalClickHandler = (event) => {
  // 如果菜单显示，且点击的不是菜单内部元素
  if (props.show && menuRef.value && !menuRef.value.contains(event.target)) {
    closeMenu()
  }
}

// 处理ESC键关闭
const handleKeyDown = (event) => {
  if (event.key === 'Escape' && props.show) {
    closeMenu()
  }
}

// 组件挂载时添加全局事件监听
onMounted(() => {
  // 添加全局点击事件，使用捕获阶段
  document.addEventListener('click', globalClickHandler, true)
  document.addEventListener('contextmenu', globalClickHandler, true)
  document.addEventListener('keydown', handleKeyDown)
})

// 组件卸载时移除全局事件监听
onBeforeUnmount(() => {
  document.removeEventListener('click', globalClickHandler, true)
  document.removeEventListener('contextmenu', globalClickHandler, true)
  document.removeEventListener('keydown', handleKeyDown)
})

</script>

<style scoped>
.context-menu {
  position: fixed;
  background: var(--background-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  box-shadow: var(--shadow-md);
  min-width: 160px;
  max-width: 240px;
  overflow: hidden;
  padding: 4px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.menu-item:hover {
  background: var(--background-tertiary);
}

.menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.menu-item.disabled:hover {
  background: none;
}

.menu-item.danger:hover {
  background: #fee2e2;
  color: #b91c1c;
}

.menu-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.menu-item-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  user-select: none;
}

.menu-divider {
  height: 1px;
  background-color: var(--border-color-light);
  margin: 4px 0;
}
</style> 