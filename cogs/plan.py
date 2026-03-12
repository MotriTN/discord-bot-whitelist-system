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

class EditPlanModal(disnake.ui.Modal):
    def __init__(self, plan: DailyPlan, review_message: disnake.Message):
        self.plan_id = plan.id
        self.review_message = review_message
        components = [
            disnake.ui.TextInput(
                label="Primary Objective",
                placeholder="What is the one thing you must conquer today?",
                custom_id="objective",
                style=disnake.TextInputStyle.short,
                max_length=200,
                value=plan.objective
            ),
            disnake.ui.TextInput(
                label="Self-Correction Habit",
                placeholder="What is a habit or mistake you will monitor to self-correct?",
                custom_id="habit",
                style=disnake.TextInputStyle.short,
                max_length=200,
                value=plan.habit
            ),
        ]
        super().__init__(title="Edit Strategic Plan", custom_id=f"edit_plan_{plan.id}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        objective = inter.text_values["objective"]
        habit = inter.text_values["habit"]

        db = next(get_db())
        plan = db.query(DailyPlan).filter(DailyPlan.id == self.plan_id).first()
        
        if not plan or plan.is_reviewed:
            await inter.response.send_message(embed=error_embed("Invalid Plan", "This plan cannot be edited."), ephemeral=True)
            return

        plan.objective = objective
        plan.habit = habit
        db.commit()

        embed = disnake.Embed(
            title=f"Daily Review: {plan.date.strftime('%Y-%m-%d')}",
            description="Did you conquer your objectives?",
            color=disnake.Color.from_rgb(52, 152, 219)
        )
        embed.add_field(name="Primary Objective", value=plan.objective, inline=False)
        embed.add_field(name="Self-Correction Habit", value=plan.habit, inline=False)

        try:
            await self.review_message.edit(embed=embed)
        except:
            pass
        
        await inter.response.send_message(embed=success_embed("Plan Updated", "Your daily plan has been successfully updated."), ephemeral=True)

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

    @disnake.ui.button(label="Edit Plan", style=disnake.ButtonStyle.primary, custom_id="btn_edit")
    async def edit_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        db = next(get_db())
        plan = db.query(DailyPlan).filter(DailyPlan.id == self.plan.id).first()
        if plan.is_reviewed:
            await inter.response.send_message(embed=error_embed("Already Reviewed", "This plan has already been accounted for and cannot be edited."), ephemeral=True)
            return
        await inter.response.send_modal(EditPlanModal(plan, inter.message))

    @disnake.ui.button(label="Delete Plan", style=disnake.ButtonStyle.secondary, custom_id="btn_delete")
    async def delete_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        db = next(get_db())
        plan = db.query(DailyPlan).filter(DailyPlan.id == self.plan.id).first()
        if plan.is_reviewed:
            await inter.response.send_message(embed=error_embed("Already Reviewed", "This plan has already been accounted for. Use /clear_history instead."), ephemeral=True)
            return

        db.delete(plan)
        db.commit()

        for child in self.children:
            child.disabled = True

        await inter.response.edit_message(embed=success_embed("Plan Deleted", "Your unreviewed plan has been successfully deleted."), view=self)


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

    @commands.slash_command(name="history", description="View your past daily strategic plans and victories (Private)")
    async def history(self, inter: disnake.ApplicationCommandInteraction):
        db = next(get_db())
        user = db.query(User).filter(User.id == inter.author.id).first()

        if not user:
            await inter.response.send_message(embed=error_embed("No History", "You have not made any plans yet."), ephemeral=True)
            return

        past_plans = db.query(DailyPlan).filter(
            DailyPlan.user_id == user.id,
            DailyPlan.is_reviewed == True
        ).order_by(DailyPlan.date.desc()).limit(10).all()

        if not past_plans:
            await inter.response.send_message(embed=info_embed("Empty Archives", "You have not completed any reviews yet. Complete your first review to see your history."), ephemeral=True)
            return

        embed = disnake.Embed(
            title="Your Accountability Ledger",
            description="Your 10 most recent reviews:",
            color=disnake.Color.from_rgb(52, 152, 219)
        )
        
        for plan in past_plans:
            emoji = "🟢" if plan.status == "victory" else "🔴"
            embed.add_field(
                name=f"{emoji} {plan.date.strftime('%b %d, %Y')}",
                value=f"**Objective:** {plan.objective[:75]}{'...' if len(plan.objective) > 75 else ''}",
                inline=False
            )
            
        embed.set_footer(text=f"Total Aura: {user.aura}")

        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="clear_history", description="Clear your accountability history (Private)")
    async def clear_history(
        self, 
        inter: disnake.ApplicationCommandInteraction, 
        date: str = commands.Param(default=None, description="Optional: specific date to clear (YYYY-MM-DD). Leave empty to clear ALL history.")
    ):
        db = next(get_db())
        user = db.query(User).filter(User.id == inter.author.id).first()

        if not user:
            await inter.response.send_message(embed=error_embed("No History", "You have not made any plans yet."), ephemeral=True)
            return

        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                await inter.response.send_message(embed=error_embed("Invalid Date", "Please format the date exactly as YYYY-MM-DD (e.g., 2026-03-12)."), ephemeral=True)
                return

            plan = db.query(DailyPlan).filter(
                DailyPlan.user_id == user.id,
                DailyPlan.date == target_date
            ).first()

            if not plan:
                await inter.response.send_message(embed=error_embed("Not Found", f"No plan was found on your record for {date}."), ephemeral=True)
                return

            if plan.status == "victory":
                user.aura = max(0, user.aura - 15)
            
            db.delete(plan)
            db.commit()
            
            await inter.response.send_message(embed=success_embed("Archive Deleted", f"Your plan and review for **{date}** have been expunged from the ledger."), ephemeral=True)

        else:
            plans = db.query(DailyPlan).filter(DailyPlan.user_id == user.id).all()
            if not plans:
                await inter.response.send_message(embed=info_embed("Empty Archives", "Your accountability ledger is already empty."), ephemeral=True)
                return
            
            deleted_count = 0
            for plan in plans:
                if plan.status == "victory":
                    user.aura = max(0, user.aura - 15)
                db.delete(plan)
                deleted_count += 1
            
            db.commit()
            await inter.response.send_message(embed=success_embed("Ledger Cleared", f"Your entire accountability history (**{deleted_count}** records) has been completely wiped."), ephemeral=True)

def setup(bot):
    bot.add_cog(PlanCog(bot))
