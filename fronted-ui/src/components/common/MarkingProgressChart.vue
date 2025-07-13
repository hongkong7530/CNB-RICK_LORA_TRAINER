<template>
  <div class="marking-progress-chart">
    <div class="chart-header" v-if="showHeader">
      <h4 class="chart-title">
        标记进度监控
        <span v-if="currentProgress !== null" class="progress-values">
          <span class="progress-value" title="当前进度">{{ currentProgress }}%</span>
          <span v-if="queueInfo" class="queue-status">
            (队列: {{ queueInfo.processing }}/{{ queueInfo.submitted + queueInfo.processing }})
          </span>
        </span>
      </h4>
    </div>
    <div class="chart-container" ref="chartContainer">
      <div v-if="isLoading" class="loading-placeholder">加载中...</div>
      <div v-else-if="!hasData" class="empty-placeholder">
        <div class="empty-icon">📊</div>
        <div class="empty-text">暂无标记数据</div>
        <div class="empty-desc" v-if="isMarking">标记进行中，数据将在标记过程中更新</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { 
  GridComponent, 
  TooltipComponent, 
  TitleComponent,
  LegendComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useTheme } from '@/composables/useTheme'

// 注册必要的组件
echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  CanvasRenderer
])

const props = defineProps({
  // 进度数据数组，格式为 [{time: string, percentage: number, submitted: number, processing: number, completed: number}, ...]
  progressData: {
    type: Array,
    default: () => []
  },
  // 是否显示加载状态
  isLoading: {
    type: Boolean,
    default: false
  },
  // 是否正在标记
  isMarking: {
    type: Boolean,
    default: false
  },
  // 图表高度
  height: {
    type: String,
    default: '400px'
  },
  // 是否显示标题
  showHeader: {
    type: Boolean,
    default: true
  }
})

const { theme } = useTheme()
const chartContainer = ref(null)
const chart = ref(null)

// 计算属性
const hasData = computed(() => {
  return props.progressData && props.progressData.length > 0
})

const currentProgress = computed(() => {
  if (!hasData.value) return null
  const latest = props.progressData[props.progressData.length - 1]
  return latest ? Math.round(latest.percentage || 0) : null
})

const queueInfo = computed(() => {
  if (!hasData.value) return null
  const latest = props.progressData[props.progressData.length - 1]
  if (!latest) return null
  return {
    submitted: latest.submitted || 0,
    processing: latest.processing || 0,
    completed: latest.completed || 0
  }
})

// 获取主题颜色
const getThemeColors = () => {
  const root = document.documentElement
  return {
    primary: getComputedStyle(root).getPropertyValue('--color-primary').trim(),
    success: getComputedStyle(root).getPropertyValue('--color-success').trim(),
    warning: getComputedStyle(root).getPropertyValue('--color-warning').trim(),
    textPrimary: getComputedStyle(root).getPropertyValue('--color-text-primary').trim(),
    textSecondary: getComputedStyle(root).getPropertyValue('--color-text-secondary').trim(),
    border: getComputedStyle(root).getPropertyValue('--color-border').trim()
  }
}

// 初始化图表
const initChart = () => {
  if (!chartContainer.value) return

  const colors = getThemeColors()
  
  chart.value = echarts.init(chartContainer.value, null, {
    renderer: 'canvas',
    useDirtyRect: true
  })

  const option = {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 500,
    animationEasing: 'cubicOut',
    grid: {
      left: '3%',
      right: '3%',
      bottom: '8%',
      top: '10%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.textPrimary === '#ffffff' ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: colors.border,
      textStyle: {
        color: colors.textPrimary === '#ffffff' ? '#ffffff' : '#333333'
      },
      formatter: function(params) {
        if (!params || params.length === 0) return ''
        
        const data = params[0].data
        const time = new Date(data.time).toLocaleTimeString()
        
        return `
          <div style="margin: 0; padding: 0;">
            <div style="margin-bottom: 4px; font-weight: bold;">时间: ${time}</div>
            <div style="margin-bottom: 2px;">进度: ${data.percentage.toFixed(1)}%</div>
            <div style="margin-bottom: 2px;">提交: ${data.submitted}</div>
            <div style="margin-bottom: 2px;">处理中: ${data.processing}</div>
            <div>完成: ${data.completed}</div>
          </div>
        `
      }
    },
    xAxis: {
      type: 'time',
      axisLine: {
        lineStyle: {
          color: colors.border
        }
      },
      axisLabel: {
        color: colors.textSecondary,
        formatter: function(value) {
          return new Date(value).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })
        }
      },
      splitLine: {
        show: false
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '进度 (%)',
        nameTextStyle: {
          color: colors.textSecondary
        },
        min: 0,
        max: 100,
        axisLine: {
          lineStyle: {
            color: colors.border
          }
        },
        axisLabel: {
          color: colors.textSecondary,
          formatter: '{value}%'
        },
        splitLine: {
          lineStyle: {
            color: colors.border,
            opacity: 0.3
          }
        }
      },
      {
        type: 'value',
        name: '队列数量',
        nameTextStyle: {
          color: colors.textSecondary
        },
        axisLine: {
          lineStyle: {
            color: colors.border
          }
        },
        axisLabel: {
          color: colors.textSecondary
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '进度',
        type: 'line',
        yAxisIndex: 0,
        data: [],
        smooth: true,
        lineStyle: {
          color: colors.primary,
          width: 3
        },
        itemStyle: {
          color: colors.primary
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: colors.primary + '40' },
              { offset: 1, color: colors.primary + '10' }
            ]
          }
        },
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false
      },
      {
        name: '处理中',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true,
        lineStyle: {
          color: colors.warning,
          width: 2
        },
        itemStyle: {
          color: colors.warning
        },
        symbol: 'circle',
        symbolSize: 4,
        showSymbol: false
      },
      {
        name: '完成',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true,
        lineStyle: {
          color: colors.success,
          width: 2
        },
        itemStyle: {
          color: colors.success
        },
        symbol: 'circle',
        symbolSize: 4,
        showSymbol: false
      }
    ],
    legend: {
      data: ['进度', '处理中', '完成'],
      textStyle: {
        color: colors.textSecondary
      },
      bottom: 0
    }
  }

  chart.value.setOption(option)
  updateChart()
}

// 更新图表数据
const updateChart = () => {
  if (!chart.value || !hasData.value) return

  const progressSeries = []
  const processingSeries = []
  const completedSeries = []

  props.progressData.forEach(item => {
    const timestamp = new Date(item.time).getTime()
    progressSeries.push({
      value: [timestamp, item.percentage || 0],
      time: item.time,
      percentage: item.percentage || 0,
      submitted: item.submitted || 0,
      processing: item.processing || 0,
      completed: item.completed || 0
    })
    processingSeries.push([timestamp, item.processing || 0])
    completedSeries.push([timestamp, item.completed || 0])
  })

  chart.value.setOption({
    series: [
      { data: progressSeries },
      { data: processingSeries },
      { data: completedSeries }
    ]
  })
}

// 调整图表大小
const resizeChart = () => {
  if (chart.value) {
    chart.value.resize()
  }
}

// 监听窗口大小变化
let resizeObserver = null

onMounted(async () => {
  await nextTick()
  initChart()
  
  // 监听容器大小变化
  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      resizeChart()
    })
    if (chartContainer.value) {
      resizeObserver.observe(chartContainer.value)
    }
  }
  
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  if (chart.value) {
    chart.value.dispose()
    chart.value = null
  }
  
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  
  window.removeEventListener('resize', resizeChart)
})

// 监听数据变化
watch(() => props.progressData, updateChart, { deep: true })

// 监听主题变化
watch(() => theme.value, () => {
  if (chart.value) {
    chart.value.dispose()
    nextTick(() => {
      initChart()
    })
  }
})
</script>

<style scoped>
.marking-progress-chart {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
  border-radius: 8px;
  overflow: hidden;
}

.chart-header {
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.chart-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.progress-values {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
}

.progress-value {
  color: var(--color-primary);
  font-weight: 600;
}

.queue-status {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.chart-container {
  flex: 1;
  position: relative;
  min-height: 200px;
  padding: 8px;
}

.loading-placeholder,
.empty-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-secondary);
}

.loading-placeholder {
  font-size: 14px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  text-align: center;
  opacity: 0.7;
  max-width: 300px;
}
</style>