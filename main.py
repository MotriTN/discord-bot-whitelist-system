import os
import disnake
from disnake.ext import commands
from config import DISCORD_TOKEN, GUILD_ID
from database.database import engine, Base
import database.models  # Import models so Base.metadata knows about them

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

class LineageBot(commands.InteractionBot):
    def __init__(self):
        intents = disnake.Intents.default()
        intents.members = True # Essential for role assignments
        kwargs = {
            "intents": intents,
            "activity": disnake.Activity(type=disnake.ActivityType.watching, name="Lineage Protocol Tests")
        }
        if GUILD_ID:
            kwargs["test_guilds"] = [GUILD_ID]
        super().__init__(**kwargs)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("The Lineage Protocol is active.")

bot = LineageBot()

initial_extensions = [
    "cogs.trust",
    "cogs.report",
    "cogs.admin",
    "cogs.audit",
    "cogs.tasks",
    "cogs.network",
    "cogs.plan",
]

if __name__ == "__main__":
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")

    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("CRITICAL: DISCORD_TOKEN not found in environment variables. Define it in .env file.")
