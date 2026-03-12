import disnake
from disnake.ext import commands
from database.database import get_db
from database.models import User, Trust, Report

class AuditCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="identity", description="View a member's Lineage Protocol profile")
    async def identity(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        target_member = member or inter.author
        db = next(get_db())
        user = db.query(User).filter(User.id == target_member.id).first()

        if not user:
            # User has no history
            embed = disnake.Embed(
                title=f"User Profile: {target_member.display_name}",
                description="This user has no activity history on the Lineage Protocol.",
                color=disnake.Color.dark_grey()
            )
            await inter.response.send_message(embed=embed)
            return

        # Status
        roles = [r.name for r in target_member.roles]
        aura_status = "Neutral"
        embed_color = disnake.Color.from_rgb(52, 152, 219) # Clean Blue
        if "Whitelisted" in roles:
            aura_status = "Whitelisted"
            embed_color = disnake.Color.from_rgb(46, 204, 113) # Clean Green
        elif "Blacklisted" in roles:
            aura_status = "Blacklisted"
            embed_color = disnake.Color.from_rgb(231, 76, 60) # Clean Red

        # Trusts
        trusts_given = db.query(Trust).filter(Trust.truster_id == user.id, Trust.active == True).all()
        trusts_received = db.query(Trust).filter(Trust.trustee_id == user.id, Trust.active == True).all()
        reports_received = db.query(Report).filter(Report.reported_id == user.id, Report.active == True).all()

        trusted_list = [f"<@{t.trustee_id}>" for t in trusts_given]
        trusted_text = ", ".join(trusted_list) if trusted_list else "None"

        trusters_list = list(set([f"<@{t.truster_id}>" for t in trusts_received]))
        trusters_text = ", ".join(trusters_list) if trusters_list else "None"

        embed = disnake.Embed(
            title=f"User Profile: {target_member.display_name}",
            color=embed_color
        )
        embed.set_thumbnail(url=target_member.display_avatar.url)
        embed.add_field(name="Protocol Status", value=aura_status, inline=False)
        embed.add_field(name=f"Currently Trusting ({len(trusts_given)})", value=trusted_text, inline=False)
        embed.add_field(name=f"Trusted By ({len(trusters_list)})", value=trusters_text, inline=False)
        embed.add_field(name="Active Reports Recieved", value=str(len(reports_received)), inline=True)
        
        if target_member.id == inter.author.id:
            embed.add_field(name="Monthly Quota Remaining", value=f"Trusts: **{user.trust_charges}** | Reports: **{user.report_charges}**", inline=False)
        
        await inter.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(AuditCog(bot))
