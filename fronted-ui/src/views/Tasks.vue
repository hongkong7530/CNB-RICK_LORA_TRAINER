<template>
  <div class="tasks-page">
    <div class="tasks-container">
      <!-- 使用TaskList组件 -->
      <TaskList
        ref="taskListRef"
        :selectedTaskId="selectedTaskId"
        @select="handleTaskSelect"
        @update:tasks="allTasks = $event"
      />
      
      <!-- 任务详情区域 -->
      <div class="task-detail-container" v-if="selectedTaskId">
        <router-view />
      </div>
      
      <!-- 无选中任务时的空状态 -->
      <div class="empty-state" v-else>
        <div class="empty-content">
          <DocumentIcon class="empty-icon" />
          <h3>请选择任务</h3>
          <p>在左侧列表中选择一个任务查看详情，或创建新任务</p>
          <button class="mac-btn primary" @click="openCreateTaskModal">
            <PlusIcon class="btn-icon" />
            新建任务
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  DocumentIcon,
  PlusIcon
} from '@heroicons/vue/24/outline'
import TaskList from '@/components/tasks/TaskList.vue'

const route = useRoute()
const router = useRouter()

// 状态
const allTasks = ref([])
const taskListRef = ref(null)

// 当前选中的任务ID（从路由参数获取）
const selectedTaskId = computed(() => route.params.id || 0)

// 处理任务选择
const handleTaskSelect = (task, deleteContext) => {
  if (task) {
    // 导航到任务详情页
    router.push(`/tasks/${task.id}`)
  } else {
    // 任务被删除时的智能处理逻辑
    handleTaskDeleted(deleteContext)
  }
}

// 处理任务删除后的智能选择逻辑
const handleTaskDeleted = (deleteContext) => {
  if (!deleteContext) {
    // 如果没有删除上下文，回到空状态
    router.push('/tasks')
    return
  }
  
  const { deletedTaskId, tasksBeforeDelete, tasksAfterDelete } = deleteContext
  
  // 如果删除后还有任务，智能选择下一个任务
  if (tasksAfterDelete && tasksAfterDelete.length > 0) {
    // 在删除前的任务列表中找到被删除任务的位置
    const deletedIndex = tasksBeforeDelete.findIndex(task => task.id === deletedTaskId)
    
    let nextTask = null
    if (deletedIndex !== -1) {
      // 找到了被删除任务的位置，智能选择下一个任务
      if (deletedIndex < tasksAfterDelete.length) {
        // 选择原位置的任务（实际上是原来的下一个任务）
        nextTask = tasksAfterDelete[deletedIndex]
      } else if (tasksAfterDelete.length > 0) {
        // 如果删除的是最后一个，选择新的最后一个任务
        nextTask = tasksAfterDelete[tasksAfterDelete.length - 1]
      }
    } else {
      // 如果没找到位置，选择第一个任务
      nextTask = tasksAfterDelete[0]
    }
    
    if (nextTask) {
      router.push(`/tasks/${nextTask.id}`)
      return
    }
  }
  
  // 如果没有任务了，回到空状态页面
  router.push('/tasks')
}

// 打开创建任务模态框
const openCreateTaskModal = () => {
  if (taskListRef.value) {
    taskListRef.value.showTaskModal = true
  }
}

</script>

<style scoped>
.tasks-page {
  height: 100%;
  padding: 20px;
}

.tasks-container {
  display: flex;
  height: 100%;
  gap: 20px;
}

.task-detail-container {
  flex: 1;
  overflow: auto;
  min-width: 0;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  min-width: 0;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  max-width: 400px;
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.empty-content h3 {
  font-size: 18px;
  margin: 0 0 8px 0;
}

.empty-content p {
  color: var(--text-secondary);
  margin: 0 0 24px 0;
  line-height: 1.5;
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

.btn-icon {
  width: 16px;
  height: 16px;
}
</style> 