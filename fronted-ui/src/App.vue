<template>
  <div class="app-background">
    <div class="blur-layer" :style="blurPosition"></div>
    <div class="gradient-layer"></div>
  </div>
  <app-layout />
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useTheme } from '@/composables/useTheme'

// 初始化主题系统
useTheme()

// 视差效果状态
const blurPosition = ref({ transform: 'translate(0px, 0px)' })

// 处理鼠标移动
const handleMouseMove = (e) => {
  const moveX = (e.clientX - window.innerWidth / 2) * 0.01
  const moveY = (e.clientY - window.innerHeight / 2) * 0.01
  blurPosition.value = {
    transform: `translate(${moveX}px, ${moveY}px)`
  }
}

// 组件挂载时添加事件监听
onMounted(() => {
  window.addEventListener('mousemove', handleMouseMove)
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
})
</script>

<style>
.app-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  overflow: hidden;
}

.blur-layer {
  position: absolute;
  top: -20px;
  left: -20px;
  right: -20px;
  bottom: -20px;
  background: var(--bg-blur-gradient);
  filter: blur(30px);
  transition: var(--theme-transition);
}

.gradient-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-main-gradient);
  backdrop-filter: blur(20px);
  transition: var(--theme-transition);
}
</style>
