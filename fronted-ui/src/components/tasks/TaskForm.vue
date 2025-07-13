<template>
  <form @submit.prevent="handleSubmit" class="task-form">
    <div class="form-group">
      <label>任务名称</label>
      <input 
        v-model="form.name"
        class="mac-input"
        placeholder="请输入任务名称"
        :disabled="props.loading"
      >
    </div>
    
    <div class="form-group">
      <label>任务描述</label>
      <textarea
        v-model="form.description"
        class="mac-textarea"
        placeholder="请输入任务描述"
        :disabled="props.loading"
      />
    </div>
  </form>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const form = ref({
  name: '',
  description: ''
})

const handleSubmit = () => {
  if (!form.value.name) {
    return
  }
  return { ...form.value }  // 返回表单数据
}

// 暴露提交方法给父组件
defineExpose({
  submit: handleSubmit
})
</script>

<style scoped>
.task-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  color: var(--text-secondary);
}

.mac-textarea {
  min-height: 100px;
  resize: vertical;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  font-size: 14px;
  font-family: inherit;
}

.mac-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.1);
}
</style> 