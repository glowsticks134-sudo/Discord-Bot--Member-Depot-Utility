
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


def get_guild_data(guild_id: int) -> dict:
    return load_data().get(str(guild_id), {})


def set_guild_value(guild_id: int, key: str, value):
    data = load_data()
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {}
    data[gid][key] = value
    os.makedirs("data", exist_ok=True)
    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def bronze_embed(title, description=None, color=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color or config.COLOR_PRIMARY,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=config.FOOTER_TEXT)
    return embed


class Bronze(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.awarded: set = set()

    @app_commands.command(name="setbronze", description="Set the Bronze role to be given for the free bronze status promotion")
    @app_commands.describe(role="The Bronze role to assign")
    @app_commands.default_permissions(administrator=True)
    async def setbronze(self, interaction: discord.Interaction, role: discord.Role):
        set_guild_value(interaction.guild.id, "bronze_role_id", role.id)
        await interaction.response.send_message(embed=bronze_embed(
            "✅ Bronze Role Set",
            f"The Bronze role has been set to {role.mention}.\n"
            f"Members who set the correct status will automatically receive this role.",
            config.COLOR_SUCCESS
        ), ephemeral=True)

    @app_commands.command(name="freebronze", description="Send the Free Bronze promotion embed")
    @app_commands.default_permissions(administrator=True)
    async def freebronze(self, interaction: discord.Interaction):
        d = get_guild_data(interaction.guild.id)
        server_link = d.get("server_link")

        if not server_link:
            await interaction.response.send_message(embed=bronze_embed(
                "❌ Server Link Not Set",
                "Please set the server link first using `/setlink` → **Server Link**.",
                config.COLOR_ERROR
            ), ephemeral=True)
            return

        embed = discord.Embed(
            title="🥉 Free Bronze",
            color=0xCD7F32,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(
            name="How to claim your free Bronze role:",
            value=(
                "**1.** Copy the link below.\n"
                "**2.** Go to your Discord profile and set your **Custom Status** to:\n"
                f"```Free member {server_link}```\n"
                "**3.** Wait a moment — the bot will detect your status and automatically give you the **Bronze** role!\n\n"
                "⚠️ Your status must contain **exactly** the link shown above.\n"
                "⚠️ Do **not** remove the status until you receive the role."
            ),
            inline=False
        )
        embed.add_field(
            name="📋 Copy the status text:",
            value=f"```Free member {server_link}```",
            inline=False
        )
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild
        d = get_guild_data(guild.id)

        server_link = d.get("server_link")
        bronze_role_id = d.get("bronze_role_id")

        if not server_link or not bronze_role_id:
            return

        bronze_role = guild.get_role(bronze_role_id)
        if not bronze_role:
            return

        if bronze_role in after.roles:
            return

        if after.id in self.awarded:
            return

        custom_status = None
        for activity in after.activities:
            if isinstance(activity, discord.CustomActivity) and activity.state:
                custom_status = activity.state
                break

        if custom_status and server_link in custom_status:
            try:
                await after.add_roles(bronze_role, reason="Free Bronze: status promotion detected")
                self.awarded.add(after.id)

                try:
                    dm_embed = discord.Embed(
                        title="🥉 Bronze Role Granted!",
                        description=(
                            f"Hey {after.mention}! Your **Bronze** role has been granted in **{guild.name}**.\n\n"
                            "Thank you for supporting us by setting your status! 🎉"
                        ),
                        color=0xCD7F32,
                        timestamp=datetime.datetime.utcnow()
                    )
                    dm_embed.set_footer(text=config.FOOTER_TEXT)
                    await after.send(embed=dm_embed)
                except Exception:
                    pass

            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"[FreeBronze] Error giving role to {after}: {e}")


async def setup(bot):
    await bot.add_cog(Bronze(bot))
