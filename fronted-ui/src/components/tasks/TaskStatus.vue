<template>
  <div class="task-status" :class="{ 'compact-mode': compact }">
    <!-- 任务阶段进度条 -->
    <div class="task-phases" ref="phasesContainer" @mousedown="startDrag" @mousemove="onDrag" @mouseup="stopDrag"
      @mouseleave="handlePhaseMouseLeave" @mouseenter="handleStatusMouseEnter">
      <div v-for="(state, index) in taskStates" :key="state.status" ref="phaseItems" class="phase-item" :class="{
        'active': isStateActive(state.status),
        'completed': isStateCompleted(state.status),
        'error': isStateError(state.status)
      }">
        <div class="phase-icon">
          <component :is="getPhaseIcon(state.status)" class="icon" />
        </div>
        <div class="phase-info" v-if="!compact">
          <div class="phase-name">{{ state.label }}</div>
          <div class="phase-time" v-if="getStateTime(state.status)">
            {{ getStateTime(state.status) }}
          </div>
        </div>
        <!-- 紧凑模式下的节点名称 -->
        <div v-if="compact" class="phase-name-compact">
          {{ state.label }}
        </div>
        <div v-if="index < taskStates.length - 1" class="phase-connector" />
      </div>
    </div>

    <!-- 当前任务状态 -->
    <div v-if="isTaskActive && !compact" class="current-progress">
      <div class="progress-header">
        <div class="progress-title">
          <ClockIcon class="progress-icon" />
          <span>当前进度</span>
        </div>
        <div class="progress-time">{{ getRunningTime() }}</div>
      </div>
      <div class="progress-bar">
        <div class="progress-value" :style="{ width: `${task.progress}%` }" />
      </div>
      <div class="progress-text">{{ task.progress }}%</div>
    </div>

    <!-- 错误信息面板 - 暂时注释掉 -->
    <!--
    <div v-if="task?.status === 'ERROR'" class="error-section">
      <div class="error-header">
        <ExclamationTriangleIcon class="error-icon" />
        <span>错误信息</span>
      </div>
      <div class="error-content">
        <div v-if="parsedError" class="parsed-error">
          <div class="error-type">{{ parsedError.type }}</div>
          <div class="error-message">{{ parsedError.message }}</div>
          
          <div class="traceback-section">
            <button class="traceback-toggle" @click="toggleTraceback">
              {{ showTraceback ? '收起' : '展开' }}异常栈
              <ChevronDownIcon v-if="!showTraceback" class="toggle-icon" />
              <ChevronUpIcon v-else class="toggle-icon" />
            </button>
            <pre v-if="showTraceback" class="traceback">{{ parsedError.traceback }}</pre>
          </div>
        </div>
        <div v-else class="error-message">{{ task.error_message }}</div>
      </div>
    </div>
    -->

    <!-- 任务状态日志 - 仅在非compact模式下显示为内部元素 -->
    <template v-if="!compact">
      <div v-for="(status, statusKey) in sortedStatusHistory" :key="statusKey" class="status-record">
        <div class="status-header">
          <div class="status-badge" :class="getStatusClass(statusKey)">
            {{ getStatusText(statusKey) }}
          </div>
          <div class="status-time">
            <span>{{ formatDate(status?.start_time) }}</span>
            <span v-if="status?.end_time">- {{ formatDate(status?.end_time) }}</span>
            <span v-if="status?.end_time" class="status-duration">
              ({{ calculateDuration(status?.start_time, status?.end_time) }})
            </span>
          </div>
        </div>
        <div class="status-logs">
          <div v-for="log in getVisibleLogs(sortedLogs(status?.logs), statusKey)" 
               :key="log.time" 
               class="log-item" 
               :class="{ 'error-log': statusKey === 'ERROR' }">
            <div class="log-time">{{ formatTime(log?.time) }}</div>
            <div class="log-message">{{ log?.message }}</div>
          </div>
          
          <!-- 折叠/展开按钮 -->
          <div v-if="(status?.logs?.length || 0) > 15" class="logs-toggle">
            <button @click="toggleLogExpansion(statusKey)" class="toggle-button">
              {{ isLogExpanded(statusKey) ? '收起' : `显示更多 (${(status?.logs?.length || 0) - 15})` }}
              <ChevronDownIcon v-if="!isLogExpanded(statusKey)" class="toggle-icon" />
              <ChevronUpIcon v-else class="toggle-icon" />
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>

  <!-- 使用Teleport将日志面板传送到body层级，确保不被其他元素遮挡 -->
  <Teleport to="body">
    <div v-if="compact && isLogsVisible" 
         class="status-logs-popup" 
         :style="popupStyle" 
         ref="logsPopup"
         @mouseenter="handleLogsMouseEnter"
         @mouseleave="handleLogsMouseLeave">
      <h4>任务状态日志</h4>
      <div class="logs-content">
        <div v-for="(status, statusKey) in sortedStatusHistory" :key="statusKey" class="log-entry">
          <div class="log-status" :class="getStatusClass(statusKey)">
            {{ getStatusText(statusKey) }}
          </div>
          <div class="log-time">
            <span>{{ formatDate(status?.start_time) }}</span>
            <span v-if="status?.end_time">- {{ formatDate(status?.end_time) }}</span>
            <span v-if="status?.end_time" class="status-duration">
              ({{ calculateDuration(status?.start_time, status?.end_time) }})
            </span>
          </div>
          <!-- 显示最新的5条日志 -->
          <div class="logs-preview">
            <div v-for="log in getNewestLogs(status?.logs)" 
                :key="log.time" 
                class="log-item"
                :class="{ 'error-log': statusKey === 'ERROR' }">
              <div class="log-time">{{ formatTime(log?.time) }}</div>
              <div class="log-message">{{ log?.message }}</div>
            </div>
            <div v-if="!status?.logs || status?.logs.length === 0" class="no-logs">
              该状态无日志记录
            </div>
          </div>
        </div>
        <div v-if="!Object.keys(sortedStatusHistory).length" class="no-logs">
          暂无状态日志
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
/* eslint-disable */
import { computed, ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import {
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  FlagIcon,
  DocumentIcon,
  TagIcon,
  CommandLineIcon,
  ArrowUpCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/vue/24/outline'
import { formatDateTime, formatDuration, formatDate, formatTime } from '@/utils/datetime'
import { 
  getStatusText, 
  getStatusClass, 
  statusTextMap 
} from '@/utils/taskStatus'

const props = defineProps({
  task: {
    type: Object,
    required: true,
    default: () => ({})
  },
  compact: {
    type: Boolean,
    default: false
  }
})

// 控制弹窗位置的样式
const popupStyle = ref({
  top: '0px',
  left: '50%'
});

// 日志弹窗引用
const logsPopup = ref(null);
const phasesContainer = ref(null);

// 计算弹窗位置
const updatePopupPosition = () => {
  if (phasesContainer.value) {
    const rect = phasesContainer.value.getBoundingClientRect();
    // 获取进度条容器的宽度
    const containerWidth = rect.width;
    
    // 计算中心点位置
    const centerX = rect.left + (rect.width / 2);
    
    // 获取视窗宽度
    const viewportWidth = window.innerWidth;
    const margin = 20; // 边缘安全距离
    
    // 确保弹窗不会超出视窗左右边界
    let leftPos = centerX - (containerWidth / 2); // 修正left值计算，使弹窗居中
    if (leftPos < margin) {
      // 太靠近左边界，调整位置
      leftPos = margin;
    } else if (leftPos + containerWidth > viewportWidth - margin) {
      // 太靠近右边界，调整位置
      leftPos = viewportWidth - margin - containerWidth;
    }
    
    // 计算弹窗位置，并设置与进度条容器相同的宽度
    popupStyle.value = {
      top: `${rect.bottom + 10}px`,
      left: `${leftPos}px`,
      width: `${containerWidth}px`,
    };
  }
};

// 获取状态的最新日志（最多5条）
const getNewestLogs = (logs) => {
  if (!logs || !Array.isArray(logs)) return [];
  // 按时间排序并只返回最新的5条
  return sortedLogs(logs).slice(0, 5);
};

// 添加内部状态控制
const isLogsVisible = ref(false)
const hoverTimer = ref(null)

// 处理状态栏鼠标进入
const handleStatusMouseEnter = () => {
  clearTimeout(hoverTimer.value)
  hoverTimer.value = null
  isLogsVisible.value = true
}

// 处理状态栏鼠标离开
const handleStatusMouseLeave = () => {
  // 设置延迟，让用户有时间移动到日志面板上
  hoverTimer.value = setTimeout(() => {
    isLogsVisible.value = false
  }, 300) // 300毫秒延迟
}

// 处理日志面板鼠标进入
const handleLogsMouseEnter = () => {
  clearTimeout(hoverTimer.value)
  hoverTimer.value = null
  isLogsVisible.value = true
}

// 处理日志面板鼠标离开
const handleLogsMouseLeave = () => {
  // 设置延迟，避免鼠标在面板和状态栏之间移动时闪烁
  hoverTimer.value = setTimeout(() => {
    isLogsVisible.value = false
  }, 200)
}

// 监听显示状态变化，更新弹窗位置
watch(isLogsVisible, (show) => {
  if (show) {
    nextTick(() => {
      updatePopupPosition()
    })
  }
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
  if (hoverTimer.value) {
    clearTimeout(hoverTimer.value)
  }
  window.removeEventListener('resize', updatePopupPosition)
})

// 定义任务状态流程
const taskStates = [
  { status: 'NEW', label: statusTextMap.NEW },
  { status: 'SUBMITTED', label: statusTextMap.SUBMITTED },
  { status: 'MARKING', label: statusTextMap.MARKING },
  { status: 'MARKED', label: statusTextMap.MARKED },
  { status: 'TRAINING', label: statusTextMap.TRAINING },
  { status: 'COMPLETED', label: statusTextMap.COMPLETED },
  // 添加 ERROR 状态
  { status: 'ERROR', label: statusTextMap.ERROR }
]

// 状态判断方法
const isStateActive = (status) => {
  // 根据status_history中的最后一个状态判断
  if (!props.task?.status_history) return false
  
  // 获取所有状态键
  const statusKeys = Object.keys(props.task.status_history)
  if (statusKeys.length === 0) return false
  
  // 从状态流程中找出当前状态的索引
  const taskStateKeys = taskStates.map(s => s.status)
  
  // 过滤出存在于taskStates中的状态
  const validStatusKeys = statusKeys.filter(key => taskStateKeys.includes(key))
  
  // 获取最后一个有效状态
  const lastValidStatus = validStatusKeys.reduce((last, current) => {
    const lastIndex = taskStateKeys.indexOf(last)
    const currentIndex = taskStateKeys.indexOf(current)
    return currentIndex > lastIndex ? current : last
  }, validStatusKeys[0])
  return lastValidStatus === status
}

const isStateCompleted = (status) => {
  if (!props.task?.status) return false
  const stateIndex = taskStates.findIndex(s => s.status === status)
  const currentIndex = taskStates.findIndex(s => s.status === props.task.status)
  return currentIndex > stateIndex && props.task.status !== 'ERROR'
}

const isStateError = (status) => {
  if (!props.task?.status) return false
  return props.task.status === 'ERROR' && status === props.task.status
}

// 获取状态时间和消息
const getStateTime = (status) => {
  // 如果status_history不存在，直接返回null
  if (!props.task?.status_history) return null;

  // status_history是对象类型
  const stateHistory = props.task.status_history[status]
  return stateHistory ? formatDateTime(stateHistory.start_time) : null
}


// 计算任务是否处于活动状态
const isTaskActive = computed(() => {
  if (!props.task?.status) return false
  return ['MARKING', 'TRAINING'].includes(props.task.status)
})

// 计算运行时长
const runningTime = ref('')
let timer = null

const updateRunningTime = () => {
  if (props.task?.started_at && isTaskActive.value) {
    const start = new Date(props.task.started_at)
    const duration = Date.now() - start.getTime()
    runningTime.value = formatDuration(duration)
  }
}

const getRunningTime = () => runningTime.value

const phaseItems = ref([])
const isDragging = ref(false)
const startX = ref(0)
const scrollLeft = ref(0)

// 开始拖动
const startDrag = (e) => {
  isDragging.value = true
  const container = phasesContainer.value
  startX.value = e.pageX - container.offsetLeft
  scrollLeft.value = container.scrollLeft
}

// 拖动中
const onDrag = (e) => {
  if (!isDragging.value) return

  const container = phasesContainer.value
  const x = e.pageX - container.offsetLeft
  const walk = (x - startX.value) // 增加滚动速度
  container.scrollLeft = scrollLeft.value - walk
}

// 停止拖动
const stopDrag = () => {
  if (!isDragging.value) return

  isDragging.value = false
}

// 滚动到当前活动状态
const scrollToActivePhase = async () => {
  await nextTick()
  if (!phasesContainer.value) return

  const activeIndex = taskStates.findIndex(s => isStateActive(s.status))
  if (activeIndex === -1) return

  const activeElement = phaseItems.value[activeIndex]
  if (!activeElement) return

  const container = phasesContainer.value
  const scrollLeft = activeElement.offsetLeft - (container.clientWidth / 2) + (activeElement.clientWidth / 2)

  container.scrollTo({
    left: Math.max(0, scrollLeft),
    behavior: 'smooth'
  })
}

// 获取阶段图标
const getPhaseIcon = (status) => {
  if (isStateCompleted(status)) return CheckCircleIcon
  if (isStateActive(status)) return ClockIcon
  if (isStateError(status)) return XCircleIcon

  // 为每个状态设置特定图标
  const iconMap = {
    'NEW': DocumentIcon,
    'SUBMITTED': ArrowUpCircleIcon,
    'MARKING': TagIcon,
    'MARKED': CheckCircleIcon,
    'TRAINING': CommandLineIcon,
    'COMPLETED': FlagIcon,
    'ERROR':XCircleIcon
  }

  return iconMap[status] || CheckCircleIcon
}

// const showTraceback = ref(false)

// const toggleTraceback = () => {
//   showTraceback.value = !showTraceback.value
// }

// 计算状态持续时间
const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return ''
  
  const start = new Date(startTime).getTime()
  const end = new Date(endTime).getTime()
  const duration = end - start
  
  return formatDuration(duration)
}

// 对状态历史按时间从新到旧排序
const sortedStatusHistory = computed(() => {
  if (!props.task?.status_history) return {}
  
  // 获取状态历史对象的条目
  const entries = Object.entries(props.task.status_history)
  
  // 按开始时间从新到旧排序
  entries.sort((a, b) => {
    const timeA = new Date(a[1].start_time || 0).getTime()
    const timeB = new Date(b[1].start_time || 0).getTime()
    return timeB - timeA // 从新到旧排序
  })
  
  // 转换回对象
  return Object.fromEntries(entries)
})

// 对日志按时间从新到旧排序
const sortedLogs = (logs) => {
  if (!logs || !Array.isArray(logs)) return []
  
  // 创建副本以避免修改原始数据
  return [...logs].sort((a, b) => {
    const timeA = new Date(a.time || 0).getTime()
    const timeB = new Date(b.time || 0).getTime()
    return timeB - timeA // 从新到旧排序
  })
}

// 日志展开状态管理
const expandedLogs = ref({})

// 检查特定状态的日志是否展开
const isLogExpanded = (statusKey) => {
  return !!expandedLogs.value[statusKey]
}

// 切换日志展开状态
const toggleLogExpansion = (statusKey) => {
  expandedLogs.value[statusKey] = !expandedLogs.value[statusKey]
}

// 获取可见的日志
const getVisibleLogs = (logs, statusKey) => {
  if (!logs || logs.length <= 15 || isLogExpanded(statusKey)) {
    return logs
  }
  
  // 如果未展开且日志数量超过15，则只显示前15条
  return logs.slice(0, 15)
}

// 处理阶段区域鼠标离开（同时处理拖动结束和鼠标离开）
const handlePhaseMouseLeave = (e) => {
  // 先处理拖动结束
  stopDrag();
  // 再处理鼠标离开
  handleStatusMouseLeave();
};

// 窗口大小变化时更新位置
onMounted(() => {
  if (props.compact) {
    window.addEventListener('resize', updatePopupPosition);
    nextTick(updatePopupPosition);
  }
  if (isTaskActive.value) {
    updateRunningTime();
    timer = setInterval(updateRunningTime, 1000);
  }
  scrollToActivePhase();
});

// 监听任务状态变化
watch(() => props.task?.status, () => {
  scrollToActivePhase();
});
</script>

<style scoped>
.task-status {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  max-height: 100%;
}

/* 紧凑模式样式 */
.task-status.compact-mode .task-phases {
  background: transparent;
  border: none;
}

.task-status.compact-mode .phase-item {
  min-width: auto;
  margin: 0 8px; /* 增加节点间距 */
}

.task-status.compact-mode .phase-icon {
  width: 32px;  /* 增大图标尺寸 */
  height: 32px; /* 增大图标尺寸 */
}

.task-status.compact-mode .phase-icon svg {
  width: 18px;  /* 增大图标尺寸 */
  height: 18px; /* 增大图标尺寸 */
}

.task-status.compact-mode .phase-connector {
  height: 2px;
  top: 16px;  /* 调整连接线位置，与更大的图标居中对齐 */
}

/* 紧凑模式下的节点名称样式 */
.task-status.compact-mode .phase-name-compact {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  text-align: center;
  max-width: 60px; /* 增加宽度 */
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* 任务阶段样式 */
.task-phases {
  display: flex;
  align-items: flex-start;
  background: var(--background-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color-light);
  -webkit-overflow-scrolling: touch;
  scroll-behavior: auto;
  /* 隐藏滚动条但保持功能 */
  scrollbar-width: none;
  /* Firefox */
  -ms-overflow-style: none;
  /* IE and Edge */
  cursor: grab;
  user-select: none;
  /* 防止文本选择 */
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  cursor: grabbing !important;
}


/* 隐藏 Webkit 滚动条 */
.task-phases::-webkit-scrollbar {
  display: none;
}

.phase-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 0 0 auto;
  min-width: 120px;
  gap: 2px;
  padding: 0 var(--spacing-2);
}

.phase-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--background-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--border-color);
  transition: all var(--transition-speed);
  position: relative;
  z-index: 1;
}

.phase-icon svg {
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
}

.phase-item.completed .phase-icon {
  background: var(--success-color);
  border-color: var(--success-color);
}

.phase-item.completed .phase-icon svg {
  color: var(--text-primary-inverse);
}

.phase-item.active .phase-icon {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.phase-item.active .phase-icon svg {
  color: var(--text-primary-inverse);
}

.phase-item.error .phase-icon {
  background: var(--danger-color);
  border-color: var(--danger-color);
}

.phase-item.error .phase-icon svg {
  color: var(--text-primary-inverse);
}

.phase-info {
  text-align: center;
  min-width: 80px;
}

.phase-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.phase-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.phase-connector {
  position: absolute;
  top: 18px;
  right: -50%;
  width: 100%;
  height: 2px;
  background: var(--border-color-light);
}

.phase-item.completed .phase-connector {
  background: var(--success-color);
}

/* 添加悬停效果 */
.phase-item:hover .phase-icon {
  transform: scale(1.1);
  box-shadow: var(--shadow-sm);
}

/* 添加活动状态的动画 */
.phase-item.active .phase-icon {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--primary-color) 40%, transparent);
  }

  70% {
    box-shadow: 0 0 0 6px color-mix(in srgb, var(--primary-color) 0%, transparent);
  }

  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--primary-color) 0%, transparent);
  }
}

/* 当前进度样式 */
.current-progress {
  padding: var(--spacing-4);
  background: var(--background-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color-light);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.progress-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-weight: 500;
}

.progress-icon {
  width: 18px;
  height: 18px;
  color: var(--primary-color);
}

.progress-time {
  font-size: 14px;
  color: var(--text-secondary);
}

.progress-bar {
  height: 8px;
  background: var(--background-tertiary);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--spacing-2);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
}

.progress-value {
  height: 100%;
  background: linear-gradient(to right, #3b82f6, #60a5fa);
  border-radius: 4px;
  transition: width var(--transition-speed);
  box-shadow: 0 0 5px rgba(59, 130, 246, 0.5);
  position: relative;
  animation: pulse-progress 2s infinite;
}

@keyframes pulse-progress {
  0% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4);
  }
  70% {
    box-shadow: 0 0 0 5px rgba(59, 130, 246, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
}

.progress-text {
  font-size: 13px;
  color: var(--text-secondary);
  text-align: right;
}

/* 错误信息面板样式 - 保留但暂时不使用 */
/*
.error-section {
  flex-shrink: 0;
  max-height: 300px;
  display: flex;
  flex-direction: column;
}

.error-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
  padding: 0 var(--spacing-2);
}

.error-icon {
  width: 18px;
  height: 18px;
  color: var(--danger-color);
}

.error-content {
  flex: 1;
  overflow: auto;
  background: color-mix(in srgb, var(--danger-color) 5%, white);
  border: 1px solid color-mix(in srgb, var(--danger-color) 20%, white);
  padding: var(--spacing-4);
  border-radius: var(--radius-md);
}

.parsed-error {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.error-type {
  font-weight: 600;
  font-size: 15px;
  color: var(--danger-color);
}

.error-message {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: break-word;
}

.traceback-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  margin-top: var(--spacing-2);
}

.traceback-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  background: transparent;
  border: none;
  color: var(--primary-color);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  align-self: flex-start;
}

.traceback-toggle:hover {
  background: color-mix(in srgb, var(--primary-color) 10%, transparent);
}

.toggle-icon {
  width: 14px;
  height: 14px;
}

.traceback {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-primary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background: color-mix(in srgb, var(--danger-color) 5%, transparent);
  padding: var(--spacing-3);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--danger-color);
}
*/

.status-record {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-time {
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  gap: var(--spacing-1);
  flex-wrap: wrap;
}

.status-duration {
  color: var(--text-tertiary);
  font-style: italic;
}

.status-logs {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-left: 16px;
  padding-left: 16px;
  border-left: 2px solid var(--border-color-light);
}

.log-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
  width: 100%;
}

.log-time {
  color: var(--text-tertiary);
  white-space: nowrap;
  flex-shrink: 0;
}

.log-message {
  color: var(--text-secondary);
  word-break: break-word;
  overflow-wrap: break-word;
  flex: 1;
  white-space: normal;
  line-height: 1.4;
}

/* 添加错误日志样式 */
.error-log .log-message {
  color: var(--danger-color);
  font-weight: 500;
}

.error-log .log-time {
  color: color-mix(in srgb, var(--danger-color) 70%, var(--text-tertiary));
}

.logs-toggle {
  margin-top: var(--spacing-2);
  display: flex;
  justify-content: center;
}

.toggle-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: 12px;
  color: var(--primary-color);
  background: transparent;
  border: none;
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color var(--transition-speed);
}

.toggle-button:hover {
  background-color: color-mix(in srgb, var(--primary-color) 10%, transparent);
}

.toggle-icon {
  width: 14px;
  height: 14px;
}

/* 日志弹窗样式 */
.status-logs-popup {
  position: fixed;
  background: var(--background-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  padding: 12px;
  /* 宽度由JavaScript动态设置，不再使用固定值 */
  max-height: 400px;
  overflow-y: auto;
  z-index: 9999;
  transition: all 0.2s ease-in-out;
  backdrop-filter: blur(5px);
  background-color: rgba(255, 255, 255, 0.95);
  opacity: 0;
  transform: translateY(10px);
  animation: fadeInUp 0.3s forwards;
  box-sizing: border-box;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.status-logs-popup::-webkit-scrollbar {
  width: 6px;
}

.status-logs-popup::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.status-logs-popup::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.status-logs-popup::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.status-logs-popup h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 15px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 6px;
  text-align: center;
}

.logs-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.log-entry {
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 6px;
  background-color: rgba(0, 0, 0, 0.03);
  border-left: 3px solid var(--border-color);
  transition: all 0.2s;
  width: 100%;
  box-sizing: border-box;
}

.log-entry:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.log-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 5px;
}

.log-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 5px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.logs-preview {
  margin-top: 8px;
  border-top: 1px dashed rgba(0, 0, 0, 0.1);
  padding-top: 8px;
  width: 100%;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
  width: 100%;
  box-sizing: border-box;
}

.log-message {
  flex: 1;
  color: var(--text-primary);
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
}

.error-log .log-message {
  color: var(--danger-color);
}

.no-logs {
  font-style: italic;
  color: var(--text-secondary);
  text-align: center;
  padding: 8px 0;
}

.status-duration {
  font-style: italic;
  color: var(--text-tertiary);
  margin-left: 4px;
}
</style>