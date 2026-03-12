import disnake
from disnake.ext import commands
from database.database import get_db
from database.models import User, Trust, TrustBlock
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

        # Check if target has blocked author from trusting
        block = db.query(TrustBlock).filter(TrustBlock.blocker_id == target.id, TrustBlock.blocked_id == author.id).first()
        if block:
            await inter.response.send_message(embed=error_embed("Access Denied", f"{member.mention} has blocked you from trusting them."), ephemeral=True)
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
        author.trust_charges += 1
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
            
        author.trust_charges += revoked_count
        db.commit()

        # Update integrity for all affected members
        for trustee_id in trustee_ids:
            member = inter.guild.get_member(trustee_id)
            if member:
                await check_member_integrity(self.bot, db, member)

        await inter.response.send_message(embed=success_embed("All Trusts Revoked", f"Successfully revoked **{revoked_count}** active trust{'s' if revoked_count > 1 else ''}."))

    @commands.slash_command(name="block", description="Block a member from trusting you (and sever their current trust)")
    async def block_trust(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        if member.id == inter.author.id:
            await inter.response.send_message(embed=error_embed("Invalid Action", "You cannot block yourself."), ephemeral=True)
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

        # Check if already blocked
        existing_block = db.query(TrustBlock).filter(TrustBlock.blocker_id == author.id, TrustBlock.blocked_id == target.id).first()
        if existing_block:
            await inter.response.send_message(embed=error_embed("Already Blocked", f"You have already blocked {member.mention} from trusting you."), ephemeral=True)
            return

        # Create block
        new_block = TrustBlock(blocker_id=author.id, blocked_id=target.id)
        db.add(new_block)

        # Sever active trust if exists (target trusting author)
        severed = False
        active_trust = db.query(Trust).filter(Trust.truster_id == target.id, Trust.trustee_id == author.id, Trust.active == True).first()
        if active_trust:
            active_trust.active = False
            severed = True
            
        db.commit()

        if severed:
            await check_member_integrity(self.bot, db, inter.author)

        embed_msg = f"{member.mention} can no longer trust you."
        if severed:
            embed_msg += "\n*Their active trust towards you was forcibly severed.*"
            
        await inter.response.send_message(embed=success_embed("Member Blocked", embed_msg), ephemeral=True)

    @commands.slash_command(name="unblock", description="Unblock a member, allowing them to trust you again")
    async def unblock_trust(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        db = next(get_db())
        block = db.query(TrustBlock).filter(TrustBlock.blocker_id == inter.author.id, TrustBlock.blocked_id == member.id).first()
        
        if not block:
            await inter.response.send_message(embed=error_embed("Not Found", f"You do not have {member.mention} blocked."), ephemeral=True)
            return

        db.delete(block)
        db.commit()

        await inter.response.send_message(embed=success_embed("Member Unblocked", f"{member.mention} can now trust you again."), ephemeral=True)

def setup(bot):
    bot.add_cog(TrustCog(bot))
