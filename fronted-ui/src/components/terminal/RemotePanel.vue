<template>
  <BaseModal
    v-model="show"
    :title="asset?.name"
    width="80vw"
    @close="handleClose"
    :tabs="tabs"
    :defaultActiveTab="activeTabIndex"
    @tab-change="handleTabChange"
  >
    <template #body>
      <div class="tab-content">
        <!-- 终端标签页内容 -->
        <div v-show="activeTab === 'terminal'" class="terminal-container">
          <Terminal 
            v-if="asset?.id" 
            :assetId="asset.id"
            ref="terminalComponent"
          />
        </div>
        
        <!-- 文件管理标签页内容 -->
        <div v-show="activeTab === 'fileManager'" class="file-manager-container">
          <FileManager :asset="asset" v-if="asset" />
        </div>
      </div>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import BaseModal from '@/components/common/Modal.vue'
import FileManager from '@/components/terminal/FileManager.vue'
import Terminal from '@/components/terminal/Terminal.vue'
import { CommandLineIcon, FolderIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: Boolean,
  asset: Object
})

const emit = defineEmits(['update:modelValue'])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 定义标签页配置
const tabs = [
  { title: '终端', icon: CommandLineIcon },
  { title: '文件管理', icon: FolderIcon }
]

// 标签页状态
const activeTab = ref('terminal')
const activeTabIndex = ref(0)
const terminalComponent = ref(null)

// 处理标签页切换
const handleTabChange = (index) => {
  activeTabIndex.value = index
  activeTab.value = index === 0 ? 'terminal' : 'fileManager'
}

// 监听显示状态变化
watch(show, (newVal) => {
  if (!newVal) {
    // 当关闭窗口时，清理终端
    if (terminalComponent.value) {
      terminalComponent.value.cleanupTerminal()
    }
  }
})

const handleClose = () => {
  // 清理终端连接
  if (terminalComponent.value) {
    terminalComponent.value.cleanupTerminal()
  }
  show.value = false
}
</script>

<style scoped>
.terminal-container {
  width: 100%;
  height: 580px;
  overflow: hidden;
  position: relative;
}

.tab-content {
  background: #fff;
  border-radius: 0 0 6px 6px;
}

.file-manager-container {
  height: 580px;
  overflow: auto;
  padding: 0;
  border-radius: 0 0 6px 6px;
}
</style> 