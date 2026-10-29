# Agent-Learning | 大模型应用工程与智能体开发实践

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/uv-fast%20packaging-purple.svg)](https://github.com/astral-sh/uv)
[![Docker](https://img.shields.io/badge/Docker-Desktop%20%2F%20WSL2-2496ED.svg)](https://www.docker.com/)
[![LeetCode](https://img.shields.io/badge/LeetCode-50%2B%20Solved-orange.svg)](https://leetcode.cn/u/serene-i3assirxg/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 本仓库记录从零构建生产级 **AI Agent / 大模型应用工程** 的完整代码演进路径与技术实践沉淀。  
> 坚持**“防御性编程、白板推导、指标量化、原生造轮子”**原则，拒绝无思考的玩具式 API 拼装。

---

## 📌 阶段规划概览

- [x] **阶段 0：工程功底与基础工具链筑基（W1–W14 · 进行中）**
  - Python 3.11 核心语法、`typing` 类型注解系统、面向对象与防御性编程
  - 高效包管理工具 `uv` 与现代虚拟环境管理
  - Windows 原生 + WSL2 混合双引擎、Docker 容器化隔离实操
  - 原生手写 mini-agent（ReAct 循环）、FastAPI + SSE 打字机流式传输、Redis 生产级分布式限流
  - 算法每日冲刺：力扣已突破 50+ 题（Medium 26+，滑动窗口/双指针专题精通）
- [ ] **阶段 1：大模型底层数学与结构原理（W15–W26）**
  - PyTorch 5 步标准训练循环、从零手撕多头自注意力（MHA）与因果掩码（Causal Mask）
  - mini-GPT 搭建、自回归文本生成、KV Cache 推理加速与 GQA 显存推导、LoRA 低秩微调
- [ ] **阶段 2：工业级垂直领域 RAG 知识库问答（W27–W36 · 项目 1）**
  - 混合检索（BM25 + 向量召回）与 RRF 融合去重、Cross-Encoder 交叉重排序
  - 流式服务化包装、自动化评测（Ragas 忠实度/召回率基准量化）
- [ ] **阶段 3：生产级复杂状态机 Agent 智能体（W37–W52 · 项目 2）**
  - LangGraph 图状态机、MCP (Model Context Protocol) 标准协议服务解耦
  - 写操作严格幂等校验、Docker 安全沙箱防护、50 条黄金评测集与 Badcase 归因闭环

---

## 📂 阶段 0 代码目录与进度归档

```text
D:\Agent-Learning\
├── w1_check.py              # W1: Python 3.11 环境可用性自检与数学计算逻辑
├── w2_data_process.py       # W2: 现代工程化数据处理器（CSV/JSON 管道、类型注解、异常防御）
├── student.csv              # W2 数据源示例（含数据校验容错测试用例）
├── result.json              # W2 结构化分析报表导出文件
├── README.md                # 仓库全局自述文档与工程规范
└── 待解决.md                # 学习路径中待复盘、待攻关的技术债务清单
```

### 核心模块说明

#### 1. `w1_check.py`（环境初始化与递归/迭代验证）
* 验证现代 Python 包管理器 `uv` 与 `.venv` 虚拟环境隔离机制；
* 基础数值计算与终端交互闭环。

#### 2. `w2_data_process.py`（工程级数据处理管道）
* **面向对象路径**：使用标准库 `pathlib.Path` 实现跨平台路径无缝兼容；
* **类型安全自解释**：全面接入 `typing` 模块（`List`, `Dict`, `Any`），函数签名完备规范；
* **三重防御性工程设计**：
  1. *物理检查*：文件存在性提前探活（`exists()` 拦截）；
  2. *容错防崩*：`try...except (ValueError, KeyError)` 自动过滤损坏数据行并记录告警，保障批处理长流程不因局部脏数据中断；
  3. *数学安全*：空数据集除以零（`ZeroDivisionError`）主动兜底防御。
* **模块解耦**：规范配置 `if __name__ == "__main__":` 入口，支持无副作用第三方复用。

---

## 🚀 快速上手与本地复现

### 1. 克隆仓库
```bash
git clone https://github.com/cryat0117/Agent-Learning.git
cd Agent-Learning
```

### 2. 环境配置（推荐使用 `uv` 极速初始化）
```bash
# 创建虚拟环境
uv venv

# Windows PowerShell 激活（或直接使用 uv run 免激活执行）
.venv\Scripts\activate
```

### 3. 执行模块
```bash
# 运行 W1 自检脚本
uv run python w1_check.py

# 运行 W2 工程化数据分析与报表导出
uv run python w2_data_process.py
```

---

## 🛠️ 技术底座与开发环境

* **操作系统**：Windows 10 / WSL2 (Ubuntu 22.04 LTS)
* **主开发语言**：Python 3.11+
* **容器化环境**：Docker Desktop 29+ (WSL2 Engine, 镜像数据外置挂载)
* **代码编辑器**：Visual Studio Code (Pylance, GitLens)
* **版本控制**：Git 2.40+ (严格遵循 Conventional Commits 规范)
