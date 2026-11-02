# Agent-Learning | 大模型应用工程与智能体开发实践

<div align="left">

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/uv-fast%20packaging-DE5FE9.svg?logo=astral&logoColor=white)](https://github.com/astral-sh/uv)
[![Docker](https://img.shields.io/badge/Docker-Desktop%20%2F%20WSL2-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![LeetCode](https://img.shields.io/badge/LeetCode-60%20Solved%20%7C%2031%20Medium-FFA116.svg?logo=leetcode&logoColor=white)](https://leetcode.cn/u/serene-i3assirxg/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Defensive%20PEP8-000000.svg)](https://peps.python.org/pep-0008/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

> 本仓库记录从零构建生产级 **AI Agent / 大模型应用工程** 的完整代码演进路径与技术实践沉淀。  
> 坚持**“防御性编程、原生造轮子、白板推导、指标量化”**原则，拒绝无思考的玩具式 API 拼装。

---

## 📌 培养方案与阶段架构

```mermaid
flowchart LR
    A["阶段 0: 工程筑基与工具链<br/>(W1-W14 · 进行中)"] --> B["阶段 1: 底层数学与自注意力<br/>(W15-W26)"]
    B --> C["阶段 2: 工业级垂直 RAG<br/>(W27-W36 · 项目 1)"]
    C --> D["阶段 3: 复杂状态机 Agent<br/>(W37-W52 · 项目 2)"]
```

| 阶段 | 周期 | 核心攻关方向 | 关键交付物 / 里程碑 | 状态 |
|---|---|---|---|:---:|
| **阶段 0** | **W1–W14** | **工程筑基与现代 Python 工具链**<br>• `uv` 极速虚拟环境与依赖管理<br>• WSL2 + Docker 容器化隔离沙箱<br>• 类型系统（`typing`）与防御性编程<br>• 原生手写 ReAct 循环、FastAPI + SSE 流式传输 | • `w1_check.py` 环境与计算自检<br>• `w2_data_process.py` 生产级数据管道<br>• 手撕 Mini-Agent（100 行 ReAct）<br>• 算法进度：**60 题（Medium 31）** | 🔥 **进行中** |
| **阶段 1** | **W15–W26** | **大模型底层结构与数学推导**<br>• PyTorch 5 步训练循环与张量计算<br>• 从零手撕 Multi-Head Attention 与因果掩码<br>• mini-GPT 搭建、自回归生成、KV Cache 与 GQA 显存推导 | • 从零实现 Transformer 核心算子<br>• LoRA 低秩微调实战验证 | ⏳ 待启动 |
| **阶段 2** | **W27–W36** | **工业级垂直领域 RAG 知识库系统**<br>• 混合检索（BM25 + 向量召回）与 RRF 融合去重<br>• Cross-Encoder 语义重排序（Re-ranking）<br>• Ragas 自动化量化评测（忠实度/上下文召回率） | • **项目 1：企业级 RAG 问答服务**<br>• 完整的 Benchmark 与量化评测报告 | ⏳ 待启动 |
| **阶段 3** | **W37–W52** | **生产级复杂状态机 Agent 系统**<br>• LangGraph 图状态机流转控制<br>• MCP (Model Context Protocol) 协议服务解耦<br>• 写操作严格幂等校验与 Docker 执行沙箱 | • **项目 2：生产级自动化 Agent**<br>• 50 条黄金评测集与 Badcase 归因闭环 | ⏳ 待启动 |

---

## 📂 项目结构与模块索引

```text
D:\Agent-Learning\
├── w1_check.py              # W1: Python 3.11 环境可用性自检与阶乘递归/迭代逻辑
├── w2_data_process.py       # W2: 生产级数据清洗与统计分析管道（RFC 8259 / 防御性校验）
├── student.csv              # W2: 数据源文件（含各种恶性边界用例）
├── result.json              # W2: 结构化统计分析与异常日志导出报表
├── 待处理.md                # 技术债务与待复盘清单
└── README.md                # 仓库核心架构与工程规范文档
```

---

## 🛠️ 核心交付模块深度解析

### 1. `w1_check.py`（环境初始化与基础运算自检）
* **开发环境基线**：验证现代 Python 解释器、`uv` 虚拟环境隔离及终端标准 I/O 交互。
* **算法鲁棒性**：实现循环与递归双版本阶乘逻辑，校验边界输入与栈深度基本约束。

### 2. `w2_data_process.py`（工业级防御性数据处理管道）

该脚本将输入的原始 CSV 数据清洗并统计，输出标准 JSON 报告。重点落实现代工程规范，拒绝假设“输入数据总是合法的”：

```
[原始 CSV 输入]
       │
       ▼
 [物理探活] ── 文件存在性检查 (pathlib.Path.exists)
       │
       ▼
 [格式净化] ── UTF-8-SIG 自动剥离 Excel BOM 头
       │
       ▼
 [数据清洗] ── 校验表头完整性 (fail-fast)
       │    ── 过滤空姓名、去除首尾空白字符
       │    ── 姓名重复性碰撞去重检测
       │    ── math.isfinite() 拦截 NaN / Inf / -Inf
       │    ── 截断非 [0, 100] 的非法越界分数
       │
       ▼
 [指标聚合] ── 动态统计有效行、均分、及格率
       │    ── 记录精确到原因的 skipped_reasons 异常分布
       │
       ▼
 [持久输出] ── json.dump(allow_nan=False) 保证严格跨语言 RFC 8259 兼容
       │
       ▼
[标准 result.json 报表]
```

#### 🛡️ 核心工程防御特性：
1. **跨平台路径无缝兼容**：全量使用标准库 `pathlib.Path`，彻底杜绝 Windows 与 Linux 下的路径斜杠硬编码问题；
2. **静态类型自解释**：全面接入 `typing` 模块（`List`, `Dict`, `Any`, `Optional`），函数签名完备，消除 IDE 悬停类型未知；
3. **BOM 头静默失效防御**：读取模式指定 `utf-8-sig`，彻底解决 Excel 导出 CSV 自带 `\ufeff` 导致首列表头匹配失败的隐蔽故障；
4. **数学级边界阻断**：引入 `math.isfinite()` 拦截浮点异常（`NaN`, `Infinity`），结合区间 `0 <= score <= 100` 实施二次语义门禁；
5. **RFC 8259 严格序列化**：输出 JSON 时强制显式声明 `allow_nan=False`，避免 Python 特有的非标准 `NaN` 逃逸到下游其他语言系统造成解析崩溃；
6. **恒定结构契约（Predictable Contract）**：无论数据是否存在异常，输出格式保持恒定包含 `status`, `average`, `count`, `skipped`, `skipped_reasons`, `data` 等确定性键值。

---

## 🚀 快速开始与本地复现

### 1. 环境准备
确保本机已安装 Python 3.11+ 以及新一代包管理器 [`uv`](https://github.com/astral-sh/uv)。

```bash
# 检查 uv 安装状态
uv --version
```

### 2. 克隆仓库与初始化虚拟环境
```bash
git clone https://github.com/cryat0117/Agent-Learning.git
cd Agent-Learning

# 使用 uv 秒级创建 .venv 虚拟环境
uv venv

# Windows PowerShell 激活（可选，uv run 支持免激活执行）
.venv\Scripts\activate
```

### 3. 执行核心脚本
```bash
# 1. 运行环境自检与递归验证脚本
uv run python w1_check.py

# 2. 运行工业级数据清洗与统计分析管道
uv run python w2_data_process.py
```

### 4. 验证交付物
运行完成后，可在当前目录直接检查生成的分析报表：
```bash
# 查看分析结果
Get-Content result.json
```

输出示例：
```json
{
  "status": "ok",
  "average": 74.0,
  "count": 3,
  "skipped": 8,
  "skipped_reasons": {
    "非数字": 3,
    "超出 0-100": 1,
    "NaN/Inf": 2,
    "姓名为空": 1,
    "重复姓名": 1
  },
  "data": [
    {"name": "张三", "score": 85.0},
    {"name": "李四", "score": 92.0},
    {"name": "王五", "score": 45.0}
  ]
}
```

---

## ⚙️ 工程规范与开发环境

* **操作系统**：Windows 11 / WSL2 (Ubuntu 22.04 LTS) 混合双引擎
* **主开发语言**：Python 3.11+
* **包与环境管理**：`uv` (Astral)
* **容器化底座**：Docker Desktop 29+ (WSL2 Engine，镜像数据盘外置持久化)
* **代码风格**：严格遵循 PEP 8，强化函数单一职责与提前防御返回（Guard Clauses）
* **版本控制规范**：Git (严格遵循 [Conventional Commits](https://www.conventionalcommits.org/))
  * `feat:` 新增功能与交付模块
  * `fix:` 修复边界条件与逻辑缺陷
  * `refactor:` 代码结构重构与坏味道清理
  * `docs:` 文档与架构规范更新

---

## 📖 相关文档归档

* [**`待处理.md`**](待处理.md)：日常开发过程中的技术债务、待复盘卡点与攻关清单。

---

<div align="center">
  <sub>Crafted with engineering rigor · Aiming for Production-grade Agent Architecture</sub>
</div>
