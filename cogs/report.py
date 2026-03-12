import disnake
from disnake.ext import commands
from database.database import get_db
from database.models import User, Report
from utils.integrity import check_member_integrity
from utils.embeds import success_embed, error_embed, info_embed
from config import ADMIN_CHANNEL_ID

class ReportCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="report", description="Cast a shadow of doubt upon a member")
    async def report(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        if member.id == inter.author.id:
            await inter.response.send_message(embed=error_embed("Invalid Action", "You cannot report yourself."), ephemeral=True)
            return

        db = next(get_db())
        author = db.query(User).filter(User.id == inter.author.id).first()
        target = db.query(User).filter(User.id == member.id).first()

        if not author:
            author = User(id=inter.author.id)
            db.add(author)
        if not target:
            target = User(id=member.id)
            db.add(target)
        db.commit()

        if author.report_charges <= 0:
            await inter.response.send_message(embed=error_embed("Quota Exceeded", "You have exhausted your report charges for this month. Quotas reset on the 1st."), ephemeral=True)
            return

        existing_report = db.query(Report).filter(Report.reporter_id == author.id, Report.reported_id == target.id, Report.active == True).first()
        if existing_report:
            await inter.response.send_message(embed=error_embed("Already Reported", f"You have already reported {member.mention}."), ephemeral=True)
            return

        report = Report(reporter_id=author.id, reported_id=target.id, reason=reason, active=True)
        db.add(report)
        author.report_charges -= 1
        db.commit()

        await check_member_integrity(self.bot, db, member)

        # Send report details to the defined admin channel
        admin_channel = self.bot.get_channel(ADMIN_CHANNEL_ID)
        if admin_channel:
            alert_embed = info_embed(
                "⚠️ New Report Filed",
                f"**Reporter:** {inter.author.mention}\n**Reported:** {member.mention}\n**Reason:** {reason}"
            )
            await admin_channel.send(embed=alert_embed)

        await inter.response.send_message(embed=success_embed("Report Submitted", f"Successfully recorded report against {member.mention}.\nRemaining monthly charges: **{author.report_charges}**"))

    @commands.slash_command(name="forgive", description="Lift the shadow from a member")
    async def forgive(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        db = next(get_db())
        author = db.query(User).filter(User.id == inter.author.id).first()
        if not author:
            await inter.response.send_message(embed=error_embed("Invalid Action", "You have no active reports to revoke."), ephemeral=True)
            return

        report = db.query(Report).filter(Report.reporter_id == author.id, Report.reported_id == member.id, Report.active == True).first()
        if not report:
            await inter.response.send_message(embed=error_embed("Report Not Found", f"You do not currently have an active report for {member.mention}."), ephemeral=True)
            return

        report.active = False
        db.commit()

        await check_member_integrity(self.bot, db, member)

        await inter.response.send_message(embed=success_embed("Report Retracted", f"Successfully revoked your report against {member.mention}."))

def setup(bot):
    bot.add_cog(ReportCog(bot))
