# SJTU Canvas Skill

一个面向上海交通大学 Canvas（`oc.sjtu.edu.cn`）的命令行课程助手，帮你管理课程、作业、文件、成绩，并内置课件提取、日历同步等 AI 学习辅助能力。

本工具基于 [Hermes Agent 的 sjtu-canvas-skill](https://github.com/nousresearch/hermes-agent) 开发，并借鉴了 [xhh678876/sjtu-canvas](https://github.com/xhh678876/sjtu-canvas) 的 AI 学习特性进行增强。

> 💡 除上海交大外，也可通过修改 `base_url` 适配任何 Canvas LMS 实例。

---

## 目录

- [功能特性](#功能特性)
- [目录结构](#目录结构)
- [环境要求](#环境要求)
- [安装](#安装)
- [获取 Canvas API Token](#获取-canvas-api-token)
- [配置](#配置)
- [快速开始](#快速开始)
- [命令详解](#命令详解)
- [AI 学习工作流](#ai-学习工作流)
- [常见问题](#常见问题)
- [致谢与许可](#致谢与许可)

---

## 功能特性

| 分类 | 功能 | 说明 |
|---|---|---|
| 📚 课程 | 查看课程列表 | 列出当前用户所有活跃课程，含课程号、学期、教师 |
| 📝 作业 | 当前学期作业查询 | 一键列出本学期所有未过期作业，并标注提交状态（推荐） |
| 📝 作业 | 全量 DDL 追踪 | 跨学期查看所有课程的未来截止时间 |
| 📝 作业 | 提交作业 | 命令行直接上传文件并提交，支持附带评语 |
| 📊 成绩 | 成绩查询 | 查看各科已出成绩，自动计算加权总分 |
| 📂 文件 | 文件 / 文件夹管理 | 列出课程文件与目录结构 |
| 📂 文件 | 批量下载课件 | 按扩展名过滤，一键下载某课程的 PDF / PPT 等 |
| 🧠 课件学习 | 内容提取 | PPT / PDF / DOCX / TXT / MD → Markdown，配合 LLM 生成笔记 |
| 🧠 课件学习 | 期末复习包 | 批量提取目录下所有课件为 Markdown |
| 💬 讨论区 | 浏览课程讨论 | 查看讨论话题列表与完整内容 |
| ⏰ 日历 | DDL 日历同步 | 将 DDL 同步到 Apple 日历，iCloud 推送到 iPhone（macOS） |
| 🤖 智能交互 | JSON 输出 | `--json` 输出机器可读数据，便于 Agent 集成 |

---

## 目录结构

```
sjtu-canvas-skill-fancy/
├── scripts/                 # Python 源码
│   ├── main.py              # CLI 入口，定义全部命令
│   ├── client.py            # Canvas API 客户端
│   ├── file_extractor.py    # 课件内容提取器（PPT/PDF/DOCX → Markdown）
│   ├── calendar_sync.py     # DDL → Apple 日历同步（macOS）
│   └── __init__.py
├── references/              # 参考文档
│   └── troubleshooting.md   # 故障排查（WSL 网络、Token、学期检测）
├── SKILL.md                 # Agent 技能定义
├── config.json              # 配置项 JSON Schema 定义
├── config.example.json      # 配置示例
├── pyproject.toml           # 项目依赖与构建配置
├── uv.lock                  # 依赖锁文件（保证可复现构建）
├── .gitignore
└── README.md
```

---

## 环境要求

- **Python ≥ 3.12**
- **[uv](https://docs.astral.sh/uv/)**（推荐的包管理器与运行环境）
- 网络可访问 `oc.sjtu.edu.cn`

> 无需 uv 也可运行：`pip install -e .` 后直接使用 `main` 命令，或 `python -m scripts.main`。

---

## 安装

### 1. 克隆仓库

```bash
git clone git@github.com:Fancyyyf/sjtu-canvas-skill-fancy.git
cd sjtu-canvas-skill-fancy
```

### 2. 安装依赖

使用 uv（推荐）：

```bash
uv sync
```

若需课件提取功能（PPT / PDF / DOCX），额外安装可选依赖：

```bash
uv sync --extra extract
# 或
uv pip install python-pptx pdfplumber python-docx
```

### 3. 配置 Token

见下方 [获取 Canvas API Token](#获取-canvas-api-token) 与 [配置](#配置)。

---

## 获取 Canvas API Token

1. 登录 [SJTU Canvas](https://oc.sjtu.edu.cn)
2. 点击左侧 **账户（Account）** → **设置（Settings）**
3. 向下滚动到 **已批准的集成（Approved Integrations）**
4. 点击 **+ 新建访问令牌（+ New Access Token）**
5. 填写：
   - **用途（Purpose）**：例如 `sjtu-canvas-skill`
   - **过期时间（Expires）**：建议选择一年
6. 点击 **生成令牌（Generate Token）**
7. **⚠️ 立即复制**：令牌只显示一次，关闭后无法再次查看

---

## 配置

本工具支持三种配置方式，优先级从高到低依次为：

1. **命令行参数**：`--token`、`--base-url`
2. **环境变量**：`TOKEN`、`BASE_URL`、`SAVE_DIR`、`CALENDAR_NAME`
3. **`.env` 文件**（项目根目录）

### 方式一：`.env` 文件（推荐）

在项目根目录创建 `.env`：

```bash
echo "TOKEN=你的Canvas令牌" > .env
```

可选配置：

```bash
# .env
TOKEN=你的Canvas令牌
BASE_URL=https://oc.sjtu.edu.cn
SAVE_DIR=~/Downloads/Canvas课件   # 课件默认下载目录
CALENDAR_NAME=Canvas作业           # Apple 日历分类名
```

### 方式二：环境变量

```bash
export TOKEN=你的Canvas令牌
export BASE_URL=https://oc.sjtu.edu.cn
```

### 方式三：命令行参数

```bash
uv run main --token 你的Canvas令牌 list-courses
```

### 首次运行交互式输入

若未配置 Token 且处于交互式终端，程序会提示你输入，并可选择自动写入 `.env`：

```bash
uv run main list-courses
# TOKEN not found ... 
# Please enter your Canvas API token: ****
# Save TOKEN to project .env for future runs? [Y/n]
```

> 更多配置项说明见 `config.json`（JSON Schema）与 `config.example.json`（示例）。其中 `current_term` 通常无需手动设置，工具会根据系统日期自动识别当前学期。

---

## 快速开始

```bash
# 查看本学期所有未过期作业（含提交状态）—— 最常用
uv run main list-current-assignments

# 查看所有课程
uv run main list-courses

# 查看所有课程的未来 DDL
uv run main list-ddls

# 查看某门课的成绩
uv run main grades 12345

# 列出某门课的文件
uv run main list-files 12345

# 提交作业
uv run main submit 12345 67890 ./homework.py --comment "第一次提交"
```

---

## 命令详解

所有命令统一以 `uv run main <命令>` 执行。全局选项：

| 选项 | 说明 |
|---|---|
| `--token TEXT` | Canvas API 令牌（也可用 `TOKEN` 环境变量） |
| `--base-url TEXT` | Canvas 地址，默认 `https://oc.sjtu.edu.cn` |
| `--json` | 输出原始 JSON（适合程序 / Agent 处理） |

> 注意：`--json` 等全局选项需放在子命令之前，例如 `uv run main --json list-courses`。

### 📚 课程

```bash
# 列出当前用户所有活跃课程
uv run main list-courses
```

### 📝 作业

```bash
# 列出本学期所有未过期作业，并标注提交状态（推荐）
uv run main list-current-assignments
uv run main list-current-assignments --term "2025-2026 Spring"   # 指定学期

# 列出所有课程的未来 DDL
uv run main list-ddls

# 列出指定课程的所有作业
uv run main list-assignments 12345

# 提交作业（可一次提交多个文件）
uv run main submit 12345 67890 ./main.py ./report.pdf --comment "最终版"
```

### 📊 成绩

```bash
# 查看某门课的所有作业成绩与加权总分
uv run main grades 12345
```

### 📂 文件

```bash
# 列出课程文件 / 文件夹
uv run main list-files 12345
uv run main list-folders 12345

# 批量下载课件（可按扩展名过滤）
uv run main batch-download 12345 --ext .pdf --ext .pptx --path ~/Downloads/课程

# 下载单个文件（URL 来自 list-files 输出）
uv run main download-file "https://..." --path ./downloads
```

### 🧠 课件提取（无需 Token）

```bash
# 提取单个文件为 Markdown
uv run main extract-file lecture.pptx
uv run main extract-file lecture.pdf -o lecture.md     # 保存到文件

# 批量提取目录下所有课件
uv run main batch-extract ~/Downloads/Canvas课件/传热学 -o ~/Downloads/传热学_md
```

### 💬 讨论区

```bash
# 列出课程讨论话题
uv run main list-discussions 12345

# 查看某个话题的完整内容
uv run main get-discussion 12345 9999
```

### ⏰ 日历同步（macOS）

```bash
# 将未来 30 天的 DDL 同步到 Apple 日历
uv run main sync-calendar
uv run main sync-calendar --days 60
```

### 👤 其他

```bash
# 查看当前用户信息
uv run main get-me
```

---

## AI 学习工作流

本工具可与 LLM 配合，实现"不止查数据"的学习辅助。

### 1. 课件总结

```bash
# ① 下载课件
uv run main batch-download 12345 --ext .pdf --ext .pptx

# ② 提取为 Markdown
uv run main batch-extract ~/Downloads/Canvas课件/课程名 -o ~/Downloads/课程名_md

# ③ 将 Markdown 交给 LLM 生成学习笔记
```

### 2. 作业辅导

1. `list-assignments <course_id>` 获取作业要求
2. `batch-download` + `batch-extract` 提取对应课件
3. 结合作业要求与课件内容，让 LLM 定位知识点、给出解题思路

### 3. DDL 管理

1. `list-ddls` 查看所有未来截止时间
2. `sync-calendar` 同步到 Apple 日历（macOS，iCloud 推送至 iPhone）
3. 可配合 cron 定时巡检 `list-ddls --json` 并推送提醒

### 4. 期末复习包

```bash
# ① 批量下载所有课件
uv run main batch-download 12345 --path ~/Downloads/复习包

# ② 批量转为 Markdown
uv run main batch-extract ~/Downloads/复习包 -o ~/Downloads/复习包_md

# ③ 导入 NotebookLM 或其他 RAG 工具
```

---

## 常见问题

详见 [`references/troubleshooting.md`](references/troubleshooting.md)，摘要如下：

| 问题 | 解决方案 |
|---|---|
| WSL 下 `SSL_ERROR_SYSCALL` 连接失败 | 更新 CA 证书、调整 WSL2 MTU，或在 Windows 宿主机运行 |
| Token 时而有效时而失败 | Token 本身有效，是网络 / SSL 层问题，非鉴权问题 |
| 学期识别不正确 | 用 `--term "2025-2026 Spring"` 手动指定 |
| 提取课件报"需要安装 xxx" | 安装可选依赖：`uv pip install python-pptx pdfplumber python-docx` |

**学期自动识别规则**：

- 1–2 月 → 上一学年 Fall（如 `2025-2026 Fall`）
- 3–7 月 → 上一学年 Spring（如 `2025-2026 Spring`）
- 8–12 月 → 本学年 Fall（如 `2026-2027 Fall`）

---

## 致谢与许可

- 基于 [Hermes Agent 的 sjtu-canvas-skill](https://github.com/nousresearch/hermes-agent)（Nous Research）
- AI 学习特性借鉴 [xhh678876/sjtu-canvas](https://github.com/xhh678876/sjtu-canvas)

本项目采用 [MIT 许可证](LICENSE)。
