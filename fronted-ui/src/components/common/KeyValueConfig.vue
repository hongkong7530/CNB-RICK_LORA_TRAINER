<template>
  <div class="key-value-config">
    <div 
      v-for="(value, key) in modelValue" 
      :key="key"
      class="key-value-item"
    >
      <div class="key-name">{{ key }}</div>
      <input 
        :value="value"
        @input="updateValue(key, $event.target.value)"
        class="mac-input"
        :placeholder="`${key}的值`"
        :disabled="disabled"
      >
      <button 
        type="button" 
        class="key-value-remove" 
        @click="removeItem(key)"
        :disabled="disabled"
      >×</button>
    </div>
    
    <div class="key-value-add" v-if="!disabled">
      <input 
        v-model="newItem.key"
        class="mac-input"
        :placeholder="keyPlaceholder"
      >
      <input 
        v-model="newItem.value"
        class="mac-input"
        :placeholder="valuePlaceholder"
      >
      <button 
        type="button" 
        class="mac-btn small" 
        @click="addItem"
      >{{ addButtonText }}</button>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, reactive } from 'vue'
import message from '@/utils/message'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  keyPlaceholder: {
    type: String,
    default: '键名'
  },
  valuePlaceholder: {
    type: String,
    default: '值'
  },
  addButtonText: {
    type: String,
    default: '添加'
  },
  keyRequiredMessage: {
    type: String,
    default: '请输入键名'
  }
})

const emit = defineEmits(['update:modelValue'])

const newItem = reactive({
  key: '',
  value: ''
})

// 更新值
const updateValue = (key, value) => {
  const updatedValue = { ...props.modelValue, [key]: value }
  emit('update:modelValue', updatedValue)
}

// 添加新项
const addItem = () => {
  if (!newItem.key) {
    message.warning(props.keyRequiredMessage)
    return
  }
  
  // 创建一个新对象以触发响应式更新
  const updatedValue = { ...props.modelValue, [newItem.key]: newItem.value }
  
  // 触发更新事件
  emit('update:modelValue', updatedValue)
  
  // 清空输入
  newItem.key = ''
  newItem.value = ''
}

// 移除项
const removeItem = (key) => {
  // 创建一个新对象以触发响应式更新
  const updatedValue = { ...props.modelValue }
  delete updatedValue[key]
  
  // 触发更新事件
  emit('update:modelValue', updatedValue)
}
</script>

<style scoped>
.key-value-config {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 12px;
  background: var(--background-tertiary);
}

.key-value-item {
  display: grid;
  grid-template-columns: 150px 1fr 30px;
  gap: 8px;
  align-items: center;
}

.key-name {
  font-weight: 500;
  font-size: 13px;
  color: var(--text-primary);
}

.key-value-remove {
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0;
}

.key-value-remove:hover:not(:disabled) {
  color: var(--danger-color);
}

.key-value-remove:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.key-value-add {
  display: grid;
  grid-template-columns: 150px 1fr auto;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border-color);
}

.mac-btn.small {
  height: 36px;
  padding: 0 12px;
  font-size: 12px;
  background: var(--info-bg);
  color: var(--info-color);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.mac-btn.small:hover {
  background: var(--info-bg-hover);
}

.mac-input {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--background-secondary);
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
}

.mac-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 20%, transparent);
}

.mac-input:disabled {
  background: var(--background-tertiary);
  cursor: not-allowed;
}
</style> 