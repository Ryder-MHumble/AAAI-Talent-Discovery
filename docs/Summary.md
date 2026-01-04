# AAAI-26 海外华人学者智能发现系统
## 1. 项目背景与目标

AAAI-26（第26届国际人工智能大会）聚集了全球AI学者。为更高效服务于国内人才引进与国际学术交流，我们亟需精准识别在海外工作的华人学者：

- **人才引进**：全国高校、研究院所重点招聘对象
- **学术交流**：促进国际合作与交流
- **产业对接**：连接海外前沿技术与国内产业

### 业务挑战

| 传统痛点         | 负面影响                 |
|------------------|-------------------------|
| 人工筛选耗时长    | 600+人需数周             |
| 信息难核实        | 姓名相似易误判           |
| 验证成本高        | 主页访问/背景调查繁琐     |
| 数据格式不统一    | 难以结构化收集与分析     |

### 项目目标

打造一个**全自动、高精度**的海外华人学者发现系统：

- > **自动化率 ≥ 95%**（人工复核仅5%）
- > **识别准确率 ≥ 90%**（多轮验证机制）
- > **单人处理≤20秒，批量<4小时**
- > **邮箱/本科院校结构化提取≥70%**

---

## 2. 核心价值与创新点

### 技术创新亮点

- **多智能体协同架构：** 基于LangGraph建模，专业分工、状态驱动。
- **国产LLM智能解析：** 集成SiliconFlow（DeepSeek-V3）模型，支持多语种信息抽取与语义匹配。
- **端到端自动流转：** 数据采集/筛选/主页定位/身份验证全自动闭环。
- **可组合API服务：** 易于对接业务系统，支持快速集成。

```mermaid
graph LR
  A[数据采集] --> B[身份筛选]
  B --> C[主页搜索]
  C --> D[身份验证]
  style A fill:#e3f2fd
  style B fill:#fff3e0
  style C fill:#f3e5f5
  style D fill:#e8f5e9
```

### 业务成果

- **降本增效**：人力成本下降80%，处理周期4周→1天
- **数据资产化**：学者数据库可持续运营与分析
- **服务导向**：接口开放，支持BD/HR自动化操作
- **智能决策**：系统自动优先级排序与推荐

---

## 3. 技术架构设计

### 系统组成

```mermaid
graph TB
  subgraph "外部系统"
    A1[BD/HR系统]
    A2[AAAI官网]
  end

  subgraph "API服务层"
    B1[FastAPI接口]
    B2[请求路由]
    B3[响应输出]
  end

  subgraph "智能体编排"
    C1[数据采集]
    C2[身份筛选]
    C3[信息侦探]
    C4[审核验证]
  end

  subgraph "工具集"
    D1[DuckDuckGo搜索]
    D2[Firecrawl抓取]
    D3[HTTP/语义匹配]
    D4[LLM提取]
  end

  subgraph "数据层"
    E1[队列存储/Redis]
    E2[Excel导出]
  end

  A1 --> B1
  A2 --> C1
  B2 --> C1
  C1 --> C2 --> C3 --> C4
  C3 --> D1 & D2
  C4 --> D3 & D4
  C4 --> E1
  B3 --> E2
  E1 --> E2

  style C1 fill:#bbdefb
  style C2 fill:#ffe0b2
  style C3 fill:#f8bbd0
  style C4 fill:#c8e6c9
```

### 技术栈精选

| 层次       | 技术               | 优势                                 |
|------------|--------------------|--------------------------------------|
| API        | FastAPI            | 高并发、类型安全、文档自动生成       |
| 智能体      | LangGraph/LangChain| 状态管控、易扩展、社区活跃           |
| LLM        | SiliconFlow (DeepSeek-V3) | 国内服务、低延迟、强中文理解      |
| 搜索       | DuckDuckGo         | 免费免密钥、抗封禁、隐私安全         |
| 抓取       | Firecrawl MCP      | 支持JS渲染、结构化内容输出           |
| 中文NLP    | xpinyin            | 名字拼音判定、姓氏支持               |
| 导出       | pandas/openpyxl    | Excel兼容性强、便于业务分析          |

---

## 4. 多智能体自动工作流

### 4.1 工作流概览

```mermaid
stateDiagram-v2
  [*] --> 数据采集
  数据采集 --> 身份筛选: 预处理候选人
  身份筛选 --> 信息侦探: 跳过非华人/大陆学者
  信息侦探 --> 审核验证: 定位主页
  信息侦探 --> 失败: 未找到主页
  审核验证 --> 已验证: 核验通过，提取信息
  审核验证 --> 失败: 校验失败
  已验证 --> 路由判断: 有待处理继续
  失败 --> 路由判断
  路由判断 --> 信息侦探: 下一个候选人
  路由判断 --> [*]: 全部完成
```

### 4.2 智能体节点简述

#### ① 数据采集（IngestionNode）
- **任务**：AAAI会议各页抓取&初步字段提取
- **输入**：AAAI专题页URL
- **输出**：标准候选人条目（姓名/单位/角色）

#### ② 身份筛选（FilterNode）
- **任务**：自动识别海外华人学者
- **算法要点**：
  - 中文姓名检测（直接/拼音/常见姓氏）
  - 海外单位判定（大陆高校/研究院关键词屏蔽）
- **标准示例**：

  | 姓名           | 单位             | 结果             |
  |----------------|------------------|------------------|
  | Haoyang Li     | CMU              | ✅ PASS          |
  | Jie Tang       | Tsinghua          | ❌ SKIP（大陆）   |
  | John Smith     | MIT              | ❌ SKIP（非华人） |

#### ③ 信息侦探（DetectiveNode）
- **任务**：自动搜索并排序主页（DuckDuckGo+评分），按优先级交由验证
- **排序权重**：域名（.edu,+2分）、姓名特征(+4分)、关键词(+3分)、社媒(-5分)、PDF(-2分)
- **Firecrawl优势**：SEO抗干扰能力强、结构化输出便于AI理解

#### ④ 审核验证（AuditorNode）
- **三层校验闭环**：
  1. 连通性检查（HTTP 200）
  2. 语义匹配（姓名/单位关键词双命中）
  3. LLM抽取（邮箱、中文名、本科、单位复核）

---

## 5. 关键技术方案

### 5.1 并发与稳定性优化

- 异步限流（建议值：DuckDuckGo并发不超3路）
- 超时/重试机制，全流程平均单人<25s
- Firecrawl失效时自动降级原生抓取

```python
from asyncio import Semaphore
class ConcurrencyController:
    def __init__(self, max_concurrent=3):
        self.semaphore = Semaphore(max_concurrent)
    async def execute(self, task):
        async with self.semaphore:
            return await task()
```

| 环节            | 优化后单次耗时（秒） |
|-----------------|-------------------|
| 搜索            | 2~5               |
| 抓取            | 3~8               |
| LLM提取         | 3~8               |
| 单人全流程      | 15~25             |
| 600人全流程     | 2~3小时           |

### 5.2 容错与多路降级

- Firecrawl不可用时降级httpx，无可用则标记失败，流程不中断。

---

## 6. API接口一览

| 接口路径                             | 场景             |
|--------------------------------------|------------------|
| POST `/api/v1/check-person`          | 单人快速校验     |
| POST `/api/v1/jobs/aaai-full-scan`   | 会议批量启动     |
| GET `/api/v1/jobs/{id}/status`       | 任务进度查询     |
| GET `/api/v1/jobs/{id}/export`       | 结果Excel导出    |
| GET `/health`                        | 系统健康检查     |

**接口示例**：

- 单人验证请求
    ```json
    {
      "name": "Haoyang Li",
      "affiliation": "Carnegie Mellon University"
    }
    ```
- 成功响应
    ```json
    {
      "name": "Haoyang Li",
      "status": "VERIFIED",
      "homepage": "...",
      "email": "haoyangle@cs.cmu.edu",
      "name_cn": "李浩阳",
      "bachelor_univ": "Shanghai Jiao Tong University"
    }
    ```
- 失败响应
    ```json
    {
      "name": "John Smith",
      "status": "FAILED",
      "message": "未找到有效主页"
    }
    ```
- 导出的Excel含两表：已验证信息与统计汇总

---

## 7. 数据流与验证逻辑

**主流程（简化）：**

```mermaid
sequenceDiagram
    participant U as 用户/系统
    participant A as FastAPI
    participant G as LangGraph工作流
    participant T as 工具层
    participant L as SiliconFlow LLM
    participant D as 数据存储
    
    U->>A: POST /jobs/aaai-full-scan
    A->>G: 启动工作流
    
    G->>G: 数据采集智能体<br/>加载候选人列表
    G->>G: 身份筛选智能体<br/>标记SKIPPED
    
    loop 每个PENDING候选人
        G->>T: 侦探智能体调用搜索
        T->>T: DuckDuckGo搜索主页
        T-->>G: 返回候选URL列表
        
        G->>T: 调用Firecrawl抓取
        T->>T: 深度抓取 + 清洗
        T-->>G: 返回Markdown内容
        
        G->>G: 审核智能体验证
        
        alt 内容匹配成功
            G->>L: 调用LLM提取信息
            L-->>G: 返回结构化数据
            G->>D: 更新候选人状态=VERIFIED
        else 验证失败
            G->>D: 更新候选人状态=FAILED
        end
    end
    
    G-->>A: 工作流完成
    A->>D: 生成Excel报告
    A-->>U: 返回下载链接
```

### 7.2 验证决策树

```mermaid
graph TD
    A[候选人] --> B{中文姓名?}
    B -->|否| C[SKIPPED<br/>非华人]
    B -->|是| D{大陆单位?}
    D -->|是| E[SKIPPED<br/>非海外]
    D -->|否| F[执行搜索]
    
    F --> G{找到主页?}
    G -->|否| H[FAILED<br/>无主页]
    G -->|是| I[Firecrawl抓取]
    
    I --> J{HTTP 200?}
    J -->|否| K[FAILED<br/>不可访问]
    J -->|是| L{语义匹配?}
    
    L -->|否| M[FAILED<br/>内容不符]
    L -->|是| N[LLM提取信息]
    
    N --> O[VERIFIED<br/>成功验证]
    
    style C fill:#ffcdd2
    style E fill:#ffcdd2
    style H fill:#ffcdd2
    style K fill:#ffcdd2
    style M fill:#ffcdd2
    style O fill:#c8e6c9
```
---

## 10. 风险及质量控制

### 核心风险及应对

| 风险项                   | 概率 | 影响 | 管控措施                |
|--------------------------|------|------|-------------------------|
| DuckDuckGo限流           | 中   | 中   | 并发限流、备用API       |
| Firecrawl服务失效        | 低   | 高   | 降级方案+监控           |
| LLM抽取失败              | 中   | 中   | 多模型/Prompt策略冗余   |
| 误识别率                | 低   | 高   | 加强姓名算法&抽查       |
| AAAI官网结构变动         | 低   | 中   | 解析器容错与热补丁      |
| 数据与隐私合规           | 低   | 高   | 仅公开数据、加密存储    |

### 质量保障三重门

1. **自动校验**（二元机制：主页连通性+内容语义双判）
2. **规则复查**（邮箱/URL有效性)
3. **人工抽检**（10%随机，低于85%召回全量复查）

---

**人工复核流程简述**：
- 系统定期随机抽检10%样本，由人工二次确认
- 准确率<85%时触发全量复核，并回馈优化算法与Prompt
