<template>
  <div 
    class="asset-card mac-card"
    :class="{'is-local': asset.is_local, 'is-disabled': !asset.enabled }"
  >
    <!-- 卡片头部 -->
    <div class="asset-card-header">
      <div class="asset-title">
        <ServerIcon v-if="!asset.is_local" class="asset-icon" />
        <ComputerDesktopIcon v-else class="asset-icon local" />
        <span class="asset-name text-ellipsis">{{ asset.name }}</span>
        <span v-if="asset.is_local" class="local-badge">本地</span>
      </div>
      <div class="asset-status-badge" :class="getStatusClass(asset)">
        <template v-if="!asset.enabled">已禁用</template>
        <template v-else>{{ getStatusText(asset.status) }}</template>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="asset-card-content">
      <!-- 基础信息区 -->
      <div class="info-section">
        <h4 class="section-label">基础信息</h4>
        <div class="info-grid">
          <div class="info-item" v-if="!asset.is_local">
            <ComputerDesktopIcon class="info-icon" />
            <span class="info-label">IP地址:</span>
            <span class="info-text text-ellipsis">{{ asset.ip }}:{{ asset.ssh_port }}</span>
          </div>
          <div class="info-item" v-if="!asset.is_local">
            <UserIcon class="info-icon" />
            <span class="info-label">用户名:</span>
            <span class="info-text text-ellipsis">{{ asset.ssh_username }}</span>
          </div>
          <div class="info-item" v-if="asset.is_local">
            <ComputerDesktopIcon class="info-icon" />
            <span class="info-label">类型:</span>
            <span class="info-text text-ellipsis">本地资产</span>
          </div>
          <div class="info-item">
            <ClockIcon class="info-icon" />
            <span class="info-label">更新时间:</span>
            <span class="info-text text-ellipsis">{{ formatDate(asset.updated_at) }}</span>
          </div>
        </div>
      </div>

      <!-- 能力信息区 -->
      <div class="capability-section">
        <h4 class="section-label">服务能力</h4>
        <div class="capability-tags">
          <div class="capability-tag" 
                v-if="asset.lora_training?.enabled"
                :class="{ 'is-verified': asset.lora_training?.verified }">
            <BeakerIcon class="tag-icon" />
            <span>Lora训练</span>
            <span class="verify-status">{{ asset.lora_training?.verified ? '(已验证)' : '(未验证)' }}</span>
          </div>
          <div class="capability-tag" 
                v-if="asset.ai_engine?.enabled"
                :class="{ 'is-verified': asset.ai_engine?.verified }">
            <CpuChipIcon class="tag-icon" />
            <span>AI引擎</span>
            <span class="verify-status">{{ asset.ai_engine?.verified ? '(已验证)' : '(未验证)' }}</span>
          </div>
          <div class="no-capability" v-if="!asset.lora_training?.enabled && !asset.ai_engine?.enabled">
            暂无配置服务能力
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片操作栏 -->
    <div class="asset-card-actions">
      <button 
        class="mac-btn small terminal-btn" 
        @click.stop="$emit('open-terminal', asset)"
        :disabled="asset.status !== 'CONNECTED' || asset.is_local || !asset.enabled"
        :title="getTerminalBtnTitle(asset)"
      >
        <TerminalIcon class="btn-icon" />
        <span>终端</span>
      </button>
      <button 
        class="mac-btn small verify-btn" 
        :disabled="asset.isVerifying || !asset.enabled"
        @click.stop="$emit('verify', asset)"
      >
        <template v-if="!asset.isVerifying">
          <CheckCircleIcon class="btn-icon" />
          <span>验证</span>
        </template>
        <template v-else>
          <span class="loading-spinner"></span>
          <span>验证</span>
        </template>
      </button>
      <button 
        class="mac-btn small toggle-btn" 
        :class="{ 'toggle-on': asset.enabled, 'toggle-off': !asset.enabled }"
        @click.stop="$emit('toggle', asset)"
      >
        <PowerIcon class="btn-icon" />
        <span>{{ asset.enabled ? '禁用' : '启用' }}</span>
      </button>
      <button class="mac-btn small edit-btn" @click.stop="$emit('edit', asset)">
        <PencilIcon class="btn-icon" />
        <span>编辑</span>
      </button>
      <button class="mac-btn small delete-btn" @click.stop="$emit('delete', asset)">
        <TrashIcon class="btn-icon" />
        <span>删除</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { format } from 'date-fns'
import {
  ServerIcon,
  ComputerDesktopIcon,
  UserIcon,
  BeakerIcon,
  CpuChipIcon,
  PencilIcon,
  TrashIcon,
  ClockIcon,
  CheckCircleIcon,
  CommandLineIcon as TerminalIcon,
  PowerIcon
} from '@heroicons/vue/24/outline'

defineProps({
  asset: {
    type: Object,
    required: true
  }
})

defineEmits(['select', 'edit', 'delete', 'verify', 'open-terminal', 'toggle'])

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'CONNECTED': '已连接',
    'PENDING': '待连接',
    'CONNECTION_ERROR': '连接错误'
  }
  return statusMap[status] || status
}

// 添加状态样式类名映射
const getStatusClass = (asset) => {
  if (!asset.enabled) return 'disabled'
  
  const statusClassMap = {
    'CONNECTED': 'connected',
    'PENDING': 'pending',
    'CONNECTION_ERROR': 'connection-error'
  }
  return statusClassMap[asset.status] || ''
}

// 获取终端按钮标题
const getTerminalBtnTitle = (asset) => {
  if (asset.is_local) return '本地资产不支持终端操作'
  if (asset.status !== 'CONNECTED') return '请先验证SSH连接'
  return '打开终端'
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return ''
  try {
    return format(new Date(date), 'yyyy-MM-dd HH:mm')
  } catch (error) {
    console.error('日期格式化错误:', error)
    return date
  }
}
</script>

<style scoped>
.asset-card {
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: var(--background-secondary);
  border-radius: 12px;
  border: 1px solid var(--border-color-light);
  transition: var(--theme-transition);
  gap: 16px;
  cursor: pointer;
  position: relative;
}

.asset-card.is-local {
  background: linear-gradient(to bottom, var(--background-secondary), color-mix(in srgb, var(--primary-color) 8%, var(--background-secondary)));
  border: 1px solid color-mix(in srgb, var(--primary-color) 30%, var(--border-color-light));
}

.asset-card.is-disabled {
  background: var(--background-tertiary);
  border: 1px dashed var(--border-color);
  opacity: 0.7;
}

.asset-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color-light);
}

.asset-title {
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 70%;
}

.asset-icon {
  width: 20px;
  height: 20px;
  color: var(--text-secondary);
  transition: var(--theme-transition);
}

.asset-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
  transition: var(--theme-transition);
}

.asset-status-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

/* 已连接状态 */
.asset-status-badge.connected {
  background: color-mix(in srgb, var(--success-color) 15%, var(--background-secondary));
  color: var(--success-color);
}

/* 待连接状态 */
.asset-status-badge.pending {
  background: color-mix(in srgb, var(--warning-color) 15%, var(--background-secondary));
  color: var(--warning-color);
}

/* 连接错误状态 */
.asset-status-badge.connection-error {
  background: color-mix(in srgb, var(--danger-color) 15%, var(--background-secondary));
  color: var(--danger-color);
}

/* 禁用状态 */
.asset-status-badge.disabled {
  background: var(--background-tertiary);
  color: var(--text-tertiary);
}

/* 本地资产状态 */
.asset-status-badge.local {
  background: color-mix(in srgb, var(--primary-color) 15%, var(--background-secondary));
  color: var(--primary-color);
}

.asset-card-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

/* 新增分区样式 */
.info-section, .capability-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--background-tertiary);
  padding: 12px;
  border-radius: 8px;
  transition: var(--theme-transition);
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--border-color-light);
  transition: var(--theme-transition);
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.info-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
  flex-shrink: 0;
  transition: var(--theme-transition);
}

.info-label {
  font-size: 13px;
  color: var(--text-tertiary);
  min-width: 60px;
  flex-shrink: 0;
  transition: var(--theme-transition);
}

.info-text {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
  transition: var(--theme-transition);
}

.capability-tags {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.capability-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--background-secondary);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  border: 1px solid var(--border-color-light);
  transition: var(--theme-transition);
}

.capability-tag.is-verified {
  background: color-mix(in srgb, var(--success-color) 15%, var(--background-secondary));
  color: var(--success-color);
  border-color: var(--success-color);
}

.verify-status {
  margin-left: auto;
  font-size: 12px;
  opacity: 0.8;
}

.no-capability {
  padding: 10px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  background: var(--background-tertiary);
  border-radius: 6px;
  border: 1px dashed var(--border-color-light);
  transition: var(--theme-transition);
}

.tag-icon {
  width: 16px;
  height: 16px;
}

.asset-card-actions {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color-light);
  margin-top: auto;
  flex-shrink: 0;
}

.mac-btn.small {
  padding: 6px;
  font-size: 12px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: var(--theme-transition);
  border: 1px solid var(--border-color-light);
}

.verify-btn {
  background: color-mix(in srgb, var(--info-color) 15%, var(--background-secondary));
  color: var(--info-color);
  border-color: var(--info-color);
}

.verify-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--info-color) 25%, var(--background-secondary));
  transform: translateY(-1px);
}

.verify-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.edit-btn {
  background: var(--background-tertiary);
  color: var(--text-secondary);
  border-color: var(--border-color);
}

.edit-btn:hover {
  background: color-mix(in srgb, var(--text-secondary) 10%, var(--background-tertiary));
  transform: translateY(-1px);
}

.delete-btn {
  background: color-mix(in srgb, var(--danger-color) 15%, var(--background-secondary));
  color: var(--danger-color);
  border-color: var(--danger-color);
}

.delete-btn:hover {
  background: color-mix(in srgb, var(--danger-color) 25%, var(--background-secondary));
  transform: translateY(-1px);
}

.terminal-btn {
  background: color-mix(in srgb, var(--info-color) 15%, var(--background-secondary));
  color: var(--info-color);
  border-color: var(--info-color);
}

.terminal-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--info-color) 25%, var(--background-secondary));
  transform: translateY(-1px);
}

.terminal-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: var(--background-tertiary);
  color: var(--text-tertiary);
  border-color: var(--border-color-light);
}

.btn-icon {
  width: 14px;
  height: 14px;
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 加载动画 */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--info-color);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@media (max-width: 768px) {
  .asset-card {
    padding: 12px;
  }
  
  .asset-card-actions {
    grid-template-columns: repeat(3, 1fr);
    row-gap: 8px;
  }
}

.local-badge {
  font-size: 11px;
  padding: 2px 6px;
  background-color: color-mix(in srgb, var(--primary-color) 15%, var(--background-secondary));
  color: var(--primary-color);
  border-radius: 4px;
  margin-left: 8px;
  font-weight: 500;
  transition: var(--theme-transition);
}

.asset-icon.local {
  color: var(--primary-color);
}

.toggle-btn.toggle-on {
  background: color-mix(in srgb, var(--danger-color) 15%, var(--background-secondary));
  color: var(--danger-color);
  border-color: var(--danger-color);
}

.toggle-btn.toggle-on:hover {
  background: color-mix(in srgb, var(--danger-color) 25%, var(--background-secondary));
  transform: translateY(-1px);
}

.toggle-btn.toggle-off {
  background: color-mix(in srgb, var(--success-color) 15%, var(--background-secondary));
  color: var(--success-color);
  border-color: var(--success-color);
}

.toggle-btn.toggle-off:hover {
  background: color-mix(in srgb, var(--success-color) 25%, var(--background-secondary));
  transform: translateY(-1px);
}
</style> 