# Member Depot Bot

A Discord utility and moderation bot built for the **Member Depot** server — a place where people can farm free Discord server members to grow their own servers.

## Features

- **Moderation** — ban, unban, kick, mute, unmute, warn, purge, slowmode, lock, unlock, nick, role
- **Anti-Nuke** — detects and stops mass bans, kicks, channel deletions, role deletions, and webhook spam
- **Utility** — ping, serverinfo, userinfo, avatar, botinfo, help, embed
- **Welcome/Leave messages** — auto-posted to `#welcome` or `#general`
- **Branding** — every embed footer says `Member Depot | Made by Stichachu13`

## Setup

1. Add `DISCORD_TOKEN` as a secret (the bot token from Discord Developer Portal)
2. Start the bot via the Run button
3. Slash commands sync automatically on startup

## File Structure

- `main.py` — entry point, loads cogs, handles events
- `config.py` — branding, colors, anti-nuke thresholds
- `cogs/moderation.py` — moderation slash commands
- `cogs/antinuke.py` — anti-nuke protection system
- `cogs/utility.py` — utility slash commands

## User Preferences

- Every embed must have footer: `Member Depot | Made by Stichachu13`
- Bot name: Member Depot Bot
- Owner credit: Stichachu13
