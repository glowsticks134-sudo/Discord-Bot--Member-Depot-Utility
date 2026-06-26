
import discord
from discord.ext import commands
import os
import datetime
import asyncio
from dotenv import load_dotenv
import config

load_dotenv()

ON_REPLIT = os.environ.get("REPL_ID") is not None

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=config.PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"   Bot: {config.BOT_NAME}")
    print(f"   Server: {config.SERVER_NAME}")
    print(f"   Made by: {config.OWNER}")

    for guild in bot.guilds:
        if guild.id != config.ALLOWED_GUILD_ID:
            print(f"   ⚠️ Leaving unauthorised server: {guild.name} ({guild.id})")
            await guild.leave()

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config.SERVER_NAME} | Made by {config.OWNER}"
        )
    )
    try:
        synced = await bot.tree.sync()
        print(f"   Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"   Failed to sync commands: {e}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    if guild.id != config.ALLOWED_GUILD_ID:
        print(f"   ⚠️ Joined unauthorised server — leaving: {guild.name} ({guild.id})")
        await guild.leave()


@bot.event
async def on_member_join(member: discord.Member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome") or \
              discord.utils.get(member.guild.text_channels, name="general")
    if not channel:
        return

    embed = discord.Embed(
        title=f"👋 Welcome to {config.SERVER_NAME}!",
        description=(
            f"Hey {member.mention}, welcome to **{member.guild.name}**! 🎉\n\n"
            f"You are member **#{member.guild.member_count}**.\n"
            f"Make sure to read the rules and enjoy your stay!"
        ),
        color=config.COLOR_SUCCESS,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=config.FOOTER_TEXT)
    await channel.send(embed=embed)


@bot.event
async def on_member_remove(member: discord.Member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome") or \
              discord.utils.get(member.guild.text_channels, name="general")
    if not channel:
        return

    embed = discord.Embed(
        title="👋 Goodbye!",
        description=f"**{member}** has left **{member.guild.name}**. We hope to see them again!",
        color=config.COLOR_ERROR,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=config.FOOTER_TEXT)
    await channel.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    embed = discord.Embed(
        title="❌ Error",
        description=str(error),
        color=config.COLOR_ERROR,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=config.FOOTER_TEXT)
    await ctx.send(embed=embed, delete_after=10)


async def load_cogs():
    for cog in ["moderation", "antinuke", "utility", "faq", "info", "bronze"]:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"   Loaded cog: {cog}")
        except Exception as e:
            print(f"   Failed to load cog {cog}: {e}")


async def keepalive():
    from aiohttp import web

    async def handle(request):
        return web.Response(text="Member Depot Bot is running!")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"   Keepalive server running on port {port}")


async def main():
    async with bot:
        await load_cogs()
        token = os.environ.get("DISCORD_TOKEN")
        if not token:
            print("❌ ERROR: DISCORD_TOKEN environment variable is not set!")
            return
        await bot.start(token)


async def run():
    if ON_REPLIT:
        print("   Running on Replit — starting keepalive server.")
        await asyncio.gather(keepalive(), main())
    else:
        print("   Running on external host — skipping keepalive server.")
        await main()


asyncio.run(run())
