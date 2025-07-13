<template>
  <div class="app-layout">
    <header class="top-bar mac-card">
      <div class="left-section">
        <div class="window-controls">
          <span class="control close"></span>
          <span class="control minimize"></span>
          <span class="control maximize"></span>
        </div>
        <nav class="main-nav">
          <router-link v-for="route in mainRoutes" :key="route.path" :to="route.path" class="nav-item"
            :class="{ active: isRouteActive(route.path) }">
            <component :is="route.icon" class="nav-icon" />
            {{ route.name }}
          </router-link>
        </nav>
      </div>

      <div class="right-section">
        <!-- 新增的图标和主题切换区域 -->
        <div class="toolbar-section">
          <div class="icon-group">
            <img src="/favicon.ico" alt="Favicon" class="toolbar-icon" title="RICK-Lora训练器" />
            <img src="/cnb.ico" alt="CNB" class="toolbar-icon cnb-icon" title="CNB-云端部署" @click="openCnbSite" />
          </div>
          <div class="dynamic-text-container">
            <span class="dynamic-title">CNB—RLT Lora训练器-by RICK BeiLinMo</span>
          </div>
          <ThemeSwitcher />
        </div>
      </div>
    </header>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { routes } from '@/router'
import ThemeSwitcher from '@/components/common/ThemeSwitcher.vue'
import {
  ServerIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  BookOpenIcon
} from '@heroicons/vue/24/outline'

const route = useRoute()

/**
 * @type {Object.<string, import('@heroicons/vue/24/outline').IconComponent>}
 */
const iconMap = {
  Assets: ServerIcon,
  Tasks: ChartBarIcon,
  Settings: Cog6ToothIcon,
  Guide: BookOpenIcon
}

/**
 * 主导航路由配置
 */
const mainRoutes = computed(() => {
  return routes
    .filter(route => route.meta?.title)
    .map(route => ({
      path: route.path,
      name: route.meta.title,
      icon: iconMap[route.name]
    }))
})

/**
 * 当前激活的路由路径
 */
const currentPath = computed(() => route.path)

/**
 * 判断路由是否激活
 * @param {string} path - 路由路径
 * @returns {boolean} - 是否激活
 */
const isRouteActive = (path) => {
  // 根路由特殊处理
  if (path === '/') {
    return currentPath.value === '/'
  }

  // 检查当前路径是否以指定路径开头
  // 确保它是一个完整的路径段（例如：/tasks 匹配 /tasks 和 /tasks/123，但不匹配 /tasks-other）
  return currentPath.value === path ||
    (currentPath.value.startsWith(path) &&
      (currentPath.value[path.length] === '/' || currentPath.value.length === path.length))
}

/**
 * 打开CNB网站
 */
const openCnbSite = () => {
  window.open('https://cnb.cool/', '_blank')
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--background-primary);
  transition: var(--theme-transition);
}

.top-bar {
  height: 48px;
  padding: 0 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color-light);
  position: relative;
  z-index: 100;
  transition: var(--theme-transition);
}

.left-section {
  display: flex;
  align-items: center;
  gap: 24px;
}

.window-controls {
  display: flex;
  gap: 8px;
  padding-right: 8px;
  border-right: 1px solid var(--border-color-light);
}

.control {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control.close {
  background: #ff5f57;
}

.control.minimize {
  background: #febc2e;
}

.control.maximize {
  background: #28c840;
}

.control:hover {
  filter: brightness(0.9);
}

.main-nav {
  display: flex;
  gap: 24px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-primary);
  text-decoration: none;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: var(--theme-transition);
  cursor: pointer;
  user-select: none;
}

.nav-item:hover {
  background: var(--background-tertiary);
}

.nav-item.active {
  background: color-mix(in srgb, var(--primary-color) 10%, transparent);
  color: var(--primary-color);
}

.nav-item.active .nav-icon {
  color: var(--primary-color);
}

.nav-icon {
  width: 16px;
  height: 16px;
  transition: var(--theme-transition);
}

.right-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 工具栏区域 */
.toolbar-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 16px;
  border-left: 1px solid var(--border-color-light);
}

.icon-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-icon {
  width: 30px;
  height: 30px;
  border-radius: 4px;
  transition: var(--theme-transition);
  cursor: pointer;
  border: 1px solid transparent;
}

.toolbar-icon:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

/* CNB图标自转效果 */
.cnb-icon {
  animation: slowRotate 6s linear infinite;
}

@keyframes slowRotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.dynamic-text-container {
  display: flex;
  align-items: center;
  max-width: 300px;
  overflow: hidden;
  position: relative;
}

.dynamic-title {
  /* 动态文字样式继承自全局CSS */
}

.main-content {
  flex: 1;
  overflow: auto;
  position: relative;
  height: calc(100vh - 48px);
  width: 100%;
  padding: 20px;
  background: transparent;
}

.main-content>* {
  height: 100%;
  width: 100%;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .window-controls {
    display: none;
  }

  .main-nav {
    gap: 12px;
  }

  .nav-item {
    padding: 6px 8px;
  }

  .nav-item span {
    display: none;
  }
  
  .toolbar-section {
    gap: 8px;
  }
  
  .icon-group {
    gap: 6px;
  }
  
  .toolbar-icon {
    width: 24px;
    height: 24px;
  }
  
  .dynamic-text-container {
    max-width: 200px;
  }
}

/* 超小屏幕 */
@media (max-width: 480px) {
  .toolbar-section {
    border-left: none;
    padding-left: 8px;
  }
  
  .icon-group {
    display: none;
  }
  
  .dynamic-text-container {
    display: none;
  }
}
</style>