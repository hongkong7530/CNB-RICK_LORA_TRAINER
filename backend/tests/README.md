# 任务状态接口测试

本目录包含用于测试任务管理API的测试用例。

## 运行测试

在项目根目录下运行：

```bash
python -m unittest discover tests
```

或者运行单个测试文件：

```bash
python -m unittest tests/test_task_status.py
```

## 任务状态接口

### 获取任务状态

**URL**: `/api/v1/tasks/<task_id>/status`
**方法**: `GET`
**描述**: 获取指定任务的状态信息

**响应示例**:

```json
{
  "id": 1,
  "name": "测试任务",
  "status": "MARKING",
  "progress": 45,
  "error_message": null,
  "started_at": "2025-03-16T12:30:45",
  "updated_at": "2025-03-16T12:35:22",
  "completed_at": null,
  "recent_logs": [
    {
      "time": "2025-03-16T12:30:45",
      "message": "任务已开始标记"
    },
    {
      "time": "2025-03-16T12:35:22",
      "message": "标记进度: 45%"
    }
  ],
  "marking_asset_id": 2,
  "training_asset_id": null
}
```

**可能的状态**:
- `NEW`: 新建
- `SUBMITTED`: 已提交
- `MARKING`: 标记中
- `MARKED`: 已标记
- `TRAINING`: 训练中
- `COMPLETED`: 已完成
- `ERROR`: 错误

**错误响应**:

```json
{
  "error": "任务不存在",
  "message": "未找到ID为 999 的任务"
}
```

## 前端使用示例

```javascript
// 获取任务状态
async function getTaskStatus(taskId) {
  try {
    const response = await fetch(`/api/v1/tasks/${taskId}/status`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '获取任务状态失败');
    }
    return await response.json();
  } catch (error) {
    console.error('获取任务状态错误:', error);
    throw error;
  }
}

// 定期轮询任务状态
function pollTaskStatus(taskId, callback, interval = 3000) {
  const timer = setInterval(async () => {
    try {
      const status = await getTaskStatus(taskId);
      callback(status);
      
      // 如果任务已完成或出错，停止轮询
      if (['COMPLETED', 'ERROR', 'MARKED'].includes(status.status)) {
        clearInterval(timer);
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error);
      clearInterval(timer);
    }
  }, interval);
  
  return timer; // 返回计时器，以便外部可以停止轮询
}
``` 