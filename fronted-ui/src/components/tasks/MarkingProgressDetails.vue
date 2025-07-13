<template>
  <div class="marking-progress-details">
    <div class="details-header">
      <h3 class="details-title">任务 - {{ taskName }}</h3>
      <div class="header-info" v-if="markingProgress">
        <div class="progress-info">
          <span class="progress-label">标记进度:</span>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
          <span class="progress-text">{{ progressPercent }}%</span>
        </div>
        <div class="queue-info">
          <span>队列: 提交{{ markingProgress.submitted_count }} | 处理中{{ markingProgress.processing_count }} | 完成{{ markingProgress.completed_count }}</span>
          <span v-if="markingProgress.current_task_id">当前任务: {{ markingProgress.current_task_id.substring(0, 8) }}</span>
        </div>
      </div>
    </div>

    <div class="details-content">
      <!-- 左侧进度监控区域 -->
      <div class="progress-section">
        <MarkingProgressChart :progress-data="progressData" :is-loading="isLoadingProgress" :is-marking="isMarking" height="100%" />
      </div>

      <!-- 右侧系统监控区域 -->
      <div class="system-section">
        <h4 class="section-title">系统监控</h4>
        
        <!-- 系统状态卡片 -->
        <div class="system-stats-grid">
          <div class="stat-card" v-if="systemStats">
            <div class="stat-header">
              <span class="stat-icon">💾</span>
              <span class="stat-label">内存使用</span>
            </div>
            <div class="stat-content">
              <div class="stat-bar">
                <div class="stat-fill" :style="{ width: `${systemStats.ram_usage || 0}%` }"></div>
              </div>
              <div class="stat-text">
                {{ (systemStats.ram_used_gb || 0).toFixed(1) }}GB / {{ (systemStats.ram_total_gb || 0).toFixed(1) }}GB
              </div>
            </div>
          </div>

          <div class="stat-card" v-if="systemStats && systemStats.gpu_usage !== undefined">
            <div class="stat-header">
              <span class="stat-icon">🎮</span>
              <span class="stat-label">GPU使用</span>
            </div>
            <div class="stat-content">
              <div class="stat-bar">
                <div class="stat-fill gpu" :style="{ width: `${systemStats.gpu_usage || 0}%` }"></div>
              </div>
              <div class="stat-text">
                {{ (systemStats.gpu_memory_used || 0).toFixed(1) }}GB / {{ (systemStats.gpu_memory_total || 0).toFixed(1) }}GB
              </div>
            </div>
          </div>

          <div class="stat-card" v-if="systemStats && systemStats.cpu_usage !== undefined">
            <div class="stat-header">
              <span class="stat-icon">⚡</span>
              <span class="stat-label">CPU使用</span>
            </div>
            <div class="stat-content">
              <div class="stat-bar">
                <div class="stat-fill cpu" :style="{ width: `${systemStats.cpu_usage || 0}%` }"></div>
              </div>
              <div class="stat-text">{{ (systemStats.cpu_usage || 0).toFixed(1) }}%</div>
            </div>
          </div>

          <div class="stat-card" v-if="systemStats && systemStats.gpu_temperature !== undefined">
            <div class="stat-header">
              <span class="stat-icon">🌡️</span>
              <span class="stat-label">GPU温度</span>
            </div>
            <div class="stat-content">
              <div class="stat-text large">{{ systemStats.gpu_temperature || 0 }}°C</div>
            </div>
          </div>
        </div>

        <!-- 当前任务信息 -->
        <div class="current-task-info" v-if="markingProgress && markingProgress.current_task_id">
          <h5 class="info-title">当前处理任务</h5>
          <div class="task-details">
            <div class="task-item">
              <span class="task-label">任务ID:</span>
              <span class="task-value">{{ markingProgress.current_task_id }}</span>
            </div>
            <div class="task-item" v-if="markingProgress.total_images">
              <span class="task-label">图片总数:</span>
              <span class="task-value">{{ markingProgress.total_images }}</span>
            </div>
          </div>
        </div>

        <!-- 数据源指示器 -->
        <div class="data-source" v-if="dataSource">
          <span class="source-icon" :class="{ realtime: dataSource.isRealtime, database: dataSource.isDatabase, mock: dataSource.isMock }">
            {{ dataSource.isMock ? '🤖' : (dataSource.isRealtime ? '🟢' : '💾') }}
          </span>
          <span class="source-text">
            {{ dataSource.isMock ? '模拟数据' : (dataSource.isRealtime ? '实时数据' : '历史数据') }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useTheme } from '@/composables/useTheme'
import MarkingProgressChart from '../common/MarkingProgressChart.vue'
import { tasksApi } from '@/api/tasks'

export default {
  name: 'MarkingProgressDetails',
  components: {
    MarkingProgressChart
  },
  props: {
    taskId: {
      type: Number,
      required: true
    },
    taskName: {
      type: String,
      default: ''
    },
    historyRecordId: {
      type: Number,
      default: null
    }
  },
  setup(props) {
    const { theme } = useTheme()

    // 响应式数据
    const progressData = ref([])
    const markingProgress = ref(null)
    const systemStats = ref(null)
    const isLoadingProgress = ref(false)
    const refreshTimer = ref(null)
    const isComponentMounted = ref(false)

    // 计算属性
    const progressPercent = computed(() => {
      if (!markingProgress.value) return 0
      return Math.round(markingProgress.value.percentage || 0)
    })

    const isMarking = computed(() => {
      return markingProgress.value && markingProgress.value.processing_count > 0
    })

    const dataSource = computed(() => {
      if (!progressData.value || progressData.value.length === 0) return null
      // 检查最近的数据是否来自数据库或模拟数据
      const isFromDatabase = progressData.value.some(item => item.from_database)
      const isFromMock = progressData.value.some(item => item.from_mock)
      
      if (isFromMock) {
        return {
          isRealtime: false,
          isDatabase: false,
          isMock: true
        }
      }
      
      return {
        isRealtime: !isFromDatabase,
        isDatabase: isFromDatabase,
        isMock: false
      }
    })

    // 生成模拟数据
    const generateMockData = (taskStatus) => {
      const isCompleted = ['MARKED', 'COMPLETED'].includes(taskStatus)
      
      if (isCompleted) {
        // 标记完成状态：显示100%完成
        return {
          success: true,
          progress: {
            percentage: 100,
            submitted_count: 0,
            processing_count: 0,
            completed_count: 10,
            current_task_id: null,
            total_images: 10
          },
          system_stats: {
            ram_usage: 45,
            ram_used_gb: 7.2,
            ram_total_gb: 16,
            gpu_usage: 25,
            gpu_memory_used: 2.1,
            gpu_memory_total: 8,
            cpu_usage: 15,
            gpu_temperature: 65
          },
          from_mock: true
        }
      } else {
        // 标记进行中状态：显示动态进度
        const currentTime = Date.now()
        const progressPercent = Math.min(90, (currentTime % 30000) / 30000 * 100) // 30秒循环，最大90%
        
        return {
          success: true,
          progress: {
            percentage: progressPercent,
            submitted_count: Math.ceil(10 * (1 - progressPercent / 100)),
            processing_count: progressPercent < 90 ? 1 : 0,
            completed_count: Math.floor(10 * progressPercent / 100),
            current_task_id: progressPercent < 90 ? props.taskId?.toString() : null,
            total_images: 10
          },
          system_stats: {
            ram_usage: 60 + Math.random() * 10,
            ram_used_gb: 9.6 + Math.random() * 1.4,
            ram_total_gb: 16,
            gpu_usage: 70 + Math.random() * 20,
            gpu_memory_used: 5.6 + Math.random() * 1.4,
            gpu_memory_total: 8,
            cpu_usage: 40 + Math.random() * 20,
            gpu_temperature: 72 + Math.random() * 8
          },
          from_mock: true
        }
      }
    }

    // 获取当前任务状态（从父组件或全局状态获取）
    const getCurrentTaskStatus = () => {
      // 这里可以从路由、props或全局状态获取任务状态
      // 暂时使用一个简单的方法，可以根据实际情况调整
      return 'MARKING' // 默认返回MARKING状态，实际使用时需要获取真实状态
    }

    // 获取标记进度数据
    const fetchMarkingProgress = async () => {
      if (!props.taskId || !isComponentMounted.value) return

      try {
        isLoadingProgress.value = progressData.value.length === 0
        let data

        // 如果提供了historyRecordId，从历史记录中获取进度数据
        if (props.historyRecordId) {
          const historyData = await tasksApi.getExecutionHistoryById(props.historyRecordId)
          if (historyData && historyData.marking_progress_data) {
            data = {
              success: true,
              progress: historyData.marking_progress_data.progress || {},
              system_stats: historyData.marking_progress_data.system_stats || {},
              timeline: historyData.marking_progress_data.timeline || [],
              from_database: true
            }
          }
        } else {
          try {
            data = await tasksApi.getMarkingProgress(props.taskId)
          } catch (apiError) {
            console.warn('API获取标记进度失败，使用模拟数据:', apiError)
            // API失败时使用模拟数据
            data = generateMockData(getCurrentTaskStatus())
          }
        }

        // 检查组件是否仍然挂载
        if (!isComponentMounted.value) return

        if (data && data.success) {
          markingProgress.value = data.progress
          systemStats.value = data.system_stats
          
          // 添加时间戳用于图表显示
          const timestamp = new Date()
          const progressEntry = {
            time: timestamp.toISOString(),
            percentage: data.progress.percentage || 0,
            submitted: data.progress.submitted_count || 0,
            processing: data.progress.processing_count || 0,
            completed: data.progress.completed_count || 0,
            from_database: data.from_database || false,
            from_mock: data.from_mock || false
          }

          // 更新进度数据，保持最近50个数据点
          progressData.value.push(progressEntry)
          if (progressData.value.length > 50) {
            progressData.value.shift()
          }
        }
      } catch (error) {
        console.error('获取标记进度失败:', error)
        // 最后的降级方案：使用模拟数据
        const mockData = generateMockData(getCurrentTaskStatus())
        markingProgress.value = mockData.progress
        systemStats.value = mockData.system_stats
      } finally {
        isLoadingProgress.value = false
      }
    }

    // 开始定时刷新
    const startRefresh = () => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value)
      }
      
      // 只有在没有历史记录ID时才进行实时刷新
      if (!props.historyRecordId) {
        refreshTimer.value = setInterval(fetchMarkingProgress, 3000) // 每3秒刷新一次
      }
    }

    // 停止定时刷新
    const stopRefresh = () => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value)
        refreshTimer.value = null
      }
    }

    // 生命周期钩子
    onMounted(() => {
      isComponentMounted.value = true
      fetchMarkingProgress()
      startRefresh()
    })

    onUnmounted(() => {
      isComponentMounted.value = false
      stopRefresh()
    })

    // 监听props变化
    watch(() => props.taskId, () => {
      progressData.value = []
      markingProgress.value = null
      systemStats.value = null
      fetchMarkingProgress()
      startRefresh()
    })

    watch(() => props.historyRecordId, () => {
      progressData.value = []
      markingProgress.value = null
      systemStats.value = null
      fetchMarkingProgress()
      
      // 历史记录模式下停止刷新
      if (props.historyRecordId) {
        stopRefresh()
      } else {
        startRefresh()
      }
    })

    return {
      progressData,
      markingProgress,
      systemStats,
      isLoadingProgress,
      progressPercent,
      isMarking,
      dataSource,
      fetchMarkingProgress
    }
  }
}
</script>

<style scoped>
.marking-progress-details {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg-primary);
  border-radius: 8px;
  overflow: hidden;
}

.details-header {
  padding: 16px 20px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.details-title {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-info {
  display: flex;
  gap: 24px;
  align-items: center;
  flex-wrap: wrap;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.progress-bar {
  width: 120px;
  height: 8px;
  background: var(--color-bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  min-width: 40px;
}

.queue-info {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.details-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  min-height: 0;
}

.progress-section {
  flex: 1;
  min-width: 0;
}

.system-section {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.system-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-card {
  padding: 12px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.stat-icon {
  font-size: 16px;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-bar {
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.stat-fill.gpu {
  background: var(--color-success);
}

.stat-fill.cpu {
  background: var(--color-warning);
}

.stat-text {
  font-size: 11px;
  color: var(--color-text-secondary);
  text-align: center;
}

.stat-text.large {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: center;
}

.current-task-info {
  padding: 12px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

.info-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.task-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.task-value {
  font-size: 12px;
  color: var(--color-text-primary);
  font-family: monospace;
  word-break: break-all;
}

.data-source {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--color-bg-tertiary);
  border-radius: 4px;
  font-size: 12px;
}

.source-icon.mock {
  color: var(--color-warning);
}

.source-icon.realtime {
  color: var(--color-success);
}

.source-icon.database {
  color: var(--color-text-secondary);
}

.source-text {
  color: var(--color-text-secondary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .details-content {
    flex-direction: column;
  }
  
  .system-section {
    width: 100%;
  }
  
  .header-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>