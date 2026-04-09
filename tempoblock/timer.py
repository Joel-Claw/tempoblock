"""
Timer and daemon functionality for auto-unblock
"""

import json
import signal
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console

from .blocker import Blocker

console = Console()


class Timer:
    """Manages block timers and auto-unblock."""

    def __init__(self):
        self.blocker = Blocker()
        self.data_dir = Path.home() / ".tempoblock"
        self.pid_file = self.data_dir / "daemon.pid"

    def start_daemon(self):
        """Start background daemon to monitor and unblock expired blocks."""
        import sys

        # Check if daemon already running
        if self.pid_file.exists():
            pid = int(self.pid_file.read_text().strip())
            import os

            try:
                os.kill(pid, 0)  # Check if process exists
                console.print("[yellow]Daemon already running[/yellow]")
                return
            except OSError:
                pass  # Process doesn't exist, start new one

        # Fork to background
        pid = os.fork()
        if pid > 0:
            # Parent exits
            console.print("[green]✓ Timer daemon started[/green]")
            return

        # Child continues
        os.setsid()

        # Write PID
        self.pid_file.write_text(str(os.getpid()))

        # Ignore signals
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        # Loop until no blocks remain
        while True:
            self.blocker.check_and_unblock()

            state = json.loads((self.data_dir / "state.json").read_text())
            if not state.get("blocks"):
                break

            time.sleep(60)  # Check every minute

        self.pid_file.unlink()
        sys.exit(0)

    def stop_daemon(self):
        """Stop the background daemon."""
        if not self.pid_file.exists():
            console.print("[yellow]No daemon running[/yellow]")
            return

        import os

        pid = int(self.pid_file.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            console.print("[green]✓ Daemon stopped[/green]")
        except OSError:
            console.print("[yellow]Daemon was not running[/yellow]")
        finally:
            if self.pid_file.exists():
                self.pid_file.unlink()

    def daemon_status(self) -> bool:
        """Check if daemon is running."""
        if not self.pid_file.exists():
            return False

        import os

        pid = int(self.pid_file.read_text().strip())
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            self.pid_file.unlink()
            return False

    def sleep_with_countdown(self, minutes: int, message: str = "Block active"):
        """Sleep with a countdown display (for foreground mode)."""
        end_time = datetime.now() + timedelta(minutes=minutes)

        while datetime.now() < end_time:
            remaining = end_time - datetime.now()
            mins, secs = divmod(int(remaining.total_seconds()), 60)
            console.print(f"\r[cyan]{message}: {mins:02d}:{secs:02d} remaining[/cyan]", end="")
            time.sleep(1)

        console.print()  # New line
        console.print("[green]✓ Block expired, unblocking...[/green]")
        self.blocker.unblock_all()