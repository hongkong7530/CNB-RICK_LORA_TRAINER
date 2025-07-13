import { ref } from 'vue'
import mitt from 'mitt'

// 创建事件总线实例
export const emitter = mitt()

// 用于存储最后发送的事件状态
const lastEvents = ref({})

// 增强的emitter，可以存储最后发送的事件数据
export const enhancedEmitter = {
  emit(type, data) {
    lastEvents.value[type] = {
      data,
      timestamp: Date.now()
    }
    emitter.emit(type, data)
  },
  on(type, handler) {
    emitter.on(type, handler)
  },
  off(type, handler) {
    emitter.off(type, handler)
  },
  getLastEvent(type) {
    return lastEvents.value[type]
  }
}

export default emitter 