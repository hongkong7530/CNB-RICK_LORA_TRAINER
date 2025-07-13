# CNB-RICK_LORA_TRAINER
## CNB赋能-小白一键式云端Lora训练平台
![RLT Logo](fronted-ui\public\favicon.ico)
![CNB Logo](docs\云原生构建.png)
## 项目简介

RICK LORA TRAINER (RLT) 是一个基于ComfyUI和秋叶训练器的自动化LORA训练平台，旨在简化AI绘图LORA模型的训练流程。该项目通过直观的用户界面和自动化工作流程，使得即使是零基础的用户也能轻松训练出高质量的LORA模型。
---
参考资料：
- [CNB-云原生构建](https;//cnb.cool)
- [RLT](https://github.com/SmartRick/RLT)  基于RLT二次开发
- [秋叶akki训练器](https://github.com/Akegarasu/lora-scripts)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
---
## 简易功能展示
- 前端页面-资产
![RLT](docs\资产管理-本地资产说明.png)
![RLT](docs\资产管理-新建资产说明.png)

- 前端页面-任务
![RLT](docs\任务管理-新建任务按钮.png)
![RLT](docs\任务管理-查看详情.png)
![RLT](docs\任务管理-训练详情.png)

- 部分系统功能展示
![RLT](docs\系统设置-系统配置.png)
![RLT](docs\系统设置-标记配置.png)
![RLT](docs\翻译配置-谷歌.png)
![RLT](docs\训练配置-1.png)
![RLT](docs\训练配置-2.png)

## 快速体验-CNB一键启动
![CNB](docs\CNB-仓库主页.png)
![CNB](docs\有问题提issue.png)


## 核心特性

### 1. 零参数配置训练
- 预设优化的训练参数
- 自动处理训练流程
- 适合新手快速上手

### 2. 资产管理系统
- 支持多训练节点管理
- 训练素材自动下载与处理
- 模型资产统一管理

### 3. 自动化工作流程
- 素材自动下载（支持百度网盘）
- 智能数据标注处理
- 一键式LORA模型训练
- 训练完成后自动上传成品模型

### 4. 任务管理
- 可视化任务状态追踪
- 实时训练进度展示
- 训练日志实时查看
- 失败任务自动重试
- 历史训练数据查询

### 5. 灵活配置
- 可定制的训练参数
- 节点资源分配策略
- 调度间隔设置
- 并发限制控制

## 系统架构

### 后端架构
- Flask + SQLAlchemy
- WebSocket实时通信
- 多线程任务调度
- ComfyUI API集成

### 前端架构
- Vue 3框架
- 响应式界面设计
- 实时数据更新

## 工作流程

```
素材收集 -> 自动标注 -> LORA训练 -> 模型生成 -> 效果预览
```

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 14+
- ComfyUI环境
- 秋叶训练器（可选）

### 安装步骤

1. 克隆项目
```bash
git clone <repository_url>
cd lora-automatic-traning
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd fronted-ui
npm install
```

4. 启动服务
```bash
# 启动后端
cd backend
python run.py

# 启动前端
cd fronted-ui
npm run serve
```

## 使用指南

1. **创建训练任务**
   - 上传训练素材或提供下载链接
   - 选择训练类型和参数（或使用默认配置）
   - 提交任务

2. **监控训练进度**
   - 在任务列表查看所有任务状态
   - 点击任务查看详细训练日志和进度

3. **查看训练结果**
   - 训练完成后自动生成预览图
   - 下载训练好的LORA模型

## 核心模块

- **TaskScheduler**: 任务调度与管理
- **ComfyUIAPI**: 与ComfyUI交互的API封装
- **AssetManager**: 资产管理系统
- **TrainingService**: 训练服务
- **ConfigService**: 配置管理

## 常见问题

1. **如何调整训练参数？**
   - 在设置页面可以修改默认训练参数
   - 也可以在创建任务时为单个任务指定参数

2. **支持哪些训练模型？**
   - 目前主要支持Flux-LORA模型训练
   - 计划后续添加更多模型支持

3. **如何处理训练失败？**
   - 系统会自动重试失败的任务
   - 可以查看详细错误日志进行排查

## 开发计划

- [ ] 添加更多模型训练支持
- [ ] 优化训练参数自动推荐
- [ ] 增强批量处理能力
- [ ] 添加模型评分系统

## 贡献指南

欢迎提交Pull Request或Issue来帮助改进项目。

## 许可证

MIT License
