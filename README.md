# Agent-Learning | 大模型应用工程与智能体开发实践

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/uv-fast%20packaging-purple.svg)](https://github.com/astral-sh/uv)
[![Docker](https://img.shields.io/badge/Docker-Desktop%20%2F%20WSL2-2496ED.svg)](https://www.docker.com/)
[![LeetCode](https://img.shields.io/badge/LeetCode-60%20Solved%20%C2%B7%2031%20Medium-orange.svg)](https://leetcode.cn/u/serene-i3assirxg/)
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
  - 算法每日冲刺：力扣 **60 题**（Easy 29 / **Medium 31** / Hard 0），滑动窗口与双指针专题推进中
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
└── 待处理.md                # 学习路径中待复盘、待攻关的技术债务清单
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

## 📅 学习日志（W1–W2）

> 规则：每天 3 行 —— **学了什么 / 卡在哪 / 产出是什么**。
> 卡点列为 `—` 表示当天没遇到硬阻塞（**以后要真记，卡点才是最值钱的部分**）。

### 2026-10-16（五）· 提前启动
| 项 | 内容 |
|---|---|
| 学了什么 | 建 GitHub 仓库；装 Python / uv / VSCode；写 `w1_check.py`（阶乘 + 终端输入输出） |
| 卡在哪 | — |
| 产出 | 3 次 commit + 首次推送（`a25332c feat: add w1_check script`） |

> 📌 比 W1 正式开始（10/19）早了 3 天。

### 2026-10-19 ~ 10-25 · **W1 正式周（10/22 完成）**
| 项 | 内容 |
|---|---|
| 学了什么 | 黑马 Python+AI **P9–P56**（48 集 / 12.4h）：字面量、运算符、if/match/循环、列表·字符串·元组·集合·字典、列表推导式 |
| 卡在哪 | — |
| 产出 | 仓库可用 + 首个脚本跑通 · ✅ **比计划提前 3 天** |

> 本周无新 commit —— 代码在 10/16 已提前提交，这周主要是看视频 + 刷题。

### 2026-10-26（一）· W2 第 1 天
| 项 | 内容 |
|---|---|
| 学了什么 | 函数基础与进阶（作用域/传参/默认参数/`*args`/lambda/递归）、类型注解（P57–P76） |
| 卡在哪 | — |
| 产出 | 建 **`待处理.md`** 记录技术债（23:07 建「待解决」，23:09 改名「待处理」） |

### 2026-10-28（三）· **W2 核心交付完成**
| 项 | 内容 |
|---|---|
| 学了什么 | 文件操作与 JSON（P110–P112）；`csv.DictWriter` / `DictReader`、`json.dump` 参数 |
| 卡在哪 | — |
| 产出 | **`828457b feat: w2 csv and json`** —— CSV→JSON 统计管道跑通 · ✅ **比计划提前 3 天（3 天走完 7 天）** |

### 2026-10-29（四）· 重构日
| 项 | 内容 |
|---|---|
| 做了什么 | 把脚本重构成模块化三层（`export_initial` / `analyze` / `main`）；补全类型注解；加防御性校验 |
| 卡在哪 | — |
| 产出 | 3 次 refactor commit（14:52 / 15:03 / 15:59）+ README 全面重写（徽章、目录树、模块说明、快速上手） |

### 2026-10-30（五）· 按代码评审加固
| 项 | 内容 |
|---|---|
| 做了什么 | ① 读 CSV 改 `utf-8-sig`（**剥 BOM**）② `math.isfinite()` 拦 **NaN / Inf** ③ 分数范围 `[0,100]` ④ 空姓名丢弃 ⑤ 同名去重 ⑥ 零有效记录抛异常 ⑦ 返回契约恒定（`status/avg/count/skipped/data`）⑧ 表头校验 fail-fast ⑨ 种子数据不再覆盖 |
| 卡在哪 | **BOM 这条最难消化** —— 不剥 BOM 时整张表被静默跳过、脚本还报"分析完成" |
| 产出 | 2 次 commit：`26664ad`（BOM/NaN/契约）、`818b111`（边界测试 NaN·Inf·越界） |

> ⚠️ **仍未做**：`json.dump` 缺 `allow_nan=False`。目前靠 `math.isfinite` 前置拦截，属于"单点防御"；加上它才是双保险，能保证 `result.json` 在**任何语言**里都能被解析。

### 📊 W1–W2 阶段小结（截至 10-30）

| 指标 | 数值 | 对照计划 |
|---|---|---|
| 完成周次 | W1、W2 全部完成 | ✅ 比计划提前约 6 天 |
| 视频 | P9–P98 + P110–P112 ≈ **21h** | 按计划覆盖 |
| 代码 | 2 个模块 + README + 技术债清单 | 超出计划（计划只要求 1 个脚本） |
| LeetCode | **60 题**（Easy 29 / Medium 31） | **计划 W11 才要求 60 题 → 提前 8.5 周** |
| 日均投入 | 约 4 h | 略高于 22–27h/周 的上限，注意可持续性 |

**下一步（W3，11/02–11/08）**：面向对象 + 异常（黑马 P77–P87，视频 3.2h）；把 W2 脚本重构成类结构（抽 `BaseAnalyzer`、写 `CsvAnalyzer` / `JsonAnalyzer`、自定义 `ScoreOutOfRangeError`）。

---

## 🛠️ 技术底座与开发环境

* **操作系统**：Windows 10 / WSL2 (Ubuntu 22.04 LTS)
* **主开发语言**：Python 3.11+
* **容器化环境**：Docker Desktop 29+ (WSL2 Engine, 镜像数据外置挂载)
* **代码编辑器**：Visual Studio Code (Pylance, GitLens)
* **版本控制**：Git 2.40+ (严格遵循 Conventional Commits 规范)
