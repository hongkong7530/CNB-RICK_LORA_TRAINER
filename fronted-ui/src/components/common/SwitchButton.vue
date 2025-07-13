<template>
  <button 
    class="switch-button" 
    :class="{ 'is-active': modelValue }"
    @click="toggle"
    type="button"
  >
    <div class="switch-button-toggle"></div>
  </button>
</template>

<script>
export default {
  name: 'BaseSwitchButton',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  methods: {
    toggle() {
      this.$emit('update:modelValue', !this.modelValue)
    }
  }
}
</script>

<style scoped>
.switch-button {
  position: relative;
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background: var(--border-color);
  border: none;
  cursor: pointer;
  transition: all var(--transition-speed);
  padding: 2px;
}

.switch-button.is-active {
  background: var(--primary-color);
}

.switch-button-toggle {
  width: 20px;
  height: 20px;
  background: var(--background-secondary);
  border-radius: 50%;
  transition: transform var(--transition-speed);
}

.switch-button.is-active .switch-button-toggle {
  transform: translateX(20px);
}
</style> 