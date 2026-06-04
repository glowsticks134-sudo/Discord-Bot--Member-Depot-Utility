
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import os
import config

CHANNELS_FILE = "data/channels.json"


def load_channels() -> dict:
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_channels(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_guild_channels(guild_id: int) -> dict:
    data = load_channels()
    return data.get(str(guild_id), {})


def set_guild_channel(guild_id: int, key: str, channel_id: int):
    data = load_channels()
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {}
    data[gid][key] = channel_id
    save_channels(data)


def info_embed(title, description=None, color=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color or config.COLOR_PRIMARY,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=config.FOOTER_TEXT)
    return embed


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setchannel", description="Set a channel for the bot to reference in embeds")
    @app_commands.describe(
        channel_type="Which channel to set (add-bot, farm-here, or plans)",
        channel="The channel to assign"
    )
    @app_commands.choices(channel_type=[
        app_commands.Choice(name="add-bot", value="add_bot"),
        app_commands.Choice(name="farm-here", value="farm_here"),
        app_commands.Choice(name="plans", value="plans"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def setchannel(self, interaction: discord.Interaction, channel_type: app_commands.Choice[str], channel: discord.TextChannel):
        set_guild_channel(interaction.guild.id, channel_type.value, channel.id)

        labels = {
            "add_bot": "add-bot",
            "farm_here": "farm-here",
            "plans": "plans"
        }

        embed = info_embed(
            "✅ Channel Set",
            f"The **{labels[channel_type.value]}** channel has been set to {channel.mention}.\n\n"
            f"This will be used in `/sendhowto` embeds.",
            config.COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="channelinfo", description="View the currently set channels for this server")
    @app_commands.default_permissions(administrator=True)
    async def channelinfo(self, interaction: discord.Interaction):
        channels = get_guild_channels(interaction.guild.id)

        def fmt(key):
            cid = channels.get(key)
            return f"<#{cid}>" if cid else "❌ Not set"

        embed = info_embed("📋 Channel Settings", color=config.COLOR_PRIMARY)
        embed.add_field(name="add-bot", value=fmt("add_bot"), inline=True)
        embed.add_field(name="farm-here", value=fmt("farm_here"), inline=True)
        embed.add_field(name="plans", value=fmt("plans"), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sendhowto", description="Send the 'How To Use Member Depot' embed")
    @app_commands.default_permissions(manage_messages=True)
    async def sendhowto(self, interaction: discord.Interaction):
        channels = get_guild_channels(interaction.guild.id)

        add_bot = f"<#{channels['add_bot']}>" if channels.get("add_bot") else "**#add-bot**"
        farm_here = f"<#{channels['farm_here']}>" if channels.get("farm_here") else "**#farm-here**"
        plans = f"<#{channels['plans']}>" if channels.get("plans") else "**#plans**"

        embed = discord.Embed(
            title="How To Use Member Depot",
            description=(
                f"• Navigate over to {add_bot} and add the bot to your server.\n"
                f"• Then, navigate over to {farm_here} and run the **Command** below.\n\n"
                f"**Command**\n"
                f"• !djoin (Server ID)\n"
                f"• **Want More Members?** {plans}!"
            ),
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sendtos", description="Send the Member Depot TOS embed")
    @app_commands.default_permissions(manage_messages=True)
    async def sendtos(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Member Depot TOS",
            description=(
                "1.) **We do NOT offer refunds unless we believe it's our fault.**\n"
                "2.) **We do NOT allow selling/trading/buying between members.**\n"
                "3.) **Follow Discord's [TOS](https://discord.com/terms).**\n"
                "4.) **We do not condone any sort of disrespect.**\n"
                "5.) **No advertising.**\n"
                "6.) **We strictly only take F&F for paypal, sending as g&s = Banned from server & NO Refund.**\n"
                "7.) **No doxing etc.**"
            ),
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Info(bot))
