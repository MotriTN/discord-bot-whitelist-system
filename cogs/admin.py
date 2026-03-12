import disnake
from disnake.ext import commands
from database.database import get_db
from database.models import User, Trust
from utils.integrity import check_member_integrity
from utils.embeds import success_embed, error_embed, info_embed
from config import ADMIN_CHANNEL_ID

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="whitelist", description="Admin: Instantly grant the Whitelisted status")
    @commands.has_permissions(administrator=True)
    async def whitelist(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        db = next(get_db())
        user = db.query(User).filter(User.id == member.id).first()
        if not user:
            user = User(id=member.id)
            db.add(user)

        user.is_admin_whitelisted = True
        db.commit()

        await check_member_integrity(self.bot, db, member)

        await inter.response.send_message(embed=success_embed("Whitelisted", f"Successfully whitelisted {member.mention}."))

    @commands.slash_command(name="blacklist", description="Admin: Instantly banish a member and check their trusters")
    @commands.has_permissions(administrator=True)
    async def blacklist(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        db = next(get_db())
        user = db.query(User).filter(User.id == member.id).first()
        if not user:
            user = User(id=member.id)
            db.add(user)

        user.is_admin_blacklisted = True
        db.commit()

        # Trigger "Sins of the Brother"
        # Find who trusted them
        trusts_received = db.query(Trust).filter(Trust.trustee_id == user.id, Trust.active == True).all()
        trusters = [f"<@{t.truster_id}>" for t in trusts_received]
        
        truster_text = "\n".join(trusters) if trusters else "No one."

        # Alert the admins
        admin_channel = self.bot.get_channel(ADMIN_CHANNEL_ID)
        if admin_channel:
            embed = info_embed(
                "⚠️ Blacklist Alert",
                f"{member.mention} has been manually blacklisted by an administrator.\n\n**Users who trusted this member:**\n{truster_text}\n\n*Review recommended.*"
            )
            await admin_channel.send(embed=embed)

        await check_member_integrity(self.bot, db, member)

        await inter.response.send_message(embed=success_embed("Blacklisted", f"Successfully blacklisted {member.mention}."))

def setup(bot):
    bot.add_cog(AdminCog(bot))
