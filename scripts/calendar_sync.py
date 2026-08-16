#!/usr/bin/env python3
"""DDL → Apple Calendar 同步工具 (macOS only)"""

import subprocess
import sys
import json
import os
from datetime import datetime, timezone, timedelta

TZ_SHANGHAI = timezone(timedelta(hours=8))

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")


def _load_calendar_name() -> str:
    # Prefer environment variable, then config.json (value format), then default
    env_name = os.environ.get("CALENDAR_NAME", "").strip()
    if env_name:
        return env_name
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                data = json.load(f)
                name = data.get("calendar_name", "")
                if name:
                    return name
        except Exception:
            pass
    return "Canvas作业"


CALENDAR_NAME = _load_calendar_name()


def ensure_calendar() -> bool:
    """确保 Canvas作业 日历存在"""
    script = f'''
tell application "Calendar"
    set calNames to name of every calendar
    if calNames does not contain "{CALENDAR_NAME}" then
        make new calendar with properties {{name:"{CALENDAR_NAME}"}}
    end if
end tell
'''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
    return r.returncode == 0


def create_event(summary: str, due_dt: datetime, description: str = "") -> bool:
    """在 Apple Calendar 创建事件"""
    # 事件开始时间设为截止前1小时，结束时间设为截止时间
    start_hour = max(0, due_dt.hour - 1)
    script = f'''
tell application "Calendar"
    tell calendar "{CALENDAR_NAME}"
        set startDate to current date
        set year of startDate to {due_dt.year}
        set month of startDate to {due_dt.month}
        set day of startDate to {due_dt.day}
        set hours of startDate to {start_hour}
        set minutes of startDate to 0
        set seconds of startDate to 0

        set endDate to current date
        set year of endDate to {due_dt.year}
        set month of endDate to {due_dt.month}
        set day of endDate to {due_dt.day}
        set hours of endDate to {due_dt.hour}
        set minutes of endDate to {due_dt.minute}
        set seconds of endDate to 0

        make new event with properties {{summary:"{summary}", start date:startDate, end date:endDate, description:"{description}"}}
    end tell
end tell
'''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
    return r.returncode == 0


def list_existing_events() -> list:
    """列出 Canvas作业 日历中的现有事件"""
    script = f'''
tell application "Calendar"
    tell calendar "{CALENDAR_NAME}"
        set eventList to {{}}
        repeat with e in events
            set end of eventList to summary of e
        end repeat
        return eventList
    end tell
end tell
'''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        return [s.strip() for s in r.stdout.strip().split(",") if s.strip()]
    return []


def sync_ddls(ddls: list) -> int:
    """同步 DDL 列表到 Apple Calendar（跳过已存在的）"""
    # 启动日历
    subprocess.run(["open", "-a", "Calendar"], capture_output=True)
    import time
    time.sleep(2)

    ensure_calendar()
    existing = list_existing_events()

    synced = 0
    skipped = 0
    for d in ddls:
        summary = f"📝 [{d['course']}] {d['assignment']}"
        if summary in existing:
            skipped += 1
            continue

        due_str = d["due_at"]
        due_dt = datetime.fromisoformat(due_str.replace("Z", "+00:00")).astimezone(TZ_SHANGHAI)
        desc = f"课程: {d['course']}\n作业: {d['assignment']}\nDDL: {d['due_local']}\n满分: {d.get('points', '?')}"

        if create_event(summary, due_dt, desc):
            print(f"✅ {summary} → {d['due_local']}")
            synced += 1
        else:
            print(f"❌ {summary}")

    print(f"\n同步完成: {synced} 新增, {skipped} 已存在")
    return synced


if __name__ == "__main__":
    # 当直接运行时，需要从 canvas_api 导入
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from client import CanvasClient

    # 这需要配置，仅作演示
    print("请通过主 CLI 使用: uv run main sync-calendar")