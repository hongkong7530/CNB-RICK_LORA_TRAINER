# CNB-Rick Lora训练调度器

## 注意事项

### 1. 训练之前，请设置好正确的全局训练参数

  如果你不懂得如何配置，请你在 系统设置>Lora训练配置 页面 找到 参数推荐 开关 >开关各一次< 你会发现参数变成的预设值，然后保存设置就行!

### 2. 关于翻译功能

  考虑到很多人懒得申请免费的百度api翻译接口，直接内置了谷歌翻译，但是这个服务不稳定，出现问题多重试几次或者等待一段时间
  有百度api的直接用百度翻译就行，快速又稳定

### 3. 创建训练任务

配置好参数后，您可以创建训练任务：

1. 在"任务"页面，点击"创建任务"按钮
2. 选择您刚才创建的资产
3. 确认训练参数
4. 点击"开始训练"按钮

### 4. 监控训练进度

您可以在"任务"页面监控训练进度：

1. 查看任务状态、进度和预计完成时间
2. 查看训练日志和中间结果
3. 如需要，可以暂停或取消训练任务

## 高级功能

### 自动打标功能

系统提供自动打标功能，可以自动识别图片内容并生成标签：


### 批量处理

您可以批量处理多个图片：

1. 在资产页面，选择多个图片
2. 点击"批量操作"按钮
3. 选择要执行的操作（如批量打标、批量裁剪等）

### 模型导出

训练完成后，您可以导出模型用于推理：

1. 在任务详情页面，点击"下载模型"按钮

## 参数说明

### 基本参数

- **模型训练类型**：选择要使用的基础模型类型
  - Flux-Lora：适用于高质量艺术创作
  - SD1.5-Lora：通用型，适合多种场景
  - SDXL-Lora：高分辨率，细节更丰富

- **最大训练轮次**：模型训练的总轮数，通常5-10轮即可

- **图片重复次数**：每张图片在一个训练轮次中重复使用的次数

### 高级参数

- **学习率**：控制模型学习速度，一般建议0.0001-0.001

- **网络维度**：LoRA网络的维度，影响模型容量和学习能力
  - 较小的值（如4-16）：学习简单特征，训练速度快
  - 较大的值（如64-128）：学习复杂特征，需要更多训练数据

- **批量大小**：每次更新模型参数时处理的样本数量，受GPU内存限制

## 故障排除

### 常见错误

- **CUDA内存不足**：减小批量大小或降低分辨率
- **训练不收敛**：调整学习率或增加训练轮次
- **模型过拟合**：增加正则化或减少训练轮次

### 性能优化

- 使用较小的网络维度可以加快训练速度
- 混合精度训练可以减少内存使用
- 适当调整批量大小可以提高训练效率

## 系统要求

- **GPU**：建议使用NVIDIA GPU，至少8GB显存
- **存储空间**：至少20GB可用空间
- **操作系统**：Windows 10/11、Ubuntu 20.04或更高版本

## 更新日志

### v1.2.0 (2025-06-20)
- 添加SDXL-Lora、sd1.5-Lora支持
- 优化自动打标算法
- 改进用户界面

### v1.1.0 (2025-05-15)
- 添加批量处理功能
- 改进训练稳定性
- 修复多个已知问题

### v1.0.0 (2025-04-01)
- 初始版本发布 