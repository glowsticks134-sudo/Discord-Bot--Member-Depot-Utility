import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import json
import os
import asyncio
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import config

DATA_FILE = "data/activity.json"


# ── Persistence ───────────────────────────────────────────────────────────────

def load_data():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        return {"guilds": {}, "activity": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Helpers ───────────────────────────────────────────────────────────────────

def progress_bar(current, total, length=20):
    filled = min(int(length * current / total), length) if total > 0 else 0
    return "█" * filled + "░" * (length - filled)


def get_today(timezone_str="UTC"):
    try:
        tz = ZoneInfo(timezone_str)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.datetime.now(tz).date().isoformat()


def get_guild_settings(data, guild_id):
    gid = str(guild_id)
    if gid not in data["guilds"]:
        data["guilds"][gid] = {
            "role_id": None,
            "requirement": 35,
            "timezone": "UTC",
            "announcement_channel": None,
            "last_reset": None,
        }
    return data["guilds"][gid]


def get_user_activity(data, guild_id, user_id):
    gid = str(guild_id)
    uid = str(user_id)
    if gid not in data["activity"]:
        data["activity"][gid] = {}
    if uid not in data["activity"][gid]:
        data["activity"][gid][uid] = {
            "count": 0,
            "last_message": "",
            "last_message_time": 0,
            "streak": 0,
            "last_completed": None,
            "completed_today": False,
            "date": get_today(),
        }
    return data["activity"][gid][uid]


def activity_embed(title=None, description=None, color=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color or config.COLOR_PRIMARY,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=config.FOOTER_TEXT)
    return embed


# ── Setup Modal ───────────────────────────────────────────────────────────────

class ActivitySetupModal(discord.ui.Modal, title="Activity System Setup"):
    req_input = discord.ui.TextInput(
        label="Required Messages (default: 35)",
        placeholder="35",
        required=False,
        max_length=4,
    )
    tz_input = discord.ui.TextInput(
        label="Timezone (e.g. America/New_York)",
        placeholder="UTC",
        required=False,
        max_length=60,
    )

    def __init__(self, role, channel):
        super().__init__()
        self.role = role
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        settings = get_guild_settings(data, interaction.guild.id)

        req_raw = self.req_input.value.strip()
        tz_str = self.tz_input.value.strip() or "UTC"

        try:
            requirement = max(1, int(req_raw)) if req_raw else 35
        except ValueError:
            requirement = 35

        try:
            ZoneInfo(tz_str)
        except ZoneInfoNotFoundError:
            tz_str = "UTC"

        if self.role:
            settings["role_id"] = self.role.id
        if self.channel:
            settings["announcement_channel"] = self.channel.id
        settings["requirement"] = requirement
        settings["timezone"] = tz_str
        save_data(data)

        embed = activity_embed("✅ Activity System Configured", color=config.COLOR_SUCCESS)
        embed.add_field(name="Role", value=self.role.mention if self.role else "Unchanged", inline=True)
        embed.add_field(name="Required Messages", value=str(requirement), inline=True)
        embed.add_field(name="Timezone", value=f"`{tz_str}`", inline=True)
        embed.add_field(
            name="Announcement Channel",
            value=self.channel.mention if self.channel else "Unchanged",
            inline=True,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Cog ───────────────────────────────────────────────────────────────────────

class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._lock = asyncio.Lock()
        self.daily_reset_loop.start()

    def cog_unload(self):
        self.daily_reset_loop.cancel()

    # ── Scheduled Reset ───────────────────────────────────────────────────────

    @tasks.loop(minutes=1)
    async def daily_reset_loop(self):
        data = load_data()
        changed = False
        for gid, settings in data["guilds"].items():
            tz_str = settings.get("timezone", "UTC")
            try:
                tz = ZoneInfo(tz_str)
            except Exception:
                tz = ZoneInfo("UTC")
            now = datetime.datetime.now(tz)
            today = now.date().isoformat()
            if now.hour == 0 and now.minute == 0 and settings.get("last_reset") != today:
                await self._do_reset(int(gid), data, settings, today)
                changed = True
        if changed:
            save_data(data)

    @daily_reset_loop.before_loop
    async def before_daily_reset_loop(self):
        await self.bot.wait_until_ready()

    async def _do_reset(self, guild_id: int, data: dict, settings: dict, today: str):
        gid = str(guild_id)
        guild = self.bot.get_guild(guild_id)
        role_id = settings.get("role_id")
        role = guild.get_role(role_id) if guild and role_id else None

        # Update streaks then wipe counts
        for uid, udata in data.get("activity", {}).get(gid, {}).items():
            if udata.get("completed_today"):
                udata["streak"] = udata.get("streak", 0) + 1
                udata["last_completed"] = udata.get("date")
            else:
                udata["streak"] = 0
            udata["count"] = 0
            udata["completed_today"] = False
            udata["date"] = today

        # Strip role from every member
        if role and guild:
            for member in guild.members:
                if role in member.roles:
                    try:
                        await member.remove_roles(role, reason="Daily activity reset")
                    except Exception:
                        pass

        settings["last_reset"] = today

        # Announce reset
        ann_id = settings.get("announcement_channel")
        if guild and ann_id:
            ch = guild.get_channel(ann_id)
            if ch:
                embed = activity_embed(
                    "🔄 Daily Activity Reset",
                    f"Daily counts have been reset.\nEarn **{settings.get('requirement', 35)} messages** today to unlock farming access!",
                    config.COLOR_INFO,
                )
                try:
                    await ch.send(embed=embed)
                except Exception:
                    pass

    # ── Message Listener ──────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot or message.webhook_id:
            return
        # Ignore prefix commands
        if message.content.startswith(config.PREFIX):
            return
        # Minimum length
        content = message.content.strip()
        if len(content) < 5:
            return

        async with self._lock:
            data = load_data()
            settings = get_guild_settings(data, message.guild.id)
            udata = get_user_activity(data, message.guild.id, message.author.id)
            today = get_today(settings.get("timezone", "UTC"))

            # New day — reset this user
            if udata.get("date") != today:
                udata["count"] = 0
                udata["completed_today"] = False
                udata["date"] = today

            # Already unlocked today
            if udata.get("completed_today"):
                save_data(data)
                return

            now_ts = time.time()

            # Anti-spam: 2-second cooldown per user
            if now_ts - udata.get("last_message_time", 0) < 2:
                save_data(data)
                return

            # Anti-spam: duplicate message
            if content == udata.get("last_message", ""):
                save_data(data)
                return

            udata["count"] = udata.get("count", 0) + 1
            udata["last_message"] = content
            udata["last_message_time"] = now_ts

            requirement = settings.get("requirement", 35)

            if udata["count"] >= requirement:
                udata["completed_today"] = True
                save_data(data)
                await self._grant_access(message, settings)
            else:
                save_data(data)

    async def _grant_access(self, message: discord.Message, settings: dict):
        guild = message.guild
        member = message.author
        role_id = settings.get("role_id")
        role = guild.get_role(role_id) if role_id else None

        if role:
            try:
                await member.add_roles(role, reason="Daily activity requirement met")
            except Exception:
                pass

        # DM the member
        try:
            dm = discord.Embed(
                title="🎉 Congratulations!",
                description=(
                    f"You completed today's activity requirement in **{guild.name}**!\n\n"
                    "You now have access to today's farming channels. See you tomorrow! 🌟"
                ),
                color=config.COLOR_SUCCESS,
                timestamp=datetime.datetime.utcnow(),
            )
            dm.set_footer(text=config.FOOTER_TEXT)
            await member.send(embed=dm)
        except Exception:
            pass

        # Server announcement
        ann_id = settings.get("announcement_channel")
        target = guild.get_channel(ann_id) if ann_id else message.channel
        if target:
            embed = discord.Embed(
                description=f"✅ {member.mention} has unlocked today's farming access!",
                color=config.COLOR_SUCCESS,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_footer(text=config.FOOTER_TEXT)
            try:
                await target.send(embed=embed)
            except Exception:
                pass

    # ── Admin Slash Commands ──────────────────────────────────────────────────

    activity_group = app_commands.Group(name="activity", description="Daily activity system")

    @activity_group.command(name="setup", description="Configure the activity system")
    @app_commands.describe(
        role="Role to grant when a member completes the requirement",
        channel="Channel for unlock announcements and reset notices",
    )
    @app_commands.default_permissions(administrator=True)
    async def activity_setup(
        self,
        interaction: discord.Interaction,
        role: discord.Role = None,
        channel: discord.TextChannel = None,
    ):
        await interaction.response.send_modal(ActivitySetupModal(role, channel))

    @activity_group.command(name="role", description="Set or view the activity unlock role")
    @app_commands.describe(role="Role to grant (omit to view current)")
    @app_commands.default_permissions(administrator=True)
    async def activity_role(self, interaction: discord.Interaction, role: discord.Role = None):
        data = load_data()
        settings = get_guild_settings(data, interaction.guild.id)
        if role:
            settings["role_id"] = role.id
            save_data(data)
            embed = activity_embed(description=f"✅ Activity role set to {role.mention}.", color=config.COLOR_SUCCESS)
        else:
            r = interaction.guild.get_role(settings.get("role_id")) if settings.get("role_id") else None
            embed = activity_embed(description=f"Current activity role: {r.mention if r else '`Not set`'}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @activity_group.command(name="requirement", description="Set or view the daily message requirement")
    @app_commands.describe(amount="Number of messages required (omit to view current)")
    @app_commands.default_permissions(administrator=True)
    async def activity_requirement(self, interaction: discord.Interaction, amount: int = None):
        data = load_data()
        settings = get_guild_settings(data, interaction.guild.id)
        if amount is not None:
            settings["requirement"] = max(1, amount)
            save_data(data)
            embed = activity_embed(description=f"✅ Requirement set to **{amount}** messages.", color=config.COLOR_SUCCESS)
        else:
            embed = activity_embed(description=f"Current requirement: **{settings.get('requirement', 35)}** messages.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @activity_group.command(name="timezone", description="Set or view the daily reset timezone")
    @app_commands.describe(timezone="IANA timezone e.g. America/New_York (omit to view current)")
    @app_commands.default_permissions(administrator=True)
    async def activity_timezone(self, interaction: discord.Interaction, timezone: str = None):
        data = load_data()
        settings = get_guild_settings(data, interaction.guild.id)
        if timezone:
            try:
                ZoneInfo(timezone)
                settings["timezone"] = timezone
                save_data(data)
                embed = activity_embed(description=f"✅ Timezone set to `{timezone}`.", color=config.COLOR_SUCCESS)
            except ZoneInfoNotFoundError:
                embed = activity_embed(
                    description="❌ Invalid timezone. Use a valid IANA string e.g. `America/New_York`, `Europe/London`.",
                    color=config.COLOR_ERROR,
                )
        else:
            embed = activity_embed(description=f"Current timezone: `{settings.get('timezone', 'UTC')}`")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @activity_group.command(name="reset", description="Manually reset all daily activity now")
    @app_commands.default_permissions(administrator=True)
    async def activity_reset(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with self._lock:
            data = load_data()
            settings = get_guild_settings(data, interaction.guild.id)
            today = get_today(settings.get("timezone", "UTC"))
            await self._do_reset(interaction.guild.id, data, settings, today)
            save_data(data)
        embed = activity_embed("✅ Manual reset complete.", "All daily counts cleared and unlock roles removed.", config.COLOR_SUCCESS)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @activity_group.command(name="stats", description="View activity stats for any member")
    @app_commands.describe(member="Member to check (defaults to you)")
    @app_commands.default_permissions(administrator=True)
    async def activity_stats(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        data = load_data()
        settings = get_guild_settings(data, interaction.guild.id)
        udata = get_user_activity(data, interaction.guild.id, member.id)
        today = get_today(settings.get("timezone", "UTC"))
        count = udata.get("count", 0) if udata.get("date") == today else 0
        completed = udata.get("completed_today", False) if udata.get("date") == today else False
        req = settings.get("requirement", 35)
        streak = udata.get("streak", 0)
        color = config.COLOR_SUCCESS if completed else (config.COLOR_WARNING if count > 0 else config.COLOR_ERROR)
        embed = discord.Embed(
            title=f"📊 Activity — {member.display_name}",
            color=color,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="Today's Progress",
            value=f"`{progress_bar(count, req)}`\n**{count} / {req}** messages",
            inline=False,
        )
        embed.add_field(name="Status", value="✅ Unlocked" if completed else "❌ Locked", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{streak}** day(s)", inline=True)
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── User Slash Commands ───────────────────────────────────────────────────

    @activity_group.command(name="me", description="Check your daily activity progress")
    async def activity_me(self, interaction: discord.Interaction):
        data = load_data()
        settings = get_guild_settings(data, interaction.guild.id)
        udata = get_user_activity(data, interaction.guild.id, interaction.user.id)
        today = get_today(settings.get("timezone", "UTC"))
        count = udata.get("count", 0) if udata.get("date") == today else 0
        completed = udata.get("completed_today", False) if udata.get("date") == today else False
        req = settings.get("requirement", 35)
        streak = udata.get("streak", 0)
        color = config.COLOR_SUCCESS if completed else (config.COLOR_WARNING if count > 0 else config.COLOR_ERROR)
        embed = discord.Embed(
            title="📊 Today's Activity",
            color=color,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(
            name="Progress",
            value=f"`{progress_bar(count, req)}`\n**{count} / {req}** messages",
            inline=False,
        )
        embed.add_field(name="Status", value="✅ Unlocked" if completed else "❌ Locked", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{streak}** day(s)", inline=True)
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="View today's most active members")
    async def leaderboard(self, interaction: discord.Interaction):
        data = load_data()
        settings = get_guild_settings(data, interaction.guild.id)
        today = get_today(settings.get("timezone", "UTC"))
        req = settings.get("requirement", 35)
        gid = str(interaction.guild.id)
        guild_activity = data.get("activity", {}).get(gid, {})

        entries = [
            (int(uid), udata.get("count", 0), udata.get("completed_today", False))
            for uid, udata in guild_activity.items()
            if udata.get("date") == today
        ]
        entries.sort(key=lambda x: x[1], reverse=True)
        top = entries[:10]

        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        lines = []
        for i, (uid, count, completed) in enumerate(top):
            member = interaction.guild.get_member(uid)
            name = member.display_name if member else f"User {uid}"
            lock = "✅" if completed else "❌"
            lines.append(f"{medals[i]} **{name}** {lock}\n`{progress_bar(count, req, 12)}` {count}/{req}")

        embed = discord.Embed(
            title="🏆 Daily Activity Leaderboard",
            description="\n\n".join(lines) if lines else "No activity recorded today yet.",
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Activity(bot))
