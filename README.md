# SJTU Canvas Skill - Fancy's Fork

A personal fork of the [SJTU Canvas Skill](https://github.com/nousresearch/hermes-agent/tree/main/skills/sjtu-canvas-skill) for interacting with the Shanghai Jiao Tong University Canvas LMS.

## Overview

This skill provides a command-line interface (CLI) to interact with the SJTU Canvas Learning Management System. It allows you to:

- List courses and assignments
- Query current semester assignments with completion status
- Submit assignments
- Manage files and folders
- Download course materials

## Quick Start

### 1. Clone the repository

```bash
git clone git@github.com:Fancyyyf/sjtu-canvas-skill-fancy.git
cd sjtu-canvas-skill-fancy
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Get your Canvas API Token

1. Log in to [SJTU Canvas](https://oc.sjtu.edu.cn)
2. Click **Account** (账户) in the left sidebar → **Settings** (设置)
3. Scroll down to **Approved Integrations** (已批准的集成)
4. Click **+ New Access Token** (+ 新访问令牌)
5. Fill in:
   - **Purpose** (用途): e.g., "Hermes Agent CLI" or "Personal Script"
   - **Expires** (过期时间): Choose a date (recommend 1 year)
6. Click **Generate Token** (生成令牌)
7. **Important**: Copy the token immediately! You won't be able to see it again.

### 4. Configure the token

Create a `.env` file in the project root:

```bash
echo "TOKEN=your_canvas_api_token_here" > .env
```

Or set it as an environment variable:

```bash
export TOKEN=your_canvas_api_token_here
```

### 5. Run commands

```bash
# List current semester assignments (recommended)
uv run main list-current-assignments

# List all courses
uv run main list-courses

# List assignments for a specific course
uv run main list-assignments <course_id>

# Submit an assignment
uv run main submit <course_id> <assignment_id> <file1> <file2> --comment "My submission"

# Get current user profile
uv run main get-me

# List files for a course
uv run main list-files <course_id>

# List folders for a course
uv run main list-folders <course_id>

# Download a file
uv run main download-file <file_url> --path ./downloads
```

## Detailed Usage

### Commands Reference

| Command | Description |
|---------|-------------|
| `list-current-assignments` | **推荐** - 列出当前学期所有课程的未过期作业，显示提交状态 |
| `list-courses` | 列出当前用户的所有活跃课程 |
| `list-assignments <course_id>` | 列出指定课程的所有作业 |
| `submit <course_id> <assignment_id> <files...>` | 提交作业文件 |
| `get-me` | 获取当前用户信息 |
| `list-files <course_id>` | 列出课程文件 |
| `list-folders <course_id>` | 列出课程文件夹 |
| `download-file <url>` | 下载文件 |

### Options

- `--json`: 输出原始 JSON 格式（适合程序处理）
- `--term <term>`: 指定学期，如 `"2025-2026 Spring"`，默认自动识别当前学期
- `--base-url`: Canvas 实例地址，默认 `https://oc.sjtu.edu.cn`

### Examples

```bash
# 查看当前学期作业（JSON 格式）
uv run main --json list-current-assignments

# 指定学期查看作业
uv run main list-current-assignments --term "2025-2026 Spring"

# 查看特定课程的所有作业
uv run main --json list-courses | jq '.[] | select(.name | contains("计算机"))'
uv run main list-assignments 12345

# 提交作业
uv run main submit 12345 67890 ./homework.py ./report.pdf --comment "Final submission"
```

## Configuration

The skill uses a `.env` file or environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TOKEN` | Yes | - | Canvas API token |
| `BASE_URL` | No | `https://oc.sjtu.edu.cn` | Canvas instance URL |

Configuration schema is defined in `config.json`.

## Project Structure

```
sjtu-canvas-skill-fancy/
├── scripts/              # Python CLI scripts
│   ├── main.py          # Entry point
│   ├── client.py        # Canvas API client
│   └── __init__.py
├── references/          # Documentation references
│   └── troubleshooting.md
├── SKILL.md             # Skill definition for Hermes Agent
├── config.json          # Configuration JSON Schema
├── pyproject.toml       # Python project configuration
├── .gitignore
└── README.md
```

## Key Features

- **Current semester detection**: Automatically identifies the current academic term based on date
- **Assignment filtering**: Shows only non-expired assignments with completion status
- **Robust date parsing**: Handles both ISO and transformed date formats from Canvas API
- **Comprehensive course scanning**: Includes assignments not visible on course homepage
- **JSON output**: Machine-readable output for agent integration

## Development

```bash
# Install dependencies
uv sync

# Run with development dependencies
uv sync --dev

# Format code
uv run ruff format
uv run ruff check --fix

# Type check
uv run mypy scripts/
```

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for:
- SSL connectivity issues in WSL
- Token management
- Current term detection details

## License

MIT License - Same as the original Hermes Agent project.

## Credits

Based on the [SJTU Canvas Skill](https://github.com/nousresearch/hermes-agent/tree/main/skills/sjtu-canvas-skill) from the Hermes Agent project by Nous Research.