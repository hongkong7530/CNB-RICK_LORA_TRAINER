<template>
  <div class="lora-training-params settings-view">
    <!-- 遍历所有参数分节 -->
    <div v-for="section in visibleSections" :key="section.id" class="settings-section">
      <h4 class="subsection-title">{{ section.title }}</h4>

      <!-- 主要参数网格 -->
      <div class="settings-grid">
        <!-- 渲染普通参数 -->
        <template v-for="param in section.params" :key="param.name">
          <!-- 所有参数在设置页面都是统一布局 -->
          <div v-if="shouldShowParam(param, modelValue)" class="settings-item">
            <label>
              <div class="label-text" :class="{'has-changed': hasChanged(param.name)}">
                <!-- 模型训练类型参数的特殊处理 -->
                <template v-if="param.name === 'model_train_type'">
                  <div class="label-content">
                    <span>{{ param.label }}</span>
                    <span v-if="hasChanged(param.name)" class="change-indicator"></span>
                  </div>
                  <TooltipText v-if="param.tooltip" width="320px">{{ param.tooltip }}</TooltipText>
                  
                  <!-- 为模型训练类型参数添加参数推荐开关 -->
                  <div class="param-recommendation-toggle">
                    <span class="toggle-label">参数推荐</span>
                    <TooltipText width="320px">启用后，切换模型类型时会自动应用推荐的最佳参数配置</TooltipText>
                    <SwitchButton v-model="enableParamRecommendation" />
                  </div>
                </template>
                
                <!-- 其他参数的处理 -->
                <template v-else>
                  <div class="label-content">
                    <span>{{ param.label }}</span>
                    <span v-if="hasChanged(param.name)" class="change-indicator"></span>
                  </div>
                  <TooltipText v-if="param.tooltip" width="320px">{{ param.tooltip }}</TooltipText>
                </template>
              </div>
              <span class="param-name">{{ param.name }}</span>
            </label>

            <!-- 根据不同类型渲染不同输入控件 -->
            <template v-if="param.type === 'text'">
              <input :value="modelValue[param.name]" @input="updateValue(param.name, $event.target.value)"
                :placeholder="param.placeholder" class="mac-input" :class="getThemeClass(param)" :disabled="disabled"
                :title="modelValue[param.name]" />
            </template>

            <template v-else-if="param.type === 'number'">
              <input :value="modelValue[param.name]" @input="updateValue(param.name, Number($event.target.value))"
                type="number" :placeholder="param.placeholder" :step="param.step" class="mac-input" :class="getThemeClass(param)"
                :disabled="disabled" :title="modelValue[param.name]" />
            </template>

            <template v-else-if="param.type === 'select'">
              <select :value="String(modelValue[param.name])" @change="updateValue(param.name, $event.target.value)"
                class="mac-input" :class="getThemeClass(param)" :disabled="disabled">
                <option v-for="option in getParamOptions(param, modelValue)" :key="option.value"
                  :value="String(option.value)">
                  {{ option.label }}
                </option>
              </select>
            </template>

            <template v-else-if="param.type === 'textarea'">
              <textarea :value="modelValue[param.name]" @input="updateValue(param.name, $event.target.value)"
                :placeholder="param.placeholder" class="mac-textarea" :rows="param.rows || 2"
                :disabled="disabled" :title="modelValue[param.name]"></textarea>
            </template>
          </div>
        </template>
      </div>

      <!-- 子分节 -->
      <template v-for="subsection in getSubsections(section)" :key="subsection.id">
        <div class="settings-subsection">
          <h5 class="subsection-subtitle">{{ subsection.title }}</h5>

          <div class="settings-grid">
            <template v-for="param in subsection.params" :key="param.name">
              <div v-if="shouldShowParam(param, modelValue)"
                :class="['settings-item', param.type === 'textarea' ? 'settings-item-full' : '']">
                <label>
                  <div class="label-text" :class="{'has-changed': hasChanged(param.name)}">
                    <div class="label-content">
                      <span>{{ param.label }}</span>
                      <span v-if="hasChanged(param.name)" class="change-indicator"></span>
                    </div>
                    <TooltipText v-if="param.tooltip" width="320px">{{ param.tooltip }}</TooltipText>
                  </div>
                  <span class="param-name">{{ param.name }}</span>
                </label>

                <template v-if="param.type === 'text'">
                  <input :value="modelValue[param.name]" @input="updateValue(param.name, $event.target.value)"
                    :placeholder="param.placeholder" class="mac-input" :disabled="disabled" 
                    :title="modelValue[param.name]" />
                </template>

                <template v-else-if="param.type === 'number'">
                  <input :value="modelValue[param.name]" @input="updateValue(param.name, Number($event.target.value))"
                    type="number" :placeholder="param.placeholder" :step="param.step" class="mac-input"
                    :disabled="disabled" :title="modelValue[param.name]" />
                </template>

                <template v-else-if="param.type === 'select'">
                  <select :value="String(modelValue[param.name])" @change="updateValue(param.name, $event.target.value)"
                    class="mac-input" :class="getThemeClass(param)" :disabled="disabled">
                    <option v-for="option in getParamOptions(param, modelValue)" :key="option.value"
                      :value="String(option.value)">
                      {{ option.label }}
                    </option>
                  </select>
                </template>

                <template v-else-if="param.type === 'textarea'">
                  <textarea :value="modelValue[param.name]" @input="updateValue(param.name, $event.target.value)"
                    :placeholder="param.placeholder" class="mac-textarea" :rows="param.rows || 2"
                    :disabled="disabled" :title="modelValue[param.name]"></textarea>
                </template>
              </div>
            </template>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed, onMounted, ref, watch } from 'vue';
import { PARAM_SECTIONS, RECOMMENDED_PARAMS } from '../../composables/useLoraParams';
import TooltipText from './TooltipText.vue';
import { getParamOptions, getParamThemeClass, updateModelValue, shouldShowParam, findParamDefinition } from '../../utils/paramUtils';
import objectUtils from '../../utils/object';
import SwitchButton from './SwitchButton.vue';

// 从localStorage读取参数推荐状态，默认为true
const getStoredRecommendationState = () => {
  try {
    const stored = localStorage.getItem('enableParamRecommendation');
    // 如果存储的值是字符串 'false'，则返回false，否则返回true
    return stored !== null ? stored !== 'false' : true;
  } catch (e) {
    return true;
  }
};

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  showAllParams: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue']);

// 存储初始值，用于比较是否有修改
const initialValues = ref({});
// 存储已修改的字段
const changedFields = ref(new Set());
// 是否启用参数推荐，从localStorage读取初始值
const enableParamRecommendation = ref(getStoredRecommendationState());

// 在组件挂载时，保存初始值
onMounted(() => {
  if (props.modelValue) {
    initialValues.value = { ...props.modelValue };
  }
});

// 监听modelValue变化，当外部重置值时（例如保存后），更新初始值并清除修改状态
watch(() => props.modelValue, (newVal) => {
  // 只有当isSubmitting为true时才重置状态，这里我们通过检查changedFields是否为空来判断
  // 如果changedFields不为空，说明是内部更新，不需要重置状态
  if (changedFields.value.size === 0) {
    initialValues.value = { ...newVal };
  }
}, { deep: true });

// 监听模型训练类型变化，应用推荐参数
watch(() => props.modelValue.model_train_type, (newModelType) => {
  if (enableParamRecommendation.value && newModelType) {
    applyRecommendedParams(newModelType);
  }
});

// 监听参数推荐开关状态变化，保存到localStorage
watch(enableParamRecommendation, (newValue) => {
  localStorage.setItem('enableParamRecommendation', String(newValue));
  
  if (newValue && props.modelValue.model_train_type) {
    // 如果开启了参数推荐，立即应用当前模型类型的推荐参数
    applyRecommendedParams(props.modelValue.model_train_type);
  }
});

// 应用推荐参数
const applyRecommendedParams = (modelType) => {
  const recommendedParams = RECOMMENDED_PARAMS[modelType];
  if (!recommendedParams) return;
  
  // 创建更新后的模型对象
  const updatedModel = { ...props.modelValue };
  
  // 应用推荐参数
  Object.entries(recommendedParams).forEach(([key, value]) => {
    updatedModel[key] = value;
    
    // 标记为已修改
    if (!objectUtils.deepEqual(initialValues.value[key], value)) {
      changedFields.value.add(key);
    }
  });
  
  // 发出更新事件
  emit('update:modelValue', updatedModel);
};

// 检查参数是否被修改
const hasChanged = (paramName) => {
  return changedFields.value.has(paramName);
};

// 更新值的方法，使用公共工具函数，并记录修改状态
const updateValue = (key, value) => {
  const updatedModel = updateModelValue(key, value, props.modelValue, PARAM_SECTIONS);
  
  // 处理特殊类型比较
  let initialValue = initialValues.value[key];
  let currentValue = value;
  
  // 处理布尔值和字符串的比较
  if (typeof initialValue === 'boolean' || initialValue === 'true' || initialValue === 'false') {
    // 将字符串转换为布尔值进行比较
    const boolInitial = initialValue === true || initialValue === 'true' ? true : false;
    const boolCurrent = currentValue === true || currentValue === 'true' ? true : false;
    
    if (boolInitial === boolCurrent) {
      changedFields.value.delete(key);
    } else {
      changedFields.value.add(key);
    }
  } 
  // 处理数字和字符串的比较
  else if (typeof initialValue === 'number' || !isNaN(Number(initialValue))) {
    const numInitial = typeof initialValue === 'number' ? initialValue : Number(initialValue);
    const numCurrent = typeof currentValue === 'number' ? currentValue : Number(currentValue);
    
    if (numInitial === numCurrent) {
      changedFields.value.delete(key);
    } else {
      changedFields.value.add(key);
    }
  }
  // 其他类型使用deepEqual比较
  else if (!objectUtils.deepEqual(initialValue, currentValue)) {
    changedFields.value.add(key);
  } else {
    changedFields.value.delete(key);
  }
  
  emit('update:modelValue', updatedModel);
};

// 重置修改状态，通常在保存后调用
const resetChangedState = () => {
  initialValues.value = { ...props.modelValue };
  changedFields.value.clear();
};

// 暴露方法给父组件
defineExpose({
  resetChangedState
});

// 根据showAllParams过滤可见的分节
const visibleSections = computed(() => {
  return PARAM_SECTIONS.filter(section => {
    // 如果是子分节，则不在顶层显示
    if (section.subsection) {
      return false;
    }

    // 如果不是高级配置，或者showAllParams为true，则显示
    return section.always || props.showAllParams;
  });
});

// 获取某个分节的子分节
const getSubsections = (section) => {
  if (!props.showAllParams && section.id !== 'advanced') {
    return [];
  }

  return PARAM_SECTIONS.filter(subsection =>
    subsection.subsection && subsection.parent === section.id
  );
};

// 根据参数主题获取对应的CSS类
const getThemeClass = getParamThemeClass;
</script>

<style scoped>
/* 设置页面样式 */
.settings-section {
  margin-bottom: 24px;
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin: 16px 0 12px;
  color: var(--text-primary);
  transition: var(--theme-transition);
}

.settings-grid {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.settings-item {
  display: inline-block;
  vertical-align: top;
  width: 290px;
  margin-right: 16px;
  margin-bottom: 16px;
}

.settings-item-full {
  width: 100%;
  margin-right: 0;
}

.settings-subsection {
  margin: 8px 0 16px;
}

.subsection-subtitle {
  font-size: 14px;
  font-weight: 500;
  margin: 8px 0 12px;
  color: var(--text-secondary);
  transition: var(--theme-transition);
}

/* 通用样式 */
.mac-input, .mac-textarea {
  width: 100%;
  border-radius: 6px;
  border: 1px solid var(--input-border);
  background: var(--input-bg);
  color: var(--input-text);
  font-size: 14px;
  transition: var(--theme-transition);
  /* 添加悬停提示样式 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mac-input {
  height: 36px;
  padding: 0 12px;
}

.mac-input::placeholder {
  color: var(--input-placeholder);
}

.mac-input:focus {
  outline: none;
  background: var(--input-focus-bg);
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 10%, transparent);
}

.mac-input:disabled {
  background: var(--input-disabled-bg);
  border-color: var(--input-disabled-border);
  color: var(--input-disabled-text);
  cursor: not-allowed;
}

.mac-input:hover, .mac-textarea:hover {
  background-color: var(--input-hover-bg);
  border-color: var(--input-hover-border);
  z-index: 5;
  position: relative;
}

.param-name {
  font-size: 11px;
  color: var(--text-tertiary);
  opacity: 0.8;
  font-weight: normal;
  display: block;
  margin-top: 2px;
  transition: var(--theme-transition);
}

label {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0;
  margin-bottom: 6px;
}

.label-text {
  font-size: 12px;
  color: var(--form-label-text);
  font-weight: normal;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  transition: var(--theme-transition);
}

/* 标签内容容器 */
.label-content {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 修改状态标记样式 */
.change-indicator {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--primary-color);
  transition: var(--theme-transition);
}

/* 参数推荐开关样式 */
.param-recommendation-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.toggle-label {
  font-size: 12px;
  color: var(--form-label-text);
  transition: var(--theme-transition);
}

.mac-textarea {
  min-height: 80px;
  padding: 12px;
  line-height: 1.5;
  resize: vertical;
  white-space: normal; /* 文本域需要正常换行 */
  background: var(--input-bg);
  color: var(--input-text);
  border: 1px solid var(--input-border);
  border-radius: 6px;
  transition: var(--theme-transition);
}

.mac-textarea::placeholder {
  color: var(--input-placeholder);
}

.mac-textarea:focus {
  outline: none;
  background: var(--input-focus-bg);
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 10%, transparent);
}

.mac-textarea:disabled {
  background: var(--input-disabled-bg);
  border-color: var(--input-disabled-border);
  color: var(--input-disabled-text);
  cursor: not-allowed;
}

/* 媒体查询适配 */
@media (max-width: 768px) {
  .settings-item {
    width: 100%;
    margin-right: 0;
  }
}

.theme-flux {
  border-color: var(--primary-color);
}
.theme-flux:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 20%, transparent);
}
.theme-sd {
  border-color: var(--success-color);
}
.theme-sd:focus {
  border-color: var(--success-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--success-color) 20%, transparent);
}
.theme-sdxl {
  border-color: var(--warning-color);
}
.theme-sdxl:focus {
  border-color: var(--warning-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--warning-color) 20%, transparent);
}
</style>