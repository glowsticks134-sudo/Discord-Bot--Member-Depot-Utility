
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import os
import config

CHANNELS_FILE = "data/channels.json"


def load_data() -> dict:
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_guild_data(guild_id: int) -> dict:
    return load_data().get(str(guild_id), {})


def set_guild_value(guild_id: int, key: str, value):
    data = load_data()
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {}
    data[gid][key] = value
    save_data(data)


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
        set_guild_value(interaction.guild.id, channel_type.value, channel.id)
        labels = {"add_bot": "add-bot", "farm_here": "farm-here", "plans": "plans"}
        await interaction.response.send_message(embed=info_embed(
            "✅ Channel Set",
            f"The **{labels[channel_type.value]}** channel has been set to {channel.mention}.",
            config.COLOR_SUCCESS
        ), ephemeral=True)

    @app_commands.command(name="setlink", description="Set a button link used in /sendplans")
    @app_commands.describe(
        link_type="Which link to set",
        url="The full URL (must start with https://)"
    )
    @app_commands.choices(link_type=[
        app_commands.Choice(name="Upgrade Now", value="upgrade_now_url"),
        app_commands.Choice(name="Payment Methods", value="payment_methods_url"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def setlink(self, interaction: discord.Interaction, link_type: app_commands.Choice[str], url: str):
        if not url.startswith("https://") and not url.startswith("http://"):
            await interaction.response.send_message(embed=info_embed(
                "❌ Invalid URL", "URL must start with `https://`.", config.COLOR_ERROR
            ), ephemeral=True)
            return
        set_guild_value(interaction.guild.id, link_type.value, url)
        await interaction.response.send_message(embed=info_embed(
            "✅ Link Set",
            f"**{link_type.name}** button URL has been saved.",
            config.COLOR_SUCCESS
        ), ephemeral=True)

    @app_commands.command(name="channelinfo", description="View the currently set channels and links for this server")
    @app_commands.default_permissions(administrator=True)
    async def channelinfo(self, interaction: discord.Interaction):
        d = get_guild_data(interaction.guild.id)

        def fmt_ch(key):
            cid = d.get(key)
            return f"<#{cid}>" if cid else "❌ Not set"

        def fmt_url(key):
            url = d.get(key)
            return f"[Link]({url})" if url else "❌ Not set"

        embed = info_embed("📋 Server Settings", color=config.COLOR_PRIMARY)
        embed.add_field(name="add-bot channel", value=fmt_ch("add_bot"), inline=True)
        embed.add_field(name="farm-here channel", value=fmt_ch("farm_here"), inline=True)
        embed.add_field(name="plans channel", value=fmt_ch("plans"), inline=True)
        embed.add_field(name="Upgrade Now URL", value=fmt_url("upgrade_now_url"), inline=True)
        embed.add_field(name="Payment Methods URL", value=fmt_url("payment_methods_url"), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sendhowto", description="Send the 'How To Use Member Depot' embed")
    @app_commands.default_permissions(manage_messages=True)
    async def sendhowto(self, interaction: discord.Interaction):
        d = get_guild_data(interaction.guild.id)
        add_bot = f"<#{d['add_bot']}>" if d.get("add_bot") else "**#add-bot**"
        farm_here = f"<#{d['farm_here']}>" if d.get("farm_here") else "**#farm-here**"
        plans = f"<#{d['plans']}>" if d.get("plans") else "**#plans**"

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

    @app_commands.command(name="sendrules", description="Send the Member Depot Rules embed")
    @app_commands.default_permissions(manage_messages=True)
    async def sendrules(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Member Depot Rules",
            description=(
                "1.  **Asking others to do !djoin for your server is not allowed and will result in a blacklist.**\n"
                "2.  **DM advertising is not allowed and will lead to a ban.**\n"
                "3.  **Using alternate accounts is not allowed and will result in a ban.**\n"
                "4.  **Doxing or sharing personal information is not allowed and will result in a ban.**\n"
                "5.  **Spamming is not allowed and will result in a mute.**\n"
                "6.  **Pinging staff without a valid reason is not allowed and will lead to a mute.**\n"
                "7.  **This is an English-only server, so please communicate in English.**\n"
                "8.  **Creating tickets for unnecessary reasons/issues is not allowed and will result in a mute.**\n"
                "9.  **Asking about restocks is bothersome and not allowed, and may result in a mute.**\n"
                "10.  **Opening a ticket and saying nothing within 15 minutes will result in ticket deletion and a mute.**\n"
                "11.  **Please do not spam @ staff members or the owner.**\n"
                "12.  **We do not allow 'J4J Servers' to get invites. Doing so will result in a complete reset of your invites.**\n"
                "13.  **Reselling members is not allowed and will result in a blacklist and a ban.**\n"
                "14.  **DMing staff for unnecessary reasons is not allowed and will result in a mute.**\n"
                "15.  **Scamming is highly discouraged and will not be tolerated, resulting in a ban.**"
            ),
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sendplans", description="Send the Member Depot Plans embed")
    @app_commands.default_permissions(manage_messages=True)
    async def sendplans(self, interaction: discord.Interaction):
        d = get_guild_data(interaction.guild.id)
        upgrade_url = d.get("upgrade_now_url")
        payment_url = d.get("payment_methods_url")

        embed = discord.Embed(
            title="__Plans__",
            description=(
                "Hello and Welcome to our **__PLANS__**! "
                "Here we've got some amazing and suitable offers and tools which will help you grow your server the QUICKEST! "
                "Please read below for more information."
            ),
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(
            name="__PRICES__",
            value=(
                "• @Members — Free\n"
                "• @Bronze — $2 USD\n"
                "• @Silver — $4 USD\n"
                "• @Gold — $6 USD\n"
                "• @Premium — $10 USD\n"
                "• @Diamond — $15 USD"
            ),
            inline=False
        )

        embed.add_field(
            name="__STATS__",
            value=(
                "• @Members — 2 Members\n"
                "• @Bronze — 5 Members\n"
                "• @Silver — 10 Members\n"
                "• @Gold — 15 Members\n"
                "• @Premium — 25 Members\n"
                "• @Diamond — 35 Members"
            ),
            inline=False
        )

        embed.set_footer(text=config.FOOTER_TEXT)

        view = discord.ui.View()
        if upgrade_url:
            view.add_item(discord.ui.Button(label="💰 Upgrade Now", url=upgrade_url, style=discord.ButtonStyle.link))
        if payment_url:
            view.add_item(discord.ui.Button(label="💵 Payment Methods", url=payment_url, style=discord.ButtonStyle.link))

        if not upgrade_url and not payment_url:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(embed=embed, view=view)

        if not upgrade_url or not payment_url:
            missing = []
            if not upgrade_url:
                missing.append("`Upgrade Now`")
            if not payment_url:
                missing.append("`Payment Methods`")
            await interaction.followup.send(
                embed=info_embed(
                    "⚠️ Missing Button Links",
                    f"The following button(s) have no URL set yet: {', '.join(missing)}.\n"
                    f"Use `/setlink` to add them.",
                    config.COLOR_WARNING
                ),
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Info(bot))
