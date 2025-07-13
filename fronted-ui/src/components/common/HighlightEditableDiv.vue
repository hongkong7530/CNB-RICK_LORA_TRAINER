<template>
  <div 
    class="highlight-editable-div"
    :style="{ 
      maxHeight: maxHeight,
      borderColor: focused ? borderFocusColor : borderColor
    }"
    :class="{ 'is-focused': focused }"
    :data-placeholder="placeholder"
    ref="editableDiv"
    contenteditable="true"
    @input="handleInput"
    @focus="focused = true"
    @blur="focused = false"
    @paste="handlePaste"
  ></div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'

const props = defineProps({
  // 模型值
  modelValue: {
    type: String,
    default: ''
  },
  // 需要高亮的字符（可以是数组或单个字符）
  highlightChars: {
    type: [String, Array],
    default: ','
  },
  // 高亮颜色
  highlightColor: {
    type: String,
    default: '#ff3333'
  },
  // 高亮字体粗细
  highlightFontWeight: {
    type: String,
    default: 'bold'
  },
  // 最大高度
  maxHeight: {
    type: String,
    default: '120px'
  },
  // 占位符
  placeholder: {
    type: String,
    default: ''
  },
  // 边框颜色
  borderColor: {
    type: String,
    default: 'var(--border-color, #ddd)'
  },
  // 聚焦时边框颜色
  borderFocusColor: {
    type: String,
    default: 'var(--primary-color, #0077ff)'
  }
})

// 定义可触发的事件
const emit = defineEmits(['update:modelValue', 'input', 'change'])

// 引用和状态
const editableDiv = ref(null)
const focused = ref(false)
const isComposing = ref(false) // 处理中文输入

// 创建一个唯一的标记ID
const CURSOR_MARKER_ID = 'cursor-position-marker'

// 将字符串转换为带高亮的HTML
const highlightText = (text) => {
  if (!text) return ''
  
  // 将高亮字符统一处理为数组
  const charsToHighlight = Array.isArray(props.highlightChars) 
    ? props.highlightChars 
    : [props.highlightChars]
  
  // 转义HTML特殊字符
  let escapedText = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // 创建高亮样式字符串
  const style = `color: ${props.highlightColor}; font-weight: ${props.highlightFontWeight};`
  
  // 替换每个需要高亮的字符
  charsToHighlight.forEach(char => {
    if (!char) return
    
    // 转义正则表达式特殊字符
    const escapedChar = char.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    
    // 创建替换正则
    const regex = new RegExp(escapedChar, 'g')
    
    // 替换为带样式的span，添加data-char属性
    escapedText = escapedText.replace(
      regex, 
      `<span style="${style}" class="highlighted-char" data-char="${char}">${char}</span>`
    )
  })
  
  return escapedText
}

// 从HTML中提取纯文本
const extractTextFromHtml = (html) => {
  if (!html) return ''
  
  // 创建临时DOM元素
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html
  
  // 返回文本内容
  return tempDiv.textContent || tempDiv.innerText || ''
}

// 处理输入事件
const handleInput = () => {
  if (isComposing.value) return
  
  // 插入临时标记来跟踪光标位置
  insertCursorMarker()
  
  // 获取纯文本内容（移除标记后的内容）
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = editableDiv.value.innerHTML
  const marker = tempDiv.querySelector(`#${CURSOR_MARKER_ID}`)
  
  // 光标在高亮字符附近的标记
  let markerAfterHighlight = false
  if (marker) {
    // 检查标记前面是否有高亮字符
    const prevSibling = marker.previousSibling
    if (prevSibling && prevSibling.classList && prevSibling.classList.contains('highlighted-char')) {
      markerAfterHighlight = true
    }
    
    // 移除标记以获取干净的内容
    marker.remove()
  }
  
  const plainText = extractTextFromHtml(tempDiv.innerHTML)
  
  // 发送更新事件
  emit('update:modelValue', plainText)
  emit('input', plainText)
  
  // 应用高亮样式并恢复光标位置
  nextTick(() => {
    if (!isComposing.value && editableDiv.value) {
      // 保存原来的HTML以查找标记位置
      const originalHtml = editableDiv.value.innerHTML
      
      // 应用高亮
      editableDiv.value.innerHTML = highlightText(plainText)
      
      // 在应用高亮后恢复光标位置
      restoreCursorPosition(originalHtml, markerAfterHighlight)
    }
  })
}

// 在当前光标位置插入临时标记
const insertCursorMarker = () => {
  if (!editableDiv.value) return
  
  // 获取当前选区
  const selection = window.getSelection()
  if (!selection.rangeCount) return
  
  // 获取选区范围
  const range = selection.getRangeAt(0)
  
  // 移除可能已存在的标记
  const existingMarker = editableDiv.value.querySelector(`#${CURSOR_MARKER_ID}`)
  if (existingMarker) {
    existingMarker.remove()
  }
  
  // 创建新标记
  const marker = document.createElement('span')
  marker.id = CURSOR_MARKER_ID
  marker.style.display = 'inline'
  marker.innerHTML = '​' // 零宽空格，确保标记有内容但不可见
  
  // 插入标记
  range.insertNode(marker)
}

// 根据标记恢复光标位置
const restoreCursorPosition = (originalHtml, wasAfterHighlight) => {
  if (!editableDiv.value) return
  
  try {
    // 创建临时元素来解析原始HTML
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = originalHtml
    
    // 查找标记
    const marker = tempDiv.querySelector(`#${CURSOR_MARKER_ID}`)
    if (!marker) return
    
    // 查找标记在原始文本中的位置
    let textBeforeMarker = ''
    
    // 收集标记前面的所有文本
    const collectTextBefore = (node, target) => {
      if (node === target) return true
      
      if (node.nodeType === Node.TEXT_NODE) {
        textBeforeMarker += node.textContent
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        if (node.classList && node.classList.contains('highlighted-char')) {
          // 高亮字符仅算一个字符
          textBeforeMarker += node.textContent
        } else {
          // 遍历子节点
          for (let i = 0; i < node.childNodes.length; i++) {
            if (collectTextBefore(node.childNodes[i], target)) return true
          }
          
          // 如果不包含目标，则将所有内容添加到文本
          if (node !== tempDiv) {
            let nodeText = ''
            for (let i = 0; i < node.childNodes.length; i++) {
              if (node.childNodes[i].nodeType === Node.TEXT_NODE) {
                nodeText += node.childNodes[i].textContent
              }
            }
            textBeforeMarker += nodeText
          }
        }
      }
      
      return false
    }
    
    // 遍历DOM收集标记前的文本
    collectTextBefore(tempDiv, marker)
    
    // 计算光标应该在的文本位置
    let targetPosition = textBeforeMarker.length
    
    // 如果标记在高亮字符后面，可能需要调整位置
    if (wasAfterHighlight) {
      const highlightChars = Array.isArray(props.highlightChars) 
        ? props.highlightChars 
        : [props.highlightChars]
      
      // 检查前面的字符是否是高亮字符
      const charBeforeCursor = textBeforeMarker.charAt(textBeforeMarker.length - 1)
      if (highlightChars.includes(charBeforeCursor)) {
        // 确保光标在高亮字符之后
        targetPosition = textBeforeMarker.length
      }
    }
    
    // 现在在新的高亮后的内容中找到对应位置
    setCursorAtTextPosition(targetPosition)
  } catch (e) {
    console.error('恢复光标位置失败:', e)
  }
}

// 在指定的文本位置设置光标
const setCursorAtTextPosition = (targetPosition) => {
  if (!editableDiv.value) return
  
  const textNodes = []
  let textPosition = 0
  
  // 收集所有文本节点
  const collectTextNodes = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      textNodes.push({
        node,
        start: textPosition,
        end: textPosition + node.length
      })
      textPosition += node.length
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.classList && node.classList.contains('highlighted-char')) {
        // 高亮节点只算一个字符长度
        textNodes.push({
          node,
          isHighlight: true,
          start: textPosition,
          end: textPosition + 1
        })
        textPosition += 1
      } else {
        for (let i = 0; i < node.childNodes.length; i++) {
          collectTextNodes(node.childNodes[i])
        }
      }
    }
  }
  
  // 收集文本节点
  collectTextNodes(editableDiv.value)
  
  // 查找目标位置对应的节点
  for (const item of textNodes) {
    if (item.start <= targetPosition && targetPosition <= item.end) {
      const selection = window.getSelection()
      const range = document.createRange()
      
      if (item.isHighlight) {
        // 如果是高亮节点，根据位置决定光标放在前面还是后面
        if (targetPosition === item.start) {
          // 光标在高亮字符前
          if (item.node.previousSibling && item.node.previousSibling.nodeType === Node.TEXT_NODE) {
            range.setStart(item.node.previousSibling, item.node.previousSibling.length)
            range.setEnd(item.node.previousSibling, item.node.previousSibling.length)
          } else {
            const parent = item.node.parentNode
            const index = Array.from(parent.childNodes).indexOf(item.node)
            range.setStart(parent, index)
            range.setEnd(parent, index)
          }
        } else {
          // 光标在高亮字符后
          if (item.node.nextSibling && item.node.nextSibling.nodeType === Node.TEXT_NODE) {
            range.setStart(item.node.nextSibling, 0)
            range.setEnd(item.node.nextSibling, 0)
          } else {
            const parent = item.node.parentNode
            const index = Array.from(parent.childNodes).indexOf(item.node) + 1
            range.setStart(parent, index)
            range.setEnd(parent, index)
          }
        }
      } else {
        // 普通文本节点
        const offset = targetPosition - item.start
        range.setStart(item.node, offset)
        range.setEnd(item.node, offset)
      }
      
      selection.removeAllRanges()
      selection.addRange(range)
      break
    }
  }
  
  // 如果没有找到匹配的节点，但位置在文本末尾
  if (targetPosition >= textPosition && textNodes.length > 0) {
    const lastItem = textNodes[textNodes.length - 1]
    const selection = window.getSelection()
    const range = document.createRange()
    
    if (lastItem.isHighlight) {
      // 高亮节点之后
      if (lastItem.node.nextSibling && lastItem.node.nextSibling.nodeType === Node.TEXT_NODE) {
        range.setStart(lastItem.node.nextSibling, lastItem.node.nextSibling.length)
        range.setEnd(lastItem.node.nextSibling, lastItem.node.nextSibling.length)
      } else {
        const parent = lastItem.node.parentNode
        const index = Array.from(parent.childNodes).indexOf(lastItem.node) + 1
        range.setStart(parent, index)
        range.setEnd(parent, index)
      }
    } else {
      // 普通文本节点末尾
      range.setStart(lastItem.node, lastItem.node.length)
      range.setEnd(lastItem.node, lastItem.node.length)
    }
    
    selection.removeAllRanges()
    selection.addRange(range)
  }
}

// 处理粘贴事件，只允许纯文本
const handlePaste = (event) => {
  event.preventDefault()
  
  // 获取剪贴板中的纯文本
  const text = event.clipboardData.getData('text/plain')
  
  // 插入到当前位置
  document.execCommand('insertText', false, text)
}

// 监听中文输入状态
onMounted(() => {
  if (editableDiv.value) {
    editableDiv.value.addEventListener('compositionstart', () => {
      isComposing.value = true
    })
    
    editableDiv.value.addEventListener('compositionend', (event) => {
      isComposing.value = false
      // 手动触发输入事件以更新高亮
      handleInput(event)
    })
  }
})

// 监听模型值变化，更新编辑框内容
watch(() => props.modelValue, (newValue) => {
  // 只有在没有焦点的情况下才更新内容，避免干扰用户输入
  if (!focused.value && editableDiv.value) {
    editableDiv.value.innerHTML = highlightText(newValue)
  }
})

// 初始化内容
onMounted(() => {
  if (editableDiv.value && props.modelValue) {
    editableDiv.value.innerHTML = highlightText(props.modelValue)
  }
})
</script>

<style scoped>
.highlight-editable-div {
  width: 100%;
  min-height: 38px;
  padding: 8px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  overflow-y: auto;
  white-space: pre-wrap;
  transition: border-color 0.2s ease;
  outline: none;
}

.highlight-editable-div:empty:before {
  content: attr(data-placeholder);
  color: #aaa;
  pointer-events: none;
}

.highlight-editable-div.is-focused {
  box-shadow: 0 0 0 2px rgba(0, 119, 255, 0.1);
}

/* 确保高亮样式生效 */
:deep(.highlighted-char) {
  display: inline;
}
</style> 