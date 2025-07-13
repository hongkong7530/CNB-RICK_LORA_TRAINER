<template>
  <div 
    class="loading-spinner"
    :class="{ 
      'is-small': size === 'small',
      'is-large': size === 'large'
    }"
    :style="{ 
      borderColor: color,
      borderTopColor: 'transparent'
    }"
  ></div>
</template>

<script setup>
defineProps({
  // 尺寸: small, medium, large
  size: {
    type: String,
    default: 'medium'
  },
  // 颜色
  color: {
    type: String,
    default: 'var(--primary-color)'
  }
})
</script>

<style scoped>
.loading-spinner {
  display: inline-block;
  width: 24px;
  height: 24px;
  border: 2px solid;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-spinner.is-small {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

.loading-spinner.is-large {
  width: 32px;
  height: 32px;
  border-width: 3px;
}

@keyframes spin {
  to { 
    transform: rotate(360deg);
  }
}
</style> 