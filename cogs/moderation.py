
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import config


def mod_embed(title, description, color=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color or config.COLOR_PRIMARY,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=config.FOOTER_TEXT)
    return embed


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="Reason for the ban", delete_days="Days of messages to delete (0-7)")
    @app_commands.default_permissions(administrator=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(embed=mod_embed("❌ Error", "You cannot ban someone with an equal or higher role.", config.COLOR_ERROR), ephemeral=True)
            return
        if member == interaction.guild.me:
            await interaction.response.send_message(embed=mod_embed("❌ Error", "I cannot ban myself.", config.COLOR_ERROR), ephemeral=True)
            return
        try:
            await member.send(embed=mod_embed(
                f"🔨 Banned from {config.SERVER_NAME}",
                f"You have been banned from **{interaction.guild.name}**.\n**Reason:** {reason}\n**Moderator:** {interaction.user}",
                config.COLOR_ERROR
            ))
        except Exception:
            pass
        await member.ban(reason=f"{reason} | By: {interaction.user}", delete_message_days=delete_days)
        await interaction.response.send_message(embed=mod_embed(
            "🔨 Member Banned",
            f"**{member}** has been banned.\n**Reason:** {reason}\n**Moderator:** {interaction.user}",
            config.COLOR_ERROR
        ))

    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(user_id="The user ID to unban", reason="Reason for the unban")
    @app_commands.default_permissions(administrator=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=f"{reason} | By: {interaction.user}")
            await interaction.response.send_message(embed=mod_embed(
                "✅ Member Unbanned",
                f"**{user}** has been unbanned.\n**Reason:** {reason}\n**Moderator:** {interaction.user}",
                config.COLOR_SUCCESS
            ))
        except discord.NotFound:
            await interaction.response.send_message(embed=mod_embed("❌ Error", "User not found or not banned.", config.COLOR_ERROR), ephemeral=True)

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    @app_commands.default_permissions(administrator=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(embed=mod_embed("❌ Error", "You cannot kick someone with an equal or higher role.", config.COLOR_ERROR), ephemeral=True)
            return
        try:
            await member.send(embed=mod_embed(
                f"👢 Kicked from {config.SERVER_NAME}",
                f"You have been kicked from **{interaction.guild.name}**.\n**Reason:** {reason}\n**Moderator:** {interaction.user}",
                config.COLOR_WARNING
            ))
        except Exception:
            pass
        await member.kick(reason=f"{reason} | By: {interaction.user}")
        await interaction.response.send_message(embed=mod_embed(
            "👢 Member Kicked",
            f"**{member}** has been kicked.\n**Reason:** {reason}\n**Moderator:** {interaction.user}",
            config.COLOR_WARNING
        ))

    @app_commands.command(name="mute", description="Timeout (mute) a member")
    @app_commands.describe(member="The member to mute", duration="Duration in minutes", reason="Reason for the mute")
    @app_commands.default_permissions(administrator=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int = 10, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(embed=mod_embed("❌ Error", "You cannot mute someone with an equal or higher role.", config.COLOR_ERROR), ephemeral=True)
            return
        until = discord.utils.utcnow() + datetime.timedelta(minutes=duration)
        await member.timeout(until, reason=f"{reason} | By: {interaction.user}")
        await interaction.response.send_message(embed=mod_embed(
            "🔇 Member Muted",
            f"**{member}** has been muted for **{duration} minute(s)**.\n**Reason:** {reason}\n**Moderator:** {interaction.user}",
            config.COLOR_WARNING
        ))

    @app_commands.command(name="unmute", description="Remove timeout from a member")
    @app_commands.describe(member="The member to unmute", reason="Reason for unmute")
    @app_commands.default_permissions(administrator=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.timeout(None, reason=f"{reason} | By: {interaction.user}")
        await interaction.response.send_message(embed=mod_embed(
            "🔊 Member Unmuted",
            f"**{member}** has been unmuted.\n**Moderator:** {interaction.user}",
            config.COLOR_SUCCESS
        ))

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    @app_commands.default_permissions(administrator=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await member.send(embed=mod_embed(
                f"⚠️ Warning from {config.SERVER_NAME}",
                f"You have been warned in **{interaction.guild.name}**.\n**Reason:** {reason}\n**Moderator:** {interaction.user}",
                config.COLOR_WARNING
            ))
        except Exception:
            pass
        await interaction.response.send_message(embed=mod_embed(
            "⚠️ Member Warned",
            f"**{member}** has been warned.\n**Reason:** {reason}\n**Moderator:** {interaction.user}",
            config.COLOR_WARNING
        ))

    @app_commands.command(name="purge", description="Delete a number of messages in this channel")
    @app_commands.describe(amount="Number of messages to delete (1–100)")
    @app_commands.default_permissions(administrator=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message(embed=mod_embed("❌ Error", "Amount must be between 1 and 100.", config.COLOR_ERROR), ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(embed=mod_embed(
            "🗑️ Messages Purged",
            f"Deleted **{len(deleted)}** message(s).",
            config.COLOR_SUCCESS
        ), ephemeral=True)

    @app_commands.command(name="slowmode", description="Set slowmode for the current channel")
    @app_commands.describe(seconds="Slowmode delay in seconds (0 to disable, max 21600)")
    @app_commands.default_permissions(administrator=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        if seconds < 0 or seconds > 21600:
            await interaction.response.send_message(embed=mod_embed("❌ Error", "Seconds must be between 0 and 21600.", config.COLOR_ERROR), ephemeral=True)
            return
        await interaction.channel.edit(slowmode_delay=seconds)
        status = f"**{seconds}s** slowmode enabled." if seconds > 0 else "Slowmode **disabled**."
        await interaction.response.send_message(embed=mod_embed("⏱️ Slowmode Updated", status, config.COLOR_SUCCESS))

    @app_commands.command(name="lock", description="Lock a channel so members can't send messages")
    @app_commands.describe(channel="Channel to lock (defaults to current channel)", reason="Reason for locking")
    @app_commands.default_permissions(administrator=True)
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=reason)
        await interaction.response.send_message(embed=mod_embed("🔒 Channel Locked", f"{channel.mention} has been locked.\n**Reason:** {reason}", config.COLOR_ERROR))

    @app_commands.command(name="unlock", description="Unlock a channel")
    @app_commands.describe(channel="Channel to unlock (defaults to current channel)", reason="Reason for unlocking")
    @app_commands.default_permissions(administrator=True)
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=reason)
        await interaction.response.send_message(embed=mod_embed("🔓 Channel Unlocked", f"{channel.mention} has been unlocked.\n**Reason:** {reason}", config.COLOR_SUCCESS))

    @app_commands.command(name="nick", description="Change a member's nickname")
    @app_commands.describe(member="The member", nickname="New nickname (leave blank to reset)")
    @app_commands.default_permissions(administrator=True)
    async def nick(self, interaction: discord.Interaction, member: discord.Member, nickname: str = None):
        old = member.display_name
        await member.edit(nick=nickname)
        await interaction.response.send_message(embed=mod_embed(
            "✏️ Nickname Changed",
            f"**{member}**'s nickname changed from `{old}` → `{nickname or member.name}`",
            config.COLOR_SUCCESS
        ))

    @app_commands.command(name="role", description="Add or remove a role from a member")
    @app_commands.describe(member="The member", role="The role to add/remove")
    @app_commands.default_permissions(administrator=True)
    async def role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(embed=mod_embed("➖ Role Removed", f"Removed **{role.name}** from **{member}**.", config.COLOR_WARNING))
        else:
            await member.add_roles(role)
            await interaction.response.send_message(embed=mod_embed("➕ Role Added", f"Added **{role.name}** to **{member}**.", config.COLOR_SUCCESS))


    @commands.command(name="role")
    async def role(self, ctx, member: discord.Member = None, *, role: discord.Role = None):
        if ctx.author.id != 1411750730380869828:
            return
        if member is None or role is None:
            await ctx.send(embed=mod_embed("❌ Usage", "`!role @member @role`", config.COLOR_ERROR))
            return
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(embed=mod_embed("➖ Role Removed", f"Removed **{role.name}** from **{member}**.", config.COLOR_ERROR))
        else:
            await member.add_roles(role)
            await ctx.send(embed=mod_embed("➕ Role Added", f"Added **{role.name}** to **{member}**.", config.COLOR_SUCCESS))


    PROTECTED_USERS = {1411750730380869828, 1404401068007493659, 1376202163994361956}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        mentioned_ids = {u.id for u in message.mentions}
        hit = mentioned_ids & self.PROTECTED_USERS
        if not hit:
            return
        try:
            await message.delete()
        except Exception:
            pass
        pinged = discord.utils.get(message.guild.members, id=next(iter(hit)))
        name = pinged.mention if pinged else "that user"
        await message.channel.send(
            f"Please don't ping {name}. If you need help please visit "
            f"<#1517627811257651358> and <#1517627811500785681>"
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
