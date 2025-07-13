<template>
  <div 
    class="file-manager"
    @dragenter.prevent="handleDragEnter"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <!-- 拖放上传提示覆盖层 -->
    <div class="drag-overlay" :class="{ 'active': isDragging }">
      <ArrowUpTrayIcon class="drag-icon" />
      <p>释放文件以上传到当前文件夹</p>
    </div>
    
    <!-- 工具栏 -->
    <div class="toolbar">
      <!-- 导航和路径 -->
      <div class="navigation">
        <button class="nav-btn" @click="navigateToParent" :disabled="!currentPath || currentPath === '/'">
          <ArrowUpIcon class="btn-icon" />
        </button>
        <button class="nav-btn" @click="refreshDirectory">
          <ArrowPathIcon class="btn-icon" />
        </button>
        <div class="path-breadcrumb">
          <span class="path-root" @click="navigateTo('/')">根目录</span>
          <template v-for="(segment, index) in pathSegments" :key="index">
            <span class="path-separator">/</span>
            <span 
              class="path-segment" 
              @click="navigateToSegment(index)"
            >{{ segment }}</span>
          </template>
        </div>
        <button class="nav-btn copy-path-btn" @click="copyCurrentPath" title="复制当前路径">
          <ClipboardDocumentIcon class="btn-icon" />
        </button>
      </div>
      
      <!-- 搜索和视图切换 -->
      <div class="actions">
        <div class="search-box">
          <MagnifyingGlassIcon class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索文件..." 
            class="search-input"
          >
        </div>
        <div class="view-toggle">
          <button 
            class="view-btn" 
            :class="{ active: viewMode === 'grid' }" 
            @click="viewMode = 'grid'"
          >
            <Squares2X2Icon class="btn-icon" />
          </button>
          <button 
            class="view-btn" 
            :class="{ active: viewMode === 'list' }" 
            @click="viewMode = 'list'"
          >
            <ListBulletIcon class="btn-icon" />
          </button>
        </div>
        <label class="upload-btn" :class="{ 'uploading': uploading.value }">
          <template v-if="!uploading.value">
            <ArrowUpTrayIcon class="btn-icon" />
            <span>上传</span>
          </template>
          <template v-else>
            <div class="btn-spinner"></div>
            <span>上传中...</span>
          </template>
          <input 
            type="file" 
            @change="uploadFile" 
            class="hidden-input"
            :disabled="uploading.value"
          >
        </label>
      </div>
    </div>
    
    <!-- 文件列表 -->
    <div 
      class="file-list-container"
    >
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="showEmptyState" class="empty-state">
        <FolderOpenIcon class="empty-icon" />
        <p v-if="searchQuery">没有找到匹配的文件或文件夹</p>
        <p v-else>此文件夹为空</p>
      </div>
      
      <!-- 网格视图 -->
      <div v-else-if="viewMode === 'grid'" class="grid-view">
        <!-- 文件夹 -->
        <div 
          v-for="dir in filteredDirectories" 
          :key="dir.path" 
          class="grid-item directory"
          @dblclick="handleItemDoubleClick(dir)"
          @contextmenu.prevent="showContextMenu($event, dir)"
          @dragenter.prevent="handleDragEnterItem($event, dir)"
          @dragover.prevent="handleDragOverItem($event, dir)"
          @dragleave.prevent="handleDragLeaveItem($event, dir)"
          @drop.prevent="handleDropOnItem($event, dir)"
          :class="{ 'drag-over': dragOverItem === dir.path }"
        >
          <FolderIcon class="item-icon directory-icon" />
          <span class="item-name" @click="handleItemNameClick($event, dir)">{{ dir.name }}</span>
        </div>
        
        <!-- 文件 -->
        <div 
          v-for="file in filteredFiles" 
          :key="file.path" 
          class="grid-item file"
          @dblclick="handleItemDoubleClick(file)"
          @contextmenu.prevent="showContextMenu($event, file)"
        >
          <component :is="getFileIcon(file)" class="item-icon file-icon" />
          <span class="item-name" @click="handleItemNameClick($event, file)">{{ file.name }}</span>
          <span class="item-size">{{ formatSize(file.size) }}</span>
        </div>
      </div>
      
      <!-- 列表视图 -->
      <table v-else class="list-view">
        <thead>
          <tr>
            <th class="th-name" @click="sortBy('name')">
              名称
              <ChevronUpDownIcon v-if="sortField !== 'name'" class="sort-icon" />
              <ChevronUpIcon v-else-if="sortOrder === 'asc'" class="sort-icon" />
              <ChevronDownIcon v-else class="sort-icon" />
            </th>
            <th class="th-size" @click="sortBy('size')">
              大小
              <ChevronUpDownIcon v-if="sortField !== 'size'" class="sort-icon" />
              <ChevronUpIcon v-else-if="sortOrder === 'asc'" class="sort-icon" />
              <ChevronDownIcon v-else class="sort-icon" />
            </th>
            <th class="th-modified" @click="sortBy('modified_time')">
              修改时间
              <ChevronUpDownIcon v-if="sortField !== 'modified_time'" class="sort-icon" />
              <ChevronUpIcon v-else-if="sortOrder === 'asc'" class="sort-icon" />
              <ChevronDownIcon v-else class="sort-icon" />
            </th>
          </tr>
        </thead>
        <tbody>
          <!-- 文件夹 -->
          <tr 
            v-for="dir in filteredDirectories" 
            :key="dir.path" 
            class="list-item directory"
            @dblclick="handleItemDoubleClick(dir)"
            @contextmenu.prevent="showContextMenu($event, dir)"
            @dragenter.prevent="handleDragEnterItem($event, dir)"
            @dragover.prevent="handleDragOverItem($event, dir)"
            @dragleave.prevent="handleDragLeaveItem($event, dir)"
            @drop.prevent="handleDropOnItem($event, dir)"
            :class="{ 'drag-over': dragOverItem === dir.path }"
          >
            <td class="td-name">
              <div class="name-cell">
                <FolderIcon class="item-icon directory-icon" />
                <span @click="handleItemNameClick($event, dir)">{{ dir.name }}</span>
              </div>
            </td>
            <td class="td-size">-</td>
            <td class="td-modified">{{ formatDate(dir.modified_time) }}</td>
          </tr>
          
          <!-- 文件 -->
          <tr 
            v-for="file in filteredFiles" 
            :key="file.path" 
            class="list-item file"
            @dblclick="handleItemDoubleClick(file)"
            @contextmenu.prevent="showContextMenu($event, file)"
          >
            <td class="td-name">
              <div class="name-cell">
                <component :is="getFileIcon(file)" class="item-icon file-icon" />
                <span @click="handleItemNameClick($event, file)">{{ file.name }}</span>
              </div>
            </td>
            <td class="td-size">{{ formatSize(file.size) }}</td>
            <td class="td-modified">{{ formatDate(file.modified_time) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 使用新的右键菜单组件 -->
    <ContextMenu
      v-model:show="contextMenu.show"
      :top="contextMenu.top"
      :left="contextMenu.left"
      :menu-items="getContextMenuItems(contextMenu.item)"
      @select="handleContextMenuSelect"
    />
    
    <!-- 删除确认对话框 -->
    <BaseModal
      v-model="deleteDialog.show"
      :title="deleteDialog.title"
      @confirm="deleteItem"
      :confirm-text="'删除'"
      :cancel-text="'取消'"
    >
      <template #body>
        <p>{{ deleteDialog.message }}</p>
        <p class="text-red-500 mt-2">此操作不可恢复，请谨慎操作！</p>
      </template>
      <template #footer>
        <button class="mac-btn" @click="deleteDialog.show = false">取消</button>
        <button class="mac-btn danger" @click="deleteItem">删除</button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { format } from 'date-fns'
import message from '@/utils/message'
import { terminalApi } from '@/api/terminal'
import BaseModal from '@/components/common/Modal.vue'
import ContextMenu from '@/components/common/ContextMenu.vue'
import {
  FolderIcon,
  DocumentIcon,
  ArrowUpIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  Squares2X2Icon,
  ListBulletIcon,
  FolderOpenIcon,
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  ChevronUpDownIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  PhotoIcon,
  FilmIcon,
  MusicalNoteIcon,
  DocumentTextIcon,
  DocumentChartBarIcon,
  ArchiveBoxIcon,
  CodeBracketIcon,
  ClipboardDocumentIcon,
  TrashIcon,
  CubeIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  asset: {
    type: Object,
    required: true
  }
})

// 状态变量
const currentPath = ref('/')
const directories = ref([])
const files = ref([])
const loading = ref(false)
const searchQuery = ref('')
const viewMode = ref('grid')  // 'grid' 或 'list'
const sortField = ref('name')
const sortOrder = ref('asc')  // 'asc' 或 'desc'

// 添加上传状态变量
const uploading = ref(false)

// 拖放上传相关状态
const isDragging = ref(false)
const dragOverItem = ref(null)
const dragEnterTarget = ref(null)

// 右键菜单
const contextMenu = ref({
  show: false,
  top: 0,
  left: 0,
  item: null
})

// 删除对话框
const deleteDialog = ref({
  show: false,
  title: '',
  message: '',
  item: null
})

// 计算属性：路径段
const pathSegments = computed(() => {
  if (!currentPath.value || currentPath.value === '/') return []
  return currentPath.value.split('/').filter(Boolean)
})

// 计算属性：过滤后的文件和目录
const filteredDirectories = computed(() => {
  if (!searchQuery.value) return directories.value
  const query = searchQuery.value.toLowerCase()
  return directories.value.filter(dir => 
    dir.name.toLowerCase().includes(query)
  )
})

const filteredFiles = computed(() => {
  if (!searchQuery.value) return files.value
  const query = searchQuery.value.toLowerCase()
  return files.value.filter(file => 
    file.name.toLowerCase().includes(query)
  )
})

// 计算属性：是否显示空状态
const showEmptyState = computed(() => {
  return !loading.value && filteredDirectories.value.length === 0 && filteredFiles.value.length === 0
})

// 生命周期钩子
onMounted(() => {
  loadDirectory(currentPath.value)
})

// 组件卸载时清理
onBeforeUnmount(() => {
  // 不再需要移除全局点击事件监听器，由ContextMenu组件处理
})

// 监听器
watch(() => props.asset, () => {
  if (props.asset) {
    loadDirectory(currentPath.value)
  }
})

// 方法
const loadDirectory = async (path) => {
  if (!props.asset?.id) return
  
  loading.value = true
  try {
    const response = await terminalApi.browseDirectory(
      props.asset.id, 
      path, 
      sortField.value, 
      sortOrder.value
    )
    currentPath.value = response.path
    directories.value = response.directories || []
    files.value = response.files || []
  } catch (error) {
    console.error('加载目录失败:', error)
  } finally {
    loading.value = false
  }
}

const navigateTo = (path) => {
  loadDirectory(path)
}

const navigateToParent = () => {
  if (!currentPath.value || currentPath.value === '/') return
  
  const parentPath = currentPath.value.split('/').slice(0, -1).join('/')
  navigateTo(parentPath || '/')
}

const navigateToSegment = (index) => {
  const path = '/' + pathSegments.value.slice(0, index + 1).join('/')
  navigateTo(path)
}

const refreshDirectory = () => {
  loadDirectory(currentPath.value)
}

const sortBy = (field) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'asc'
  }
  loadDirectory(currentPath.value)
}

const showContextMenu = (event, item) => {
  // 阻止事件冒泡
  event.stopPropagation()
  event.preventDefault()
  
  // 计算菜单位置，确保不会超出视口
  // 让菜单靠近鼠标点击位置
  const x = Math.min(event.clientX, window.innerWidth - 160) // 菜单宽度约160px
  const y = Math.min(event.clientY, window.innerHeight - 200) // 预留200px高度
  
  contextMenu.value = {
    show: true,
    top: y,
    left: x,
    item
  }
}

// 根据右键点击的项目，获取菜单项配置
const getContextMenuItems = (item) => {
  if (!item) return []
  
  const menuItems = []
  
  // 文件夹特有菜单项
  if (item.is_dir) {
    menuItems.push({
      type: 'item',
      id: 'open',
      label: '打开',
      icon: FolderOpenIcon,
      data: item
    })
  }
  
  // 通用菜单项
  menuItems.push({
    type: 'item',
    id: 'copy-name',
    label: '复制名称',
    icon: ClipboardDocumentIcon,
    data: item
  })
  
  menuItems.push({
    type: 'item',
    id: 'copy-path',
    label: '复制路径',
    icon: ClipboardDocumentIcon,
    data: item
  })
  
  // 文件特有菜单项
  if (!item.is_dir) {
    menuItems.push({
      type: 'item',
      id: 'download',
      label: '下载',
      icon: ArrowDownTrayIcon,
      data: item
    })
  }
  
  // 分割线
  menuItems.push({ type: 'divider' })
  
  // 删除菜单项
  menuItems.push({
    type: 'item',
    id: 'delete',
    label: '删除',
    icon: TrashIcon,
    className: 'danger',
    data: item
  })
  
  return menuItems
}

// 处理右键菜单项点击
const handleContextMenuSelect = ({ id, data }) => {
  switch (id) {
    case 'open':
      navigateTo(data.path)
      break
    case 'copy-name':
      copyItemName(data)
      break
    case 'copy-path':
      copyItemPath(data)
      break
    case 'download':
      downloadFile(data)
      break
    case 'delete':
      confirmDeleteItem(data)
      break
  }
}

const previewFile = (file) => {
  // 根据文件类型执行不同操作
  const fileType = file.name.split('.').pop()?.toLowerCase()
  
  // 对于图片类型，可以考虑预览而不是直接下载
  const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
  if (imageTypes.includes(fileType)) {
    // 这里可以添加图片预览功能
    // 暂时仍然下载
    downloadFile(file)
  } else {
    // 其他类型文件直接下载
    downloadFile(file)
  }
}

const downloadFile = async (file) => {
  if (!props.asset?.id || !file?.path) return
  
  try {
    message.info(`正在下载: ${file.name}`)
    
    // 使用terminalApi下载文件
    const fileBlob = await terminalApi.downloadFile(props.asset.id, file.path)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(fileBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = file.name
    document.body.appendChild(link)
    link.click()
    
    // 清理
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
      document.body.removeChild(link)
    }, 0)
    
    message.success(`下载成功: ${file.name}`)
  } catch (error) {
    console.error('下载文件失败:', error)
    message.error(`下载失败: ${error.message}`)
  }
}

const uploadFile = async (event) => {
  const file = event.target.files[0]
  if (!file || uploading.value) return
  
  try {
    uploading.value = true
    await uploadSingleFile(file, currentPath.value)
  } finally {
    uploading.value = false
    // 清空input，允许再次上传相同文件
    event.target.value = ''
  }
}

// 根据文件类型获取对应的图标组件
const getFileIcon = (file) => {
  const extension = file.name.split('.').pop()?.toLowerCase() || ''
  
  // 图片文件
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(extension)) {
    return PhotoIcon
  }
  
  // 视频文件
  if (['mp4', 'webm', 'avi', 'mov', 'wmv', 'flv', 'mkv'].includes(extension)) {
    return FilmIcon
  }
  
  // 音频文件
  if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(extension)) {
    return MusicalNoteIcon
  }
  
  // 文档文件
  if (['doc', 'docx', 'txt', 'rtf', 'odt', 'pdf'].includes(extension)) {
    return DocumentTextIcon
  }
  
  // 表格和演示文件
  if (['xls', 'xlsx', 'csv', 'ppt', 'pptx'].includes(extension)) {
    return DocumentChartBarIcon
  }
  
  // 压缩文件
  if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(extension)) {
    return ArchiveBoxIcon
  }
  
  // 代码文件
  if (['js', 'ts', 'html', 'css', 'py', 'java', 'c', 'cpp', 'php', 'rb', 'go'].includes(extension)) {
    return CodeBracketIcon
  }
  
  // 可执行文件
  if (['exe', 'msi', 'bin', 'sh', 'bat', 'app'].includes(extension)) {
    return CubeIcon
  }
  
  // 默认文件图标
  return DocumentIcon
}

// 拖放相关方法
const handleDragEnter = (event) => {
  event.preventDefault()
  
  // 记录进入的元素
  dragEnterTarget.value = event.target
  
  // 只有当是从外部拖入时才设置isDragging
  if (!isDragging.value) {
    isDragging.value = true
  }
}

const handleDragOver = (event) => {
  event.preventDefault()
  // 拖动时保持状态，但不做额外处理
  // 这样可以减少状态变化导致的闪烁
}

const handleDragLeave = (event) => {
  event.preventDefault()
  
  // 只有当离开的元素是进入时的元素或者是其子元素时才重置状态
  // 这样可以避免在元素内部移动时触发不必要的状态变化
  if (dragEnterTarget.value === event.target) {
    isDragging.value = false
    dragEnterTarget.value = null
  }
}

const handleDrop = async (event) => {
  event.preventDefault()
  isDragging.value = false
  dragEnterTarget.value = null
  
  // 防止重复上传
  if (uploading.value) return
  
  const files = event.dataTransfer.files
  if (files.length === 0) return
  
  try {
    uploading.value = true
    
    // 上传所有文件到当前目录
    for (let i = 0; i < files.length; i++) {
      await uploadSingleFile(files[i], currentPath.value)
    }
  } finally {
    uploading.value = false
  }
}

const handleDragEnterItem = (event, dir) => {
  event.stopPropagation()
  dragOverItem.value = dir.path
}

const handleDragOverItem = (event, dir) => {
  // 阻止事件冒泡，避免触发父元素的dragover
  event.stopPropagation()
  event.preventDefault()
  
  // 保持状态，不做额外处理
}

const handleDragLeaveItem = (event, dir) => {
  // 检查是否真的离开了元素（而不是进入了子元素）
  if (!event.currentTarget.contains(event.relatedTarget)) {
    dragOverItem.value = null
  }
  
  event.stopPropagation()
}

const handleDropOnItem = async (event, dir) => {
  // 阻止事件冒泡
  event.stopPropagation()
  isDragging.value = false
  dragEnterTarget.value = null
  
  // 防止重复上传
  if (uploading.value) return
  
  const files = event.dataTransfer.files
  if (files.length === 0) return
  
  try {
    uploading.value = true
    
    // 上传所有文件到指定目录
    for (let i = 0; i < files.length; i++) {
      await uploadSingleFile(files[i], dir.path)
    }
  } finally {
    uploading.value = false
  }
}

const uploadSingleFile = async (file, targetPath) => {
  if (!props.asset?.id) {
    message.error('资产ID不存在')
    return
  }
  
  try {
    await terminalApi.uploadFile(
      props.asset.id,
      file,
      targetPath
    )
    console.log("上传成功")
    message.success(`上传成功: ${file.name}`)
    // 如果上传到当前目录，刷新显示
    if (targetPath === currentPath.value) {
      refreshDirectory()
    }
  } catch (error) {
    console.error('上传文件失败:', error)
  }
}

// 工具函数
const formatSize = (bytes) => {
  if (bytes === undefined || bytes === null) return '-'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    return format(new Date(dateStr), 'yyyy-MM-dd HH:mm')
  } catch (error) {
    return dateStr
  }
}

// 复制文件或文件夹名称
const copyItemName = (item) => {
  if (item?.name) {
    try {
      navigator.clipboard.writeText(item.name).then(() => {
        message.success(`已复制: ${item.name}`)
      }).catch(() => {
        // 如果clipboard API失败，使用传统方法
        fallbackCopyText(item.name)
      })
    } catch (error) {
      // 如果clipboard API不可用，使用传统方法
      fallbackCopyText(item.name)
    }
  }
}

// 传统复制文本方法
const fallbackCopyText = (text) => {
  const textArea = document.createElement("textarea")
  textArea.value = text
  textArea.style.position = "fixed"
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  
  try {
    document.execCommand('copy')
    message.success(`已复制: ${text}`)
  } catch (err) {
    message.error('复制失败')
  }
  
  document.body.removeChild(textArea)
}

// 修改grid视图的文件夹双击和名称点击处理
const handleItemNameClick = (event, item) => {
  // 阻止冒泡，防止触发父元素的双击事件
  event.stopPropagation()
}

const handleItemDoubleClick = (item) => {
  if (item.is_dir) {
    navigateTo(item.path)
  } else {
    previewFile(item)
  }
}

// 确认删除文件或文件夹
const confirmDeleteItem = (item) => {
  if (!item) return
  
  const isDir = item.is_dir
  const name = item.name
  
  deleteDialog.value = {
    show: true,
    title: `删除${isDir ? '文件夹' : '文件'}`,
    message: `确定要删除${isDir ? '文件夹' : '文件'} "${name}" 吗？${isDir ? '该文件夹及其所有内容将被删除。' : ''}`,
    item
  }
}

// 删除文件或文件夹
const deleteItem = async () => {
  const item = deleteDialog.value.item
  if (!item || !props.asset?.id) return
  
  try {
    message.info(`正在删除: ${item.name}`)
    
    await terminalApi.deleteRemoteFile(
      props.asset.id,
      item.path
    )
    message.success(`删除成功: ${item.name}`)
    // 刷新当前目录
    refreshDirectory()
  } catch (error) {
    console.error('删除失败:', error)
  } finally {
    deleteDialog.value.show = false
  }
}

// 复制当前路径
const copyCurrentPath = () => {
  try {
    navigator.clipboard.writeText(currentPath.value).then(() => {
      message.success(`已复制路径: ${currentPath.value}`)
    }).catch(() => {
      // 如果clipboard API失败，使用传统方法
      fallbackCopyText(currentPath.value)
    })
  } catch (error) {
    // 如果clipboard API不可用，使用传统方法
    fallbackCopyText(currentPath.value)
  }
}

// 复制文件或文件夹路径
const copyItemPath = (item) => {
  if (item?.path) {
    try {
      navigator.clipboard.writeText(item.path).then(() => {
        message.success(`已复制路径: ${item.path}`)
      }).catch(() => {
        // 如果clipboard API失败，使用传统方法
        fallbackCopyText(item.path)
      })
    } catch (error) {
      // 如果clipboard API不可用，使用传统方法
      fallbackCopyText(item.path)
    }
  }
}
</script>

<style scoped>
.file-manager {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

/* 拖放覆盖层 */
.drag-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--background-overlay-light);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
  border: 2px dashed var(--primary-color);
  border-radius: 8px;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
  pointer-events: none;
}

.drag-overlay.active {
  opacity: 1;
  visibility: visible;
}

.drag-icon {
  width: 48px;
  height: 48px;
  color: var(--primary-color);
  margin-bottom: 16px;
}

/* 拖放到文件夹上的样式 */
.drag-over {
  position: relative;
  background-color: color-mix(in srgb, var(--primary-color) 10%, transparent);
  border-radius: 8px;
  transition: all 0.2s ease;
}

/* 拖放到文件夹上的遮罩 - 使用伪元素避免影响内容布局 */
.drag-over::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px dashed var(--primary-color);
  border-radius: 8px;
  pointer-events: none;
  z-index: 1;
}

/* 工具栏样式 */
.toolbar {
  display: flex;
  gap: 8px;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: var(--background-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.navigation {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.nav-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--background-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.copy-path-btn:hover {
  color: var(--primary-color);
}

.nav-btn:hover:not(:disabled) {
  background: var(--background-tertiary);
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.path-breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  overflow: hidden;
  white-space: nowrap;
  padding: 0 8px;
  background: var(--background-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  height: 32px;
  flex: 1;
}

.path-root, .path-segment {
  color: var(--primary-color);
  cursor: pointer;
  transition: color 0.2s;
}

.path-root:hover, .path-segment:hover {
  color: color-mix(in srgb, var(--primary-color) 80%, black);
  text-decoration: underline;
}

.path-separator {
  color: var(--text-tertiary);
  margin: 0 4px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-box {
  position: relative;
  width: 200px;
}

.search-icon {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
}

.search-input {
  width: 100%;
  height: 32px;
  padding: 0 8px 0 32px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--background-secondary);
  color: var(--text-primary);
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 20%, transparent);
}

.view-toggle {
  display: flex;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  overflow: hidden;
}

.view-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background-secondary);
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.view-btn:hover {
  background: var(--background-tertiary);
}

.view-btn.active {
  background: var(--border-color);
}

.upload-btn {
  height: 32px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--primary-color);
  color: var(--text-primary-inverse);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn:hover:not(.uploading) {
  background: color-mix(in srgb, var(--primary-color) 90%, black);
}

.upload-btn.uploading {
  background: color-mix(in srgb, var(--primary-color) 60%, transparent);
  cursor: not-allowed;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: var(--text-primary-inverse);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.hidden-input {
  display: none;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* 文件列表容器 */
.file-list-container {
  flex: 1;
  overflow: auto;
  padding: 16px;
  position: relative;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: #6b7280;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: #6b7280;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: #9ca3af;
}

/* 网格视图 */
.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 16px;
}

.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
  box-sizing: border-box; /* 确保边框不会增加元素尺寸 */
}

.grid-item:hover {
  background: var(--background-tertiary);
}

.item-icon {
  width: 40px;
  height: 40px;
  margin-bottom: 8px;
}

.directory-icon {
  color: #f59e0b;
}

.file-icon {
  color: #6b7280;
}

.item-name {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  user-select: none;
}

.item-size {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
  user-select: none;
}

/* 列表视图 */
.list-view {
  width: 100%;
  border-collapse: collapse;
}

.list-view th {
  text-align: left;
  padding: 8px 16px;
  background: #f9fafb;
  border-bottom: 1px solid var(--border-color);
  font-weight: 500;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.list-view th:hover {
  background: var(--background-tertiary);
}

.th-name {
  width: 60%;
}

.th-size {
  width: 15%;
}

.th-modified {
  width: 25%;
}

.sort-icon {
  width: 16px;
  height: 16px;
  vertical-align: middle;
  margin-left: 4px;
}

.list-view td {
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-color);
}

.list-item {
  transition: all 0.2s ease;
  box-sizing: border-box; /* 确保边框不会增加元素尺寸 */
}

.list-item:hover {
  background: #f9fafb;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.td-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.td-size {
  white-space: nowrap;
  color: #6b7280;
}

.td-modified {
  white-space: nowrap;
  color: #6b7280;
}

/* 右键菜单 */
.context-menu {
  position: fixed;
  background: var(--background-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  z-index: 1000;
  min-width: 160px;
  max-width: 200px;
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.menu-item:hover {
  background: var(--background-tertiary);
}

.menu-item.delete:hover {
  background: #fee2e2;
  color: #b91c1c;
}

.menu-icon {
  width: 16px;
  height: 16px;
}

.menu-divider {
  height: 1px;
  background-color: var(--border-color);
  margin: 4px 0;
}

/* 菜单文本不可选 */
.menu-item-text {
  user-select: none;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .actions {
    justify-content: space-between;
  }
  
  .search-box {
    width: 100%;
  }
  
  .grid-view {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
}

.mac-btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--background-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.mac-btn:hover {
  background: var(--background-tertiary);
}

.mac-btn.danger {
  background: #ef4444;
  color: var(--text-primary-inverse);
  border-color: #ef4444;
}

.mac-btn.danger:hover {
  background: #dc2626;
}

.text-red-500 {
  color: #ef4444;
}

.mt-2 {
  margin-top: 8px;
}
</style> 