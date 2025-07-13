<template>
  <div class="assets-container">
    <!-- 顶部操作栏 -->
    <div class="action-bar mac-card">
      <div class="left-actions">
        <!-- 搜索框 -->
        <div class="search-box">
          <MagnifyingGlassIcon class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="搜索资产..." 
            class="mac-search-input"
          >
        </div>
        
        <!-- 过滤器组 -->
        <div class="filter-group">
          <div class="filter-item">
            <select v-model="statusFilter" class="mac-filter-select">
              <option value="">状态</option>
              <option value="CONNECTED">已连接</option>
              <option value="PENDING">待连接</option>
              <option value="CONNECTION_ERROR">连接错误</option>
            </select>
          </div>
          <div class="filter-item">
            <select v-model="capabilityFilter" class="mac-filter-select">
              <option value="">能力</option>
              <option value="lora">Lora训练</option>
              <option value="ai">AI引擎</option>
            </select>
          </div>
          <div class="filter-item">
            <select v-model="enabledFilter" class="mac-filter-select">
              <option value="">启用状态</option>
              <option value="enabled">已启用</option>
              <option value="disabled">已禁用</option>
            </select>
          </div>
        </div>
      </div>
      
      <!-- 新建按钮 -->
      <button class="mac-action-btn" @click="showCreateAsset">
        <PlusIcon class="btn-icon" />
        新建资产
      </button>
    </div>

    <!-- 资产列表 -->
    <div class="assets-grid">
      <AssetCard 
        v-for="asset in paginatedAssets" 
           :key="asset.id" 
        :asset="asset"
        @edit="showEditModal"
        @delete="confirmDelete"
        @verify="verifyCapabilities"
        @open-terminal="openTerminal"
        @toggle="toggleAssetEnabled"
      />
    </div>

    <!-- 分页器 -->
    <div class="pagination mac-card" v-if="totalPages > 1">
      <button 
        class="mac-btn" 
        :disabled="currentPage === 1"
        @click="currentPage--"
      >
        <ChevronLeftIcon class="btn-icon" />
      </button>
      <div class="page-numbers">
        <button 
          v-for="page in displayedPages" 
          :key="page"
          class="mac-btn page-number"
          :class="{ active: currentPage === page }"
          @click="currentPage = page"
        >
          {{ page }}
        </button>
      </div>
      <button 
        class="mac-btn" 
        :disabled="currentPage === totalPages"
        @click="currentPage++"
      >
        <ChevronRightIcon class="btn-icon" />
      </button>
    </div>

    <!-- 资产表单弹窗 -->
    <AssetForm 
      v-model="showAssetModal"
      :asset="assetForm"
      :is-editing="isEditing"
      @submit-success="handleFormSuccess"
    />

    <!-- 添加终端弹窗组件 -->
    <RemotePanel
      v-if="showTerminal"
      v-model="showTerminal"
      :asset="selectedTerminalAsset"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent } from 'vue'
import AssetCard from '@/components/assets/AssetCard.vue'
import message from '@/utils/message'
import { assetApi } from '@/api/asset'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/vue/24/outline'
import RemotePanel from '@/components/terminal/RemotePanel.vue'
import AssetForm from '@/components/assets/AssetForm.vue'

defineComponent({
  name: 'AssetsManager'
})

// 状态定义
const assets = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const capabilityFilter = ref('')
const enabledFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const selectedAsset = ref(null)
const showAssetModal = ref(false)
const isEditing = ref(false)
const showTerminal = ref(false)
const selectedTerminalAsset = ref(null)

// 简化的assetForm引用，只用于传递给表单组件
const assetForm = ref(null)

// 过滤资产列表
const filteredAssets = computed(() => {
  let result = assets.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(asset => 
      asset.name.toLowerCase().includes(query) ||
      asset.ip.includes(query)
    )
  }

  // 状态过滤
  if (statusFilter.value) {
    result = result.filter(asset => 
      asset.status === statusFilter.value
    )
  }

  // 能力过滤
  if (capabilityFilter.value) {
    result = result.filter(asset => {
      if (capabilityFilter.value === 'lora') {
        return asset.lora_training?.enabled
      }
      if (capabilityFilter.value === 'ai') {
        return asset.ai_engine?.enabled
      }
      return true
    })
  }
  
  // 启用状态过滤
  if (enabledFilter.value) {
    result = result.filter(asset => {
      if (enabledFilter.value === 'enabled') {
        return asset.enabled !== false
      }
      if (enabledFilter.value === 'disabled') {
        return asset.enabled === false
      }
      return true
    })
  }

  return result
})

// 分页数据
const totalPages = computed(() => 
  Math.ceil(filteredAssets.value.length / pageSize.value)
)

const paginatedAssets = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAssets.value.slice(start, end)
})

// 显示的页码范围
const displayedPages = computed(() => {
  const delta = 2
  const range = []
  const rangeWithDots = []
  let l

  for (let i = 1; i <= totalPages.value; i++) {
    if (
      i === 1 || 
      i === totalPages.value || 
      i >= currentPage.value - delta && 
      i <= currentPage.value + delta
    ) {
      range.push(i)
    }
  }

  range.forEach(i => {
    if (l) {
      if (i - l === 2) {
        rangeWithDots.push(l + 1)
      } else if (i - l !== 1) {
        rangeWithDots.push('...')
      }
    }
    rangeWithDots.push(i)
    l = i
  })

  return rangeWithDots
})

// 获取资产列表
const fetchAssets = async () => {
  try {
    const data = await assetApi.getAssets()
    assets.value = data.map(asset => ({
      ...asset,
      isVerifying: false, // 添加验证状态标记
      status: asset.status || 'PENDING', // 确保有默认状态
      enabled: asset.enabled !== false // 确保有默认启用状态
    }))
    
    // 对资产进行状态验证
    const verifyPromises = assets.value
      .filter(asset => asset.name !== "本地系统" && asset.enabled !== false) // 排除本地系统资产和已禁用资产
      .map(asset => {
        // 标记为正在验证中
        asset.status = 'PENDING';
        asset.autoVerifying = true // 标记为自动验证
        return verifyCapabilities(asset)
      })
    
    // 并行执行所有验证
    await Promise.all(verifyPromises)
    
  } catch (error) {
    console.error('获取资产列表失败:', error)
    message.error('获取资产列表失败')
  }
}

// 验证资产能力
const verifyCapabilities = async (asset) => {
  if (asset.isVerifying) return // 如果正在验证中，直接返回
  
  try {
    asset.isVerifying = true
    const results = await assetApi.verifyCapabilities(asset.id)
    
    // 更新SSH连接状态
    if (results.ssh_connection) {
      asset.status = 'CONNECTED'
    } else {
      asset.status = 'CONNECTION_ERROR'
    }
    
    // 更新资产的验证状态
    if (asset.lora_training?.enabled) {
      asset.lora_training.verified = results.lora_training
    }
    if (asset.ai_engine?.enabled) {
      asset.ai_engine.verified = results.ai_engine
    }
    
    // 只在手动验证时显示提示
    if (!asset.autoVerifying) {
      if (results.ssh_connection) {
        message.success('SSH连接和能力验证完成')
      } else {
        message.warning('SSH连接失败，请检查连接配置')
      }
    }
  } catch (error) {
    // 更新状态为连接错误
    asset.status = 'CONNECTION_ERROR'
    
    // 只在手动验证时显示错误提示
    if (!asset.autoVerifying) {
      message.error(error.message || '验证失败')
    } else {
      console.error('自动验证失败:', error)
    }
  } finally {
    asset.isVerifying = false
    delete asset.autoVerifying
  }
}

// 删除资产
const confirmDelete = async (asset) => {
  if (confirm('确定要删除该资产吗？')) {
    try {
      await assetApi.deleteAsset(asset.id)
      message.success('资产已删除')
      await fetchAssets()
    } catch (error) {
      message.error(error.message || '删除失败')
    }
  }
}

// 显示编辑模态框
const showEditModal = (asset) => {
  isEditing.value = true
  // 将资产数据赋值给assetForm以传递给表单组件
  assetForm.value = asset
  showAssetModal.value = true
}

// 显示新建资产弹窗
const showCreateAsset = () => {
  isEditing.value = false
  assetForm.value = null
  showAssetModal.value = true
}

// 打开终端
const openTerminal = (asset) => {
  selectedTerminalAsset.value = asset
  showTerminal.value = true
}

// 处理表单提交成功
const handleFormSuccess = async (result) => {
  console.log("handleFormSuccess",result)
  await fetchAssets()
}

// 切换资产启用状态
const toggleAssetEnabled = async (asset) => {
  try {
    const newEnabledState = !asset.enabled
    const result = await assetApi.toggleAssetStatus(asset.id, newEnabledState)
    
    // 更新本地资产状态
    const index = assets.value.findIndex(a => a.id === asset.id)
    if (index !== -1) {
      assets.value[index].enabled = newEnabledState
    }
    
    message.success(`资产已${newEnabledState ? '启用' : '禁用'}`)
  } catch (error) {
    message.error(error.message || `${asset.enabled ? '禁用' : '启用'}资产失败`)
  }
}

// 在组件挂载时获取资产列表
onMounted(() => {
  fetchAssets()
})
</script>

<style scoped>
.assets-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--background-secondary);
  transition: var(--theme-transition);
}

.left-actions {
  display: flex;
  gap: 20px;
  align-items: center;
}

.search-box {
  position: relative;
  min-width: 240px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
  transition: var(--theme-transition);
}

.mac-search-input {
  width: 100%;
  height: 32px;
  padding: 0 12px 0 36px;
  border-radius: 8px;
  border: 1px solid var(--border-color-light);
  background: var(--background-tertiary);
  color: var(--text-primary);
  font-size: 14px;
  transition: var(--theme-transition);
}

.mac-search-input:focus {
  background: var(--background-secondary);
  border-color: var(--primary-color);
  outline: none;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 20%, transparent);
}

.mac-search-input::placeholder {
  color: var(--text-tertiary);
}

.filter-group {
  display: flex;
  gap: 12px;
}

.filter-item {
  position: relative;
}

.mac-filter-select {
  height: 32px;
  padding: 0 28px 0 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color-light);
  background: var(--background-secondary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  appearance: none;
  transition: var(--theme-transition);
}

.mac-filter-select:hover {
  background: var(--background-tertiary);
}

.mac-filter-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 20%, transparent);
}

.mac-action-btn {
  height: 32px;
  padding: 0 16px;
  border-radius: 8px;
  border: none;
  background: var(--primary-color);
  color: var(--text-primary-inverse);
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: var(--theme-transition);
}

.mac-action-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.mac-action-btn:active {
  opacity: 0.8;
  transform: translateY(0);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .action-bar {
    flex-direction: column;
    gap: 12px;
  }
  
  .left-actions {
    width: 100%;
    flex-direction: column;
  }
  
  .search-box {
    width: 100%;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-item {
    flex: 1;
  }
  
  .mac-filter-select {
    width: 100%;
  }
  
  .mac-action-btn {
    width: 100%;
    justify-content: center;
  }
}

.assets-grid {
  flex: 1;
  overflow: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
  padding: 0 12px 12px;
}

/* 自定义滚动条样式 */
.assets-grid::-webkit-scrollbar {
  width: 8px;
}

.assets-grid::-webkit-scrollbar-track {
  background: transparent;
}

.assets-grid::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.assets-grid::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

/* 分页器样式 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
  background: var(--background-secondary);
  transition: var(--theme-transition);
}

.page-numbers {
  display: flex;
  gap: 8px;
}

.page-number {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: 1px solid var(--border-color-light);
  background: var(--background-secondary);
  color: var(--text-primary);
  font-size: 14px;
  transition: var(--theme-transition);
}

.page-number.active {
  background: var(--primary-color);
  color: var(--text-primary-inverse);
  border-color: var(--primary-color);
}

.page-number:hover:not(.active) {
  background: var(--background-tertiary);
}

/* 表单样式 */
.asset-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 4px;
}

/* 表单区块 */
.form-section {
  background: var(--background-tertiary);
  border-radius: 8px;
  padding: 20px;
  transition: var(--theme-transition);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  transition: var(--theme-transition);
}

/* 表单项 */
.form-item {
  margin-bottom: 16px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  transition: var(--theme-transition);
}

/* 输入框样式 */
.mac-input {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color-light);
  background: var(--background-secondary);
  color: var(--text-primary);
  font-size: 14px;
  transition: var(--theme-transition);
}

.mac-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 20%, transparent);
}

/* 错误状态 */
.mac-input.is-error {
  border-color: var(--danger-color);
  background: color-mix(in srgb, var(--danger-color) 5%, var(--background-secondary));
}

.mac-input.is-error:focus {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--danger-color) 20%, transparent);
}

/* 错误提示文字 */
.error-message {
  display: block;
  color: var(--danger-color);
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.5;
  transition: var(--theme-transition);
}

/* 表单行布局 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

/* 文本域样式 */
.mac-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color-light);
  background: var(--background-secondary);
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: var(--theme-transition);
}

.mac-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 20%, transparent);
}

.mac-textarea.is-error {
  border-color: var(--danger-color);
  background: color-mix(in srgb, var(--danger-color) 5%, var(--background-secondary));
}

/* 能力区块头部 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

/* 能力表单区域 */
.capability-form {
  background: var(--background-secondary);
  border-radius: 6px;
  padding: 16px;
  margin-top: 12px;
  transition: var(--theme-transition);
}

/* 响应式调整 */
@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .form-section {
    padding: 16px;
  }
}

/* 表单验证提示动画 */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.is-error {
  animation: shake 0.3s ease-in-out;
}

/* 开关按钮容器 */
.switch-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.switch-container label {
  margin-bottom: 0;
}

/* 占位符文本样式 */
.mac-input::placeholder,
.mac-textarea::placeholder {
  color: var(--text-tertiary);
}

/* 禁用状态样式 */
.mac-input:disabled,
.mac-textarea:disabled {
  background: var(--background-tertiary);
  cursor: not-allowed;
  opacity: 0.6;
}

.mac-input[type="password"] {
  font-family: monospace;
  letter-spacing: 0.2em;
}

select.mac-input {
  padding-right: 30px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236B7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px;
  appearance: none;
  cursor: pointer;
}

select.mac-input:focus {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23007AFF'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
}

.input-with-button {
  display: flex;
  gap: 8px;
}

.input-with-button .mac-input {
  flex: 1;
}

.verify-ssh-btn {
  padding: 0 12px;
  background: color-mix(in srgb, var(--primary-color) 10%, var(--background-secondary));
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
  border-radius: 6px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition: var(--theme-transition);
}

.verify-ssh-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--primary-color) 15%, var(--background-secondary));
}

.verify-ssh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style> 