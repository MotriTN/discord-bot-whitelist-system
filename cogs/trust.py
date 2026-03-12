import disnake
from disnake.ext import commands
from database.database import get_db
from database.models import User, Trust
from utils.integrity import check_member_integrity
from utils.embeds import success_embed, error_embed

class TrustCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="trust", description="Grant your trust to a member")
    async def trust(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        if member.id == inter.author.id:
            await inter.response.send_message(embed=error_embed("Invalid Action", "You cannot grant trust to yourself."), ephemeral=True)
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

        if author.trust_charges <= 0:
            await inter.response.send_message(embed=error_embed("Quota Exceeded", "You have exhausted your trust charges for this month. Quotas reset on the 1st."), ephemeral=True)
            return

        existing_trust = db.query(Trust).filter(Trust.truster_id == author.id, Trust.trustee_id == target.id, Trust.active == True).first()
        if existing_trust:
            await inter.response.send_message(embed=error_embed("Already Trusted", f"You have already granted trust to {member.mention}."), ephemeral=True)
            return

        trust = Trust(truster_id=author.id, trustee_id=target.id, active=True)
        db.add(trust)
        author.trust_charges -= 1
        db.commit()

        await check_member_integrity(self.bot, db, member)

        await inter.response.send_message(embed=success_embed("Trust Granted", f"Successfully recorded trust for {member.mention}.\nRemaining monthly charges: **{author.trust_charges}**"))

    @commands.slash_command(name="untrust", description="Revoke your trust from a member")
    async def untrust(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        db = next(get_db())
        author = db.query(User).filter(User.id == inter.author.id).first()
        if not author:
            await inter.response.send_message(embed=error_embed("Invalid Action", "You have no active trusts to revoke."), ephemeral=True)
            return

        trust = db.query(Trust).filter(Trust.truster_id == author.id, Trust.trustee_id == member.id, Trust.active == True).first()
        if not trust:
            await inter.response.send_message(embed=error_embed("Trust Not Found", f"You do not currently have an active trust for {member.mention}."), ephemeral=True)
            return

        trust.active = False
        db.commit()

        await check_member_integrity(self.bot, db, member)

        await inter.response.send_message(embed=success_embed("Trust Revoked", f"Successfully revoked trust for {member.mention}."))

    @commands.slash_command(name="untrust_all", description="Revoke ALL your active trusts")
    async def untrust_all(self, inter: disnake.ApplicationCommandInteraction):
        db = next(get_db())
        author = db.query(User).filter(User.id == inter.author.id).first()
        if not author:
            await inter.response.send_message(embed=error_embed("Invalid Action", "You have no active trusts to revoke."), ephemeral=True)
            return

        active_trusts = db.query(Trust).filter(Trust.truster_id == author.id, Trust.active == True).all()
        if not active_trusts:
            await inter.response.send_message(embed=error_embed("Invalid Action", "You have no active trusts to revoke."), ephemeral=True)
            return

        revoked_count = 0
        trustee_ids = []
        for trust in active_trusts:
            trust.active = False
            trustee_ids.append(trust.trustee_id)
            revoked_count += 1
            
        db.commit()

        # Update integrity for all affected members
        for trustee_id in trustee_ids:
            member = inter.guild.get_member(trustee_id)
            if member:
                await check_member_integrity(self.bot, db, member)

        await inter.response.send_message(embed=success_embed("All Trusts Revoked", f"Successfully revoked **{revoked_count}** active trust{'s' if revoked_count > 1 else ''}."))


def setup(bot):
    bot.add_cog(TrustCog(bot))
