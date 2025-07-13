<template>
  <div class="log-viewer">
    <!-- 日志内容 -->
    <div 
      ref="logContainer"
      class="log-content"
      :class="{ 'auto-scroll': autoScroll }"
    >
      <!-- 空状态 -->
      <div v-if="!content" class="empty-state">
        暂无日志信息
      </div>
      
      <!-- 日志行 -->
      <template v-else>
        <div 
          v-for="(line, index) in logLines" 
          :key="index"
          class="log-line"
          :class="getLineClass(line)"
        >
          <!-- 时间戳 -->
          <span v-if="line.timestamp" class="timestamp">
            {{ formatTime(line.timestamp) }}
          </span>
          
          <!-- 日志级别 -->
          <span 
            v-if="line.level" 
            class="log-level"
            :class="line.level.toLowerCase()"
          >
            {{ line.level }}
          </span>
          
          <!-- 阶段标记 -->
          <span 
            v-if="line.stage"
            class="stage-marker"
          >
            [{{ line.stage }}]
          </span>
          
          <!-- 日志内容 -->
          <span class="message" v-html="highlightKeywords(line.message)"></span>
        </div>
      </template>
    </div>

    <!-- 控制栏 -->
    <div class="control-bar">
      <div class="left-controls">
        <button 
          class="control-btn"
          :class="{ active: autoScroll }"
          @click="toggleAutoScroll"
          title="自动滚动"
        >
          <ArrowDownCircleIcon class="btn-icon" />
        </button>
        <button 
          class="control-btn"
          @click="clearHighlight"
          :disabled="!searchKeyword"
          title="清除搜索"
        >
          <XMarkIcon class="btn-icon" />
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="search-box">
        <MagnifyingGlassIcon class="search-icon" />
        <input 
          v-model="searchKeyword"
          type="text"
          class="search-input"
          placeholder="搜索日志..."
          @input="handleSearch"
        >
        <span v-if="matchCount" class="match-count">
          {{ currentMatch }}/{{ matchCount }}
        </span>
      </div>

      <div class="right-controls">
        <button 
          class="control-btn"
          @click="scrollToMatch('prev')"
          :disabled="!matchCount"
          title="上一个"
        >
          <ChevronUpIcon class="btn-icon" />
        </button>
        <button 
          class="control-btn"
          @click="scrollToMatch('next')"
          :disabled="!matchCount"
          title="下一个"
        >
          <ChevronDownIcon class="btn-icon" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { 
  ArrowDownCircleIcon,
  MagnifyingGlassIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  content: {
    type: String,
    default: ''
  }
})

// 状态
const logContainer = ref(null)
const autoScroll = ref(true)
const searchKeyword = ref('')
const currentMatch = ref(0)
const matchCount = ref(0)

// 解析日志行
const logLines = computed(() => {
  if (!props.content) return []
  
  return props.content.split('\n').map(line => {
    // 解析日志格式
    const match = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] \[(\w+)\] (.+)$/)
    if (match) {
      return {
        timestamp: match[1],
        level: match[2],
        stage: match[3],
        message: match[4]
      }
    }
    return { message: line }
  })
})

// 格式化时间
const formatTime = (timestamp) => {
  return timestamp.split(' ')[1] // 只显示时间部分
}

// 获取行样式
const getLineClass = (line) => {
  const classes = []
  
  // 日志级别样式
  if (line.level) {
    classes.push(`level-${line.level.toLowerCase()}`)
  }
  
  // 阶段样式
  if (line.stage) {
    classes.push(`stage-${line.stage.toLowerCase()}`)
  }
  
  return classes
}

// 高亮关键词
const highlightKeywords = (text) => {
  if (!searchKeyword.value) return text
  
  const regex = new RegExp(searchKeyword.value, 'gi')
  return text.replace(regex, match => `<mark class="highlight">${match}</mark>`)
}

// 自动滚动控制
const toggleAutoScroll = () => {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    scrollToBottom()
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

// 搜索功能
const handleSearch = () => {
  if (!searchKeyword.value) {
    matchCount.value = 0
    currentMatch.value = 0
    return
  }
  
  const matches = logContainer.value.querySelectorAll('.highlight')
  matchCount.value = matches.length
  currentMatch.value = matches.length ? 1 : 0
  
  if (matches.length) {
    matches[0].scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

const scrollToMatch = (direction) => {
  const matches = logContainer.value.querySelectorAll('.highlight')
  if (!matches.length) return
  
  if (direction === 'next') {
    currentMatch.value = currentMatch.value === matches.length ? 1 : currentMatch.value + 1
  } else {
    currentMatch.value = currentMatch.value === 1 ? matches.length : currentMatch.value - 1
  }
  
  matches[currentMatch.value - 1].scrollIntoView({ behavior: 'smooth', block: 'center' })
}

const clearHighlight = () => {
  searchKeyword.value = ''
  handleSearch()
}

// 监听内容变化
watch(() => props.content, () => {
  if (autoScroll.value) {
    scrollToBottom()
  }
})
</script>

<style scoped>
.log-viewer {
  display: flex;
  flex-direction: column;
  height: 300px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--background-secondary);
}

.log-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  font-family: ui-monospace, monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.log-line {
  display: flex;
  gap: 8px;
  padding: 2px 0;
}

.timestamp {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.log-level {
  padding: 0 4px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}

.log-level.info {
  background: #EEF2FF;
  color: #4338CA;
}

.log-level.warning {
  background: #FFF7ED;
  color: #C2410C;
}

.log-level.error {
  background: #FEF2F2;
  color: #B91C1C;
}

.stage-marker {
  color: var(--primary-color);
  font-weight: 500;
  flex-shrink: 0;
}

.message {
  flex: 1;
  min-width: 0;
}

.control-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-top: 1px solid var(--border-color);
}

.left-controls,
.right-controls {
  display: flex;
  gap: 4px;
}

.control-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-btn:hover:not(:disabled) {
  background: var(--background-tertiary);
  color: var(--text-primary);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-btn.active {
  color: var(--primary-color);
  background: rgba(var(--primary-color-rgb), 0.1);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.search-box {
  flex: 1;
  position: relative;
  max-width: 300px;
}

.search-icon {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

.search-input {
  width: 100%;
  height: 28px;
  padding: 0 32px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 13px;
  background: var(--background-primary);
}

.match-count {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  color: var(--text-secondary);
}

:deep(.highlight) {
  background: #FEF08A;
  color: #854D0E;
  border-radius: 2px;
}

/* 滚动条样式 */
.log-content::-webkit-scrollbar {
  width: 6px;
}

.log-content::-webkit-scrollbar-track {
  background: transparent;
}

.log-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.log-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-color-dark);
}

/* 任务阶段样式 */
.stage-preparing {
  color: #0369A1;
}

.stage-marking {
  color: #C2410C;
}

.stage-training {
  color: #4338CA;
}

.stage-completed {
  color: #047857;
}

.stage-error {
  color: #B91C1C;
}
</style> 