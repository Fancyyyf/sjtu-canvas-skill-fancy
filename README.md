# SJTU Canvas Skill - Fancy's Fork

A personal fork of the [SJTU Canvas Skill](https://github.com/nousresearch/hermes-agent/tree/main/skills/sjtu-canvas-skill) for interacting with the Shanghai Jiao Tong University Canvas LMS.

## Overview

This skill provides a command-line interface (CLI) to interact with the SJTU Canvas Learning Management System. It allows you to:

- List courses and assignments
- Query current semester assignments with completion status
- Submit assignments
- Manage files and folders
- Download course materials

## Installation

```bash
cd sjtu-canvas-skill-fancy
uv sync
```

## Configuration

Create a `.env` file in the project root:

```env
TOKEN=your_canvas_api_token
BASE_URL=https://oc.sjtu.edu.cn  # Optional, defaults to this value
```

### Getting an API Token

1. Log in to your SJTU Canvas account
2. Go to **Account** > **Settings**
3. Scroll down to **Approved Integrations**
4. Click **+ New Access Token**
5. Give it a purpose and expiration date
6. Click **Generate Token** and copy it immediately

## Usage

All commands are available via the `main` entry point:

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

### Options

- `--json`: Output raw JSON instead of formatted tables
- `--term <term>`: Specify term (e.g., "2025-2026 Spring"), defaults to auto-detect current term

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
├── config.json          # Configuration schema
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

# Run tests (if any)
uv run pytest

# Format code
uv run ruff format
uv run ruff check --fix
```

## License

MIT License - Same as the original Hermes Agent project.