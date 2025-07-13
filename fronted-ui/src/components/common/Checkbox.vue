<template>
  <div 
    class="custom-checkbox-wrapper"
    :class="{ 'disabled': disabled }"
    @click="toggleCheck"
  >
    <div 
      class="custom-checkbox" 
      :class="{ 
        'checked': modelValue, 
        'indeterminate': indeterminate,
        'disabled': disabled
      }"
    >
      <svg v-if="modelValue && !indeterminate" class="check-icon" viewBox="0 0 24 24">
        <path 
          d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"
          fill="currentColor"
        />
      </svg>
      <div v-if="indeterminate" class="indeterminate-line"></div>
    </div>
    <label v-if="$slots.default" class="checkbox-label">
      <slot />
    </label>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  indeterminate: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue']);

const toggleCheck = () => {
  if (props.disabled) return;
  emit('update:modelValue', !props.modelValue);
};
</script>

<style scoped>
.custom-checkbox-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.custom-checkbox-wrapper.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.custom-checkbox {
  position: relative;
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 2px solid var(--border-color-dark, #ccc);
  background-color: var(--background-secondary, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.custom-checkbox.checked {
  background-color: var(--primary-color, #3B82F6);
  border-color: var(--primary-color, #3B82F6);
}

.custom-checkbox.indeterminate {
  background-color: var(--primary-color, #3B82F6);
  border-color: var(--primary-color, #3B82F6);
}

.check-icon {
  width: 16px;
  height: 16px;
  color: var(--text-primary-inverse);
}

.indeterminate-line {
  width: 10px;
  height: 2px;
  background-color: var(--text-primary-inverse);
}

.checkbox-label {
  font-size: 14px;
  color: var(--text-primary, #000);
}

.custom-checkbox:hover:not(.checked):not(.indeterminate):not(.disabled) {
  border-color: var(--primary-color, #3B82F6);
  background-color: rgba(59, 130, 246, 0.05);
}

.custom-checkbox.checked:hover:not(.disabled),
.custom-checkbox.indeterminate:hover:not(.disabled) {
  background-color: color-mix(in srgb, var(--primary-color, #3B82F6) 90%, white);
}
</style> 