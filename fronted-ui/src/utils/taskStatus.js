export const statusTextMap = {
  'NEW': '新建',
  'SUBMITTED': '已提交',
  'MARKING': '标记中',
  'MARKED': '已标记',
  'TRAINING': '训练中',
  'COMPLETED': '已完成',
  'ERROR': '错误'
}

export const statusClassMap = {
  'NEW': 'new',
  'SUBMITTED': 'submitted',
  'MARKING': 'marking',
  'MARKED': 'marked',
  'TRAINING': 'training',
  'COMPLETED': 'completed',
  'ERROR': 'error'
}

export const statusDetailColorMap = {
  'NEW': {
    background: '#F0F9FF',
    color: '#0369A1'
  },
  'SUBMITTED': {
    background: '#F0F7FF',
    color: '#1D4ED8'
  },
  'MARKING': {
    background: '#FFF7ED',
    color: '#C2410C'
  },
  'MARKED': {
    background: '#F0FDF4',
    color: '#166534'
  },
  'TRAINING': {
    background: '#EEF2FF',
    color: '#4338CA'
  },
  'COMPLETED': {
    background: '#ECFDF5',
    color: '#047857'
  },
  'ERROR': {
    background: '#FEF2F2',
    color: '#B91C1C'
  }
}

export const getStatusText = (status) => {
  return statusTextMap[status] || status || '未知状态'
}

export const getStatusClass = (status) => {
  return statusClassMap[status] || ''
}

export const getStatusDetailColor = (status) => {
  return statusDetailColorMap[status] || { background: '#F0F9FF', color: '#0369A1' }
}

export const canDeleteTask = (task) => {
  return ['NEW', 'ERROR'].includes(task?.status)
}

export const isTaskActive = (status) => {
  return ['SUBMITTED', 'MARKING', 'TRAINING'].includes(status)
} 