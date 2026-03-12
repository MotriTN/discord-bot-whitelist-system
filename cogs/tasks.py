import datetime
import disnake
from disnake.ext import commands, tasks
from database.database import SessionLocal
from database.models import User

class TasksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.monthly_reset.start()

    def cog_unload(self):
        self.monthly_reset.cancel()

    @tasks.loop(hours=24) # Check daily
    async def monthly_reset(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now(datetime.timezone.utc)
        current_month = now.month

        with SessionLocal() as db:
            # We find users whose last_reset_month is not the current month
            users_to_reset = db.query(User).filter(User.last_reset_month != current_month).all()
            
            for user in users_to_reset:
                user.trust_charges = 2
                user.report_charges = 2
                user.last_reset_month = current_month
            
            db.commit()

    @monthly_reset.before_loop
    async def before_monthly_reset(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(TasksCog(bot))
