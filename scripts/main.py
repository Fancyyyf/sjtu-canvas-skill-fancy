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
    if not token:
        if sys.stdin.isatty():
            token = await _prompt_and_maybe_save_token(json_output)
        else:
            if json_output:
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

    if not base_url or not base_url.strip():
        console.print("[bold red]Error: BASE_URL is not set or is empty.[/bold red]")
        raise asyncclick.Abort()

    client = CanvasClient(base_url=base_url, token=token)
    client.json_output = json_output
    ctx.obj = client


@cli.command("list-courses")
@asyncclick.pass_obj
async def list_courses(client: CanvasClient):
    """Lists all active courses for the current user."""
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
@asyncclick.pass_obj
async def list_assignments(client: CanvasClient, course_id: int):
    """Lists all assignments for a given course ID."""
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
@asyncclick.pass_obj
async def submit(
    client: CanvasClient,
    course_id: int,
    assignment_id: int,
    files: list[str],
    comment: str,
):
    """Submits one or more files for an assignment."""
    if not files:
        if client.json_output:
            print(
                json.dumps({"error": "You must specify at least one file to submit."})
            )
        else:
            console.print(
                "[bold red]Error: You must specify at least one file to submit.[/bold red]"
            )
        return
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
@asyncclick.pass_obj
async def get_me(client: CanvasClient):
    """Gets the profile of the current user."""
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
@asyncclick.pass_obj
async def list_files(client: CanvasClient, course_id: int):
    """Lists all files for a given course ID."""
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
@asyncclick.pass_obj
async def list_folders(client: CanvasClient, course_id: int):
    """Lists all folders for a given course ID."""
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
@asyncclick.pass_obj
async def download_file(client: CanvasClient, url: str, path: str):
    """Downloads a file from a specific URL, e.g. one from 'list-files'."""
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


def main():
    cli(_anyio_backend="asyncio")


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
@asyncclick.pass_obj
async def list_current_assignments(client: CanvasClient, term: str):
    """
    List all unexpired assignments for the current term's courses.
    Shows submission status for each assignment.
    """
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
                        # Canvas returns ISO format with T and Z
                        due_at = datetime.strptime(due_at_str, "%Y-%m-%dT%H:%M:%SZ")
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


if __name__ == "__main__":
    main()
