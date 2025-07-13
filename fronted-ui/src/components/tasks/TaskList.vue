<template>
  <div class="task-list-sidebar">
    <div class="sidebar-header">
      <h2 class="sidebar-title">任务列表</h2>
      <div class="header-actions">
        <button 
          v-if="selectedTaskIds.length > 0"
          class="batch-action-btn primary"
          @click="confirmBatchMark"
          title="批量提交标记选中的任务"
        >
          <TagIcon class="icon" />
          提交标记({{ selectedTaskIds.length }})
        </button>
        <button 
          v-if="selectedTaskIds.length > 0"
          class="batch-action-btn danger"
          @click="confirmBatchDelete"
          title="批量删除选中的任务"
        >
          <TrashIcon class="icon" />
          删除({{ selectedTaskIds.length }})
        </button>
        <button 
          class="new-task-btn"
          @click="openCreateModal"
          title="新建任务"
        >
          <PlusIcon class="icon" />
        </button>
      </div>
    </div>
    
    <!-- 搜索和过滤区域 -->
    <div class="search-filter-area">
      <div class="search-box">
        <MagnifyingGlassIcon class="search-icon" />
        <input 
          v-model="searchQuery"
          type="text" 
          placeholder="搜索任务..." 
          class="search-input"
          @input="handleSearch"
        >
      </div>
      
      <div class="filter-row">
        <select 
          v-model="statusFilter" 
          class="filter-select"
          @change="handleFilterChange"
        >
          <option value="">全部状态</option>
          <option value="NEW">新建</option>
          <option value="SUBMITTED">已提交</option>
          <option value="MARKING">标记中</option>
          <option value="MARKED">已标记</option>
          <option value="TRAINING">训练中</option>
          <option value="COMPLETED">已完成</option>
          <option value="ERROR">错误</option>
        </select>

        <select 
          v-model="dateFilter" 
          class="filter-select"
          @change="handleFilterChange"
        >
          <option value="">全部时间</option>
          <option value="today">今天</option>
          <option value="week">本周</option>
          <option value="month">本月</option>
        </select>
      </div>
    </div>
    
    <div class="task-count">
      <div class="count-info">共 {{ tasks.length }} 个任务</div>
      <div class="selection-actions" v-if="tasks.length > 0">
        <Checkbox 
          v-model="allSelected"
          :indeterminate="isIndeterminate"
        >
          {{ isAllSelected ? '取消全选' : '全选' }}
        </Checkbox>
      </div>
    </div>
    
    <!-- 任务列表 -->
    <div class="task-list">
      <div 
        v-for="task in tasks" 
        :key="task.id"
        class="task-list-item"
        :class="{ 'selected': selectedTaskId == task.id }"
        @click="selectTask(task)"
      >
        <div class="task-checkbox" @click.stop>
          <Checkbox 
            :model-value="selectedTaskIds.includes(task.id)"
            @update:model-value="(checked) => updateTaskSelection(task, checked)"
          />
        </div>
        <div class="task-icon">
          <component :is="getStatusIcon(task.status)" class="status-icon" />
        </div>
        <div class="task-item-content">
          <div class="task-name text-ellipsis">{{ task.name }}</div>
          <div class="task-meta">
            <span class="task-status" :class="getStatusClass(task.status)">
              {{ getStatusText(task.status) }}
            </span>
            <span class="task-date">{{ formatDate(task.created_at) }}</span>
          </div>
        </div>
        <div class="task-actions">
          <button 
            v-if="canEditTask(task)"
            class="action-btn edit-btn"
            @click.stop="openEditModal(task)"
            title="编辑任务"
          >
            <PencilIcon class="action-icon" />
          </button>
          <button 
            v-if="canDeleteTask(task)"
            class="action-btn delete-btn"
            @click.stop="confirmDelete(task)"
            title="删除任务"
          >
            <TrashIcon class="action-icon" />
          </button>
        </div>
      </div>
      
      <!-- 无任务时显示提示 -->
      <div v-if="tasks.length === 0" class="empty-list">
        <p>暂无任务</p>
      </div>
    </div>

    <!-- 任务模态框 -->
    <BaseModal
      v-model="showTaskModal"
      :title="isEditMode ? '编辑任务' : '新建训练任务'"
      :loading="isProcessing"
      @confirm="handleTaskSubmit"
    >
      <template #body>
        <div class="form-group">
          <label for="taskName">任务名称</label>
          <input
            id="taskName"
            v-model="currentTask.name"
            type="text"
            placeholder="输入任务名称"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label for="taskDescription">任务描述 (可选)</label>
          <textarea
            id="taskDescription"
            v-model="currentTask.description"
            placeholder="输入任务描述"
            class="form-textarea"
            rows="3"
          ></textarea>
        </div>
        <div class="form-group">
          <Checkbox v-model="currentTask.auto_training">
            自动训练（提交后自动打标并训练）
          </Checkbox>
        </div>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { 
  MagnifyingGlassIcon, 
  PlusIcon,
  DocumentIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  TagIcon,
  XCircleIcon,
  TrashIcon,
  ArrowUpCircleIcon,
  PencilIcon
} from '@heroicons/vue/24/outline'
import { tasksApi } from '@/api/tasks'
import { formatDate } from '@/utils/datetime'
import message from '@/utils/message'
import { emitter } from '@/utils/eventBus'
import { 
  getStatusText as getStatusTextUtil, 
  getStatusClass as getStatusClassUtil, 
  canDeleteTask as canDelete,
  statusDetailColorMap
} from '@/utils/taskStatus'
import BaseModal from '@/components/common/Modal.vue'
import Checkbox from '@/components/common/Checkbox.vue'

const route = useRoute()

const props = defineProps({
  selectedTaskId: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['select', 'create', 'update:tasks'])

// 状态
const tasks = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const dateFilter = ref('')
const selectedTaskIds = ref([]) // 多选模式下选中的任务ID
const showTaskModal = ref(false) // 任务模态框显示状态
const currentTask = ref({ id: 0, name: '', description: '', auto_training: false }) // 当前操作的任务
const isProcessing = ref(false) // 处理中状态
const isEditMode = ref(false) // 是否为编辑模式

// 判断当前是否在任务相关页面
const isTasksRoute = computed(() => {
  return route.path === '/tasks' || route.path.startsWith('/tasks/')
})

// 获取任务列表
const fetchTasks = async () => {
  // 只有在任务相关路由下才获取任务列表
  if (!isTasksRoute.value) return
  try {
    const data = await tasksApi.getTasks({
      status: statusFilter.value,
      search: searchQuery.value,
      date: dateFilter.value
    })
    
    tasks.value = data
    emit('update:tasks', data)
    
    // 如果有任务但没有选中的任务，默认选择第一个
    if (tasks.value.length > 0 && !props.selectedTaskId && isTasksRoute.value) {
      selectTask(tasks.value[0])
    }

    // 过滤选中任务ID，确保它们都存在于当前任务列表中
    selectedTaskIds.value = selectedTaskIds.value.filter(id => 
      tasks.value.some(task => task.id === id)
    )
  } catch (error) {
    message.error('获取任务列表失败')
  }
}

// 处理搜索和过滤
const handleSearch = () => {
  fetchTasks()
}

const handleFilterChange = () => {
  fetchTasks()
}

// 选择任务
const selectTask = (task) => {
  // 只有在任务相关页面才触发选择事件
  if (isTasksRoute.value) {
    emit('select', task)
  }
}

// 删除任务
const handleDeleteTask = async (taskId) => {
  try {
    // 删除前先记录当前任务状态和任务列表，用于智能选择
    const wasCurrentTask = props.selectedTaskId === taskId
    const tasksBeforeDelete = [...tasks.value] // 保存删除前的任务列表
    
    await tasksApi.deleteTask(taskId)
    message.success('任务已删除')
    
    // 先刷新任务列表，获取最新的任务状态
    await fetchTasks()
    
    // 如果删除的是当前正在查看的任务，通知父组件进行智能选择
    if (wasCurrentTask) {
      // 传递删除前的任务列表和被删除的任务ID，帮助父组件智能选择
      emit('select', null, { 
        deletedTaskId: taskId, 
        tasksBeforeDelete,
        tasksAfterDelete: tasks.value 
      })
    }

    // 从选中列表中移除
    selectedTaskIds.value = selectedTaskIds.value.filter(id => id !== taskId)
  } catch (error) {
    message.error('删除任务失败')
  }
}

// 批量删除任务
const handleBatchDeleteTasks = async () => {
  if (selectedTaskIds.value.length === 0) return
  
  try {
    // 删除前先记录当前任务是否在删除列表中和任务列表
    const wasCurrentTaskDeleted = selectedTaskIds.value.includes(props.selectedTaskId)
    const tasksBeforeDelete = [...tasks.value] // 保存删除前的任务列表
    const deletedTaskIds = [...selectedTaskIds.value] // 保存要删除的任务ID列表
    
    // 调用API批量删除任务
    await Promise.all(selectedTaskIds.value.map(id => tasksApi.deleteTask(id)))
    message.success(`成功删除 ${selectedTaskIds.value.length} 个任务`)
    
    // 清空选中列表
    selectedTaskIds.value = []
    
    // 先刷新任务列表，获取最新状态
    await fetchTasks()
    
    // 如果当前查看的任务被删除，通知父组件进行智能选择
    if (wasCurrentTaskDeleted) {
      emit('select', null, {
        deletedTaskId: props.selectedTaskId,
        deletedTaskIds,
        tasksBeforeDelete,
        tasksAfterDelete: tasks.value
      })
    }
  } catch (error) {
    message.error('批量删除任务失败')
  }
}

// 获取状态图标
const getStatusIcon = (status) => {
  const iconMap = {
    'NEW': DocumentIcon,
    'SUBMITTED': ArrowUpCircleIcon,
    'MARKING': TagIcon,
    'MARKED': CheckCircleIcon,
    'TRAINING': ArrowPathIcon,
    'COMPLETED': CheckCircleIcon,
    'ERROR': XCircleIcon
  }
  return iconMap[status] || ExclamationCircleIcon
}

// 使用统一的状态文本方法
const getStatusText = (status) => {
  return getStatusTextUtil(status)
}

// 使用统一的状态样式类方法
const getStatusClass = (status) => {
  return getStatusClassUtil(status)
}

// 判断任务是否可以删除
const canDeleteTask = (task) => {
  return canDelete(task)
}

// 判断任务是否可以编辑
const canEditTask = (task) => {
  // 只有NEW状态的任务才能编辑
  return task.status === 'NEW'
}

// 确认删除任务
const confirmDelete = (task) => {
  if (confirm(`确定要删除任务 "${task.name}" 吗？`)) {
    handleDeleteTask(task.id)
  }
}

// 确认批量删除任务
const confirmBatchDelete = () => {
  if (selectedTaskIds.value.length === 0) return
  
  if (confirm(`确定要删除选中的 ${selectedTaskIds.value.length} 个任务吗？`)) {
    handleBatchDeleteTasks()
  }
}

// 确认批量提交标记
const confirmBatchMark = () => {
  if (selectedTaskIds.value.length === 0) return
  
  if (confirm(`确定要提交选中的 ${selectedTaskIds.value.length} 个任务进行标记吗？`)) {
    handleBatchMark()
  }
}

// 批量提交标记
const handleBatchMark = async () => {
  if (selectedTaskIds.value.length === 0) return
  
  try {
    const result = await tasksApi.batchStartMarking(selectedTaskIds.value)
    message.success(`成功提交 ${result.task_ids.length} 个任务进行标记`)
    
    // 刷新任务列表
    fetchTasks()
  } catch (error) {
    console.log('提交标记失败',error)
  }
}

// 切换选择单个任务
const toggleTaskSelection = (task) => {
  const index = selectedTaskIds.value.indexOf(task.id)
  if (index === -1) {
    selectedTaskIds.value.push(task.id)
  } else {
    selectedTaskIds.value.splice(index, 1)
  }
}

// 更新任务选择状态
const updateTaskSelection = (task, checked) => {
  const index = selectedTaskIds.value.indexOf(task.id)
  if (checked && index === -1) {
    selectedTaskIds.value.push(task.id)
  } else if (!checked && index !== -1) {
    selectedTaskIds.value.splice(index, 1)
  }
}

// 全选计算属性
const isAllSelected = computed(() => {
  return tasks.value.length > 0 && selectedTaskIds.value.length === tasks.value.length
})

// 部分选择计算属性
const isIndeterminate = computed(() => {
  return selectedTaskIds.value.length > 0 && selectedTaskIds.value.length < tasks.value.length
})

// 全选的双向绑定计算属性
const allSelected = computed({
  get: () => isAllSelected.value,
  set: (value) => {
    if (value) {
      selectedTaskIds.value = tasks.value.map(task => task.id) // 全选
    } else {
      selectedTaskIds.value = [] // 取消全选
    }
  }
})

// 切换全选/取消全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedTaskIds.value = [] // 取消全选
  } else {
    selectedTaskIds.value = tasks.value.map(task => task.id) // 全选
  }
}

// 打开编辑任务模态框
const openEditModal = (task) => {
  currentTask.value = { 
    id: task.id,
    name: task.name, 
    description: task.description || '',
    auto_training: task.auto_training || false
  }
  isEditMode.value = true
  showTaskModal.value = true
}

// 打开新建任务模态框
const openCreateModal = () => {
  currentTask.value = { id: 0, name: '', description: '', auto_training: false }
  isEditMode.value = false
  showTaskModal.value = true
}

// 处理任务提交
const handleTaskSubmit = async () => {
  if (!currentTask.value.name) {
    message.warning('请输入任务名称')
    return
  }

  try {
    isProcessing.value = true
    
    if (isEditMode.value) {
      // 编辑模式：调用API更新任务
      await tasksApi.updateTask(currentTask.value.id, {
        name: currentTask.value.name,
        description: currentTask.value.description,
        auto_training: currentTask.value.auto_training
      })
      message.success('任务已更新')
    } else {
      // 创建模式：调用API创建任务
      const createdTask = await tasksApi.createTask(currentTask.value)
      message.success('任务创建成功')
      
      // 选择新创建的任务
      if (createdTask && createdTask.id) {
        selectTask(createdTask)
      }
    }
    
    // 重置表单
    currentTask.value = { id: 0, name: '', description: '', auto_training: false }
    showTaskModal.value = false
    isEditMode.value = false
    
    // 刷新任务列表
    fetchTasks()
  } catch (error) {
    console.error('处理任务失败:', error)
    message.error(isEditMode.value ? '编辑任务失败' : '创建任务失败')
  } finally {
    isProcessing.value = false
  }
}

// 监听selectedTaskId变化
watch(() => props.selectedTaskId, (newId) => {
  // 如果selectedTaskId被清空且有任务，则选择第一个
  if (!newId && tasks.value.length > 0 && isTasksRoute.value) {
    selectTask(tasks.value[0])
  }
})

// 监听路由变化
watch(() => route.path, (newPath) => {
  // 如果进入任务页面，则获取任务列表
  if (newPath === '/tasks' || newPath.startsWith('/tasks/')) {
    fetchTasks()
  }
}, { immediate: true })

// 组件挂载时获取任务列表并添加事件监听
onMounted(() => {
  // 监听任务状态变化事件
  emitter.on('task-status-changed', (taskId) => {
    console.log('收到任务状态变化事件:', taskId)
    fetchTasks() // 刷新任务列表
  })
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  emitter.off('task-status-changed')
})

// 暴露方法给父组件
defineExpose({
  fetchTasks,
  showTaskModal
})
</script>

<style scoped>
/* 左侧任务列表侧边栏 */
.task-list-sidebar {
  width: 350px;
  display: flex;
  flex-direction: column;
  background: var(--background-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.new-task-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: var(--primary-color);
  border: none;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.new-task-btn:hover {
  background: color-mix(in srgb, var(--primary-color) 80%, white);
}

.batch-action-btn {
  height: 32px;
  border-radius: 6px;
  border: none;
  padding: 0 10px;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.batch-action-btn.primary {
  background-color: #EFF6FF;
  color: #3B82F6;
}

.batch-action-btn.primary:hover {
  background-color: #EFF6FF;
}

.batch-action-btn.danger {
  background-color: #fee2e2;
  color: #dc2626;
}

.batch-action-btn.danger:hover {
  background-color: #fecaca;
}

.icon {
  width: 16px;
  height: 16px;
}

.search-filter-area {
  padding: 12px;
  border-bottom: 1px solid var(--border-color-light);
}

.search-box {
  position: relative;
  margin-bottom: 8px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  color: var(--text-secondary);
}

.search-input {
  width: 100%;
  height: 32px;
  padding: 0 10px 0 30px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  background: var(--background-secondary);
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  background: var(--background-primary);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.1);
}

.filter-row {
  display: flex;
  gap: 8px;
}

.filter-select {
  flex: 1;
  height: 30px;
  padding: 0 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 12px;
  background: var(--background-secondary);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 6px center;
  background-size: 12px;
}

.filter-select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.task-count {
  padding: 8px 16px;
  font-size: 12px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selection-actions {
  display: flex;
  align-items: center;
}

.select-all-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  cursor: pointer;
  user-select: none;
}

.select-all-checkbox {
  cursor: pointer;
}

.task-list {
  flex: 1;
  overflow-y: auto;
}

.task-list-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.task-list-item:hover {
  background: var(--background-secondary);
}

.task-list-item:hover .task-actions {
  opacity: 1;
}

.task-list-item.selected {
  background: color-mix(in srgb, var(--primary-color) 15%, transparent);
  border-left: 3px solid var(--primary-color);
  padding-left: 9px; /* 补偿边框宽度 */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.task-checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-select-checkbox {
  cursor: pointer;
}

.task-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--background-secondary);
}

.status-icon {
  width: 14px;
  height: 14px;
}

.task-item-content {
  flex: 1;
  min-width: 0;
}

.task-name {
  font-weight: 500;
  font-size: 13px;
  margin-bottom: 3px;
}

.task-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
}

.task-status {
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.task-status.new {
  background-color: v-bind('statusDetailColorMap.NEW.background');
  color: v-bind('statusDetailColorMap.NEW.color');
}

.task-status.submitted {
  background-color: v-bind('statusDetailColorMap.SUBMITTED.background');
  color: v-bind('statusDetailColorMap.SUBMITTED.color');
}

.task-status.marking {
  background-color: v-bind('statusDetailColorMap.MARKING.background');
  color: v-bind('statusDetailColorMap.MARKING.color');
}

.task-status.marked {
  background-color: v-bind('statusDetailColorMap.MARKED.background');
  color: v-bind('statusDetailColorMap.MARKED.color');
}

.task-status.training {
  background-color: v-bind('statusDetailColorMap.TRAINING.background');
  color: v-bind('statusDetailColorMap.TRAINING.color');
}

.task-status.completed {
  background-color: v-bind('statusDetailColorMap.COMPLETED.background');
  color: v-bind('statusDetailColorMap.COMPLETED.color');
}

.task-status.error {
  background-color: v-bind('statusDetailColorMap.ERROR.background');
  color: v-bind('statusDetailColorMap.ERROR.color');
}

.task-date {
  color: var(--text-tertiary);
}

.task-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.action-btn {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.edit-btn {
  color: #3B82F6;
}

.edit-btn:hover {
  background: #EFF6FF;
}

.delete-btn {
  color: #EF4444;
}

.delete-btn:hover {
  background: #FEE2E2;
  color: #DC2626;
}

.action-icon {
  width: 14px;
  height: 14px;
}

.empty-list {
  display: flex;
  justify-content: center;
  padding: 30px 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

/* 滚动条样式 */
.task-list::-webkit-scrollbar {
  width: 6px;
}

.task-list::-webkit-scrollbar-track {
  background: transparent;
}

.task-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.task-list::-webkit-scrollbar-thumb:hover {
  background: var(--border-color-dark);
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 14px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background: var(--background-secondary);
  transition: all 0.3s ease;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  background: var(--background-primary);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  user-select: none;
}
</style> 