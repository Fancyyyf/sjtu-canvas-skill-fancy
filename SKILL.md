---
name: sjtu-canvas-skill
description: Interacts with the SJTU Canvas API to manage courses, assignments, and files. Use this skill for tasks related to SJTU Canvas.
---

# SJTU Canvas Skill

This skill provides a command-line interface (CLI) to interact with the Shanghai Jiao Tong University (SJTU) Canvas Learning Management System. It allows you to access course information, manage assignments, and handle files.

## 1. Configuration

Configuration is handled via CLI options or environment variables. You can also create a `.env` file in the project root to store your credentials.

> **Troubleshooting**: See [`references/troubleshooting.md`](references/troubleshooting.md) for SSL connectivity issues in WSL, token management, and current term detection details.

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

### **`list-assignments <course_id>`**

Lists all assignments for a given course.

**Parameters:**

- `course_id`: The ID of the course.

**Command:**

```bash
uv run main list-assignments <course_id>
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

4. **Show completion status** (Future enhancement): Ideally show whether each assignment has been submitted. This requires Canvas API `/submissions` endpoint (not yet implemented in this skill).

5. **Include no-deadline assignments**: Assignments with `due_at: null` should also be displayed, as they may still need completion.

Example query pattern:

```bash
# Step 1: List all courses and filter by current semester
uv run main --json list-courses | jq '.[] | select(.term | contains("Spring"))'

# Step 2: For each course ID, list assignments and filter future/no-deadline ones
for course_id in <spring_course_ids>; do
  uv run main --json list-assignments $course_id
done
```

**Key principle**: When user says "作业", they mean CURRENT semester assignments only.
