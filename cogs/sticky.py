import discord
from discord.ext import commands, tasks
import datetime
import json
import os
import asyncio
import config

DATA_FILE = "data/sticky.json"
RESTOCK_CHANNEL_ID = config.CHANNEL_RESTOCK
RESTOCK_HOUR_UTC = 17
RESTOCK_MINUTE_UTC = 0


# ── Persistence ───────────────────────────────────────────────────────────────

def load_data():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Countdown Helper ──────────────────────────────────────────────────────────

def seconds_until_restock() -> int:
    now = datetime.datetime.now(datetime.timezone.utc)
    restock_today = now.replace(
        hour=RESTOCK_HOUR_UTC, minute=RESTOCK_MINUTE_UTC, second=0, microsecond=0
    )
    if now >= restock_today:
        restock_today += datetime.timedelta(days=1)
    return int((restock_today - now).total_seconds())


def format_countdown(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"**{hours}h {minutes}m {secs}s**"
    elif minutes > 0:
        return f"**{minutes}m {secs}s**"
    else:
        return f"**{secs}s**"


def next_restock_timestamp() -> int:
    now = datetime.datetime.now(datetime.timezone.utc)
    restock_today = now.replace(
        hour=RESTOCK_HOUR_UTC, minute=RESTOCK_MINUTE_UTC, second=0, microsecond=0
    )
    if now >= restock_today:
        restock_today += datetime.timedelta(days=1)
    return int(restock_today.timestamp())


def build_embed() -> discord.Embed:
    secs = seconds_until_restock()
    ts = next_restock_timestamp()
    embed = discord.Embed(
        title="🔄 Next Restock",
        color=config.COLOR_PRIMARY,
    )
    embed.add_field(
        name="⏳ Time Remaining",
        value=format_countdown(secs),
        inline=False,
    )
    embed.add_field(
        name="🕔 Restock At",
        value=f"<t:{ts}:T> • <t:{ts}:R>",
        inline=False,
    )
    embed.set_footer(text=f"{config.FOOTER_TEXT} • Updates every minute")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return embed


# ── Cog ───────────────────────────────────────────────────────────────────────

class Sticky(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._lock = asyncio.Lock()
        self._sticky_msg_id: int | None = None
        self.update_sticky.start()

    def cog_unload(self):
        self.update_sticky.cancel()

    # ── Internal Helpers ──────────────────────────────────────────────────────

    async def _get_channel(self) -> discord.TextChannel | None:
        return self.bot.get_channel(RESTOCK_CHANNEL_ID)

    async def _fetch_sticky(self, channel: discord.TextChannel) -> discord.Message | None:
        if not self._sticky_msg_id:
            data = load_data()
            self._sticky_msg_id = data.get("sticky_msg_id")
        if not self._sticky_msg_id:
            return None
        try:
            return await channel.fetch_message(self._sticky_msg_id)
        except (discord.NotFound, discord.HTTPException):
            self._sticky_msg_id = None
            save_data({})
            return None

    async def _post_sticky(self, channel: discord.TextChannel) -> discord.Message:
        msg = await channel.send(embed=build_embed())
        self._sticky_msg_id = msg.id
        save_data({"sticky_msg_id": msg.id})
        return msg

    async def _refresh_sticky(self, channel: discord.TextChannel, repost: bool = False):
        async with self._lock:
            existing = await self._fetch_sticky(channel)
            if repost or existing is None:
                if existing:
                    try:
                        await existing.delete()
                    except Exception:
                        pass
                await self._post_sticky(channel)
            else:
                try:
                    await existing.edit(embed=build_embed())
                except Exception:
                    await self._post_sticky(channel)

    # ── Background Task ───────────────────────────────────────────────────────

    @tasks.loop(minutes=1)
    async def update_sticky(self):
        channel = await self._get_channel()
        if channel:
            await self._refresh_sticky(channel, repost=False)

    @update_sticky.before_loop
    async def before_update_sticky(self):
        await self.bot.wait_until_ready()

    # ── Re-pin on New Messages ────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != RESTOCK_CHANNEL_ID:
            return
        if message.author == self.bot.user:
            return
        channel = message.channel
        await self._refresh_sticky(channel, repost=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sticky(bot))
