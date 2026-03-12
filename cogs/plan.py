import disnake
from disnake.ext import commands
from datetime import datetime
from database.database import get_db
from database.models import User, DailyPlan
from utils.embeds import success_embed, error_embed, info_embed
from config import DAILY_LOG_CHANNEL_ID

class PlanModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Primary Objective",
                placeholder="What is the one thing you must conquer today?",
                custom_id="objective",
                style=disnake.TextInputStyle.short,
                max_length=200,
            ),
            disnake.ui.TextInput(
                label="Self-Correction Habit",
                placeholder="What is a habit or mistake you will monitor to self-correct?",
                custom_id="habit",
                style=disnake.TextInputStyle.short,
                max_length=200,
            ),
        ]
        super().__init__(title="Daily Strategic Plan", custom_id="daily_plan", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        objective = inter.text_values["objective"]
        habit = inter.text_values["habit"]
        today = datetime.now().date()

        db = next(get_db())
        user = db.query(User).filter(User.id == inter.author.id).first()
        if not user:
            user = User(id=inter.author.id)
            db.add(user)
            db.commit()

        # Check if they already planned today
        existing_plan = db.query(DailyPlan).filter(
            DailyPlan.user_id == user.id,
            DailyPlan.date == today
        ).first()

        if existing_plan:
            await inter.response.send_message(embed=error_embed("Already Committed", "You have already recorded a plan for today. The time for planning has passed, now execute."), ephemeral=True)
            return

        new_plan = DailyPlan(
            user_id=user.id,
            objective=objective,
            habit=habit,
            date=today,
            is_reviewed=False
        )
        db.add(new_plan)
        db.commit()

        await inter.response.send_message(embed=success_embed("Commitment Recorded", "Commitment recorded. The review opens tomorrow."), ephemeral=True)


class ReviewView(disnake.ui.View):
    def __init__(self, plan: DailyPlan, bot: commands.Bot):
        super().__init__(timeout=None)
        self.plan = plan
        self.bot = bot

    def calculate_streak(self, db, user_id: int):
        # Fetch all past plans sorted by date descending to calculate streak
        past_plans = db.query(DailyPlan).filter(
            DailyPlan.user_id == user_id, 
            DailyPlan.is_reviewed == True
        ).order_by(DailyPlan.date.desc()).all()

        streak = 0
        for p in past_plans:
            if p.status == "victory":
                streak += 1
            elif p.status == "defeat":
                break # Streak broken
        return streak

    async def process_review(self, inter: disnake.MessageInteraction, status: str):
        db = next(get_db())
        
        # Need to query the plan again to attach it to this session
        plan = db.query(DailyPlan).filter(DailyPlan.id == self.plan.id).first()
        user = db.query(User).filter(User.id == inter.author.id).first()

        if plan.is_reviewed:
            await inter.response.send_message(embed=error_embed("Already Reviewed", "This plan has already been accounted for."), ephemeral=True)
            return

        plan.status = status
        plan.is_reviewed = True

        if status == "victory":
            user.aura += 15

        db.commit()
        
        # Calculate new streak after updating
        streak = self.calculate_streak(db, user.id)

        # Notify in public daily log channel
        log_channel = self.bot.get_channel(int(DAILY_LOG_CHANNEL_ID)) if DAILY_LOG_CHANNEL_ID else None
        
        if status == "victory":
            result_str = "🟢 Victory"
            color = disnake.Color.from_rgb(46, 204, 113)
        else:
            result_str = "🔴 Defeat"
            color = disnake.Color.from_rgb(231, 76, 60)

        embed_msg = f"Brother {inter.author.mention} has accounted for his day.\n**Result:** {result_str}\n**Current Streak:** {streak} days."
        
        if log_channel:
            public_embed = disnake.Embed(
                title="Accountability Log",
                description=embed_msg,
                color=color
            )
            public_embed.set_footer(text=f"Aura: {user.aura}")
            await log_channel.send(embed=public_embed)

        # Disable buttons
        for child in self.children:
            child.disabled = True
        
        await inter.response.edit_message(embed=success_embed("Review Complete", f"Your review has been logged as {result_str}."), view=self)

    @disnake.ui.button(label="Victory", style=disnake.ButtonStyle.success, custom_id="btn_victory")
    async def victory_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.process_review(inter, "victory")

    @disnake.ui.button(label="Defeat", style=disnake.ButtonStyle.danger, custom_id="btn_defeat")
    async def defeat_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.process_review(inter, "defeat")


class PlanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="plan", description="Submit your daily strategic plan (Private)")
    async def plan(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_modal(PlanModal())

    @commands.slash_command(name="review", description="Review your most recent unreviewed plan (Private)")
    async def review(self, inter: disnake.ApplicationCommandInteraction):
        db = next(get_db())
        user = db.query(User).filter(User.id == inter.author.id).first()

        if not user:
            await inter.response.send_message(embed=error_embed("No History", "You have not made any plans yet."), ephemeral=True)
            return

        # Find most recent unreviewed plan
        unreviewed_plan = db.query(DailyPlan).filter(
            DailyPlan.user_id == user.id,
            DailyPlan.is_reviewed == False
        ).order_by(DailyPlan.date.desc()).first()

        if not unreviewed_plan:
            await inter.response.send_message(embed=info_embed("Up to Date", "You have no pending plans to review. Create a new one with `/plan`."), ephemeral=True)
            return

        embed = disnake.Embed(
            title=f"Daily Review: {unreviewed_plan.date.strftime('%Y-%m-%d')}",
            description="Did you conquer your objectives?",
            color=disnake.Color.from_rgb(52, 152, 219)
        )
        embed.add_field(name="Primary Objective", value=unreviewed_plan.objective, inline=False)
        embed.add_field(name="Self-Correction Habit", value=unreviewed_plan.habit, inline=False)

        view = ReviewView(plan=unreviewed_plan, bot=self.bot)
        await inter.response.send_message(embed=embed, view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(PlanCog(bot))
