<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面未找到</p>
    <router-link to="/" class="mac-btn">返回首页</router-link>
  </div>
</template>

<script>
export default {
  name: 'NotFound'
}
</script>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.not-found h1 {
  font-size: 72px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-4);
}

.not-found p {
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-6);
}
</style> 