<template>
  <div class="theme-switcher">
    <!-- 主题按钮 -->
    <button 
      class="theme-btn" 
      @click="toggleDropdown"
      :class="{ active: isDropdownOpen }"
    >
      <span class="theme-icon">{{ theme.icon }}</span>
      <span class="theme-name">{{ theme.name }}</span>
      <svg class="dropdown-arrow" :class="{ rotate: isDropdownOpen }" viewBox="0 0 24 24">
        <path d="M7 10l5 5 5-5z" />
      </svg>
    </button>

    <!-- 下拉菜单 -->
    <Teleport to="body">
      <Transition name="dropdown">
        <div 
          v-if="isDropdownOpen" 
          class="theme-dropdown"
          :style="dropdownStyle"
          @click.stop
        >
          <div class="dropdown-content">
            <!-- 系统主题选项 -->
            <div 
              class="theme-option system-option"
              :class="{ active: isSystemTheme }"
              @click="handleSystemTheme"
            >
              <span class="option-icon">🖥️</span>
              <div class="option-content">
                <span class="option-name">跟随系统</span>
                <span class="option-desc">自动切换主题</span>
              </div>
              <div class="option-indicator" v-if="isSystemTheme">✓</div>
            </div>

            <div class="dropdown-divider"></div>

            <!-- 主题列表 -->
            <div 
              v-for="themeOption in availableThemes" 
              :key="themeOption.id"
              class="theme-option"
              :class="{ active: currentTheme === themeOption.id && !isSystemTheme }"
              @click="handleThemeSelect(themeOption.id)"
            >
              <span class="option-icon">{{ themeOption.icon }}</span>
              <div class="option-content">
                <span class="option-name">{{ themeOption.name }}</span>
                <span class="option-desc">{{ getThemeDescription(themeOption.id) }}</span>
              </div>
              <div class="option-indicator" v-if="currentTheme === themeOption.id && !isSystemTheme">✓</div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 背景遮罩 -->
    <Teleport to="body">
      <Transition name="backdrop">
        <div 
          v-if="isDropdownOpen" 
          class="theme-backdrop"
          @click="closeDropdown"
        ></div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useTheme } from '@/composables/useTheme'

// 主题相关状态
const { 
  currentTheme, 
  theme, 
  availableThemes, 
  isSystemTheme,
  setTheme, 
  setSystemTheme 
} = useTheme()

// 下拉菜单状态
const isDropdownOpen = ref(false)
const dropdownStyle = ref({})

// 主题描述
const getThemeDescription = (themeId) => {
  const descriptions = {
    light: '清爽明亮的界面',
    orange: '温暖活力的橘色',
    dark: '护眼舒适的夜间模式'
  }
  return descriptions[themeId] || ''
}

// 切换下拉菜单
const toggleDropdown = async () => {
  if (isDropdownOpen.value) {
    closeDropdown()
  } else {
    await openDropdown()
  }
}

// 打开下拉菜单
const openDropdown = async () => {
  isDropdownOpen.value = true
  await nextTick()
  calculateDropdownPosition()
}

// 关闭下拉菜单
const closeDropdown = () => {
  isDropdownOpen.value = false
}

// 计算下拉菜单位置
const calculateDropdownPosition = () => {
  const button = document.querySelector('.theme-btn')
  if (!button) return

  const rect = button.getBoundingClientRect()
  const dropdownWidth = 240
  const dropdownHeight = 200
  
  let left = rect.left
  let top = rect.bottom + 8

  // 确保不超出右边界
  if (left + dropdownWidth > window.innerWidth - 20) {
    left = rect.right - dropdownWidth
  }

  // 确保不超出底部边界
  if (top + dropdownHeight > window.innerHeight - 20) {
    top = rect.top - dropdownHeight - 8
  }

  dropdownStyle.value = {
    left: `${left}px`,
    top: `${top}px`
  }
}

// 处理主题选择
const handleThemeSelect = (themeId) => {
  setTheme(themeId)
  closeDropdown()
}

// 处理系统主题
const handleSystemTheme = () => {
  setSystemTheme()
  closeDropdown()
}

// 处理键盘事件
const handleKeydown = (e) => {
  if (e.key === 'Escape') {
    closeDropdown()
  }
}

// 监听窗口大小变化
const handleResize = () => {
  if (isDropdownOpen.value) {
    calculateDropdownPosition()
  }
}

// 生命周期
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.theme-switcher {
  position: relative;
  display: inline-block;
}

.theme-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--background-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--theme-transition);
  font-size: 14px;
  color: var(--text-primary);
  min-width: 120px;
}

.theme-btn:hover {
  background: var(--background-tertiary);
  border-color: var(--primary-color);
}

.theme-btn.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 20%, transparent);
}

.theme-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.theme-name {
  flex: 1;
  text-align: left;
  font-weight: 500;
}

.dropdown-arrow {
  width: 16px;
  height: 16px;
  fill: var(--text-secondary);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.dropdown-arrow.rotate {
  transform: rotate(180deg);
}

.theme-dropdown {
  position: fixed;
  z-index: 1000;
  background: var(--background-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(20px);
  width: 240px;
  overflow: hidden;
}

.dropdown-content {
  padding: 8px;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--theme-transition);
  position: relative;
}

.theme-option:hover {
  background: var(--background-tertiary);
}

.theme-option.active {
  background: color-mix(in srgb, var(--primary-color) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--primary-color) 30%, transparent);
}

.system-option {
  background: linear-gradient(135deg, 
    color-mix(in srgb, var(--primary-color) 5%, transparent),
    color-mix(in srgb, var(--info-color) 5%, transparent)
  );
  border: 1px solid color-mix(in srgb, var(--primary-color) 20%, transparent);
}

.system-option.active {
  background: linear-gradient(135deg, 
    color-mix(in srgb, var(--primary-color) 15%, transparent),
    color-mix(in srgb, var(--info-color) 15%, transparent)
  );
}

.option-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.option-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-name {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 14px;
}

.option-desc {
  font-size: 12px;
  color: var(--text-tertiary);
}

.option-indicator {
  color: var(--primary-color);
  font-weight: 600;
  font-size: 16px;
}

.dropdown-divider {
  height: 1px;
  background: var(--border-color-light);
  margin: 8px 0;
}

.theme-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  background: transparent;
}

/* 动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}

.backdrop-enter-active,
.backdrop-leave-active {
  transition: opacity 0.2s ease;
}

.backdrop-enter-from,
.backdrop-leave-to {
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .theme-dropdown {
    width: 200px;
  }
  
  .theme-btn {
    min-width: 100px;
    padding: 6px 10px;
  }
  
  .theme-name {
    display: none;
  }
}
</style>