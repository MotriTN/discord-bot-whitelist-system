import disnake
from sqlalchemy.orm import Session
from database.models import User, Trust, Report
from .embeds import info_embed
from config import ADMIN_CHANNEL_ID

async def check_member_integrity(bot: disnake.ext.commands.AutoShardedInteractionBot | disnake.ext.commands.Bot, db: Session, member: disnake.Member):
    """
    Checks the given member's active trusts and reports,
    and assigns/removes the @Whitelisted and @Blacklisted roles accordingly.
    """
    user = db.query(User).filter(User.id == member.id).first()
    if not user:
        return

    # Check for Whitelist
    whitelisted_role_name = "Whitelisted"
    whitelisted_role = disnake.utils.get(member.guild.roles, name=whitelisted_role_name)
    if not whitelisted_role:
        try:
            whitelisted_role = await member.guild.create_role(
                name=whitelisted_role_name, 
                color=disnake.Color.from_rgb(212, 175, 55),
                reason="Lineage Protocol Setup: Missing Role"
            )
        except disnake.Forbidden:
            pass
    
    # Calculate unique active trusters
    active_trusts = db.query(Trust).filter(Trust.trustee_id == user.id, Trust.active == True).all()
    unique_trusters = set([t.truster_id for t in active_trusts])

    if whitelisted_role:
        if len(unique_trusters) >= 2 or user.is_admin_whitelisted:
            if whitelisted_role not in member.roles:
                try:
                    await member.add_roles(whitelisted_role, reason="Lineage Protocol: Trust Threshold Reached")
                except disnake.Forbidden:
                    pass
        else:
            if whitelisted_role in member.roles:
                try:
                    await member.remove_roles(whitelisted_role, reason="Lineage Protocol: Below Trust Threshold")
                except disnake.Forbidden:
                    pass

    # Check for Blacklist
    blacklisted_role_name = "Blacklisted"
    blacklisted_role = disnake.utils.get(member.guild.roles, name=blacklisted_role_name)
    if not blacklisted_role:
        try:
            blacklisted_role = await member.guild.create_role(
                name=blacklisted_role_name, 
                color=disnake.Color.dark_grey(),
                reason="Lineage Protocol Setup: Missing Role"
            )
        except disnake.Forbidden:
            pass

    active_reports = db.query(Report).filter(Report.reported_id == user.id, Report.active == True).all()
    
    if blacklisted_role:
        if len(active_reports) >= 2 or user.is_admin_blacklisted:
            if blacklisted_role not in member.roles:
                try:
                    await member.add_roles(blacklisted_role, reason="Lineage Protocol: Report Threshold Reached")
                    # Notify Admins
                    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
                    if admin_channel:
                        embed = info_embed(
                            "⚠️ Automatic Blacklist",
                            f"{member.mention} has been automatically blacklisted due to reaching the report threshold.\n**Total Active Reports:** {len(active_reports)}"
                        )
                        await admin_channel.send(embed=embed)
                except disnake.Forbidden:
                    pass
        else:
            if blacklisted_role in member.roles:
                try:
                    await member.remove_roles(blacklisted_role, reason="Lineage Protocol: Forgiven")
                except disnake.Forbidden:
                    pass
