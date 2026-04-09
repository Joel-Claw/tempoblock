"""
Command-line interface for Tempoblock
"""

import argparse
import re
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table

from .blocker import Blocker
from .timer import Timer

console = Console()


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string like '2h', '30m', '1h30m' into minutes.

    Args:
        duration_str: Duration string

    Returns:
        Minutes
    """
    total_minutes = 0

    # Match hours
    hours_match = re.search(r"(\d+)h", duration_str)
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60

    # Match minutes
    mins_match = re.search(r"(\d+)m", duration_str)
    if mins_match:
        total_minutes += int(mins_match.group(1))

    # If just a number, assume minutes
    if not hours_match and not mins_match:
        try:
            total_minutes = int(duration_str)
        except ValueError:
            console.print("[red]Invalid duration. Use format like '2h', '30m', or '1h30m'[/red]")
            sys.exit(1)

    return total_minutes


def cmd_block(args):
    """Handle 'block' command."""
    blocker = Blocker()

    if not args.sites and not args.app:
        console.print("[red]Error: Specify at least one site or app to block[/red]")
        sys.exit(1)

    duration = parse_duration(args.duration)

    try:
        blocker.block_sites(
            sites=args.sites or [],
            duration_minutes=duration,
            app_names=args.app or None,
        )
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def cmd_status(args):
    """Handle 'status' command."""
    blocker = Blocker()
    timer = Timer()

    status = blocker.status()

    if not status["active_blocks"]:
        console.print("[dim]No active blocks[/dim]")
        return

    table = Table(title="Active Blocks")
    table.add_column("Domains/Apps", style="cyan")
    table.add_column("Remaining", style="green")
    table.add_column("End Time", style="dim")

    for block in status["active_blocks"]:
        domains_str = ", ".join(block["domains"][:3])
        if len(block["domains"]) > 3:
            domains_str += f" (+{len(block['domains']) - 3} more)"

        apps_str = ""
        if block["apps"]:
            apps_str = f"\nApps: {', '.join(block['apps'])}"

        table.add_row(
            domains_str + apps_str,
            f"{block['remaining_minutes']}m",
            datetime.fromisoformat(block["end_time"]).strftime("%H:%M:%S"),
        )

    console.print(table)

    if timer.daemon_status():
        console.print("[dim]Timer daemon running[/dim]")
    else:
        console.print("[yellow]Timer daemon not running - blocks won't auto-expire[/yellow]")


def cmd_clear(args):
    """Handle 'clear' command."""
    blocker = Blocker()

    if args.force:
        blocker.unblock_all()
    else:
        console.print("[yellow]Override requires waiting 30 seconds...[/yellow]")
        console.print("[dim]Press Ctrl+C to cancel[/dim]")

        import time

        try:
            for i in range(30, 0, -1):
                console.print(f"\r[cyan]{i}s remaining...[/cyan]", end="")
                time.sleep(1)
            console.print()
            blocker.unblock_all()
        except KeyboardInterrupt:
            console.print("\n[red]Cancelled[/red]")
            sys.exit(1)


def cmd_override(args):
    """Handle 'override' command - same as clear."""
    cmd_clear(args)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="tempoblock",
        description="Temporarily block distracting websites and apps",
    )
    parser.add_argument("--version", "-v", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Block command
    block_parser = subparsers.add_parser("block", help="Block sites/apps")
    block_parser.add_argument(
        "sites",
        nargs="*",
        help="Sites to block (domains or aliases like 'twitter')",
    )
    block_parser.add_argument(
        "--app",
        "-a",
        action="append",
        help="App to block (can specify multiple times)",
    )
    block_parser.add_argument(
        "duration",
        nargs="?",
        default="1h",
        help="Duration (e.g., 2h, 30m, 1h30m)",
    )
    block_parser.set_defaults(func=cmd_block)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show active blocks")
    status_parser.set_defaults(func=cmd_status)

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Remove all blocks")
    clear_parser.add_argument("--force", "-f", action="store_true", help="Skip 30s wait")
    clear_parser.set_defaults(func=cmd_clear)

    # Override command (alias for clear)
    override_parser = subparsers.add_parser("override", help="Emergency override (30s wait)")
    override_parser.add_argument("--force", "-f", action="store_true", help="Skip 30s wait")
    override_parser.set_defaults(func=cmd_override)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
