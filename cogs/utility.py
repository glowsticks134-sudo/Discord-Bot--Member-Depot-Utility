
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import platform
import config


def util_embed(title, description=None, color=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color or config.COLOR_PRIMARY,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=config.FOOTER_TEXT)
    return embed


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = util_embed("🏓 Pong!", f"Bot latency: **{latency}ms**", config.COLOR_SUCCESS if latency < 150 else config.COLOR_WARNING)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Get information about this server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>", inline=True)
        embed.add_field(name="Members", value=f"**{guild.member_count}**", inline=True)
        embed.add_field(name="Roles", value=f"**{len(guild.roles)}**", inline=True)
        embed.add_field(name="Channels", value=f"**{len(guild.channels)}**", inline=True)
        embed.add_field(name="Boosts", value=f"**{guild.premium_subscription_count}** (Tier {guild.premium_tier})", inline=True)
        embed.add_field(name="Created At", value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=False)
        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Get information about a user")
    @app_commands.describe(member="The member to look up (defaults to you)")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        roles = [r.mention for r in member.roles if r != interaction.guild.default_role]

        embed = discord.Embed(
            title=f"👤 {member}",
            color=member.color if member.color != discord.Color.default() else config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Display Name", value=member.display_name, inline=True)
        embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Bot", value="✅ Yes" if member.bot else "❌ No", inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles[:10]) or "None", inline=False)
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(member="The member whose avatar to show (defaults to you)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = util_embed(f"🖼️ {member.display_name}'s Avatar")
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(name="Links", value=f"[PNG]({member.display_avatar.replace(format='png').url}) | [JPG]({member.display_avatar.replace(format='jpg').url}) | [WEBP]({member.display_avatar.replace(format='webp').url})")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="Get information about the bot")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🤖 {config.BOT_NAME}",
            description=f"The official utility bot for **{config.SERVER_NAME}**.",
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Created By", value=f"**{config.OWNER}**", inline=True)
        embed.add_field(name="Servers", value=f"**{len(self.bot.guilds)}**", inline=True)
        embed.add_field(name="Latency", value=f"**{round(self.bot.latency * 1000)}ms**", inline=True)
        embed.add_field(name="Python", value=f"**{platform.python_version()}**", inline=True)
        embed.add_field(name="discord.py", value=f"**{discord.__version__}**", inline=True)
        embed.add_field(name="Prefix", value=f"Slash commands (`/`)", inline=True)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Show all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"📋 {config.BOT_NAME} — Command List",
            description=f"The official utility & moderation bot for **{config.SERVER_NAME}**.",
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(
            name="🔨 Moderation",
            value="`/ban` `/unban` `/kick` `/mute` `/unmute` `/warn` `/purge` `/slowmode` `/lock` `/unlock` `/nick` `/role`",
            inline=False
        )
        embed.add_field(
            name="🛡️ Anti-Nuke",
            value="`/antinuke` `/trust`",
            inline=False
        )
        embed.add_field(
            name="🔧 Utility",
            value="`/ping` `/serverinfo` `/userinfo` `/avatar` `/botinfo` `/help` `/embed`",
            inline=False
        )
        embed.add_field(
            name="❓ FAQ",
            value="`/faq` — sends an interactive FAQ dropdown",
            inline=False
        )
        embed.add_field(
            name="📋 Info & Setup",
            value="`/setchannel` `/setlink` `/channelinfo` `/sendhowto` `/sendtos` `/sendrules` `/sendplans`",
            inline=False
        )
        embed.add_field(
            name="🥉 Free Bronze",
            value="`/setbronze` `/freebronze`",
            inline=False
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="embed", description="Open the embed builder (Admin only)")
    @app_commands.describe(channel="Channel to send the embed to (defaults to current channel)")
    @app_commands.default_permissions(administrator=True)
    async def embed_cmd(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        target = channel or interaction.channel
        await interaction.response.send_modal(EmbedBuilderModal(target))


class EmbedBuilderModal(discord.ui.Modal, title="Embed Builder"):
    embed_title = discord.ui.TextInput(
        label="Title",
        placeholder="Enter the embed title...",
        max_length=256,
        required=True,
    )
    embed_description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter the embed description...",
        style=discord.TextStyle.paragraph,
        max_length=4000,
        required=True,
    )
    embed_color = discord.ui.TextInput(
        label="Color (hex, e.g. 5865F2)",
        placeholder="5865F2",
        max_length=7,
        required=False,
    )
    embed_image = discord.ui.TextInput(
        label="Image URL (optional)",
        placeholder="https://...",
        required=False,
    )
    embed_thumbnail = discord.ui.TextInput(
        label="Thumbnail URL (optional)",
        placeholder="https://...",
        required=False,
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.target_channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            hex_color = int(self.embed_color.value.lstrip("#"), 16) if self.embed_color.value.strip() else config.COLOR_PRIMARY
        except Exception:
            hex_color = config.COLOR_PRIMARY

        embed = discord.Embed(
            title=self.embed_title.value,
            description=self.embed_description.value,
            color=hex_color,
            timestamp=datetime.datetime.utcnow()
        )

        if self.embed_thumbnail.value.strip():
            embed.set_thumbnail(url=self.embed_thumbnail.value.strip())

        if self.embed_image.value.strip():
            embed.set_image(url=self.embed_image.value.strip())

        embed.set_footer(text=config.FOOTER_TEXT)

        await self.target_channel.send(embed=embed)

        confirm = discord.Embed(
            description=f"✅ Embed sent to {self.target_channel.mention}.",
            color=config.COLOR_SUCCESS
        )
        confirm.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=confirm, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Error",
                description=f"Failed to send embed: {error}",
                color=config.COLOR_ERROR
            ).set_footer(text=config.FOOTER_TEXT),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Utility(bot))
