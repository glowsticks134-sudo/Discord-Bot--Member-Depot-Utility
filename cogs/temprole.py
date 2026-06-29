import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import json
import os
import asyncio
import re
import time
import config

DATA_FILE = "data/temproles.json"


# ── Persistence ───────────────────────────────────────────────────────────────

def load_data():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        return {"temproles": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Duration Parsing ──────────────────────────────────────────────────────────

DURATION_RE = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?", re.IGNORECASE)
SUPPORTED = {"30m", "1h", "12h", "1d", "3d", "7d", "14d", "30d", "90d", "365d"}


def parse_duration(text: str) -> int | None:
    """Return total seconds from a duration string like 1d12h or 30m. None if invalid."""
    text = text.strip().lower()
    match = DURATION_RE.fullmatch(text)
    if not match or not any(match.groups()):
        return None
    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    total = days * 86400 + hours * 3600 + minutes * 60
    return total if total > 0 else None


def format_duration(seconds: int) -> str:
    """Return a human-readable duration string."""
    parts = []
    days, seconds = divmod(int(seconds), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "< 1m"


def format_expiry(expires_at: float) -> str:
    """Return a Discord relative timestamp."""
    return f"<t:{int(expires_at)}:R>"


# ── Embed Helper ──────────────────────────────────────────────────────────────

def tr_embed(title=None, description=None, color=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color or config.COLOR_PRIMARY,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=config.FOOTER_TEXT)
    return embed


# ── Cog ───────────────────────────────────────────────────────────────────────

class TempRole(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._lock = asyncio.Lock()
        self.expiry_check.start()

    def cog_unload(self):
        self.expiry_check.cancel()

    # ── Background Expiry Task ────────────────────────────────────────────────

    @tasks.loop(minutes=1)
    async def expiry_check(self):
        now = time.time()
        async with self._lock:
            data = load_data()
            remaining = []
            for entry in data.get("temproles", []):
                if now >= entry["expires_at"]:
                    await self._remove_role_entry(entry, expired=True)
                else:
                    remaining.append(entry)
            data["temproles"] = remaining
            save_data(data)

    @expiry_check.before_loop
    async def before_expiry_check(self):
        await self.bot.wait_until_ready()

    async def _remove_role_entry(self, entry: dict, expired: bool = False):
        guild = self.bot.get_guild(entry["guild_id"])
        if not guild:
            return
        member = guild.get_member(entry["user_id"])
        role = guild.get_role(entry["role_id"])

        if member and role and role in member.roles:
            try:
                await member.remove_roles(role, reason="Temporary role expired")
            except Exception:
                pass

        if expired and member and role:
            try:
                dm = tr_embed(
                    "⏰ Temporary Role Expired",
                    f"Your **{role.name}** role in **{guild.name}** has expired and has been removed automatically.",
                    config.COLOR_WARNING,
                )
                await member.send(embed=dm)
            except Exception:
                pass

    # ── Slash Commands ────────────────────────────────────────────────────────

    temprole_group = app_commands.Group(name="temprole", description="Manage temporary roles")

    @temprole_group.command(name="add", description="Give a user a role for a limited time")
    @app_commands.describe(
        member="Member to assign the role to",
        role="Role to assign temporarily",
        duration="Duration e.g. 7d, 12h, 1d12h, 30m",
    )
    @app_commands.default_permissions(manage_roles=True)
    async def temprole_add(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        duration: str,
    ):
        # Permission checks
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=tr_embed("❌ Missing Permission", "I need the **Manage Roles** permission.", config.COLOR_ERROR),
                ephemeral=True,
            )
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                embed=tr_embed("❌ Role Too High", "That role is at or above my highest role. I can't assign it.", config.COLOR_ERROR),
                ephemeral=True,
            )
            return

        if role.managed:
            await interaction.response.send_message(
                embed=tr_embed("❌ Managed Role", "That role is managed by an integration and cannot be assigned.", config.COLOR_ERROR),
                ephemeral=True,
            )
            return

        seconds = parse_duration(duration)
        if seconds is None:
            await interaction.response.send_message(
                embed=tr_embed(
                    "❌ Invalid Duration",
                    "Use a format like `7d`, `12h`, `30m`, or combined like `1d12h`.\n"
                    "Supported: `30m` `1h` `12h` `1d` `3d` `7d` `14d` `30d` `90d` `365d`",
                    config.COLOR_ERROR,
                ),
                ephemeral=True,
            )
            return

        async with self._lock:
            data = load_data()

            # Check for duplicate
            for entry in data["temproles"]:
                if entry["guild_id"] == interaction.guild.id and entry["user_id"] == member.id and entry["role_id"] == role.id:
                    await interaction.response.send_message(
                        embed=tr_embed(
                            "❌ Duplicate",
                            f"{member.mention} already has **{role.name}** as a temporary role. Remove it first.",
                            config.COLOR_ERROR,
                        ),
                        ephemeral=True,
                    )
                    return

            expires_at = time.time() + seconds

            # Assign role
            try:
                await member.add_roles(role, reason=f"Temp role for {format_duration(seconds)} by {interaction.user}")
            except discord.Forbidden:
                await interaction.response.send_message(
                    embed=tr_embed("❌ Failed", "I don't have permission to assign that role.", config.COLOR_ERROR),
                    ephemeral=True,
                )
                return

            data["temproles"].append({
                "guild_id": interaction.guild.id,
                "user_id": member.id,
                "role_id": role.id,
                "expires_at": expires_at,
            })
            save_data(data)

        dur_str = format_duration(seconds)
        embed = tr_embed("✅ Temporary Role Assigned", color=config.COLOR_SUCCESS)
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Role", value=role.mention, inline=True)
        embed.add_field(name="Duration", value=dur_str, inline=True)
        embed.add_field(name="Expires", value=format_expiry(expires_at), inline=True)
        await interaction.response.send_message(embed=embed)

        # DM member
        try:
            dm = tr_embed(
                "🎉 Temporary Role Granted",
                f"You have been given the **{role.name}** role in **{interaction.guild.name}**.\n\nThis role will expire in **{dur_str}**.",
                config.COLOR_SUCCESS,
            )
            await member.send(embed=dm)
        except Exception:
            pass

    @temprole_group.command(name="remove", description="Immediately remove a temporary role from a user")
    @app_commands.describe(member="Member to remove the role from", role="Temporary role to remove")
    @app_commands.default_permissions(manage_roles=True)
    async def temprole_remove(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        async with self._lock:
            data = load_data()
            original = data["temproles"]
            data["temproles"] = [
                e for e in original
                if not (e["guild_id"] == interaction.guild.id and e["user_id"] == member.id and e["role_id"] == role.id)
            ]

            if len(data["temproles"]) == len(original):
                await interaction.response.send_message(
                    embed=tr_embed(
                        "❌ Not Found",
                        f"{member.mention} doesn't have **{role.name}** as a temporary role.",
                        config.COLOR_ERROR,
                    ),
                    ephemeral=True,
                )
                return

            save_data(data)

        if role in member.roles:
            try:
                await member.remove_roles(role, reason=f"Temp role manually removed by {interaction.user}")
            except Exception:
                pass

        embed = tr_embed(
            "✅ Temporary Role Removed",
            f"Removed **{role.name}** from {member.mention} and cancelled its timer.",
            config.COLOR_SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    @temprole_group.command(name="list", description="View all active temporary roles in this server")
    @app_commands.default_permissions(manage_roles=True)
    async def temprole_list(self, interaction: discord.Interaction):
        data = load_data()
        entries = [e for e in data.get("temproles", []) if e["guild_id"] == interaction.guild.id]
        entries.sort(key=lambda e: e["expires_at"])

        if not entries:
            await interaction.response.send_message(
                embed=tr_embed("📋 Temporary Roles", "No active temporary roles in this server."),
                ephemeral=True,
            )
            return

        lines = []
        for e in entries[:20]:
            member = interaction.guild.get_member(e["user_id"])
            role = interaction.guild.get_role(e["role_id"])
            member_str = member.mention if member else f"`{e['user_id']}`"
            role_str = role.mention if role else f"`{e['role_id']}`"
            lines.append(f"{member_str} → {role_str} — expires {format_expiry(e['expires_at'])}")

        embed = tr_embed("📋 Active Temporary Roles", "\n".join(lines))
        if len(entries) > 20:
            embed.set_footer(text=f"Showing 20 of {len(entries)} entries. {config.FOOTER_TEXT}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TempRole(bot))
