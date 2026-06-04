
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import config

FAQ_ITEMS = [
    {
        "label": '"I am not getting any members..."',
        "value": "no_members",
        "emoji": "❓",
        "answer_title": "I am not getting any members",
        "answer": (
            "If you are not receiving members, please check the following:\n\n"
            "• Make sure your **invite link is valid** and has no expiry or usage limit set.\n"
            "• Make sure your **server is not full** (max 500K members).\n"
            "• Ensure the bot has been **properly added** to your server with the correct permissions.\n"
            "• Members may take some time to join — please be patient.\n"
            "• If the issue persists, open a support ticket."
        )
    },
    {
        "label": '"I can\'t add the bot"',
        "value": "cant_add_bot",
        "emoji": "❓",
        "answer_title": "I can't add the bot",
        "answer": (
            "If you're having trouble adding the bot, try the following:\n\n"
            "• Make sure you have the **Manage Server** permission in the server you're trying to add it to.\n"
            "• Try using a different browser or clearing your cache.\n"
            "• Make sure the bot invite link hasn't expired.\n"
            "• Disable any VPN or ad blockers that may be interfering.\n"
            "• If none of these work, open a support ticket and we'll help you out!"
        )
    },
    {
        "label": '"How do I get my Server ID?"',
        "value": "server_id",
        "emoji": "❓",
        "answer_title": "How do I get my Server ID?",
        "answer": (
            "To get your Server ID, follow these steps:\n\n"
            "**1.** Open **Discord Settings** → **Advanced**.\n"
            "**2.** Enable **Developer Mode**.\n"
            "**3.** Go to your server and **right-click the server name** (or icon on mobile).\n"
            "**4.** Click **Copy Server ID**.\n\n"
            "That's it! Paste the ID wherever it's needed."
        )
    },
    {
        "label": '"When are restocks?"',
        "value": "restocks",
        "emoji": "❓",
        "answer_title": "When are restocks?",
        "answer": (
            "Restocks happen **regularly** depending on availability.\n\n"
            "• Keep an eye on our announcements channel for restock notifications.\n"
            "• Turn on notifications for the server so you don't miss them!\n"
            "• Restocks are not on a fixed schedule — they happen as supply becomes available."
        )
    },
    {
        "label": '"How do I make my own invite link?"',
        "value": "invite_link",
        "emoji": "❓",
        "answer_title": "How do I make my own invite link?",
        "answer": (
            "Here's how to create an invite link for your server:\n\n"
            "**1.** Open your server and click the dropdown at the top.\n"
            "**2.** Go to **Invite People** (or right-click the channel you want).\n"
            "**3.** Click **Edit invite link** and set it to **Never expire** with **No usage limit**.\n"
            "**4.** Copy the link and submit it.\n\n"
            "⚠️ Make sure the invite **never expires** or members won't be able to join!"
        )
    },
    {
        "label": '"I invited people but I still haven\'t gotten members"',
        "value": "invited_no_members",
        "emoji": "❓",
        "answer_title": "I invited people but still haven't gotten members",
        "answer": (
            "This can happen for a few reasons:\n\n"
            "• Your invite link may have **expired** or hit a **usage limit** — double check the settings.\n"
            "• There may be a **delay** in processing — give it a little time.\n"
            "• The bot may not have been **set up correctly** in your server.\n"
            "• Make sure the bot has **Administrator** or the correct permissions.\n\n"
            "If the issue continues, open a support ticket with your invite link and we'll look into it."
        )
    },
    {
        "label": '"Why have I been blacklisted?"',
        "value": "user_blacklisted",
        "emoji": "❓",
        "answer_title": "Why have I been blacklisted?",
        "answer": (
            "Users can be blacklisted for the following reasons:\n\n"
            "• **Cheating or abusing** the member farming system.\n"
            "• **Providing fake or invalid** invite links.\n"
            "• **Scamming** other members of the server.\n"
            "• **Breaking** our server rules repeatedly.\n"
            "• **Chargebacks** or dishonest behavior.\n\n"
            "If you believe this was a mistake, open a support ticket to appeal."
        )
    },
    {
        "label": '"Why has my server been blacklisted?"',
        "value": "server_blacklisted",
        "emoji": "❓",
        "answer_title": "Why has my server been blacklisted?",
        "answer": (
            "Servers can be blacklisted for the following reasons:\n\n"
            "• The server **violates Discord's Terms of Service**.\n"
            "• The server is used for **spam, scams, or harmful content**.\n"
            "• The **invite link was invalid** or expired repeatedly.\n"
            "• The server owner **abused** the farming system.\n\n"
            "To appeal a server blacklist, open a support ticket with your Server ID."
        )
    },
    {
        "label": '"The stock has run out..."',
        "value": "out_of_stock",
        "emoji": "❓",
        "answer_title": "The stock has run out",
        "answer": (
            "We're sorry — the member stock has temporarily run out!\n\n"
            "• **Watch the announcements channel** for restock pings.\n"
            "• Turn on **server notifications** so you're the first to know.\n"
            "• Stock is restocked frequently, so check back soon!\n\n"
            "Thank you for your patience. 🙏"
        )
    },
]


class FAQSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=item["label"][:100],
                value=item["value"],
                emoji=item["emoji"]
            )
            for item in FAQ_ITEMS
        ]
        super().__init__(
            placeholder="Choose what you need help with here...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        item = next((i for i in FAQ_ITEMS if i["value"] == selected), None)
        if not item:
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"❓ {item['answer_title']}",
            description=item["answer"],
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class FAQView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FAQSelect())


class FAQ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="faq", description="Send the FAQ embed with dropdown")
    @app_commands.default_permissions(manage_messages=True)
    async def faq(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔎 Frequently Asked Questions",
            description=(
                "🔧 Are you not sure about something or have questions? "
                "Use the dropdown below to view answers to frequently asked questions."
            ),
            color=config.COLOR_PRIMARY,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=config.FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, view=FAQView())


async def setup(bot):
    await bot.add_cog(FAQ(bot))
