
import discord
from discord.ext import commands
import asyncio
import datetime
import config

action_log: dict = {}


def log_action(guild_id: int, user_id: int, action: str):
    key = (guild_id, user_id, action)
    now = datetime.datetime.utcnow()
    window = config.ANTINUKE_SETTINGS["action_window"]

    if key not in action_log:
        action_log[key] = []

    action_log[key] = [t for t in action_log[key] if (now - t).total_seconds() <= window]
    action_log[key].append(now)
    return len(action_log[key])


def nuke_embed(title, description):
    embed = discord.Embed(
        title=title,
        description=description,
        color=config.COLOR_ERROR,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=config.FOOTER_TEXT)
    return embed


class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trusted_ids: set = set()
        self.enabled: bool = True

    def is_trusted(self, user_id: int, guild: discord.Guild) -> bool:
        if user_id == guild.owner_id:
            return True
        if user_id in self.trusted_ids:
            return True
        return False

    async def punish(self, guild: discord.Guild, member: discord.Member, reason: str):
        log_channel = discord.utils.get(guild.text_channels, name="antinuke-log") or \
                      discord.utils.get(guild.text_channels, name="mod-log") or \
                      discord.utils.get(guild.text_channels, name="logs")

        punishment = config.ANTINUKE_SETTINGS["punishment"]
        try:
            if punishment == "ban":
                await guild.ban(member, reason=f"[Anti-Nuke] {reason}")
            elif punishment == "kick":
                await guild.kick(member, reason=f"[Anti-Nuke] {reason}")
            elif punishment == "strip":
                await member.edit(roles=[], reason=f"[Anti-Nuke] {reason}")
        except Exception as e:
            print(f"[AntiNuke] Failed to punish {member}: {e}")

        if log_channel:
            try:
                await log_channel.send(embed=nuke_embed(
                    "🛡️ Anti-Nuke Triggered",
                    f"**User:** {member} (`{member.id}`)\n**Action:** {reason}\n**Punishment:** {punishment.capitalize()}"
                ))
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        if not self.enabled:
            return
        await asyncio.sleep(0.5)
        try:
            entry = await guild.fetch_ban(user)
        except Exception:
            return

        async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if self.is_trusted(log.user.id, guild):
                return
            count = log_action(guild.id, log.user.id, "ban")
            if count >= config.ANTINUKE_SETTINGS["max_bans"]:
                member = guild.get_member(log.user.id)
                if member:
                    await self.punish(guild, member, f"Mass ban detected ({count} bans in {config.ANTINUKE_SETTINGS['action_window']}s)")
                try:
                    await guild.unban(user, reason="[Anti-Nuke] Reverting mass ban")
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if not self.enabled:
            return
        guild = member.guild
        await asyncio.sleep(0.5)
        async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if log.target.id != member.id:
                return
            if self.is_trusted(log.user.id, guild):
                return
            count = log_action(guild.id, log.user.id, "kick")
            if count >= config.ANTINUKE_SETTINGS["max_kicks"]:
                executor = guild.get_member(log.user.id)
                if executor:
                    await self.punish(guild, executor, f"Mass kick detected ({count} kicks in {config.ANTINUKE_SETTINGS['action_window']}s)")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if not self.enabled:
            return
        guild = channel.guild
        await asyncio.sleep(0.5)
        async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if self.is_trusted(log.user.id, guild):
                return
            count = log_action(guild.id, log.user.id, "channel_delete")
            if count >= config.ANTINUKE_SETTINGS["max_channel_deletes"]:
                executor = guild.get_member(log.user.id)
                if executor:
                    await self.punish(guild, executor, f"Mass channel deletion detected ({count} deletions in {config.ANTINUKE_SETTINGS['action_window']}s)")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        if not self.enabled:
            return
        guild = role.guild
        await asyncio.sleep(0.5)
        async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if self.is_trusted(log.user.id, guild):
                return
            count = log_action(guild.id, log.user.id, "role_delete")
            if count >= config.ANTINUKE_SETTINGS["max_role_deletes"]:
                executor = guild.get_member(log.user.id)
                if executor:
                    await self.punish(guild, executor, f"Mass role deletion detected ({count} deletions in {config.ANTINUKE_SETTINGS['action_window']}s)")

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel):
        if not self.enabled:
            return
        guild = channel.guild
        await asyncio.sleep(0.5)
        async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
            if self.is_trusted(log.user.id, guild):
                return
            count = log_action(guild.id, log.user.id, "webhook_create")
            if count >= config.ANTINUKE_SETTINGS["max_webhook_creates"]:
                executor = guild.get_member(log.user.id)
                if executor:
                    await self.punish(guild, executor, f"Mass webhook creation detected ({count} webhooks in {config.ANTINUKE_SETTINGS['action_window']}s)")
                try:
                    webhook = log.target
                    await webhook.delete(reason="[Anti-Nuke] Mass webhook creation")
                except Exception:
                    pass

    @discord.app_commands.command(name="antinuke", description="Toggle or view Anti-Nuke settings")
    @discord.app_commands.describe(action="enable, disable, or status")
    @discord.app_commands.default_permissions(administrator=True)
    async def antinuke_cmd(self, interaction: discord.Interaction, action: str = "status"):
        action = action.lower()
        embed = discord.Embed(color=config.COLOR_PRIMARY, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=config.FOOTER_TEXT)

        if action == "enable":
            self.enabled = True
            embed.title = "🛡️ Anti-Nuke Enabled"
            embed.description = "Anti-Nuke protection is now **active**."
            embed.color = config.COLOR_SUCCESS
        elif action == "disable":
            self.enabled = False
            embed.title = "🛡️ Anti-Nuke Disabled"
            embed.description = "Anti-Nuke protection is now **inactive**. Server is unprotected!"
            embed.color = config.COLOR_ERROR
        else:
            s = config.ANTINUKE_SETTINGS
            embed.title = "🛡️ Anti-Nuke Status"
            embed.description = f"**Status:** {'✅ Enabled' if self.enabled else '❌ Disabled'}"
            embed.add_field(name="Max Bans", value=f"`{s['max_bans']}` per `{s['action_window']}s`", inline=True)
            embed.add_field(name="Max Kicks", value=f"`{s['max_kicks']}` per `{s['action_window']}s`", inline=True)
            embed.add_field(name="Max Channel Deletes", value=f"`{s['max_channel_deletes']}` per `{s['action_window']}s`", inline=True)
            embed.add_field(name="Max Role Deletes", value=f"`{s['max_role_deletes']}` per `{s['action_window']}s`", inline=True)
            embed.add_field(name="Max Webhooks", value=f"`{s['max_webhook_creates']}` per `{s['action_window']}s`", inline=True)
            embed.add_field(name="Punishment", value=f"`{s['punishment'].capitalize()}`", inline=True)
            embed.add_field(name="Trusted Users", value=f"`{len(self.trusted_ids)}` user(s) trusted", inline=False)

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="trust", description="Add or remove a user from Anti-Nuke trusted list")
    @discord.app_commands.describe(member="The member to trust/untrust")
    @discord.app_commands.default_permissions(administrator=True)
    async def trust(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=config.FOOTER_TEXT)

        if member.id in self.trusted_ids:
            self.trusted_ids.discard(member.id)
            embed.title = "🔓 User Untrusted"
            embed.description = f"**{member}** has been removed from the trusted list."
            embed.color = config.COLOR_WARNING
        else:
            self.trusted_ids.add(member.id)
            embed.title = "🔒 User Trusted"
            embed.description = f"**{member}** has been added to the trusted list and will bypass Anti-Nuke."
            embed.color = config.COLOR_SUCCESS

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
