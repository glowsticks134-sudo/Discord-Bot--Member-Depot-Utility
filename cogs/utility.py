
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

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="embed", description="Send a custom embed (Admin only)")
    @app_commands.describe(title="Embed title", description="Embed description", color="Hex color (e.g. 5865F2)")
    @app_commands.default_permissions(administrator=True)
    async def embed_cmd(self, interaction: discord.Interaction, title: str, description: str, color: str = None):
        try:
            hex_color = int(color.lstrip("#"), 16) if color else config.COLOR_PRIMARY
        except Exception:
            hex_color = config.COLOR_PRIMARY
        embed = discord.Embed(title=title, description=description, color=hex_color, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))
