<template>
  <div class="training-loss-chart">
    <div class="chart-header" v-if="showHeader">
      <h4 class="chart-title">
        训练Loss曲线
        <span v-if="firstStepLoss && lastStepLoss" class="loss-values">
          <span class="initial-loss" title="初始Loss值">初始: {{ firstStepLoss }}</span>
          <span class="loss-arrow">→</span>
          <span class="current-loss" title="当前Loss值">当前: {{ lastStepLoss }}</span>
        </span>
      </h4>
    </div>
    <div class="chart-container" ref="chartContainer">
      <div v-if="isLoading" class="loading-placeholder">加载中...</div>
      <div v-else-if="!hasData" class="empty-placeholder">
        <div class="empty-icon">📊</div>
        <div class="empty-text">暂无训练数据</div>
        <div class="empty-desc" v-if="isTraining">训练进行中，数据将在训练过程中更新</div>
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
  // Loss数据数组，格式为 [{step: number, value: number}, ...]
  lossData: {
    type: Array,
    default: () => []
  },
  // 是否显示加载状态
  isLoading: {
    type: Boolean,
    default: false
  },
  // 是否正在训练中
  isTraining: {
    type: Boolean,
    default: false
  },
  // 是否显示标题
  showHeader: {
    type: Boolean,
    default: true
  },
  // 图表高度
  height: {
    type: String,
    default: '100%'
  },
  // 图表标题
  chartTitle: {
    type: String,
    default: 'Lora训练Loss曲线'
  }
})

// 状态变量
const chartContainer = ref(null)
const chart = ref(null)
const isComponentMounted = ref(false)
const updateTimer = ref(null) // 添加防抖定时器

// 计算属性
const hasData = computed(() => props.lossData && props.lossData.length > 0)

// 主题响应式颜色计算
const chartColors = computed(() => {
  const primaryColor = getComputedStyle(document.documentElement)
    .getPropertyValue('--primary-color').trim();
  const textPrimary = getComputedStyle(document.documentElement)
    .getPropertyValue('--text-primary').trim();
  const textSecondary = getComputedStyle(document.documentElement)
    .getPropertyValue('--text-secondary').trim();
  const borderColor = getComputedStyle(document.documentElement)
    .getPropertyValue('--border-color-light').trim();
  const backgroundSecondary = getComputedStyle(document.documentElement)
    .getPropertyValue('--background-secondary').trim();
  
  return {
    primary: primaryColor,
    text: textPrimary,
    textSecondary: textSecondary,
    border: borderColor,
    background: backgroundSecondary,
    // 半透明颜色
    primaryAlpha: primaryColor.replace('rgb', 'rgba').replace(')', ', 0.5)'),
    primaryLightAlpha: primaryColor.replace('rgb', 'rgba').replace(')', ', 0.1)'),
    backgroundAlpha: backgroundSecondary.replace('rgb', 'rgba').replace(')', ', 0.95)')
  };
});

const firstStepLoss = computed(() => {
  if (props.lossData && props.lossData.length > 0) {
    const firstLoss = props.lossData[0]
    return firstLoss.value.toFixed(4)
  }
  return null
})

const lastStepLoss = computed(() => {
  if (props.lossData && props.lossData.length > 0) {
    const lastLoss = props.lossData[props.lossData.length - 1]
    return lastLoss.value.toFixed(4)
  }
  return null
})

// 初始化图表
const initChart = () => {
  try {
    // 确保DOM元素已经存在
    if (!chartContainer.value) {
      console.warn('Chart container is not ready yet')
      return false
    }
    
    // 销毁可能存在的旧图表实例
    if (chart.value) {
      chart.value.dispose()
    }
    
    // 创建新图表实例
    console.log('即将开始初始化')
    chart.value = echarts.init(chartContainer.value, null, {
      renderer: 'canvas',
      useDirtyRect: true,
      useCoarsePointer: true,
      pointerOptions: { passive: true }
    })
    console.log('初始化完成')
    
    // 设置图表选项
    const option = {
      title: props.showHeader ? null : {
        text: props.chartTitle,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'normal',
          color: chartColors.value.text
        },
        top: 10
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: chartColors.value.backgroundAlpha,
        borderColor: chartColors.value.border,
        borderWidth: 1,
        textStyle: {
          color: chartColors.value.text,
          fontSize: 12
        },
        padding: [8, 12],
        axisPointer: {
          type: 'cross',
          lineStyle: {
            color: chartColors.value.textSecondary,
            width: 1,
            type: 'dashed'
          },
          crossStyle: {
            color: chartColors.value.primary
          },
          label: {
            backgroundColor: chartColors.value.primary
          }
        },
        extraCssText: 'box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); border-radius: 6px;',
        formatter: function(params) {
          const param = params[0];
          const stepValue = param.value[0];
          const lossValue = param.value[1].toFixed(4);
          
          return `<div style="font-weight:bold;margin-bottom:3px;">训练步数：${stepValue}</div>
                  <div style="display:flex;align-items:center;margin-top:5px;">
                      <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:${param.color};margin-right:5px;"></span>
                      <span>Loss值：${lossValue}</span>
                  </div>`;
        }
      },
      grid: {
        left: '6%',
        right: '4%',
        bottom: '6%',
        top: props.showHeader ? '8%' : '12%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: '训练步数',
        nameLocation: 'middle',
        nameGap: 35,
        nameTextStyle: {
          color: chartColors.value.textSecondary,
          fontSize: 12,
          fontWeight: 'bold'
        },
        axisLine: {
          lineStyle: {
            color: chartColors.value.border,
            width: 1
          }
        },
        axisLabel: {
          color: chartColors.value.textSecondary,
          fontSize: 12,
          margin: 10,
          formatter: function(value) {
            return value;
          }
        },
        axisTick: {
          show: false
        },
        min: 'dataMin',
        max: 'dataMax'
      },
      yAxis: {
        type: 'value',
        name: 'Loss值',
        nameLocation: 'middle',
        nameGap: 40,
        nameTextStyle: {
          color: chartColors.value.textSecondary,
          fontSize: 12,
          fontWeight: 'bold'
        },
        min: 0,
        splitLine: {
          lineStyle: {
            color: chartColors.value.border,
            type: 'dashed'
          }
        },
        axisLabel: {
          color: chartColors.value.textSecondary,
          fontSize: 12
        },
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        }
      },
      series: [
        {
          name: '总体Loss',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: function(value, params) {
            // 每隔10个点显示一次
            return params.dataIndex % 10 === 0 ? 8 : 0;
          },
          showSymbol: true,
          sampling: 'average',
          itemStyle: {
            color: chartColors.value.primary,
            borderWidth: 2,
            borderColor: chartColors.value.background,
            shadowColor: chartColors.value.primaryAlpha,
            shadowBlur: 8
          },
          lineStyle: {
            width: 3,
            color: chartColors.value.primary
          },
          emphasis: {
            scale: true,
            focus: 'series'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {
                offset: 0,
                color: chartColors.value.primaryAlpha
              },
              {
                offset: 0.8,
                color: chartColors.value.primaryLightAlpha
              }
            ])
          },
          markLine: {
            silent: true,
            lineStyle: {
              color: chartColors.value.primary,
              type: 'dashed',
              width: 1
            },
            data: [
              { 
                type: 'average', 
                name: '平均值',
                label: {
                  formatter: '{b}: {c}',
                  position: 'insideEndTop',
                  backgroundColor: chartColors.value.primaryAlpha,
                  padding: [4, 8],
                  borderRadius: 4,
                  color: chartColors.value.background,
                  fontSize: 12
                }
              }
            ]
          },
          z: 3,
          data: []
        }
      ],
      animation: true,
      animationDuration: 1500,
      animationEasing: 'cubicOut'
    }
    
    chart.value.setOption(option)
    console.log("设置图标option")
    // 添加窗口大小变化时的自适应
    window.addEventListener('resize', handleResize, { passive: true })
    
    return true
  } catch (error) {
    console.error('初始化图表失败:', error)
    return false
  }
}

// 更新图表数据
const updateChart = () => {
  // 如果没有有效的图表容器元素，不进行任何操作
  if (!chartContainer.value || !document.body.contains(chartContainer.value)) {
    console.warn('Chart container is not available or not in DOM')
    return
  }
  
  if (!chart.value) {
    // 如果图表实例不存在，尝试初始化
    const initialized = initChart()
    if (!initialized) {
      console.warn('Failed to initialize chart')
      return
    }
  }
  
  if (!props.lossData || props.lossData.length === 0) {
    console.warn('No loss data to update chart')
    return
  }
  
  try {
    // 转换数据格式
    const seriesData = props.lossData.map(item => [item.step, item.value])
    
    // 确保图表实例仍然有效
    if (chart.value && document.body.contains(chartContainer.value)) {
      chart.value.setOption({
        xAxis: {
          min: 'dataMin',
          max: 'dataMax'
        },
        series: [
          {
            data: seriesData,
            // 根据数据点数量动态决定是否显示标记点
            symbolSize: function(value, params) {
              // 数据量较小时显示更多点
              const interval = props.lossData.length > 100 ? 20 : 
                               props.lossData.length > 50 ? 10 : 5;
              return params.dataIndex % interval === 0 ? 8 : 0;
            }
          }
        ]
      }, {
        notMerge: false // 使用合并模式而不是完全替换
      })
    }
  } catch (error) {
    console.error('更新图表数据失败:', error)
  }
}

// 窗口大小变化时调整图表大小
const handleResize = () => {
  if (!chart.value || !chartContainer.value || !document.body.contains(chartContainer.value)) {
    return
  }
  
  try {
    chart.value.resize()
  } catch (error) {
    console.error('调整图表大小失败:', error)
  }
}

// 监听lossData变化，更新图表
watch(() => props.lossData, () => {
  if (isComponentMounted.value) {
    nextTick(() => {
        updateChart()
    })
  }
}, { deep: true })

// 组件挂载时
onMounted(() => {
  isComponentMounted.value = true
  nextTick(() => {
    if (props.lossData.length > 0) {
      initChart()
      updateChart()
    }
  })
})

// 组件卸载时
onUnmounted(() => {
  isComponentMounted.value = false
  
  // 清除防抖定时器
  if (updateTimer.value) {
    clearTimeout(updateTimer.value)
    updateTimer.value = null
  }
  
  // 移除窗口大小变化监听
  window.removeEventListener('resize', handleResize)
  
  // 销毁图表实例
  if (chart.value) {
    try {
      chart.value.dispose()
    } catch (error) {
      console.error('销毁图表实例失败:', error)
    }
    chart.value = null
  }
})
</script>

<style scoped>
.training-loss-chart {
  width: 100%;
  height: v-bind('height');
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 16px;
}

.chart-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.loss-values {
  font-size: 14px;
  font-weight: normal;
  color: var(--text-secondary);
  margin-left: 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.initial-loss {
  color: #e67e22;
}

.loss-arrow {
  color: var(--text-tertiary);
  font-size: 12px;
}

.current-loss {
  color: #2ecc71;
  font-weight: 500;
}

.chart-container {
  flex: 1;
  position: relative;
  min-height: 0;
  background-color: var(--background-secondary);
  border-radius: 8px;
}

.loading-placeholder,
.empty-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--background-secondary);
  border-radius: 8px;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
}

.empty-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 8px;
}
</style> 