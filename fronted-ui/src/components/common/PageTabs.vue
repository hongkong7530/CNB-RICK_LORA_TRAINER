<template>
  <div class="page-tabs" :class="tabStyle">
    <button 
      v-for="tab in tabs" 
      :key="tab.key"
      class="tab-button" 
      :class="{ active: activeTab === tab.key }"
      @click="handleTabClick(tab.key)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  tabs: {
    type: Array,
    required: true
  },
  activeTab: {
    type: String,
    required: true
  },
  tabStyle: {
    type: String,
    default: 'default', // 'default' 或 'pills'
    validator: (value) => ['default', 'pills'].includes(value)
  }
});

const emit = defineEmits(['update:activeTab']);

const handleTabClick = (tabKey) => {
  emit('update:activeTab', tabKey);
};
</script>

<style scoped>
.page-tabs {
  display: flex;
}

/* 默认样式 - 下划线风格 */
.page-tabs.default {
  border-bottom: 1px solid var(--border-color, #E5E7EB);
}

.default .tab-button {
  padding: 12px 24px;
  background: none;
  border: none;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary, #6B7280);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.default .tab-button.active {
  color: var(--primary-color, #007AFF);
  border-bottom-color: var(--primary-color, #007AFF);
}

.default .tab-button:hover:not(.active) {
  color: var(--text-primary, #4B5563);
  background-color: var(--background-hover, #F9FAFB);
}

/* 胶囊样式 */
.page-tabs.pills {
  gap: 4px;
  background: var(--background-tertiary, #F3F4F6);
  padding: 4px;
  border-radius: 8px;
}

.pills .tab-button {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary, #6B7280);
  font-size: 14px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.pills .tab-button.active {
  background: var(--background-secondary, #FFFFFF);
  color: var(--text-primary, #111827);
  font-weight: 500;
}

.pills .tab-button:hover:not(.active) {
  color: var(--text-primary, #111827);
  background-color: rgba(var(--background-secondary-rgb), 0.5);
}

/* 响应式设计 */
@media (max-width: 640px) {
  .default .tab-button {
    padding: 10px 16px;
    font-size: 14px;
    flex: 1;
    text-align: center;
  }
  
  .pills .tab-button {
    padding: 8px 12px;
    font-size: 13px;
    flex: 1;
    text-align: center;
  }
}
</style> 