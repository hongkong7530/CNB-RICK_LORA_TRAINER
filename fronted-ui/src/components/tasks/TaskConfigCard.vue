<template>
  <div class="task-config-card mac-card">
    <div class="tabs">
      <button class="tab-button" :class="{ active: activeTab === 'mark' }" @click="activeTab = 'mark'">
        打标配置
      </button>
      <button class="tab-button" :class="{ active: activeTab === 'training' }" @click="activeTab = 'training'">
        训练参数
      </button>
    </div>

    <!-- 打标配置 -->
    <div v-if="activeTab === 'mark'" class="config-section">
      <div class="card-header">
        <h3>打标配置</h3>
        <div class="toggle-switch-container">
          <span class="toggle-switch-label">使用全局配置</span>
          <div class="toggle-switch">
            <input type="checkbox" id="use_global_mark_config" v-model="config.use_global_mark_config"
              :disabled="!canEdit">
            <label for="use_global_mark_config"></label>
          </div>
        </div>
      </div>

      <!-- 触发词配置，不受全局配置开关影响，始终显示 -->
      <div class="form-group full-width trigger-words-section">
        <label>
          <span class="label-text" :class="{'has-value': hasValue(config.mark_config.trigger_words)}">触发词</span>
          <span class="label-en">trigger_words</span>
        </label>
        <textarea v-model="config.mark_config.trigger_words" :placeholder="getPlaceholder('mark', 'trigger_words')" rows="3" class="mac-textarea"
          :disabled="!canEdit" :title="config.mark_config.trigger_words"></textarea>
      </div>

      <div v-if="config.use_global_mark_config" class="global-config-message">
        使用系统全局打标配置
      </div>
      <div v-else class="marking-config">
        <div class="config-form">
          <!-- 打标配置表单内容 -->
          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.mark_config.auto_crop)}">自动裁剪图片</span>
                <span class="label-en">auto_crop</span>
              </label>
              <div class="switch-wrapper">
                <input type="checkbox" id="auto_crop" 
                  :checked="getBoolValue(config.mark_config.auto_crop)" 
                  @change="config.mark_config.auto_crop = $event.target.checked"
                  class="toggle-checkbox"
                  :disabled="!canEdit" />
                <label for="auto_crop" class="toggle-label"></label>
              </div>
            </div>
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.mark_config.default_crop_ratio)}">默认裁剪比例</span>
                <span class="label-en">default_crop_ratio</span>
              </label>
              <select v-model="config.mark_config.default_crop_ratio" class="mac-input" :disabled="!canEdit">
                <option v-for="ratio in defaultMarkConfig.crop_ratios" :key="ratio" :value="ratio">{{ ratio }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.mark_config.min_confidence)}">自动标签最小置信度</span>
              <span class="label-en">min_confidence</span>
            </label>
            <input type="range" v-model.number="config.mark_config.min_confidence" min="0" max="1" step="0.01"
              class="mac-slider" :disabled="!canEdit" />
            <div class="slider-value">{{ config.mark_config.min_confidence }}</div>
          </div>
          <div class="form-group">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.mark_config.max_tags)}">最大标签数量</span>
              <span class="label-en">max_tags</span>
            </label>
            <input type="number" v-model.number="config.mark_config.max_tags" min="1" max="100" class="mac-input"
              :placeholder="getPlaceholder('mark', 'max_tags')" :disabled="!canEdit" :title="config.mark_config.max_tags" />
          </div>

          <div class="form-group">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.mark_config.mark_algorithm)}">打标算法</span>
              <span class="label-en">mark_algorithm</span>
            </label>
            <select v-model="config.mark_config.mark_algorithm" class="mac-input" :disabled="!canEdit">
              <option v-for="algorithm in defaultMarkConfig.available_algorithms" :key="algorithm" :value="algorithm">{{ algorithm }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- 训练参数 -->
    <div v-if="activeTab === 'training'" class="config-section">
      <div class="card-header">
        <h3>训练参数</h3>
        <div class="toggle-switch-container">
          <span class="toggle-switch-label">使用全局配置</span>
          <div class="toggle-switch">
            <input type="checkbox" id="use_global_training_config" v-model="config.use_global_training_config"
              :disabled="!canEdit">
            <label for="use_global_training_config"></label>
          </div>
        </div>
      </div>

      <div v-if="config.use_global_training_config" class="global-config-message">
        使用系统全局训练参数配置
      </div>
      <div v-else class="training-config">
        <div class="config-form">
          <!-- 模型训练类型选择放在最前面 -->
          <div class="form-group">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.training_config.model_train_type)}">模型训练类型</span>
              <span class="label-en">model_train_type</span>
            </label>
            <select v-model="config.training_config.model_train_type" class="mac-input" :disabled="!canEdit">
              <option value="flux-lora">Flux-Lora</option>
              <option value="sd-lora">SD1.5-Lora</option>
              <option value="sdxl-lora">SDXL-Lora</option>
            </select>
          </div>
          
          <!-- 根据选择的模型类型显示对应的模型路径输入框 -->
          <div class="form-group" v-if="config.training_config.model_train_type === 'flux-lora'">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.training_config.flux_model_path)}">Flux模型路径</span>
              <span class="label-en">flux_model_path</span>
            </label>
            <input v-model="config.training_config.flux_model_path" :placeholder="getPlaceholder('training', 'flux_model_path')" class="mac-input theme-flux"
              :disabled="!canEdit" :title="config.training_config.flux_model_path" />
          </div>
          
          <div class="form-group" v-if="config.training_config.model_train_type === 'sd-lora'">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.training_config.sd_model_path)}">SD1.5模型路径</span>
              <span class="label-en">sd_model_path</span>
            </label>
            <input v-model="config.training_config.sd_model_path" :placeholder="getPlaceholder('training', 'sd_model_path')" class="mac-input theme-sd"
              :disabled="!canEdit" :title="config.training_config.sd_model_path" />
          </div>
          
          <div class="form-group" v-if="config.training_config.model_train_type === 'sdxl-lora'">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.training_config.sdxl_model_path)}">SDXL模型路径</span>
              <span class="label-en">sdxl_model_path</span>
            </label>
            <input v-model="config.training_config.sdxl_model_path" :placeholder="getPlaceholder('training', 'sdxl_model_path')" class="mac-input theme-sdxl"
              :disabled="!canEdit" :title="config.training_config.sdxl_model_path" />
          </div>
          
          <!-- Flux特有的模型路径输入框 -->
          <div v-if="config.training_config.model_train_type === 'flux-lora'">
            <div class="form-row">
              <div class="form-group">
                <label>
                  <span class="label-text" :class="{'has-value': hasValue(config.training_config.ae)}">自动编码器路径</span>
                  <span class="label-en">ae</span>
                </label>
                <input v-model="config.training_config.ae" :placeholder="getPlaceholder('training', 'ae')" class="mac-input theme-flux"
                  :disabled="!canEdit" :title="config.training_config.ae" />
              </div>
              <div class="form-group">
                <label>
                  <span class="label-text" :class="{'has-value': hasValue(config.training_config.clip_l)}">CLIP-L模型路径</span>
                  <span class="label-en">clip_l</span>
                </label>
                <input v-model="config.training_config.clip_l" :placeholder="getPlaceholder('training', 'clip_l')" class="mac-input theme-flux"
                  :disabled="!canEdit" :title="config.training_config.clip_l" />
              </div>
            </div>
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.t5xxl)}">T5XXL模型路径</span>
                <span class="label-en">t5xxl</span>
              </label>
              <input v-model="config.training_config.t5xxl" :placeholder="getPlaceholder('training', 't5xxl')" class="mac-input theme-flux"
                :disabled="!canEdit" :title="config.training_config.t5xxl" />
            </div>
          </div>
          
          <!-- 最重要的两个参数放在最前面 -->
          <div class="form-group">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.training_config.max_train_epochs)}">最大训练轮次</span>
              <span class="label-en">max_train_epochs</span>
            </label>
            <input type="range" v-model.number="config.training_config.max_train_epochs" min="1" max="20" step="1"
              class="mac-slider" :disabled="!canEdit" />
            <div class="slider-value">{{ config.training_config.max_train_epochs }}</div>
          </div>

          <div class="form-group">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.training_config.repeat_num)}">图片重复次数</span>
              <span class="label-en">repeat_num</span>
            </label>
            <input type="range" v-model.number="config.training_config.repeat_num" min="1" max="50" step="1"
              class="mac-slider" :disabled="!canEdit" />
            <div class="slider-value">{{ config.training_config.repeat_num }}</div>
          </div>

          <!-- 基础训练参数 -->
          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.train_batch_size)}">批量大小</span>
                <span class="label-en">train_batch_size</span>
              </label>
              <input type="number" v-model.number="config.training_config.train_batch_size" min="1" 
                :placeholder="getPlaceholder('training', 'train_batch_size')"
                class="mac-input" :disabled="!canEdit" :title="config.training_config.train_batch_size" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.resolution)}">分辨率</span>
                <span class="label-en">resolution</span>
              </label>
              <input v-model="config.training_config.resolution" :placeholder="getPlaceholder('training', 'resolution')" class="mac-input"
                :disabled="!canEdit" :title="config.training_config.resolution" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.network_dim)}">网络维度 (Dim)</span>
                <span class="label-en">network_dim</span>
              </label>
              <input type="number" v-model.number="config.training_config.network_dim" min="1" 
                :placeholder="getPlaceholder('training', 'network_dim')"
                class="mac-input" :disabled="!canEdit" :title="config.training_config.network_dim" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.network_alpha)}">网络Alpha值</span>
                <span class="label-en">network_alpha</span>
              </label>
              <input type="number" v-model.number="config.training_config.network_alpha" min="1" 
                :placeholder="getPlaceholder('training', 'network_alpha')"
                class="mac-input" :disabled="!canEdit" :title="config.training_config.network_alpha" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.learning_rate)}">基础学习率</span>
                <span class="label-en">learning_rate</span>
              </label>
              <input type="number" v-model.number="config.training_config.learning_rate" step="0.0001" min="0"
                :placeholder="getPlaceholder('training', 'learning_rate')" class="mac-input" :disabled="!canEdit" 
                :title="config.training_config.learning_rate" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.unet_lr)}">Unet学习率</span>
                <span class="label-en">unet_lr</span>
              </label>
              <input type="number" v-model.number="config.training_config.unet_lr" step="0.0001" min="0"
                :placeholder="getPlaceholder('training', 'unet_lr')" class="mac-input" :disabled="!canEdit" 
                :title="config.training_config.unet_lr" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.text_encoder_lr)}">文本编码器学习率</span>
                <span class="label-en">text_encoder_lr</span>
              </label>
              <input type="number" v-model.number="config.training_config.text_encoder_lr" step="0.00001" min="0"
                :placeholder="getPlaceholder('training', 'text_encoder_lr')" class="mac-input" :disabled="!canEdit" 
                :title="config.training_config.text_encoder_lr" />
            </div>
          </div>

          <div class="form-group">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.training_config.lr_scheduler)}">学习率调度器</span>
              <span class="label-en">lr_scheduler</span>
            </label>
            <select v-model="config.training_config.lr_scheduler" class="mac-input" :disabled="!canEdit">
              <option value="cosine_with_restarts">余弦退火(cosine_with_restarts)</option>
              <option value="constant">恒定(constant)</option>
              <option value="constant_with_warmup">预热恒定(constant_with_warmup)</option>
              <option value="cosine">余弦(cosine)</option>
              <option value="linear">线性(linear)</option>
              <option value="polynomial">多项式(polynomial)</option>
            </select>
          </div>
          <div class="form-group">
            <label>
              <span class="label-text" :class="{'has-value': hasValue(config.training_config.optimizer_type)}">优化器类型</span>
              <span class="label-en">optimizer_type</span>
            </label>
            <select v-model="config.training_config.optimizer_type" class="mac-input" :disabled="!canEdit">
              <option value="AdamW8bit">AdamW8bit (推荐)</option>
              <option value="AdamW">AdamW</option>
              <option value="Lion">Lion</option>
              <option value="SGDNesterov">SGDNesterov</option>
              <option value="SGDNesterov8bit">SGDNesterov8bit</option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.lr_warmup_steps)}">预热步数</span>
                <span class="label-en">lr_warmup_steps</span>
              </label>
              <input type="number" v-model.number="config.training_config.lr_warmup_steps" min="0" 
                :placeholder="getPlaceholder('training', 'lr_warmup_steps')"
                class="mac-input" :disabled="!canEdit" :title="config.training_config.lr_warmup_steps" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.lr_scheduler_num_cycles)}">学习率循环次数</span>
                <span class="label-en">lr_scheduler_num_cycles</span>
              </label>
              <input type="number" v-model.number="config.training_config.lr_scheduler_num_cycles" min="1"
                :placeholder="getPlaceholder('training', 'lr_scheduler_num_cycles')" class="mac-input" :disabled="!canEdit" 
                :title="config.training_config.lr_scheduler_num_cycles" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.save_every_n_epochs)}">每N轮保存一次</span>
                <span class="label-en">save_every_n_epochs</span>
              </label>
              <input type="number" v-model.number="config.training_config.save_every_n_epochs" min="1" 
                :placeholder="getPlaceholder('training', 'save_every_n_epochs')"
                class="mac-input" :disabled="!canEdit" :title="config.training_config.save_every_n_epochs" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.sample_every_n_epochs)}">每N轮采样一次</span>
                <span class="label-en">sample_every_n_epochs</span>
              </label>
              <input type="number" v-model.number="config.training_config.sample_every_n_epochs" min="1" 
                :placeholder="getPlaceholder('training', 'sample_every_n_epochs')"
                class="mac-input" :disabled="!canEdit" :title="config.training_config.sample_every_n_epochs" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.clip_skip)}">CLIP跳过层数</span>
                <span class="label-en">clip_skip</span>
              </label>
              <input type="number" v-model.number="config.training_config.clip_skip" min="1" max="12" 
                :placeholder="getPlaceholder('training', 'clip_skip')"
                class="mac-input" :disabled="!canEdit" :title="config.training_config.clip_skip" />
            </div>
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.seed)}">随机种子</span>
                <span class="label-en">seed</span>
              </label>
              <input type="number" v-model.number="config.training_config.seed" 
                :placeholder="getPlaceholder('training', 'seed')" class="mac-input"
                :disabled="!canEdit" :title="config.training_config.seed" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.mixed_precision)}">混合精度</span>
                <span class="label-en">mixed_precision</span>
              </label>
              <select v-model="config.training_config.mixed_precision" class="mac-input" :disabled="!canEdit">
                <option value="bf16">bf16 (推荐)</option>
                <option value="no">不使用(no)</option>
                <option value="fp16">fp16</option>
              </select>
            </div>
          </div>

          <!-- 采样相关设置 -->
          <div class="section-divider">
            <h4>采样预览设置</h4>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.generate_preview)}">生成预览图</span>
                <span class="label-en">generate_preview</span>
              </label>
              <div class="switch-wrapper">
                <input type="checkbox" id="generate_preview" v-model="config.training_config.generate_preview"
                  class="toggle-checkbox" :disabled="!canEdit" />
                <label for="generate_preview" class="toggle-label"></label>
              </div>
            </div>
            <div class="form-group" v-if="config.training_config.generate_preview">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.use_image_tags)}">使用图片标签</span>
                <span class="label-en">use_image_tags</span>
              </label>
              <div class="switch-wrapper">
                <input type="checkbox" id="use_image_tags" v-model="config.training_config.use_image_tags"
                  class="toggle-checkbox" :disabled="!canEdit" />
                <label for="use_image_tags" class="toggle-label"></label>
              </div>
            </div>
          </div>

          <div v-if="config.training_config.generate_preview" class="config-form">
            <div class="form-row" v-if="config.training_config.use_image_tags">
              <div class="form-group">
                <label>
                  <span class="label-text" :class="{'has-value': hasValue(config.training_config.max_image_tags)}">最多采用图片提示词数量</span>
                  <span class="label-en">max_image_tags</span>
                </label>
                <input type="number" v-model.number="config.training_config.max_image_tags" min="0" 
                  :placeholder="getPlaceholder('training', 'max_image_tags')"
                  class="mac-input" :disabled="!canEdit" :title="config.training_config.max_image_tags" />
              </div>
            </div>

            <div class="form-group full-width">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.positive_prompts)}">正向提示词</span>
                <span class="label-en">positive_prompts</span>
              </label>
              <textarea v-model="config.training_config.positive_prompts" 
                :placeholder="getPlaceholder('training', 'positive_prompts')" rows="2"
                class="mac-textarea" :disabled="!canEdit" :title="config.training_config.positive_prompts"></textarea>
            </div>

            <div class="form-group full-width">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.negative_prompts)}">负向提示词</span>
                <span class="label-en">negative_prompts</span>
              </label>
              <textarea v-model="config.training_config.negative_prompts" 
                :placeholder="getPlaceholder('training', 'negative_prompts')" rows="2"
                class="mac-textarea" :disabled="!canEdit" :title="config.training_config.negative_prompts"></textarea>
            </div>
            <div class="form-group">
              <label>
                <span class="label-text" :class="{'has-value': hasValue(config.training_config.sample_sampler)}">采样器</span>
                <span class="label-en">sample_sampler</span>
              </label>
              <select v-model="config.training_config.sample_sampler" class="mac-input" :disabled="!canEdit">
                <option value="euler_a">euler_a</option>
                <option value="euler">euler</option>
                <option value="ddpm">ddpm</option>
                <option value="ddim">ddim</option>
                <option value="dpm++_2m">dpm++_2m</option>
                <option value="dpm++_sde">dpm++_sde</option>
              </select>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>
                  <span class="label-text" :class="{'has-value': hasValue(config.training_config.sample_width)}">采样图宽度</span>
                  <span class="label-en">sample_width</span>
                </label>
                <input type="number" v-model.number="config.training_config.sample_width" min="64" step="8"
                  :placeholder="getPlaceholder('training', 'sample_width')" class="mac-input" :disabled="!canEdit" 
                  :title="config.training_config.sample_width" />
              </div>
              <div class="form-group">
                <label>
                  <span class="label-text" :class="{'has-value': hasValue(config.training_config.sample_height)}">预览图高度</span>
                  <span class="label-en">sample_height</span>
                </label>
                <input type="number" v-model.number="config.training_config.sample_height" min="64" step="8"
                  :placeholder="getPlaceholder('training', 'sample_height')" class="mac-input" :disabled="!canEdit" 
                  :title="config.training_config.sample_height" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  <span class="label-text" :class="{'has-value': hasValue(config.training_config.sample_cfg)}">CFG强度</span>
                  <span class="label-en">sample_cfg</span>
                </label>
                <input type="number" v-model.number="config.training_config.sample_cfg" min="1" step="0.5"
                  :placeholder="getPlaceholder('training', 'sample_cfg')" class="mac-input" :disabled="!canEdit" 
                  :title="config.training_config.sample_cfg" />
              </div>
              <div class="form-group">
                <label>
                  <span class="label-text" :class="{'has-value': hasValue(config.training_config.sample_steps)}">迭代步数</span>
                  <span class="label-en">sample_steps</span>
                </label>
                <input type="number" v-model.number="config.training_config.sample_steps" min="1" 
                  :placeholder="getPlaceholder('training', 'sample_steps')"
                  class="mac-input" :disabled="!canEdit" :title="config.training_config.sample_steps" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { tasksApi } from '@/api/tasks'; // 导入任务API
import { settingsApi } from '@/api/settings'; // 导入设置API

// 添加判断值是否存在的辅助函数
const hasValue = (value) => {
  if (value === undefined || value === null) return false;
  if (typeof value === 'string') return value.trim() !== '';
  if (typeof value === 'number') return true; // 数字类型（包括0）视为有值
  if (typeof value === 'boolean') return true; // 布尔值（包括false）视为有值
  return true;
};

// 添加处理布尔值的辅助函数
const getBoolValue = (value) => {
  return value === true || value === 'true';
};

// 训练参数默认值
const defaultTrainingConfig = {
  model_train_type: 'flux-lora',
  flux_model_path: '',
  sd_model_path: '',
  sdxl_model_path: '',
  ae: '',
  clip_l: '',
  t5xxl: '',
  max_train_epochs: 10,
  train_batch_size: 1,
  network_dim: 64,
  network_alpha: 32,
  learning_rate: 0.0001,
  unet_lr: 0.0005,
  text_encoder_lr: 0.00001,
  resolution: '512,512',
  lr_scheduler: 'cosine_with_restarts',
  lr_warmup_steps: 0,
  lr_scheduler_num_cycles: 1,
  save_every_n_epochs: 1,
  sample_every_n_epochs: 1,
  clip_skip: 1,
  seed: 42,
  mixed_precision: 'bf16',
  optimizer_type: 'AdamW8bit',
  repeat_num: 1,
  generate_preview: true,
  use_image_tags: false,
  max_image_tags: 5,
  positive_prompts: '1girl, solo',
  negative_prompts: 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,signature, watermark, username, blurry',
  sample_width: 512,
  sample_height: 768,
  sample_cfg: 7,
  sample_steps: 24,
  sample_sampler: 'euler'
};

// 打标配置默认值
const defaultMarkConfig = {
  auto_crop: true,
  crop_ratios: ['1:1', '3:2', '4:3', '2:3', '16:9', '9:16'],
  default_crop_ratio: '1:1',
  min_confidence: 0.6,
  max_tags: 20,
  trigger_words: '',
  mark_algorithm: 'wd-v1-4-convnext-tagger-v2',
  available_algorithms: [
    'wd-vit-tagger-v3',
    'wd-swinv2-tagger-v3',
    'wd-convnext-tagger-v3',
    'wd-v1-4-moat-tagger-v2',
    'wd-v1-4-convnextv2-tagger-v2',
    'wd-v1-4-convnext-tagger-v2',
    'wd-v1-4-convnext-tagger',
    'wd-v1-4-vit-tagger-v2',
    'wd-v1-4-swinv2-tagger-v2',
    'wd-v1-4-vit-tagger',
    'joycaption2'
  ]
};

const props = defineProps({
  taskId: {
    type: [Number, String],
    required: true
  },
  canEdit: {
    type: Boolean,
    default: true
  }
});

// 修改emit，发送配置对象而不仅是通知
const emit = defineEmits(['config-changed']);

// 组件状态
const isLoading = ref(false);
const saveConfigTimer = ref(null);
const config = ref({
  task_id: null,
  task_name: '',
  use_global_mark_config: true,
  use_global_training_config: true,
  mark_config: { ...defaultMarkConfig },
  training_config: { ...defaultTrainingConfig }
});

// 全局配置
const globalMarkConfig = ref({ ...defaultMarkConfig });
const globalTrainingConfig = ref({ ...defaultTrainingConfig });

// 激活的选项卡
const activeTab = ref('mark');

// 获取任务配置
const fetchConfig = async () => {
  if (!props.taskId) return;

  try {
    isLoading.value = true;
    
    // 并行请求任务配置和全局配置
    const [taskConfigData, globalMarkData, globalTrainingData] = await Promise.all([
      tasksApi.getTaskConfig(props.taskId),
      settingsApi.getTaskMarkConfig(props.taskId),
      settingsApi.getTaskTrainingConfig(props.taskId)
    ]);
    
    // 更新任务配置
    if (taskConfigData) {
      config.value = taskConfigData;
      // 组件挂载时获取配置后，也向父组件发送配置
      emit('config-changed', taskConfigData);
    }
    
    // 更新全局配置
    if (globalMarkData) {
      globalMarkConfig.value = { ...globalMarkData };
    }
    
    if (globalTrainingData) {
      globalTrainingConfig.value = { ...globalTrainingData };
    }
  } catch (error) {
    console.error('获取任务配置失败:', error);
  } finally {
    isLoading.value = false;
  }
};

// 获取输入框的placeholder值，优先使用全局配置的值
const getPlaceholder = (configType, fieldName) => {
  if (configType === 'mark') {
    return globalMarkConfig.value[fieldName] !== undefined 
      ? String(globalMarkConfig.value[fieldName]) 
      : defaultMarkConfig[fieldName] !== undefined 
        ? String(defaultMarkConfig[fieldName])
        : '';
  } else if (configType === 'training') {
    return globalTrainingConfig.value[fieldName] !== undefined 
      ? String(globalTrainingConfig.value[fieldName]) 
      : defaultTrainingConfig[fieldName] !== undefined 
        ? String(defaultTrainingConfig[fieldName])
        : '';
  }
  return '';
};

// 保存配置到后端
const saveConfig = () => {
  if (!props.taskId || !props.canEdit) return;

  // 避免频繁请求，使用防抖处理
  if (saveConfigTimer.value) {
    clearTimeout(saveConfigTimer.value);
  }

  saveConfigTimer.value = setTimeout(async () => {
    try {
      isLoading.value = true;

      // 创建要发送的配置对象
      const updateData = {
        use_global_mark_config: config.value.use_global_mark_config,
        use_global_training_config: config.value.use_global_training_config
      };

      // 根据全局配置标志决定是否发送详细配置
      if (!config.value.use_global_mark_config) {
        // 创建一个不包含空字符串值的mark_config对象
        updateData.mark_config = {};
        Object.entries(config.value.mark_config).forEach(([key, value]) => {
          if (value !== '') {
            updateData.mark_config[key] = value;
          }
        });
      } else if (config.value.mark_config?.trigger_words !== undefined && config.value.mark_config?.trigger_words !== '') {
        // 特殊处理触发词：即使使用全局配置，也保留触发词设置（如果不为空）
        updateData.mark_config = { trigger_words: config.value.mark_config.trigger_words };
      }

      if (!config.value.use_global_training_config) {
        // 创建一个不包含空字符串值的training_config对象
        updateData.training_config = {};
        Object.entries(config.value.training_config).forEach(([key, value]) => {
          if (hasValue(value)) {
            updateData.training_config[key] = value;
          }
        });
      }

      // 调用更新接口
      await tasksApi.updateTaskConfig(props.taskId, updateData);
      
      // 发送配置已更新事件
      emit('config-changed', config.value);
    } catch (error) {
      console.error('保存任务配置失败:', error);
    } finally {
      isLoading.value = false;
    }
  }, 500); // 500ms防抖
};

// 监听整个config对象的变化，一次性处理所有配置更新
watch(() => config.value, (newConfig) => {
  // 在保存到后端的同时通知父组件配置已变更
  saveConfig();
}, { deep: true, flush: 'post' });

// 监听taskId变化，重新获取配置
watch(() => props.taskId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    fetchConfig();
  }
});

// 组件挂载时获取配置
onMounted(() => {
  fetchConfig();
});
</script>

<style scoped>
.tabs {
  display: flex;
  border-bottom: 1px solid #E5E7EB;
  margin-bottom: 16px;
}

.tab-button {
  padding: 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #6B7280;
  position: relative;
  transition: all 0.2s;
}
.mac-card{
  padding: 0px 20px 20px 20px;
}

.tab-button.active {
  color: #007AFF;
  font-weight: 500;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #007AFF;
}

.tab-button:hover:not(.active) {
  color: #374151;
  background-color: rgba(0, 0, 0, 0.02);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  font-size: 16px;
  margin: 0;
}

.toggle-switch-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-switch-label {
  font-size: 14px;
  color: #6B7280;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.toggle-switch input {
  height: 0;
  width: 0;
  visibility: hidden;
  position: absolute;
}

.toggle-switch label {
  cursor: pointer;
  width: 48px;
  height: 24px;
  background: #E5E7EB;
  display: block;
  border-radius: 24px;
  position: relative;
  transition: 0.3s;
}

.toggle-switch label:after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: var(--background-secondary);
  border-radius: 20px;
  transition: 0.3s;
}

.toggle-switch input:checked+label {
  background: #007AFF;
}

.toggle-switch input:checked+label:after {
  left: calc(100% - 2px);
  transform: translateX(-100%);
}

.toggle-switch input:disabled+label {
  opacity: 0.5;
  cursor: not-allowed;
}

.global-config-message {
  padding: 24px;
  text-align: center;
  background-color: #F9FAFB;
  border-radius: 8px;
  color: #6B7280;
  font-style: italic;
}

.config-section {
  padding: 0 0 16px 0;
}

.marking-config,
.training-config {
  width: 100%;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group.full-width {
  width: 100%;
  min-width: 100%;
}

.form-group label {
  font-size: 14px;
  color: var(--text-secondary, #6B7280);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.label-text {
  font-weight: 500;
}

.label-en {
  font-size: 12px;
  color: var(--text-tertiary, #9CA3AF);
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

.mac-input {
  height: 36px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
  font-size: 14px;
  color: #1C1C1E;
  background-color: var(--background-secondary);
  transition: all 0.2s ease;
  /* 添加悬停提示样式 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

.mac-input:hover {
  background-color: #F9FAFB;
  z-index: 5;
  position: relative;
}

.mac-textarea {
  width: 100%;
  min-height: 80px;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
  background: #FFFFFF;
  color: #1C1C1E;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: all 0.2s ease;
  white-space: normal;
  overflow: auto;
  text-overflow: clip;
}

.mac-textarea:focus {
  outline: none;
  border-color: #007AFF;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.mac-slider {
  width: 100%;
  height: 4px;
  background: #E5E7EB;
  border-radius: 2px;
  outline: none;
  -webkit-appearance: none;
}

.mac-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007AFF;
  cursor: pointer;
}

.slider-value {
  font-size: 14px;
  color: #6B7280;
  text-align: center;
  margin-top: 4px;
}

.switch-wrapper {
  position: relative;
  display: inline-block;
}

.toggle-checkbox {
  height: 0;
  width: 0;
  visibility: hidden;
  position: absolute;
}

.toggle-label {
  cursor: pointer;
  width: 48px;
  height: 24px;
  background: #E5E7EB;
  display: block;
  border-radius: 24px;
  position: relative;
}

.toggle-label:after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: var(--background-secondary);
  border-radius: 20px;
  transition: 0.3s;
}

.toggle-checkbox:checked+.toggle-label {
  background: #007AFF;
}

.toggle-checkbox:checked+.toggle-label:after {
  left: calc(100% - 2px);
  transform: translateX(-100%);
}

.toggle-checkbox:disabled+.toggle-label {
  opacity: 0.5;
  cursor: not-allowed;
}

.trigger-words-section {
  margin-top: 8px;
  margin-bottom: 16px;
}

.section-divider {
  border-top: 1px solid #E5E7EB;
  padding-top: 16px;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
  }

  .form-group {
    width: 100%;
  }
}

/* 添加模型类型主题样式 */
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

/* 添加CSS样式 */
.mac-input, .mac-textarea {
  /* 现有样式... */
  /* 添加溢出处理样式 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mac-input:hover, .mac-textarea:hover {
  background-color: #F9FAFB;
  z-index: 5;
  position: relative;
}
</style>