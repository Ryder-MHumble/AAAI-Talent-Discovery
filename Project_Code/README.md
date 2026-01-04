# AAAI-26 人才猎手 🎯

> **用于识别海外华人学者的智能系统**

一个快速验证想法的自动化服务，用于从AAAI-26会议中发现和验证海外华人学者信息。

---

## 主要功能

- 🤖 自动从AAAI官网抓取候选人信息
- 🔍 智能过滤识别华人姓名
- ✅ 自动搜索并验证学者主页
- 🧠 使用AI提取关键信息（中文名、邮箱、本科院校）
- 📊 一键导出Excel报告

---

## 快速启动

### 1. 安装依赖

```bash
cd Project_Code
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# SiliconFlow API密钥（必需）
SILICONFLOW_API_KEY=你的密钥
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3

# 运行环境
APP_ENV=DEV

# Firecrawl配置（可选 - 增强抓取能力）
FIRECRAWL_API_KEY=
FIRECRAWL_ENABLED=false
```

### 3. 启动服务

```bash
# 方式1: 使用启动脚本
bash start.sh

# 方式2: 直接运行
python -m app.main
```

服务将在 http://localhost:8000 启动

---

## 如何使用

### API文档

启动服务后访问：http://localhost:8000/docs

### 主要接口

1. **单人验证** - `/api/v1/check-person`
   - 快速验证单个学者信息
   - 立即返回结果

2. **批量任务** - `/api/v1/jobs/aaai-full-scan`
   - 启动批量抓取任务
   - 后台运行，可查询进度

3. **导出报告** - `/api/v1/jobs/{job_id}/export`
   - 下载Excel格式结果
   - 支持仅验证通过或全部候选人

---

## 项目结构

```
Project_Code/
├── app/
│   ├── main.py              # 应用入口
│   ├── core/                # 核心配置
│   │   ├── config.py       # 环境配置
│   │   └── llm.py          # AI模型配置
│   ├── api/                 # API接口
│   │   ├── endpoints.py    # 路由定义
│   │   └── models.py       # 数据模型
│   ├── agents/              # 智能体工作流
│   │   ├── graph.py        # 工作流定义
│   │   ├── state.py        # 状态管理
│   │   ├── nodes/          # 处理节点
│   │   └── tools/          # 工具函数
│   └── services/            # 业务服务
│       └── excel_service.py # Excel导出
├── requirements.txt         # Python依赖
└── start.sh                # 启动脚本
```

---

## 工作流程

系统使用4个智能体节点协同工作：

1. **采集节点** - 从AAAI官网获取候选人列表
2. **过滤节点** - 识别华人姓名并过滤大陆学者
3. **侦探节点** - 搜索候选人主页
4. **审计节点** - 验证主页并提取信息

---

## 开发模式

默认使用测试数据（5个模拟候选人），适合快速验证功能。

要切换到生产模式（真实抓取）：
```env
APP_ENV=PROD
```

---

## 常见问题

**Q: 如何获取SiliconFlow API密钥？**  
A: 访问 https://cloud.siliconflow.cn 注册并创建API密钥

**Q: 为什么有些学者验证失败？**  
A: 可能原因：
- 找不到个人主页
- 主页无法访问
- 主页内容与姓名/单位不匹配

**Q: Firecrawl是什么？必须吗？**  
A: Firecrawl是增强抓取工具，支持JavaScript渲染。非必需，不配置时使用普通抓取方式。

---

## 技术栈

- FastAPI - Web框架
- LangGraph - 智能体编排
- SiliconFlow - AI模型服务
- DuckDuckGo - 免费搜索引擎
- pandas - 数据处理和Excel导出

---

## 说明

这是一个快速验证想法的原型项目，专注于功能实现而非生产部署。代码注释已全部中文化，方便理解和修改。
