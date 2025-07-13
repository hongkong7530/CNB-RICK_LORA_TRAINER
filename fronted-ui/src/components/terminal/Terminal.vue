<template>
  <div class="terminal-container">
    <div v-if="connectionError" class="error-message">
      <p>{{ connectionError }}</p>
      <button @click="connectWebSocket">重试</button>
    </div>
    <div ref="terminalRef" class="terminal"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import { WebglAddon } from 'xterm-addon-webgl'
import 'xterm/css/xterm.css'

const props = defineProps({
  assetId: [Number, String]
})

const terminalRef = ref(null)
const terminal = ref(null)
const socket = ref(null)
const fitAddon = ref(null)

// 连接状态
const isConnected = ref(false)
const connecting = ref(false)
const connectionError = ref('')

const emit = defineEmits(['connect', 'disconnect', 'error'])

onMounted(() => {
  initTerminal()
})

// 监听大小变化
const handleResize = () => {
  if (fitAddon.value && terminal.value) {
    fitAddon.value.fit()
    
    // 发送新的终端大小到服务器
    if (socket.value?.readyState === WebSocket.OPEN && terminal.value) {
      socket.value.send(JSON.stringify({ 
        type: 'resize', 
        data: {
          rows: terminal.value.rows, 
          cols: terminal.value.cols 
        }
      }))
    }
  }
}

onBeforeUnmount(() => {
  cleanupTerminal()
  window.removeEventListener('resize', handleResize)
})

const initTerminal = () => {
  if (!terminalRef.value || !props.assetId) return
  
  // 确保清理之前的终端
  cleanupTerminal()
  
  // 初始化终端
  terminal.value = new Terminal({
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
      background: '#1E1E1E',
      foreground: '#D4D4D4',
      cursor: '#FFFFFF',
      selectionBackground: 'rgba(255, 255, 255, 0.3)'
    },
    cursorBlink: true,
    convertEol: true,  // 将接收到的换行符转换为回车+换行符
    scrollback: 1000,  // 滚动历史行数
    rows: 24,  // 设置初始行数
    cols: 80,  // 设置初始列数
    allowTransparency: true
  })

  // 添加插件
  fitAddon.value = new FitAddon()
  const webLinksAddon = new WebLinksAddon()
  
  terminal.value.loadAddon(fitAddon.value)
  terminal.value.loadAddon(webLinksAddon)
  
  // 尝试添加WebGL插件以提高性能
  try {
    const webglAddon = new WebglAddon()
    terminal.value.loadAddon(webglAddon)
  } catch (e) {
    console.warn('WebGL渲染加载失败，将使用Canvas渲染', e)
  }

  // 打开终端
  terminal.value.open(terminalRef.value)
  fitAddon.value.fit()
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize)

  // 连接WebSocket
  connectWebSocket()
}

const getWebSocketUrl = (assetId) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/v1/terminal/${assetId}`
}

const connectWebSocket = () => {
  if (!props.assetId || !terminal.value) {
    console.error('Asset ID is missing or terminal not initialized')
    return
  }
  
  // 如果已有连接，先断开
  if (socket.value) {
    socket.value.close()
    socket.value = null
  }
  
  connectionError.value = ''
  connecting.value = true
  
  const wsUrl = getWebSocketUrl(props.assetId)
  console.log('Connecting to WebSocket:', wsUrl)
  
  socket.value = new WebSocket(wsUrl)
  
  socket.value.onopen = () => {
    isConnected.value = true
    connecting.value = false
    terminal.value?.write('已连接到终端...\r\n')
    emit('connect')
    
    // 发送初始终端大小
    if (terminal.value) {
      const { rows, cols } = terminal.value
      socket.value.send(JSON.stringify({ type: 'resize', data: { rows, cols } }))
    }
  }
  
  socket.value.onmessage = (event) => {
    if (!terminal.value) return
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'error') {
        terminal.value.write(`\r\n\x1b[31m错误: ${data.data}\x1b[0m\r\n`)
        isConnected.value = false
        connectionError.value = data.data
        emit('error', data.data)
      } else if (data.type === 'data') {
        terminal.value.write(data.data)
      }
    } catch (error) {
      // 如果不是JSON格式，则当作原始终端数据处理
      terminal.value.write(event.data)
    }
  }
  
  socket.value.onclose = () => {
    isConnected.value = false
    connecting.value = false
    emit('disconnect')
    
    if (terminal.value) {
      terminal.value.write('\r\n\x1b[33m连接已关闭。尝试重新连接...\x1b[0m\r\n')
    }
    
    // 自动重连逻辑
    if (!connectionError.value && terminalRef.value) {
      setTimeout(() => {
        if (terminalRef.value && terminal.value) {
          connectWebSocket()
        }
      }, 3000)
    }
  }
  
  socket.value.onerror = (error) => {
    isConnected.value = false
    connecting.value = false
    connectionError.value = '连接错误: 请检查网络连接或服务器状态'
    emit('error', '连接错误: 请检查网络连接或服务器状态')
    console.error('WebSocket error:', error)
    
    if (terminal.value) {
      terminal.value.write('\r\n\x1b[31m连接错误: 请检查网络连接或服务器状态\x1b[0m\r\n')
    }
  }
  
  if (terminal.value) {
    // 发送终端输入到服务器
    terminal.value.onData(data => {
      if (socket.value?.readyState === WebSocket.OPEN) {
        socket.value.send(JSON.stringify({ type: 'data', data }))
      }
    })
  }
}

const cleanupTerminal = () => {
  try {
    // 移除事件监听
    window.removeEventListener('resize', handleResize)
    
    // 清理终端
    if (terminal.value) {
      try {
        terminal.value.dispose()
      } catch (error) {
        console.debug('Terminal dispose error:', error)
      }
    }

    // 关闭WebSocket连接
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
    
    // 清理插件
    fitAddon.value = null
    terminal.value = null
    
  } catch (error) {
    console.error('Terminal cleanup failed:', error)
  } finally {
    isConnected.value = false
    connecting.value = false
  }
}

// 对外暴露方法
defineExpose({
  connectWebSocket,
  cleanupTerminal,
  isConnected,
  connecting,
  connectionError
})

// 监听assetId变化
watch(() => props.assetId, (newVal, oldVal) => {
  if (newVal !== oldVal && newVal) {
    if (terminalRef.value) {
      // 重新初始化终端
      cleanupTerminal()
      setTimeout(() => {
        initTerminal()
      }, 100)
    }
  }
})
</script>

<style scoped>
.terminal-container {
  width: 100%;
  height: 100%;
  background: #1E1E1E;
  border-radius: 6px;
  overflow: hidden;
  padding: 4px;
  position: relative;
}

.terminal {
  width: 100%;
  height: 100%;
}

.error-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 16px;
  border-radius: 6px;
  text-align: center;
  z-index: 10;
}

.error-message button {
  margin-top: 10px;
  padding: 6px 12px;
  background-color: #27c93f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 确保xterm渲染正确 */
:deep(.xterm-viewport) {
  border-radius: 4px;
  overflow-y: auto;
}

:deep(.xterm) {
  padding: 4px;
}
</style> 