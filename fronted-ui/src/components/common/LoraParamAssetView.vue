<template>
  <div class="lora-training-params asset-view">
    <!-- 遍历所有参数分节 -->
    <div v-for="section in visibleSections" :key="section.id" class="params-section">
      <h4 class="params-section-title">{{ section.title }}</h4>

      <!-- 主要参数网格 -->
      <div class="params-grid">
        <!-- 渲染普通参数 -->
        <template v-for="param in section.params" :key="param.name">
          <!-- 特殊参数：单独一行显示 -->
          <div v-if="shouldShowParam(param, modelValue) && 
                   (param.name === 'model_train_type' || 
                    param.name === 'flux_model_path' ||
                    param.name === 'sd_model_path' ||
                    param.name === 'sdxl_model_path' ||
                    param.name === 'ae' ||
                    param.name === 'clip_l' ||
                    param.name === 't5xxl')"
               class="param-item param-item-full">
            <label>
              <div class="label-text" :class="{'has-value': hasValue(modelValue[param.name])}">
                {{ param.label }}
                <TooltipText v-if="param.tooltip" width="400px">{{ param.tooltip }}</TooltipText>
              </div>
              <span class="param-name">{{ param.name }}</span>
            </label>
            
            <!-- 根据不同类型渲染不同输入控件 -->
            <template v-if="param.type === 'text'">
              <input 
                :value="modelValue[param.name]" 
                @input="updateValue(param.name, $event.target.value)"
                :placeholder="param.placeholder" 
                class="mac-input" 
                :class="getThemeClass(param)"
                :disabled="disabled" 
                :title="modelValue[param.name]"
              />
            </template>
            
            <template v-else-if="param.type === 'number'">
              <input 
                :value="modelValue[param.name]" 
                @input="updateValue(param.name, Number($event.target.value))"
                type="number" 
                :placeholder="param.placeholder" 
                :step="param.step" 
                class="mac-input"
                :class="getThemeClass(param)"
                :disabled="disabled" 
                :title="modelValue[param.name]"
              />
            </template>
            
            <template v-else-if="param.type === 'select'">
              <select 
                :value="String(modelValue[param.name])"
                @change="updateValue(param.name, $event.target.value)" 
                class="mac-input"
                :class="getThemeClass(param)"
                :disabled="disabled"
              >
                <option 
                  v-for="option in getParamOptions(param, modelValue)" 
                  :key="option.value" 
                  :value="String(option.value)"
                >
                  {{ option.label }}
                </option>
              </select>
            </template>
          </div>

          <!-- 文本区域类型的参数（正向提示词、负面提示词）：独立一行 -->
          <div v-else-if="shouldShowParam(param, modelValue) && param.type === 'textarea'"
               class="param-item param-item-full">
            <label>
              <div class="label-text" :class="{'has-value': hasValue(modelValue[param.name])}">
                {{ param.label }}
                <TooltipText v-if="param.tooltip" width="400px">{{ param.tooltip }}</TooltipText>
              </div>
              <span class="param-name">{{ param.name }}</span>
            </label>
            
            <textarea 
              :value="modelValue[param.name]" 
              @input="updateValue(param.name, $event.target.value)"
              :placeholder="param.placeholder" 
              class="mac-textarea" 
              :class="getThemeClass(param)"
              :rows="param.rows || 2"
              :disabled="disabled"
              :title="modelValue[param.name]"
            ></textarea>
          </div>

          <!-- 默认情况：一行两个配置 -->
          <div v-else-if="shouldShowParam(param, modelValue)" class="param-item-half">
            <label>
              <div class="label-text" :class="{'has-value': hasValue(modelValue[param.name])}">
                {{ param.label }}
                <TooltipText v-if="param.tooltip" width="400px">{{ param.tooltip }}</TooltipText>
              </div>
              <span class="param-name">{{ param.name }}</span>
            </label>
            
            <!-- 根据不同类型渲染不同输入控件 -->
            <template v-if="param.type === 'text'">
              <input 
                :value="modelValue[param.name]" 
                @input="updateValue(param.name, $event.target.value)"
                :placeholder="param.placeholder" 
                class="mac-input" 
                :class="getThemeClass(param)"
                :disabled="disabled" 
                :title="modelValue[param.name]"
              />
            </template>
            
            <template v-else-if="param.type === 'number'">
              <input 
                :value="modelValue[param.name]" 
                @input="updateValue(param.name, Number($event.target.value))"
                type="number" 
                :placeholder="param.placeholder" 
                :step="param.step" 
                class="mac-input"
                :class="getThemeClass(param)"
                :disabled="disabled" 
                :title="modelValue[param.name]"
              />
            </template>
            
            <template v-else-if="param.type === 'select'">
              <select 
                :value="String(modelValue[param.name])"
                @change="updateValue(param.name, $event.target.value)" 
                class="mac-input"
                :class="getThemeClass(param)"
                :disabled="disabled"
              >
                <option 
                  v-for="option in getParamOptions(param, modelValue)" 
                  :key="option.value" 
                  :value="String(option.value)"
                >
                  {{ option.label }}
                </option>
              </select>
            </template>
          </div>
        </template>
      </div>

      <!-- 子分节 -->
      <template v-for="subsection in getSubsections(section)" :key="subsection.id">
        <div class="params-subsection">
          <h5 class="params-subsection-title">{{ subsection.title }}</h5>
          
          <!-- 如果是桶排序和精度的特殊布局 -->
          <div v-if="subsection.id === 'bucket' || subsection.id === 'precision'" class="params-grid">
            <!-- 参数直接使用统一布局，不再区分特殊容器 -->
            <template v-for="param in subsection.params" :key="param.name">
              <div v-if="shouldShowParam(param, modelValue)" class="param-item-half">
                <label>
                  <div class="label-text" :class="{'has-value': hasValue(modelValue[param.name])}">
                    {{ param.label }}
                    <TooltipText v-if="param.tooltip" width="400px">{{ param.tooltip }}</TooltipText>
                  </div>
                  <span class="param-name">{{ param.name }}</span>
                </label>
                
                <template v-if="param.type === 'text'">
                  <input 
                    :value="modelValue[param.name]" 
                    @input="updateValue(param.name, $event.target.value)"
                    :placeholder="param.placeholder" 
                    class="mac-input" 
                    :class="getThemeClass(param)"
                    :disabled="disabled" 
                    :title="modelValue[param.name]"
                  />
                </template>
                
                <template v-else-if="param.type === 'number'">
                  <input 
                    :value="modelValue[param.name]" 
                    @input="updateValue(param.name, Number($event.target.value))"
                    type="number" 
                    :placeholder="param.placeholder" 
                    :step="param.step" 
                    class="mac-input"
                    :class="getThemeClass(param)"
                    :disabled="disabled" 
                    :title="modelValue[param.name]"
                  />
                </template>
                
                <template v-else-if="param.type === 'select'">
                  <select 
                    :value="String(modelValue[param.name])"
                    @change="updateValue(param.name, $event.target.value)" 
                    class="mac-input"
                    :class="getThemeClass(param)"
                    :disabled="disabled"
                  >
                    <option 
                      v-for="option in getParamOptions(param, modelValue)" 
                      :key="option.value" 
                      :value="String(option.value)"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </template>
              </div>
            </template>
          </div>
          
          <div v-else class="params-grid">
            <template v-for="param in subsection.params" :key="param.name">
              <!-- 文本区域类型的参数（正向提示词、负面提示词）：独立一行 -->
              <div v-if="shouldShowParam(param, modelValue) && 
                        (param.type === 'textarea' || 
                         param.name === 'positive_prompt' || 
                         param.name === 'negative_prompt')"
                   class="param-item param-item-full">
                <label>
                  <div class="label-text" :class="{'has-value': hasValue(modelValue[param.name])}">
                    {{ param.label }}
                    <TooltipText v-if="param.tooltip" width="400px">{{ param.tooltip }}</TooltipText>
                  </div>
                  <span class="param-name">{{ param.name }}</span>
                </label>
                
                <textarea 
                  :value="modelValue[param.name]" 
                  @input="updateValue(param.name, $event.target.value)"
                  :placeholder="param.placeholder" 
                  class="mac-textarea" 
                  :class="getThemeClass(param)"
                  :rows="param.rows || 2"
                  :disabled="disabled"
                  :title="modelValue[param.name]"
                ></textarea>
              </div>

              <!-- 默认情况：一行两个配置 -->
              <div v-else-if="shouldShowParam(param, modelValue)" class="param-item-half">
                <label>
                  <div class="label-text" :class="{'has-value': hasValue(modelValue[param.name])}">
                    {{ param.label }}
                    <TooltipText v-if="param.tooltip" width="400px">{{ param.tooltip }}</TooltipText>
                  </div>
                  <span class="param-name">{{ param.name }}</span>
                </label>
                
                <template v-if="param.type === 'text'">
                  <input 
                    :value="modelValue[param.name]" 
                    @input="updateValue(param.name, $event.target.value)"
                    :placeholder="param.placeholder" 
                    class="mac-input" 
                    :class="getThemeClass(param)"
                    :disabled="disabled" 
                    :title="modelValue[param.name]"
                  />
                </template>
                
                <template v-else-if="param.type === 'number'">
                  <input 
                    :value="modelValue[param.name]" 
                    @input="updateValue(param.name, Number($event.target.value))"
                    type="number" 
                    :placeholder="param.placeholder" 
                    :step="param.step" 
                    class="mac-input"
                    :class="getThemeClass(param)"
                    :disabled="disabled" 
                    :title="modelValue[param.name]"
                  />
                </template>
                
                <template v-else-if="param.type === 'select'">
                  <select 
                    :value="String(modelValue[param.name])"
                    @change="updateValue(param.name, $event.target.value)" 
                    class="mac-input"
                    :class="getThemeClass(param)"
                    :disabled="disabled"
                  >
                    <option 
                      v-for="option in getParamOptions(param, modelValue)" 
                      :key="option.value" 
                      :value="String(option.value)"
                    >
                      {{ option.label }}
                    </option>
                  </select>
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
import { defineProps, defineEmits, computed, onMounted } from 'vue';
import { PARAM_SECTIONS } from '../../composables/useLoraParams';
import TooltipText from './TooltipText.vue';
import { getParamOptions, getParamThemeClass, updateModelValue, shouldShowParam } from '../../utils/paramUtils';

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

// 添加判断值是否存在的辅助函数
const hasValue = (value) => {
  if (value === undefined || value === null) return false;
  if (typeof value === 'string') return value.trim() !== '';
  if (typeof value === 'number') return true; // 数字类型（包括0）视为有值
  if (typeof value === 'boolean') return true; // 布尔值（包括false）视为有值
  return true;
};

// 根据参数主题获取对应的CSS类
const getThemeClass = getParamThemeClass;

// 更新值的方法，使用公共工具函数
const updateValue = (key, value) => {
  const updatedModel = updateModelValue(key, value, props.modelValue, PARAM_SECTIONS);
  emit('update:modelValue', updatedModel);
};

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

// 在组件挂载时，根据当前model_train_type设置依赖默认值
onMounted(() => {
  if (props.modelValue.model_train_type) {
    // 创建一个新对象，避免直接修改props
    const updatedModel = { ...props.modelValue };
    
    // 调用updateValue更新依赖的默认值
    updateValue('model_train_type', updatedModel.model_train_type);
  }
});
</script>

<style scoped>
/* 资产表单样式 */
.params-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px dashed #E5E7EB;
  padding-top: 16px;
}

.params-section:first-child {
  border-top: none;
  padding-top: 0;
}

.params-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #4B5563;
  margin: 0;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 4px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.param-item label {
  font-size: 12px;
  color: #6B7280;
}

.param-item-half {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
  min-width: 0;
}

.param-item-half label {
  font-size: 12px;
  color: #6B7280;
}

.param-item-full {
  grid-column: span 2;
}

.param-item-group {
  display: flex;
  gap: 12px;
}

/* 通用样式 */
.mac-input, .mac-textarea {
  width: 100%;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
  background: #FFFFFF;
  color: #1C1C1E;
  font-size: 14px;
  transition: all 0.2s ease;
  /* 添加悬停提示样式 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mac-input {
  height: 36px;
  padding: 0 12px;
}

.mac-input:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.mac-input:disabled {
  background: #F3F4F6;
  cursor: not-allowed;
}

.mac-input:hover, .mac-textarea:hover {
  background-color: #F9FAFB;
  z-index: 5;
  position: relative;
}

/* 不同模型类型的主题样式 */
.theme-flux {
  border-color: #0A84FF;
}

.theme-flux:focus {
  border-color: #0A84FF;
  box-shadow: 0 0 0 2px rgba(10, 132, 255, 0.2);
}

.theme-sd {
  border-color: #30D158;
}

.theme-sd:focus {
  border-color: #30D158;
  box-shadow: 0 0 0 2px rgba(48, 209, 88, 0.2);
}

.theme-sdxl {
  border-color: #FF9F0A;
}

.theme-sdxl:focus {
  border-color: #FF9F0A;
  box-shadow: 0 0 0 2px rgba(255, 159, 10, 0.2);
}

.param-name {
  font-size: 11px;
  color: #6B7280;
  opacity: 0.8;
  font-weight: normal;
  display: block;
  margin-top: 2px;
}

label {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0;
}

.label-text {
  font-size: 12px;
  color: #6B7280;
  font-weight: normal;
}

.label-text.has-value::after {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #007AFF;
  margin-left: 6px;
  vertical-align: middle;
}

.params-subsection {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed #E5E7EB;
  grid-column: 1 / -1;
}

.params-subsection-title {
  font-size: 13px;
  font-weight: 500;
  color: #4B5563;
  margin: 0 0 12px 0;
}

.mac-textarea {
  min-height: 80px;
  padding: 12px;
  line-height: 1.5;
  resize: vertical;
  white-space: normal; /* 文本域需要正常换行 */
}

.mac-textarea:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.mac-textarea:disabled {
  background: #F3F4F6;
  cursor: not-allowed;
}

/* 媒体查询适配 */
@media (max-width: 768px) {
  .params-grid {
    grid-template-columns: 1fr;
  }
}
</style> 