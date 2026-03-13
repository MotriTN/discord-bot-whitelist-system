import os
from dotenv import load_dotenv

load_dotenv(override=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///lineage.db")
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID", "0"))
DAILY_LOG_CHANNEL_ID = int(os.getenv("DAILY_LOG_CHANNEL_ID", "0"))
guild_id_env = os.getenv("GUILD_ID")
GUILD_ID = int(guild_id_env) if guild_id_env else None
