
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
            f"> Quick tip: Please do **!checkqueue (Server ID)** in <#{config.CHANNEL_FARM_HERE}> and if you're in the queue then that's why. "
            "If you're not in the queue then proceed to read the next steps. The reason for this issue is because there is **no stock** left. "
            "However, we highly advise you to do the command again just to be sure. If you still get **no joins** it's because the bot is **out of stock.**\n\n"
            f"> However, there are some solutions to get an accurate answer to why. Please head to <#{config.CHANNEL_FARM_HERE}> and do **!checkserver (ServerID)** "
            f"and it should tell you what you need to know. We also advise you to check <#{config.CHANNEL_STOCK}>."
        )
    },
    {
        "label": '"I can\'t add the bot"',
        "value": "cant_add_bot",
        "emoji": "❓",
        "answer_title": "I can't add the bot",
        "answer": (
            "> The bot can join a maximum of 100 servers. That's why it leaves servers every **1 hour** so you can add it again. "
            "Then you can add it again after an hour."
        )
    },
    {
        "label": '"How do I get my Server ID?"',
        "value": "server_id",
        "emoji": "❓",
        "answer_title": "How do I get my Server ID?",
        "answer": (
            "> **Mobile:** Hold down your Server > Click more options > Copy Server ID\n"
            "> **PC:** Right click your Server > Click Copy Server ID\n\n"
            "Still can't see it? > Click profile > Settings > Advanced > Turn on developer mode and try the steps again."
        )
    },
    {
        "label": '"When are restocks?"',
        "value": "restocks",
        "emoji": "❓",
        "answer_title": "When are restocks?",
        "answer": (
            "We do **one restock a day**. Meaning one restock of **160 stock** at **16:30 GMT**. "
            "We also **may** __sometimes__ do another (2nd) restock after the scheduled restock the same day."
        )
    },
    {
        "label": '"How do I make my own invite link?"',
        "value": "invite_link",
        "emoji": "❓",
        "answer_title": "How do I make my own invite link?",
        "answer": (
            "> **Mobile:** Hold down any channel > Click \"Invite People\" > set invite link to \"7 days\"\n"
            "> **PC:** Right click any channel > Click \"Invite People\" > set invite link to \"7 days\""
        )
    },
    {
        "label": '"I invited people but I still have 0 invites"',
        "value": "invited_no_members",
        "emoji": "❓",
        "answer_title": "I invited people but I still have 0 invites",
        "answer": (
            "> This is either because they haven't joined yet, or because you haven't made your own invite link. "
            "Please go through the FAQ menu and select **\"How do I make my own invite link\"**"
        )
    },
    {
        "label": '"Why have I been blacklisted?"',
        "value": "user_blacklisted",
        "emoji": "❓",
        "answer_title": "Why have I been blacklisted?",
        "answer": (
            f"> Please create a ticket via <#{config.CHANNEL_TICKETS}> and ask staff to check the reason why you have been blacklisted."
        )
    },
    {
        "label": '"Why has my server been blacklisted?"',
        "value": "server_blacklisted",
        "emoji": "❓",
        "answer_title": "Why has my server been blacklisted?",
        "answer": (
            f"> Please create a ticket via <#{config.CHANNEL_TICKETS}> and ask staff to check the reason why your Server ID has been blacklisted."
        )
    },
    {
        "label": '"The stock has run out. Please wait for restock"',
        "value": "out_of_stock",
        "emoji": "❓",
        "answer_title": "The stock has run out. Please wait for restock",
        "answer": (
            "> This means that the stock has run out. If you'd like to check the stock, "
            f"please head over to <#{config.CHANNEL_STOCK}>."
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
            custom_id="faq_persistent_select",
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
        bot.add_view(FAQView())

    @app_commands.command(name="faq", description="Post the FAQ embed with interactive dropdown")
    @app_commands.default_permissions(administrator=True)
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
