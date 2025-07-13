import { createVNode, render } from 'vue'
import Message from '../components/common/Message.vue'

/**
 * @typedef {'success' | 'warning' | 'error' | 'info'} MessageType
 */

// 消息队列
const messageQueue = []
// 当前显示的消息实例
const instances = []
// 最大显示消息数量
const MAX_MESSAGES = 5
// 消息间距
const MESSAGE_GAP = 16

/**
 * 创建消息实例
 * @param {Object} options 
 * @param {string} options.content - 消息内容
 * @param {MessageType} options.type - 消息类型
 * @param {number} options.duration - 显示时长
 * @param {number} options.offset - 消息偏移量
 */
const createMessage = (options) => {
  const container = document.createElement('div')
  
  const vnode = createVNode(Message, {
    content: options.content,
    type: options.type,
    duration: options.duration,
    offset: options.offset,
    onClose: () => closeMessage(instance)
  })
  
  render(vnode, container)
  document.body.appendChild(container)
  
  const instance = {
    vnode,
    container,
    id: Date.now() + Math.random().toString(36).substring(2, 9),
    close: () => {
      if (instance.vnode && instance.vnode.component) {
        instance.vnode.component.exposed.hide()
      }
    }
  }
  
  if (vnode.component) {
    vnode.component.exposed.show()
  }
  
  return instance
}

/**
 * 关闭消息
 * @param {Object} instance 消息实例
 */
const closeMessage = (instance) => {
  const index = instances.findIndex(item => item.id === instance.id)
  if (index === -1) return
  
  // 从实例列表中移除
  instances.splice(index, 1)
  
  // 重新计算剩余消息的位置
  updateMessagePositions()
  
  // 从DOM中移除
  setTimeout(() => {
    render(null, instance.container)
    document.body.removeChild(instance.container)
    
    // 检查队列中是否有待显示的消息
    if (messageQueue.length > 0 && instances.length < MAX_MESSAGES) {
      const nextMessage = messageQueue.shift()
      showMessage(nextMessage)
    }
  }, 300) // 等待动画结束
}

/**
 * 更新所有消息的位置
 */
const updateMessagePositions = () => {
  let currentOffset = 20
  
  instances.forEach(instance => {
    if (instance.vnode && instance.vnode.component) {
      instance.vnode.component.exposed.updateOffset(currentOffset)
      
      // 计算下一个消息的位置
      const el = instance.container.firstElementChild
      if (el) {
        currentOffset += el.offsetHeight + MESSAGE_GAP
      } else {
        currentOffset += 70 // 默认高度 + 间距
      }
    }
  })
}

/**
 * 显示消息
 * @param {Object} options 消息选项
 */
const showMessage = (options) => {
  // 如果当前显示的消息数量已达到最大值，则加入队列
  if (instances.length >= MAX_MESSAGES) {
    messageQueue.push(options)
    return null
  }
  
  // 计算新消息的位置
  let offset = 20
  if (instances.length > 0) {
    const lastInstance = instances[instances.length - 1]
    const el = lastInstance.container.firstElementChild
    if (el) {
      offset = lastInstance.vnode.component.exposed.getOffset() + el.offsetHeight + MESSAGE_GAP
    } else {
      offset += instances.length * (70 + MESSAGE_GAP)
    }
  }
  
  options.offset = offset
  const instance = createMessage(options)
  instances.push(instance)
  
  return instance
}

/**
 * 消息提示服务
 */
const message = {
  /**
   * 成功提示
   * @param {string} content 提示内容
   * @param {number} duration 提示持续时间
   */
  success(content, duration = 3000) {
    return showMessage({
      type: 'success',
      content,
      duration
    })
  },
  
  /**
   * 错误提示
   * @param {string|Error|Object} error 错误信息或错误对象
   * @param {number} duration 提示持续时间
   */
  error(error, duration = 3000) {
    // 处理各种错误类型
    let content = '操作失败'
    
    if (typeof error === 'string') {
      content = error
    } else if (error instanceof Error) {
      content = error.message || '操作失败'
    } else if (error && error.msg) {
      // 处理统一格式的错误对象
      content = error.msg
    } else if (error && error.message) {
      content = error.message
    }
    
    return showMessage({
      type: 'error',
      content,
      duration
    })
  },
  
  /**
   * 警告提示
   * @param {string} content 提示内容
   * @param {number} duration 提示持续时间
   */
  warning(content, duration = 3000) {
    return showMessage({
      type: 'warning',
      content,
      duration
    })
  },
  
  /**
   * 信息提示
   * @param {string} content 提示内容
   * @param {number} duration 提示持续时间
   */
  info(content, duration = 3000) {
    return showMessage({
      type: 'info',
      content,
      duration
    })
  },
  
  /**
   * 关闭所有消息
   */
  closeAll() {
    messageQueue.length = 0
    // 复制数组，避免在遍历过程中修改原数组
    const instancesCopy = [...instances]
    instancesCopy.forEach(instance => instance.close())
  }
}

export default message 