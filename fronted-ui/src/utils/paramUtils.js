/**
 * 参数处理工具函数
 */

/**
 * 根据参数名在参数定义中查找完整的参数定义
 * @param {string} paramName - 参数名称
 * @param {Array} paramSections - 参数定义区域数组
 * @returns {Object|null} - 参数定义对象或null
 */
export const findParamDefinition = (paramName, paramSections) => {
  for (const section of paramSections) {
    const param = section.params.find(p => p.name === paramName);
    if (param) return param;
    
    // 查找子分节
    if (section.subsection) {
      for (const subsection of paramSections.filter(s => s.parent === section.id)) {
        const subParam = subsection.params.find(p => p.name === paramName);
        if (subParam) return subParam;
      }
    }
  }
  return null;
};

/**
 * 根据参数定义正确解析值的类型
 * @param {string|number|boolean} value - 需要解析的值
 * @param {Object} paramDef - 参数定义
 * @returns {string|number|boolean} - 解析后的值
 */
export const parseParamValue = (value, paramDef) => {
  if (!paramDef) return value;
  
  let parsedValue = value;
  
  if (paramDef.type === 'number') {
    // 确保数字类型是实际的数字
    parsedValue = Number(value);
  } else if (paramDef.type === 'select') {
    // 处理选择类型，特别是布尔值
    if (value === 'true') {
      parsedValue = true;
    } else if (value === 'false') {
      parsedValue = false;
    } else if (paramDef.options) {
      // 检查选项中是否有布尔值
      const matchingOption = paramDef.options.find(opt => String(opt.value) === String(value));
      if (matchingOption && typeof matchingOption.value === 'boolean') {
        parsedValue = matchingOption.value;
      }
    }
  }
  
  return parsedValue;
};

/**
 * 获取参数选项
 * @param {Object} param - 参数定义
 * @param {Object} modelValue - 当前模型值
 * @returns {Array} - 选项数组
 */
export const getParamOptions = (param, modelValue) => {
  // 如果参数有标准options属性，直接使用
  if (param.options) {
    return param.options;
  }
  // 如果参数有options_by_type属性，根据当前model_train_type选择对应的选项列表
  else if (param.options_by_type && modelValue.model_train_type) {
    return param.options_by_type[modelValue.model_train_type] || [];
  }
  
  return [];
};

/**
 * 根据参数生成主题CSS类
 * @param {Object} param - 参数定义
 * @returns {string} - CSS类名
 */
export const getParamThemeClass = (param) => {
  if (param.name === 'flux_model_path' || param.theme === 'flux') return 'theme-flux';
  if (param.name === 'sd_model_path' || param.theme === 'sd') return 'theme-sd';
  if (param.name === 'sdxl_model_path' || param.theme === 'sdxl') return 'theme-sdxl';
  return '';
};

/**
 * 更新模型参数值，处理类型转换和依赖更新
 * @param {string} key - 参数名称
 * @param {any} value - 新值
 * @param {Object} modelValue - 当前模型值
 * @param {Array} paramSections - 参数定义区域数组
 * @returns {Object} - 更新后的模型
 */
export const updateModelValue = (key, value, modelValue, paramSections) => {
  // 根据参数定义找到当前参数
  const paramDef = findParamDefinition(key, paramSections);
  
  // 解析值类型
  const parsedValue = parseParamValue(value, paramDef);
  
  // 创建更新后的模型
  const updatedModel = {
    ...modelValue,
    [key]: parsedValue
  };
  
  // 处理依赖更新
  handleDependencies(key, value, updatedModel);
  
  return updatedModel;
};

/**
 * 处理参数依赖关系更新
 * @param {string} key - 参数名称
 * @param {any} value - 新值
 * @param {Object} updatedModel - 更新中的模型
 */
const handleDependencies = (key, value, updatedModel) => {
  // 如果更新的是model_train_type，则同时更新依赖的默认值
  if (key === 'model_train_type') {
    // 根据不同的训练类型设置对应的网络模块默认值
    if (value === 'flux-lora' &&
      !['networks.lora_flux', 'networks.oft_flux', 'lycoris.kohya'].includes(updatedModel.network_module)) {
      updatedModel.network_module = 'networks.lora_flux';
    }
    else if ((value === 'sd-lora' || value === 'sdxl-lora') &&
      !['networks.lora', 'networks.dylora', 'networks.oft', 'lycoris.kohya'].includes(updatedModel.network_module)) {
      updatedModel.network_module = 'networks.lora';
    }
  }
};

/**
 * 判断参数是否应该显示
 * @param {Object} param - 参数定义
 * @param {Object} allParams - 所有参数值
 * @returns {boolean} - 是否应该显示
 */
export const shouldShowParam = (param, allParams) => {
  if (!param.depends) return true;
  
  // 支持多条件依赖 (使用 || 分隔)
  if (param.depends.includes('||')) {
    const conditions = param.depends.split('||').map(c => c.trim());
    // 任一条件满足即可显示
    return conditions.some(condition => checkSingleCondition(condition, allParams));
  }
  
  // 单条件依赖
  return checkSingleCondition(param.depends, allParams);
};

/**
 * 检查单个条件
 * @param {string} condition - 条件字符串
 * @param {Object} allParams - 所有参数值
 * @returns {boolean} - 条件是否满足
 */
const checkSingleCondition = (condition, allParams) => {
  const [dependName, dependValue] = condition.split('=');
  return String(allParams[dependName]) === dependValue;
};

/**
 * 获取选择框选中值对应的标签文本
 * @param {Object} param - 参数定义
 * @param {any} value - 当前选中值
 * @param {Object} modelValue - 当前模型值
 * @returns {string} - 对应的标签文本
 */
export const getSelectedLabel = (param, value, modelValue) => {
  const options = getParamOptions(param, modelValue);
  const option = options.find(opt => String(opt.value) === String(value));
  return option ? option.label : String(value);
}; 