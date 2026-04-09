# Tempoblock

**Temporarily block distracting websites and apps for focused work.**

You know the pattern: you're trying to work, but Twitter/YouTube/Reddit keeps calling. You block them, but then you need to actually check something and unblock them, and next thing you know you've lost an hour.

Tempoblock makes blocking **temporary and intentional**.

```bash
# Block Twitter for 2 hours
tb block twitter.com 2h

# Block YouTube for 30 minutes
tb block youtube.com 30m

# Block multiple sites
tb block twitter.com youtube.com reddit.com 1h

# Block apps too (kills them and prevents relaunch)
tb block --app Discord --app Slack 45m

# Check what's blocked
tb status

# Emergency override (30s wait to make you think)
tb override

# Clear all blocks immediately
tb clear
```

## Features

- **Website blocking** via `/etc/hosts` (Linux/Mac)
- **App blocking** - kills processes and prevents relaunch
- **Timer-based** - auto-unblocks after duration
- **Emergency override** with 30-second wait (stops impulsive unblocks)
- **Session logging** - track your focused time
- **No cloud, no accounts** - everything stays local

## Installation

```bash
pip install tempoblock
```

## How It Works

### Website Blocking

Tempoblock adds entries to your `/etc/hosts` file:

```
127.0.0.1  twitter.com
127.0.0.1  www.twitter.com
```

When the timer expires, it removes them. Your original hosts file is backed up before any changes.

### App Blocking

Tempoblock uses `psutil` to kill matching processes and periodically checks for relaunches during the block period.

## Why Another Blocker?

- **Simple**: One command to block, one to check status
- **Temporary**: No permanent config changes
- **Emergency brake**: The 30-second override wait actually works
- **Local**: No accounts, no cloud, no tracking

## License

MIT