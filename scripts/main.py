import os
import sys
import json
import asyncclick
from pathlib import Path
from dotenv import load_dotenv, set_key
from rich.console import Console
from rich.table import Table
from .client import CanvasClient

# Load environment variables from project .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE)

# Rich console for pretty printing
console = Console()


async def _prompt_and_maybe_save_token(json_output: bool) -> str:
    """Prompt for TOKEN and optionally persist it to .env for future runs."""
    if not json_output:
        console.print(
            "[yellow]TOKEN not found in CLI args, environment, or .env.[/yellow]"
        )

    token = await asyncclick.prompt(
        "Please enter your Canvas API token", hide_input=True
    )
    token = token.strip()
    if not token:
        raise asyncclick.Abort()

    save_token = asyncclick.confirm(
        "Save TOKEN to project .env for future runs?", default=True
    )
    if save_token:
        set_key(str(ENV_FILE), "TOKEN", token, quote_mode="never")
        if not json_output:
            console.print(f"[green]Saved TOKEN to {ENV_FILE}[/green]")

    os.environ["TOKEN"] = token
    return token


@asyncclick.group()
@asyncclick.option(
    "--token",
    envvar="TOKEN",
    default="",
    help="Canvas API token. Can also be set with TOKEN environment variable.",
)
@asyncclick.option(
    "--base-url",
    envvar="BASE_URL",
    default="https://oc.sjtu.edu.cn",
    help="Canvas base URL. Can also be set with BASE_URL environment variable.",
)
@asyncclick.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output raw JSON instead of formatted tables.",
)
@asyncclick.pass_context
async def cli(ctx, token: str, base_url: str, json_output: bool):
    """
    A CLI tool for SJTU Canvas based on the Rust implementation.
    """
    token = (token or "").strip()
    # Store token and base_url in context for commands that need them
    ctx.obj = {
        "token": token,
        "base_url": base_url,
        "json_output": json_output,
        "client": None,
    }


async def _get_client(ctx) -> CanvasClient:
    """Lazy-load the Canvas client only when needed."""
    obj = ctx.obj
    if obj["client"] is None:
        token = obj["token"]
        if not token:
            if sys.stdin.isatty():
                token = await _prompt_and_maybe_save_token(obj["json_output"])
            else:
                if obj["json_output"]:
                    print(
                        json.dumps(
                            {
                                "status": "error",
                                "message": "TOKEN missing and stdin is non-interactive.",
                            }
                        )
                    )
                else:
                    console.print(
                        "[bold red]Error: TOKEN missing and stdin is non-interactive.[/bold red]"
                    )
                raise asyncclick.Abort()

        if not obj["base_url"] or not obj["base_url"].strip():
            console.print("[bold red]Error: BASE_URL is not set or is empty.[/bold red]")
            raise asyncclick.Abort()

        obj["client"] = CanvasClient(base_url=obj["base_url"], token=token)
        obj["client"].json_output = obj["json_output"]
    return obj["client"]


@cli.command("list-courses")
@asyncclick.pass_context
async def list_courses(ctx):
    """Lists all active courses for the current user."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print("[bold cyan]Fetching courses...[/bold cyan]")
    try:
        courses = await client.get_courses()
        if client.json_output:
            active_courses = []
            for course in courses:
                if course.get("enrollment_state", "active") != "active":
                    continue
                active_courses.append(
                    {
                        "id": course.get("id"),
                        "name": course.get("name", "N/A"),
                        "course_code": course.get("course_code", "N/A"),
                        "term": course.get("term", {}).get("name", "N/A"),
                        "teachers": [
                            teacher.get("display_name", "N/A")
                            for teacher in course.get("teachers", [])
                        ],
                    }
                )
            print(json.dumps(active_courses, ensure_ascii=False))
            return
        if not courses:
            console.print("[yellow]No courses found.[/yellow]")
            return

        table = Table(title="Courses")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Course Code", style="cyan")
        table.add_column("Term", style="magenta")
        table.add_column("Teacher(s)", style="yellow")

        for course in courses:
            if course.get("enrollment_state", "active") == "active":
                teachers = ", ".join(
                    [
                        teacher.get("display_name", "N/A")
                        for teacher in course.get("teachers", [])
                    ]
                )
                term = course.get("term", {}).get("name", "N/A")
                table.add_row(
                    str(course["id"]),
                    course.get("name", "N/A"),
                    course.get("course_code", "N/A"),
                    term,
                    teachers,
                )
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("list-assignments")
@asyncclick.argument("course_id", type=int)
@asyncclick.pass_context
async def list_assignments(ctx, course_id: int):
    """Lists all assignments for a given course ID."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print(
            f"[bold cyan]Fetching assignments for course {course_id}...[/bold cyan]"
        )
    try:
        assignments = await client.get_assignments(course_id)
        if client.json_output:
            compact_assignments = []
            for assign in assignments:
                due_at = assign.get("due_at", "N/A")
                if due_at and due_at != "N/A":
                    due_at = due_at.replace("T", " ").replace("Z", "")
                compact_assignments.append(
                    {
                        "id": assign.get("id"),
                        "name": assign.get("name", "N/A"),
                        "due_at": due_at,
                        "points_possible": assign.get("points_possible", "N/A"),
                    }
                )
            print(json.dumps(compact_assignments, ensure_ascii=False))
            return
        if not assignments:
            console.print("[yellow]No assignments found for this course.[/yellow]")
            return
        table = Table(title=f"Assignments for Course {course_id}")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Due At", style="magenta")
        table.add_column("Points Possible", style="cyan")
        for assign in assignments:
            due_at = assign.get("due_at", "N/A")
            if due_at and due_at != "N/A":
                due_at = due_at.replace("T", " ").replace("Z", "")
            table.add_row(
                str(assign["id"]),
                assign.get("name", "N/A"),
                due_at,
                str(assign.get("points_possible", "N/A")),
            )
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("submit")
@asyncclick.argument("course_id", type=int)
@asyncclick.argument("assignment_id", type=int)
@asyncclick.argument("files", type=str, nargs=-1)
@asyncclick.option("--comment", "-c", help="Add a text comment to the submission.")
@asyncclick.pass_context
async def submit(
    ctx,
    course_id: int,
    assignment_id: int,
    files: tuple,
    comment: str,
):
    """Submits one or more files for an assignment."""
    if not files:
        if ctx.obj["json_output"]:
            print(
                json.dumps({"error": "You must specify at least one file to submit."})
            )
        else:
            console.print(
                "[bold red]Error: You must specify at least one file to submit.[/bold red]"
            )
        return
    client = await _get_client(ctx)
    try:
        await client.submit_assignment(course_id, assignment_id, list(files), comment)
        if client.json_output:
            print(
                json.dumps(
                    {
                        "status": "success",
                        "message": "Assignment submitted successfully",
                    }
                )
            )
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(
                f"[bold red]An error occurred during submission: {e}[/bold red]"
            )
    finally:
        await client.close()


@cli.command("get-me")
@asyncclick.pass_context
async def get_me(ctx):
    """Gets the profile of the current user."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print("[bold cyan]Fetching user profile...[/bold cyan]")
    try:
        me = await client.get_me()
        if client.json_output:
            print(
                json.dumps(
                    {
                        "id": me.get("id"),
                        "name": me.get("name"),
                        "primary_email": me.get("primary_email", "N/A"),
                        "locale": me.get("locale", "N/A"),
                        "time_zone": me.get("time_zone", "N/A"),
                    },
                    ensure_ascii=False,
                )
            )
            return
        table = Table(title="My Profile")
        table.add_column("Attribute", style="bold green")
        table.add_column("Value", style="cyan")
        table.add_row("ID", str(me.get("id")))
        table.add_row("Name", me.get("name"))
        table.add_row("Primary Email", me.get("primary_email", "N/A"))
        table.add_row("Locale", me.get("locale", "N/A"))
        table.add_row("Time Zone", me.get("time_zone", "N/A"))
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("list-files")
@asyncclick.argument("course_id", type=int)
@asyncclick.pass_context
async def list_files(ctx, course_id: int):
    """Lists all files for a given course ID."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print(
            f"[bold cyan]Fetching files for course {course_id}...[/bold cyan]"
        )
    try:
        files = await client.get_files(course_id)
        if client.json_output:
            compact_files = []
            for f in files:
                compact_files.append(
                    {
                        "id": f.get("id"),
                        "name": f.get("display_name", "N/A"),
                        "size_kb": round(f.get("size", 0) / 1024, 2),
                        "content_type": f.get("content-type", "N/A"),
                        "url": f.get("url", "N/A"),
                    }
                )
            print(json.dumps(compact_files, ensure_ascii=False))
            return
        if not files:
            console.print("[yellow]No files found for this course.[/yellow]")
            return
        table = Table(title=f"Files for Course {course_id}")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Size (KB)", style="cyan")
        table.add_column("Content Type", style="magenta")
        table.add_column("URL", style="blue", overflow="fold")
        for f in files:
            size_kb = f.get("size", 0) / 1024
            table.add_row(
                str(f["id"]),
                f.get("display_name", "N/A"),
                f"{size_kb:.2f}",
                f.get("content-type", "N/A"),
                f.get("url", "N/A"),
            )
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("list-folders")
@asyncclick.argument("course_id", type=int)
@asyncclick.pass_context
async def list_folders(ctx, course_id: int):
    """Lists all folders for a given course ID."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print(
            f"[bold cyan]Fetching folders for course {course_id}...[/bold cyan]"
        )
    try:
        folders = await client.get_folders(course_id)
        if client.json_output:
            compact_folders = []
            for folder in folders:
                compact_folders.append(
                    {
                        "id": folder.get("id"),
                        "name": folder.get("name", "N/A"),
                        "files_count": folder.get("files_count", "N/A"),
                        "full_name": folder.get("full_name", "N/A"),
                    }
                )
            print(json.dumps(compact_folders, ensure_ascii=False))
            return
        if not folders:
            console.print("[yellow]No folders found for this course.[/yellow]")
            return
        table = Table(title=f"Folders for Course {course_id}")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Files Count", style="cyan")
        table.add_column("Full Name", style="magenta")
        for folder in folders:
            table.add_row(
                str(folder["id"]),
                folder.get("name", "N/A"),
                str(folder.get("files_count", "N/A")),
                folder.get("full_name", "N/A"),
            )
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("download-file")
@asyncclick.argument("url")
@asyncclick.option("--path", default=".", help="The directory to save the file in.")
@asyncclick.pass_context
async def download_file(ctx, url: str, path: str):
    """Downloads a file from a specific URL, e.g. one from 'list-files'."""
    client = await _get_client(ctx)
    try:
        if not client.json_output:
            console.print(f"[bold cyan]Downloading from {url}...[/bold cyan]")
        result = await client.download_file(url, path)
        if client.json_output:
            print(
                json.dumps(
                    {
                        "status": "success",
                        "filename": result["filename"],
                        "path": os.path.abspath(result["path"]),
                        "size": result["size"],
                    }
                )
            )
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(
                f"[bold red]An error occurred during download: {e}[/bold red]"
            )
    finally:
        await client.close()


@cli.command("grades")
@asyncclick.argument("course_id", type=int)
@asyncclick.pass_context
async def grades(ctx, course_id: int):
    """View grades for a specific course."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print(f"[bold cyan]Fetching grades for course {course_id}...[/bold cyan]")
    try:
        grades_data = await client.get_course_grades(course_id)
        if client.json_output:
            print(json.dumps(grades_data, ensure_ascii=False))
            return
        if not grades_data:
            console.print("[yellow]No assignments found for this course.[/yellow]")
            return

        # Calculate stats
        scored = [g for g in grades_data if g["score"] is not None]
        total_possible = sum(g["points_possible"] or 0 for g in scored)
        total_score = sum(g["score"] or 0 for g in scored)

        table = Table(title=f"Grades for Course {course_id}")
        table.add_column("Assignment", style="bold green")
        table.add_column("Score", style="cyan")
        table.add_column("Points Possible", style="magenta")
        table.add_column("Grade", style="yellow")
        table.add_column("Status", style="blue")

        for g in grades_data:
            score_str = str(g["score"]) if g["score"] is not None else "—"
            grade_str = g["grade"] if g["grade"] else "—"
            status = g["workflow_state"] if g["workflow_state"] else "unsubmitted"
            table.add_row(
                g["name"],
                score_str,
                str(g["points_possible"] or "—"),
                grade_str,
                status,
            )

        console.print(table)
        if scored:
            if total_possible > 0:
                console.print(
                    f"\n[bold]Total: {total_score}/{total_possible} ({total_score/total_possible*100:.1f}%)[/bold]"
                )
            else:
                console.print("\n[bold]Total: —[/bold]")

    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("list-discussions")
@asyncclick.argument("course_id", type=int)
@asyncclick.pass_context
async def list_discussions(ctx, course_id: int):
    """List all discussion topics for a course."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print(f"[bold cyan]Fetching discussions for course {course_id}...[/bold cyan]")
    try:
        discussions = await client.list_discussions(course_id)
        if client.json_output:
            compact = []
            for d in discussions:
                compact.append({
                    "id": d.get("id"),
                    "title": d.get("title", "N/A"),
                    "message": d.get("message", "N/A")[:200] if d.get("message") else "N/A",
                    "posted_at": d.get("posted_at", "N/A"),
                    "author": d.get("author", {}).get("display_name", "N/A") if d.get("author") else "N/A",
                })
            print(json.dumps(compact, ensure_ascii=False))
            return
        if not discussions:
            console.print("[yellow]No discussions found for this course.[/yellow]")
            return

        table = Table(title=f"Discussions for Course {course_id}")
        table.add_column("ID", style="dim")
        table.add_column("Title", style="bold green")
        table.add_column("Author", style="cyan")
        table.add_column("Posted At", style="magenta")
        table.add_column("Preview", style="yellow", overflow="fold")

        for d in discussions:
            msg = d.get("message", "") or ""
            preview = msg[:100] + "..." if len(msg) > 100 else msg
            author = d.get("author", {}).get("display_name", "N/A") if d.get("author") else "N/A"
            posted = d.get("posted_at", "N/A")
            if posted and posted != "N/A":
                posted = posted.replace("T", " ").replace("Z", "")
            table.add_row(
                str(d.get("id")),
                d.get("title", "N/A"),
                author,
                posted,
                preview,
            )
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("get-discussion")
@asyncclick.argument("course_id", type=int)
@asyncclick.argument("topic_id", type=int)
@asyncclick.pass_context
async def get_discussion(ctx, course_id: int, topic_id: int):
    """Get full discussion topic with entries."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print(f"[bold cyan]Fetching discussion {topic_id}...[/bold cyan]")
    try:
        discussion = await client.get_full_discussion(course_id, topic_id)
        if client.json_output:
            print(json.dumps(discussion, ensure_ascii=False))
        else:
            console.print(f"[bold green]{discussion.get('title', 'N/A')}[/bold green]")
            console.print(f"Author: {discussion.get('author', {}).get('display_name', 'N/A')}")
            console.print(f"Posted: {discussion.get('posted_at', 'N/A')}")
            console.print(f"\n{discussion.get('message', 'N/A')}")
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("batch-download")
@asyncclick.argument("course_id", type=int)
@asyncclick.option("--path", default=None, help="Save directory (default from config or ~/Downloads/Canvas课件)")
@asyncclick.option("--ext", "extensions", multiple=True, help="File extensions to filter (e.g., .pdf .pptx)")
@asyncclick.pass_context
async def batch_download(ctx, course_id: int, path: str, extensions: tuple):
    """Batch download course files with optional extension filter."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print(f"[bold cyan]Fetching files for course {course_id}...[/bold cyan]")

    try:
        # Get course info for name
        courses = await client.get_courses()
        course = next((c for c in courses if c["id"] == course_id), None)
        if not course:
            if client.json_output:
                print(json.dumps({"status": "error", "message": "Course not found"}))
            else:
                console.print("[bold red]Course not found[/bold red]")
            return

        course_name = course.get("name", f"Course_{course_id}")
        save_dir = path or os.environ.get("SAVE_DIR", "").strip() or os.path.expanduser("~/Downloads/Canvas课件")
        ext_list = list(extensions) if extensions else None

        if not client.json_output:
            console.print(f"[dim]Saving to: {save_dir}/{course_name}[/dim]")
            if ext_list:
                console.print(f"[dim]Filtering extensions: {ext_list}[/dim]")

        downloaded = await client.download_course_files(course_id, course_name, save_dir, ext_list)

        if client.json_output:
            print(json.dumps({"status": "success", "files": downloaded}))
        else:
            console.print(f"\n[green]Downloaded {len(downloaded)} files[/green]")

    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("list-ddls")
@asyncclick.pass_context
async def list_ddls(ctx):
    """List all upcoming DDLs across all courses."""
    client = await _get_client(ctx)
    if not client.json_output:
        console.print("[bold cyan]Fetching all upcoming DDLs...[/bold cyan]")
    try:
        ddls = await client.get_all_upcoming_ddls()
        if client.json_output:
            print(json.dumps(ddls, ensure_ascii=False))
            return
        if not ddls:
            console.print("[yellow]No upcoming DDLs found.[/yellow]")
            return

        table = Table(title="Upcoming DDLs")
        table.add_column("Status", style="green")
        table.add_column("Course", style="bold cyan")
        table.add_column("Assignment", style="bold yellow")
        table.add_column("Due (Local)", style="magenta")
        table.add_column("Points", style="blue")

        for d in ddls:
            status_icon = "✅" if d["submitted"] else "❌"
            status_text = "已完成" if d["submitted"] else "未完成"
            status_style = "green" if d["submitted"] else "red"
            table.add_row(
                f"[{status_style}]{status_icon} {status_text}[/{status_style}]",
                d["course"],
                d["assignment"],
                d["due_local"],
                str(d["points"]) if d["points"] else "—",
            )

        console.print(table)
        console.print(f"\n[dim]总计: {len(ddls)} 个未来 DDL[/dim]")

    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("sync-calendar")
@asyncclick.option("--days", default=30, help="Sync DDLs within N days (default: 30)")
@asyncclick.pass_context
async def sync_calendar(ctx, days: int):
    """Sync upcoming DDLs to Apple Calendar (macOS only)."""
    if sys.platform != "darwin":
        if ctx.obj["json_output"]:
            print(json.dumps({"status": "error", "message": "Calendar sync only supported on macOS"}))
        else:
            console.print("[bold red]Calendar sync is only available on macOS[/bold red]")
        return

    client = await _get_client(ctx)
    if not client.json_output:
        console.print(f"[bold cyan]Fetching DDLs for next {days} days...[/bold cyan]")

    try:
        from datetime import datetime, timezone, timedelta
        TZ_SHANGHAI = timezone(timedelta(hours=8))
        now = datetime.now(TZ_SHANGHAI)
        end = now + timedelta(days=days)

        ddls = await client.get_all_upcoming_ddls()
        ddls = [d for d in ddls if datetime.fromisoformat(d["due_at"].replace("Z", "+00:00")).astimezone(TZ_SHANGHAI) <= end]

        if not ddls:
            if client.json_output:
                print(json.dumps({"status": "success", "message": "No DDLs to sync", "synced": 0}))
            else:
                console.print("[yellow]No DDLs to sync in the specified period.[/yellow]")
            return

        import subprocess
        import json as json_lib

        # Load calendar name: env var first, then config.json, then default
        calendar_name = os.environ.get("CALENDAR_NAME", "").strip()
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
        if not calendar_name and os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    calendar_name = json_lib.load(f).get("calendar_name", "")
            except Exception:
                calendar_name = ""
        if not calendar_name:
            calendar_name = "Canvas作业"

        def ensure_calendar():
            script = f'''
tell application "Calendar"
    set calNames to name of every calendar
    if calNames does not contain "{calendar_name}" then
        make new calendar with properties {{name:"{calendar_name}"}}
    end if
end tell
'''
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
            return r.returncode == 0

        def create_event(summary: str, due_dt, description: str = ""):
            start_hour = max(0, due_dt.hour - 1)
            script = f'''
tell application "Calendar"
    tell calendar "{calendar_name}"
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

        def list_existing():
            script = f'''
tell application "Calendar"
    tell calendar "{calendar_name}"
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

        subprocess.run(["open", "-a", "Calendar"], capture_output=True)
        import time
        time.sleep(2)

        ensure_calendar()
        existing = list_existing()

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
                if not client.json_output:
                    console.print(f"[green]✅ {summary} → {d['due_local']}[/green]")
                synced += 1
            else:
                if not client.json_output:
                    console.print(f"[red]❌ {summary}[/red]")

        if client.json_output:
            print(json.dumps({"status": "success", "synced": synced, "skipped": skipped}))
        else:
            console.print(f"\n[bold]同步完成: {synced} 新增, {skipped} 已存在[/bold]")

    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("extract-file")
@asyncclick.argument("file_path")
@asyncclick.option("--output", "-o", default=None, help="Output markdown file path")
@asyncclick.pass_context
async def extract_file(ctx, file_path: str, output: str):
    """Extract text from PPT/PDF/DOCX file to Markdown. Does not require a Canvas token."""
    json_output = ctx.obj["json_output"]
    if not os.path.exists(file_path):
        if json_output:
            print(json.dumps({"status": "error", "message": f"File not found: {file_path}"}))
        else:
            console.print(f"[bold red]File not found: {file_path}[/bold red]")
        return

    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from file_extractor import extract_to_markdown

        if not json_output:
            console.print(f"[bold cyan]Extracting: {file_path}[/bold cyan]")

        md = extract_to_markdown(file_path, output)

        if json_output:
            print(json.dumps({"status": "success", "content_length": len(md), "output": output}))
        else:
            if output:
                console.print(f"[green]Saved to: {output}[/green]")
            else:
                console.print(md[:3000])
                if len(md) > 3000:
                    console.print(f"\n[dim]... (共 {len(md)} 字符)[/dim]")

    except Exception as e:
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")


@cli.command("batch-extract")
@asyncclick.argument("directory")
@asyncclick.option("--output", "-o", default=None, help="Output directory for markdown files")
@asyncclick.option("--ext", "extensions", multiple=True, help="File extensions to include (default: .pptx .pdf .docx)")
@asyncclick.pass_context
async def batch_extract(ctx, directory: str, output: str, extensions: tuple):
    """Batch extract course materials to Markdown. Does not require a Canvas token."""
    json_output = ctx.obj["json_output"]
    if not os.path.isdir(directory):
        if json_output:
            print(json.dumps({"status": "error", "message": f"Directory not found: {directory}"}))
        else:
            console.print(f"[bold red]Directory not found: {directory}[/bold red]")
        return

    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from file_extractor import batch_extract as do_batch_extract

        ext_set = set(extensions) if extensions else {".pptx", ".pdf", ".docx"}

        if not json_output:
            console.print(f"[bold cyan]Extracting files from: {directory}[/bold cyan]")
            if output:
                console.print(f"[dim]Output directory: {output}[/dim]")

        results = do_batch_extract(directory, output, ext_set)

        if json_output:
            print(json.dumps({"status": "success", "count": len(results)}))
        else:
            console.print(f"\n[green]Extracted {len(results)} files[/green]")

    except Exception as e:
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")


async def get_current_term() -> str:
    """Get the current term based on current date."""
    from datetime import datetime
    now = datetime.now()
    year = now.year
    month = now.month

    if month >= 8 and month <= 12:
        # Fall semester: Aug-Dec (current year to next year)
        return f"{year}-{year+1} Fall"
    elif month >= 3 and month <= 7:
        # Spring semester: Mar-Jul (previous year to current year)
        return f"{year-1}-{year} Spring"
    else:
        # Jan-Feb: belongs to previous year's Fall term
        return f"{year-1}-{year} Fall"


async def filter_current_term_courses(courses: list, current_term: str) -> list:
    """Filter courses to only include current term courses."""
    filtered = []
    for course in courses:
        if course.get("enrollment_state", "active") != "active":
            continue
        term_name = course.get("term", {}).get("name", "")
        if current_term in term_name:
            filtered.append(course)
    return filtered


@cli.command("list-current-assignments")
@asyncclick.option(
    "--term",
    default=None,
    help="Specify term to filter (e.g., '2025-2026 Spring'). Defaults to current term.",
)
@asyncclick.pass_context
async def list_current_assignments(ctx, term: str):
    """
    List all unexpired assignments for the current term's courses.
    Shows submission status for each assignment.
    """
    client = await _get_client(ctx)
    if not client.json_output:
        console.print("[bold cyan]Fetching current term assignments...[/bold cyan]")

    try:
        # Determine current term
        current_term = term or await get_current_term()
        if not client.json_output:
            console.print(f"[dim]Current term: {current_term}[/dim]")

        # Get all courses
        all_courses = await client.get_courses()
        current_courses = await filter_current_term_courses(all_courses, current_term)

        if not current_courses:
            if client.json_output:
                print(json.dumps([]))
            else:
                console.print(f"[yellow]No active courses found for term: {current_term}[/yellow]")
            return

        from datetime import datetime
        now = datetime.now()

        all_assignments = []

        for course in current_courses:
            course_id = course["id"]
            course_name = course.get("name", "N/A")

            try:
                assignments = await client.get_assignments(course_id)

                for assign in assignments:
                    due_at_str = assign.get("due_at")

                    # Skip assignments with past due dates
                    if due_at_str:
                        # Robust date parsing: support ISO and transformed formats
                        try:
                            due_at = datetime.strptime(due_at_str, "%Y-%m-%dT%H:%M:%SZ")
                        except ValueError:
                            due_at = datetime.strptime(due_at_str, "%Y-%m-%d %H:%M:%S")
                        if due_at < now:
                            continue
                        due_display = due_at.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        # No due date - include it
                        due_display = "无截止日期"

                    # Check submission status
                    is_submitted, workflow_state = await client.is_assignment_submitted(
                        course_id, assign["id"]
                    )

                    status_icon = "✓" if is_submitted else "✗"
                    status_text = "已完成" if is_submitted else "未完成"

                    all_assignments.append({
                        "course_id": course_id,
                        "course_name": course_name,
                        "assignment_id": assign["id"],
                        "name": assign["name"],
                        "due_at": due_display,
                        "points_possible": assign.get("points_possible", 0),
                        "submitted": is_submitted,
                        "status": status_text,
                        "status_icon": status_icon,
                        "workflow_state": workflow_state,
                    })
            except Exception as e:
                if not client.json_output:
                    console.print(f"[red]Error fetching assignments for {course_name}: {e}[/red]")
                continue

        # Sort by due date (items without due date go last)
        all_assignments.sort(
            key=lambda x: x["due_at"] if x["due_at"] != "无截止日期" else "9999-99-99"
        )

        if client.json_output:
            # For JSON output, create compact version
            compact = []
            for a in all_assignments:
                compact.append({
                    "course": a["course_name"],
                    "name": a["name"],
                    "due_at": a["due_at"],
                    "submitted": a["submitted"],
                    "status": a["status"],
                    "id": a["assignment_id"],
                    "points": a["points_possible"],
                })
            print(json.dumps(compact, ensure_ascii=False))
            return

        if not all_assignments:
            console.print("[yellow]No upcoming assignments found for current term.[/yellow]")
            return

        # Display table
        table = Table(title=f"Current Term Assignments ({current_term})")
        table.add_column("状态", style="green")
        table.add_column("课程", style="bold cyan")
        table.add_column("作业", style="bold yellow")
        table.add_column("截止时间", style="magenta")
        table.add_column("分值", style="blue")
        table.add_column("ID", style="dim")

        for a in all_assignments:
            status_style = "green" if a["submitted"] else "red"
            table.add_row(
                f"[{status_style}]{a['status_icon']} {a['status']}[/{status_style}]",
                a["course_name"],
                a["name"],
                a["due_at"],
                str(a["points_possible"]),
                str(a["assignment_id"]),
            )

        console.print(table)
        console.print(f"\n[dim]总计: {len(all_assignments)} 个未过期作业[/dim]")

    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


def main():
    cli(_anyio_backend="asyncio")


if __name__ == "__main__":
    main()
