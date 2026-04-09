"""
Core blocking functionality
"""
from __future__ import annotations

import json
import os
import platform
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from rich.console import Console

console = Console()

# Common website aliases
WEBSITE_ALIASES = {
    "twitter": ["twitter.com", "x.com", "www.twitter.com", "www.x.com"],
    "youtube": ["youtube.com", "www.youtube.com", "youtu.be"],
    "reddit": ["reddit.com", "www.reddit.com"],
    "facebook": ["facebook.com", "www.facebook.com", "m.facebook.com"],
    "instagram": ["instagram.com", "www.instagram.com"],
    "tiktok": ["tiktok.com", "www.tiktok.com"],
    "discord": ["discord.com", "discord.gg", "www.discord.com"],
    "twitch": ["twitch.tv", "www.twitch.tv"],
    "linkedin": ["linkedin.com", "www.linkedin.com"],
    "news": [
        "cnn.com",
        "bbc.com",
        "nytimes.com",
        "theguardian.com",
        "reuters.com",
        "bbc.co.uk",
    ],
}

# App process names
APP_PROCESSES = {
    "discord": ["Discord", "discord"],
    "slack": ["slack", "Slack"],
    "spotify": ["spotify", "Spotify"],
    "steam": ["steam", "Steam"],
    "zoom": ["zoom", "Zoom"],
    "teams": ["teams", "Microsoft Teams"],
    "skype": ["skype", "Skype"],
}


class Blocker:
    """Manages website and app blocking."""

    def __init__(self):
        self.system = platform.system()
        if self.system == "Linux":
            self.hosts_path = Path("/etc/hosts")
        elif self.system == "Darwin":
            self.hosts_path = Path("/etc/hosts")
        elif self.system == "Windows":
            self.hosts_path = (
                Path(os.environ["SYSTEMROOT"]) / "system32" / "drivers" / "etc" / "hosts"
            )
        else:
            raise RuntimeError(f"Unsupported system: {self.system}")

        self.data_dir = Path.home() / ".tempoblock"
        self.data_dir.mkdir(exist_ok=True)
        self.state_file = self.data_dir / "state.json"
        self.backup_file = self.data_dir / "hosts_backup"

    def _load_state(self) -> dict:
        """Load current state."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "blocks": [],
            "original_hosts": None,
        }

    def _save_state(self, state: dict):
        """Save current state."""
        self.state_file.write_text(json.dumps(state, indent=2))

    def _get_hosts_content(self) -> str:
        """Read hosts file content."""
        return self.hosts_path.read_text()

    def _write_hosts(self, content: str):
        """Write hosts file (requires sudo on Linux/Mac)."""
        if self.system in ("Linux", "Darwin"):
            # Use tee to write with sudo
            import subprocess

            result = subprocess.run(
                ["sudo", "tee", str(self.hosts_path)],
                input=content.encode(),
                capture_output=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Failed to write hosts file: {result.stderr.decode()}")
        else:
            self.hosts_path.write_text(content)

    def _backup_hosts(self):
        """Backup original hosts file."""
        if not self.backup_file.exists():
            shutil.copy(self.hosts_path, self.backup_file)

    def block_sites(
        self,
        sites: List[str],
        duration_minutes: int,
        app_names: Optional[List[str]] = None,
    ):
        """
        Block websites (and optionally apps) for a duration.

        Args:
            sites: List of sites to block (domains or aliases like "twitter")
            duration_minutes: How long to block in minutes
            app_names: Optional list of app names to block
        """
        # Expand aliases
        domains = []
        for site in sites:
            if site.lower() in WEBSITE_ALIASES:
                domains.extend(WEBSITE_ALIASES[site.lower()])
            else:
                # Add both with and without www
                domains.append(site)
                if not site.startswith("www."):
                    domains.append(f"www.{site}")

        domains = list(set(domains))  # Remove duplicates

        # Backup hosts
        self._backup_hosts()

        # Read current hosts
        hosts_content = self._get_hosts_content()

        # Add block entries
        block_entries = []
        for domain in domains:
            entry = f"127.0.0.1  {domain}"
            if entry not in hosts_content:
                block_entries.append(entry)

        if block_entries:
            # Calculate end time
            end_time = datetime.now() + timedelta(minutes=duration_minutes)

            # Write new hosts
            new_content = hosts_content.rstrip() + "\n\n# Tempoblock Start\n"
            new_content += "\n".join(block_entries) + "\n"
            new_content += f"# Tempoblock End: {end_time.isoformat()}\n"

            self._write_hosts(new_content)

            # Save state
            state = self._load_state()
            state["blocks"].append(
                {
                    "domains": domains,
                    "apps": app_names or [],
                    "start_time": datetime.now().isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_minutes": duration_minutes,
                }
            )
            self._save_state(state)

            console.print(
                f"[green]✓ Blocked {len(domains)} domains for {duration_minutes}m[/green]"
            )
            if app_names:
                console.print(f"[green]  Apps: {', '.join(app_names)}[/green]")

    def unblock_all(self):
        """Remove all blocks."""
        state = self._load_state()

        if self.backup_file.exists():
            # Restore original hosts
            original = self.backup_file.read_text()
            self._write_hosts(original)
            console.print("[green]✓ Removed all blocks[/green]")
        else:
            # Remove just our entries
            hosts_content = self._get_hosts_content()
            lines = hosts_content.split("\n")
            new_lines = []
            in_block = False

            for line in lines:
                if "# Tempoblock Start" in line:
                    in_block = True
                    continue
                if "# Tempoblock End" in line:
                    in_block = False
                    continue
                if not in_block:
                    new_lines.append(line)

            self._write_hosts("\n".join(new_lines))
            console.print("[green]✓ Removed all blocks[/green]")

        # Clear state
        state["blocks"] = []
        self._save_state(state)

    def status(self) -> dict:
        """Get current blocking status."""
        state = self._load_state()
        active_blocks = []

        for block in state.get("blocks", []):
            end_time = datetime.fromisoformat(block["end_time"])
            if datetime.now() < end_time:
                remaining = end_time - datetime.now()
                active_blocks.append(
                    {
                        "domains": block["domains"],
                        "apps": block.get("apps", []),
                        "remaining_minutes": int(remaining.total_seconds() / 60),
                        "end_time": block["end_time"],
                    }
                )

        return {
            "active_blocks": active_blocks,
            "total_blocked": sum(len(b["domains"]) for b in active_blocks),
        }

    def check_and_unblock(self):
        """Check if any blocks have expired and unblock them."""
        state = self._load_state()
        active_blocks = []

        for block in state.get("blocks", []):
            end_time = datetime.fromisoformat(block["end_time"])
            if datetime.now() >= end_time:
                console.print(f"[dim]Block expired: {block['domains'][:3]}...[/dim]")
            else:
                active_blocks.append(block)

        if len(active_blocks) != len(state.get("blocks", [])):
            # Some blocks expired, update hosts
            if not active_blocks:
                self.unblock_all()
            else:
                # Rewrite hosts with only active blocks
                original = self.backup_file.read_text() if self.backup_file.exists() else ""
                if original:
                    new_content = original.rstrip() + "\n\n"
                    for block in active_blocks:
                        new_content += "# Tempoblock Start\n"
                        for domain in block["domains"]:
                            new_content += f"127.0.0.1  {domain}\n"
                        new_content += f"# Tempoblock End: {block['end_time']}\n"
                    self._write_hosts(new_content)

            state["blocks"] = active_blocks
            self._save_state(state)
