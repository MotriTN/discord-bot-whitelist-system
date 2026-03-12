import disnake
from disnake.ext import commands
from database.database import get_db
from database.models import User, Trust
from utils.embeds import success_embed, error_embed

class NetworkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="sanctuary", description="Whitelisted: Create a private channel for you and those you trust")
    async def sanctuary(self, inter: disnake.ApplicationCommandInteraction):
        # Check if the user is Whitelisted
        roles = [r.name for r in inter.author.roles]
        if "Whitelisted" not in roles:
            await inter.response.send_message(embed=error_embed("Access Denied", "Only members with the **Whitelisted** status can create a Sanctuary."), ephemeral=True)
            return

        db = next(get_db())
        author = db.query(User).filter(User.id == inter.author.id).first()
        
        if not author:
            await inter.response.send_message(embed=error_embed("Invalid Action", "You have not formed any bonds yet."), ephemeral=True)
            return

        # Fetch active trustees
        active_trusts = db.query(Trust).filter(Trust.truster_id == author.id, Trust.active == True).all()
        trustee_ids = [t.trustee_id for t in active_trusts]

        # Setup channel name and category
        category_name = "Lineage Sanctuaries"
        sanctuary_name = f"sanctuary-of-{inter.author.display_name.lower()[:15]}"

        # Look for category, create if not exists
        category = disnake.utils.get(inter.guild.categories, name=category_name)
        if not category:
            try:
                category = await inter.guild.create_category(name=category_name, reason="Lineage Protocol: Sanctuaries Category Creation")
            except disnake.Forbidden:
                await inter.response.send_message(embed=error_embed("Missing Permissions", "I do not have the permissions to create channels/categories in this server."), ephemeral=True)
                return

        # Define channel permissions
        overwrites = {
            inter.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            inter.author: disnake.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
            inter.guild.me: disnake.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
        }

        # Add permissions for trustees
        added_trustees = 0
        for trustee_id in trustee_ids:
            member = inter.guild.get_member(trustee_id)
            if member:
                overwrites[member] = disnake.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True)
                added_trustees += 1

        # Create the channel
        try:
            channel = await inter.guild.create_text_channel(
                name=sanctuary_name,
                category=category,
                overwrites=overwrites,
                topic=f"The private sanctuary of {inter.author.display_name} and their trusted circle.",
                reason=f"Lineage Protocol: Sanctuary requested by {inter.author.display_name}"
            )
        except disnake.Forbidden:
            await inter.response.send_message(embed=error_embed("Missing Permissions", "I do not have the permissions to create channels in this server."), ephemeral=True)
            return

        # Success message
        success_msg = f"Your sanctuary has been forged at {channel.mention}.\n**{added_trustees}** trusted member{'s' if added_trustees != 1 else ''} have been granted entry."
        if trustee_ids and added_trustees == 0:
            success_msg += "\n\n*(Note: Some trusted members could not be added because they are currently not in the server.)*"

        await inter.response.send_message(embed=success_embed("Sanctuary Forged", success_msg))

def setup(bot):
    bot.add_cog(NetworkCog(bot))
