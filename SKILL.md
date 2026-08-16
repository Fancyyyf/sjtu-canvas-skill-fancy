---
name: sjtu-canvas-skill
description: Interacts with the SJTU Canvas API to manage courses, assignments, files, grades, discussions, and more. Supports file extraction (PPT/PDF/DOCX → Markdown), Apple Calendar sync, and AI-powered study workflows.
---

# SJTU Canvas Skill

This skill provides a command-line interface (CLI) to interact with the Shanghai Jiao Tong University (SJTU) Canvas Learning Management System. It allows you to access course information, manage assignments, handle files, extract course materials, sync DDLs to Apple Calendar, and more.

## 1. Configuration

Configuration is handled via CLI options, environment variables, or a `config.json` file in the project root.

> **Troubleshooting**: See [`references/troubleshooting.md`](references/troubleshooting.md) for SSL connectivity issues in WSL, token management, and current term detection details.

### Configuration File (`config.json`)

Create a `config.json` file in the project root:

```json
{
  "token": "YOUR_CANVAS_API_TOKEN",
  "base_url": "https://oc.sjtu.edu.cn",
  "save_dir": "~/Downloads/Canvas课件",
  "calendar_name": "Canvas作业",
  "current_term": "2025-2026 Spring",
  "timeout": 30,
  "cache_enabled": false,
  "cache_ttl": 300
}
```

### Environment Variables

- `TOKEN`: Your Canvas API token.
- `BASE_URL`: The base URL for the Canvas instance (defaults to `https://oc.sjtu.edu.cn`).

### CLI Options

- `--token`: Your Canvas API token.
- `--base-url`: The base URL for the Canvas instance.
- `--json`: Output raw JSON instead of formatted tables (ideal for agent usage).

### How to get an API Token

1.  Log in to your SJTU Canvas account.
2.  Go to **Account** > **Settings**.
3.  Scroll down to the **Approved Integrations** section.
4.  Click **+ New Access Token**.
5.  Give it a purpose (e.g., "Gemini CLI Agent") and an expiration date.
6.  Click **Generate Token**.
7.  **Important**: Copy the generated token immediately. You will not be able to see it again.

## 2. Commands

All commands are available via the `main` entry point. You can run them using `uv run main [command]`.

---

### **`list-courses`**

Lists all active courses for the current user.

**Command:**

```bash
uv run main list-courses
```

---

### **`list-current-assignments`** (推荐)

列出当前学期所有课程的未过期作业，并显示提交状态。这是查询作业的推荐命令。

**特点：**
- 自动识别当前学期（基于当前日期）
- 只显示未过期的作业
- 显示每个作业的提交状态（已完成/未完成）
- 包含所有课程，包括不显示在首页的作业
- 健壮解析 Canvas 返回的日期格式（支持 ISO 及已转换格式），避免因解析错误遗漏作业

**Command:**

```bash
uv run main list-current-assignments
```

**选项：**
- `--term <term>`: 指定学期（如 "2025-2026 Spring"），默认自动识别当前学期
- `--json`: 输出JSON格式（便于程序处理）

**示例输出：**
```
状态    课程                    作业                 截止时间
✓ 已完成  计算机系统基础（2）     Homework5          2026-05-10 15:59:59
✗ 未完成  高级数据结构            Lab1 Graph Database 2026-05-10 15:59:59
```

---

### **`list-ddls`**

列出所有课程的未来 DDL（截止时间），包含提交状态。比 `list-current-assignments` 更全面，适合跨学期查看。

**Command:**

```bash
uv run main list-ddls
```

---

### **`list-assignments <course_id>`**

Lists all assignments for a given course.

**Parameters:**

- `course_id`: The ID of the course.

**Command:**

```bash
uv run main list-assignments <course_id>
```

---

### **`grades <course_id>`**

查看指定课程的所有作业成绩，自动计算已出成绩的加权总分。

**Command:**

```bash
uv run main grades <course_id>
```

---

### **`submit <course_id> <assignment_id> <files...>`**

Submits one or more files for an assignment.

**Parameters:**

- `course_id`: The ID of the course.
- `assignment_id`: The ID of the assignment.
- `files`: One or more paths to the files to submit.

**Options:**

- `--comment <comment>`: Add a text comment to the submission.

**Command:**

```bash
uv run main submit <course_id> <assignment_id> <file1> <file2> --comment "My submission"
```

---

### **`get-me`**

Gets the profile of the current user.

**Command:**

```bash
uv run main get-me
```

---

### **`list-files <course_id>`**

Lists all files for a given course.

**Parameters:**

- `course_id`: The ID of the course.

**Command:**

```bash
uv run main list-files <course_id>
```

---

### **`list-folders <course_id>`**

Lists all folders for a given course.

**Parameters:**

- `course_id`: The ID of the course.

**Command:**

```bash
uv run main list-folders <course_id>
```

---

### **`batch-download <course_id>`**

批量下载课程文件，支持按扩展名过滤（如只下载 PDF/PPTX）。

**Parameters:**

- `course_id`: The ID of the course.

**Options:**

- `--path <path>`: 保存目录（默认从 config.json 读取或 ~/Downloads/Canvas课件）
- `--ext <ext>`: 文件扩展名过滤，可多次指定（如 `--ext .pdf --ext .pptx`）

**Command:**

```bash
uv run main batch-download <course_id> --path ~/Downloads/Courses --ext .pdf --ext .pptx
```

---

### **`download-file <url>`**

Downloads a file from a specific URL.

**Parameters:**

- `url`: The URL of the file to download.

**Options:**

- `--path <path>`: The directory to save the file in (defaults to the current directory).

**Command:**

```bash
uv run main download-file <file_url> --path /path/to/save
```

---

### **`list-discussions <course_id>`**

列出课程的讨论区话题。

**Command:**

```bash
uv run main list-discussions <course_id>
```

---

### **`get-discussion <course_id> <topic_id>`**

获取讨论区话题的完整内容（包含回复）。

**Command:**

```bash
uv run main get-discussion <course_id> <topic_id>
```

---

### **`sync-calendar`**

将未来 N 天内的 DDL 同步到 Apple Calendar（仅限 macOS）。通过 iCloud 自动推送到 iPhone。

**Options:**

- `--days <days>`: 同步未来多少天内的 DDL（默认 30 天）

**Command:**

```bash
uv run main sync-calendar --days 30
```

---

### **`extract-file <file_path>`**

提取 PPT/PDF/DOCX 文件内容为 Markdown，便于 AI 总结或学习。

**Parameters:**

- `file_path`: 要提取的文件路径。

**Options:**

- `--output, -o <path>`: 输出 Markdown 文件路径（不指定则打印到标准输出）

**Command:**

```bash
uv run main extract-file lecture.pptx -o lecture.md
```

**支持格式：** `.pptx`, `.ppt`, `.pdf`, `.docx`, `.txt`, `.md`

---

### **`batch-extract <directory>`**

批量提取目录下所有课件为 Markdown，适合生成期末复习包。

**Parameters:**

- `directory`: 包含课件的目录路径。

**Options:**

- `--output, -o <path>`: 输出目录（生成对应的 .md 文件）
- `--ext <ext>`: 包含的文件扩展名（默认 `.pptx .pdf .docx`）

**Command:**

```bash
uv run main batch-extract ~/Downloads/Canvas课件/传热学 -o ~/Downloads/Canvas课件/传热学_md
```

---

## 3. Complex Workflows (Recommended for Agents)

When users provide a **Chinese course name** instead of a numeric `course_id`, always resolve the course ID first, then run downstream commands.

### Workflow A: Chinese Course Name -> Course ID -> Course Queries

1. List courses in JSON mode:

```bash
uv run main --json list-courses
```

2. Find the target course by name (exact match or contains match), then extract its `id`.

3. Use that `course_id` for follow-up operations, for example:

```bash
uv run main list-assignments <course_id>
uv run main list-folders <course_id>
uv run main list-files <course_id>
uv run main grades <course_id>
uv run main batch-download <course_id> --ext .pdf
```

Important:

- Never guess `course_id` from the course name.
- If multiple courses match the same Chinese name, ask the user to confirm by showing candidate IDs and term names.

### Workflow B: Course ID -> List Files -> Download URL -> Download File

For file downloads, do not call `download-file` directly unless you already have a valid file URL.

1. Resolve `course_id` first (use Workflow A if needed).

2. List files for that course:

```bash
uv run main --json list-files <course_id>
```

3. From the returned file list, select the target file and read its `url` field.

4. Download using the URL:

```bash
uv run main download-file "<file_url>" --path ./downloads
```

Important:

- The download URL is usually time-limited; fetch and use it promptly.
- If download fails due to expired signature, re-run `list-files` to obtain a fresh URL and retry.

### Workflow C: Query Current Semester Assignments (Optimized for Users)

When user asks about "作业" (assignments), follow these principles:

1. **Default to current semester only**: Determine current semester (e.g., "2025-2026 Spring") and only query courses from that term. User doesn't care about past semesters.

2. **Filter out expired assignments**: Skip assignments where `due_at` is in the past. Only show future or no-deadline assignments.

3. **Scan ALL courses thoroughly**: Some assignments don't appear on the course homepage but exist in the full assignments list. Always use `list-assignments` command for each course, not just what's shown on homepage.

4. **Show completion status**: Show whether each assignment has been submitted (✓/✗).

5. **Include no-deadline assignments**: Assignments with `due_at: null` should also be displayed, as they may still need completion.

**Key principle**: When user says "作业", they mean CURRENT semester assignments only.

### Workflow D: AI-Powered Study (课件总结 + 作业辅导)

1. **下载课件**: `batch-download <course_id> --ext .pdf --ext .pptx`
2. **提取内容**: `batch-extract <download_dir> -o <output_dir>`
3. **AI 总结**: 将提取的 Markdown 发送给 LLM 生成学习笔记
4. **作业辅导**: 结合作业要求和对应课件内容，给出解题思路

### Workflow E: DDL Management

1. **查看所有 DDL**: `list-ddls`
2. **同步到日历**: `sync-calendar --days 30` (macOS)
3. **定期巡检**: 可设置 cron 定时运行 `list-ddls --json` 并推送通知

### Workflow F: 期末复习包生成

1. `batch-download` 下载所有课程课件
2. `batch-extract` 批量转为 Markdown
3. 导入 NotebookLM 或其他 RAG 工具进行复习

---

## 4. Python API Usage

You can also use the skill programmatically in Python:

```python
import sys
sys.path.insert(0, "scripts")
from client import CanvasClient

client = CanvasClient(base_url="https://oc.sjtu.edu.cn", token="YOUR_TOKEN")

# 课程列表
courses = await client.get_courses()

# 作业列表
assignments = await client.get_assignments(course_id)

# 成绩
grades = await client.get_course_grades(course_id)

# 所有未来 DDL
ddls = await client.get_all_upcoming_ddls()

# 批量下载
await client.download_course_files(course_id, course_name, save_dir, [".pdf", ".pptx"])

# 讨论区
discussions = await client.list_discussions(course_id)
full_discussion = await client.get_full_discussion(course_id, topic_id)

# 提交作业
await client.submit_assignment(course_id, assignment_id, ["file1.pdf"], "comment")

await client.close()
```

---

## 5. Dependencies

Core dependencies (installed via `uv sync`):
- `aiohttp` - Async HTTP client
- `asyncclick` - Async CLI framework
- `rich` - Terminal formatting
- `yarl` - URL handling
- `python-dotenv` - Environment file loading
- `pydantic` - Data validation

Optional dependencies for file extraction (install as needed):
- `python-pptx` - PPTX extraction
- `pdfplumber` - PDF extraction
- `python-docx` - DOCX extraction

Install optional deps:
```bash
uv pip install python-pptx pdfplumber python-docx
```