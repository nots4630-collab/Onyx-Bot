import discord
from discord.ext import commands
from utils.utils import create_embed, create_error_embed, create_success_embed, format_number
from database.database import db
import random

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Games cog loaded")
    
    @commands.command(name="flip", help="Flip a coin (heads or tails)")
    async def flip(self, ctx, amount: int, choice: str = "heads"):
        if amount <= 0:
            await ctx.send(embed=create_error_embed("Amount must be greater than 0."))
            return
        
        user = await db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        if user[3] < amount:
            await ctx.send(embed=create_error_embed("Insufficient balance!"))
            return
        
        choices = ["heads", "tails"]
        choice = choice.lower()
        
        if choice not in choices:
            await ctx.send(embed=create_error_embed("Choose 'heads' or 'tails'."))
            return
        
        result = random.choice(choices)
        won = result == choice
        
        if won:
            await db.update_user_balance(ctx.author.id, amount, "gambling", f"Coin flip won ({result})")
            embed = create_success_embed(
                f"🎉 You won!\n\nYou chose **{choice}**, it was **{result}**\nYou won **{format_number(amount)}** coins!"
            )
        else:
            await db.update_user_balance(ctx.author.id, -amount, "gambling", f"Coin flip lost ({result})")
            embed = create_error_embed(
                f"😢 You lost!\n\nYou chose **{choice}**, it was **{result}**\nYou lost **{format_number(amount)}** coins!"
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="dice", help="Roll a dice (1-6)")
    async def dice(self, ctx, amount: int, number: int = None):
        if amount <= 0:
            await ctx.send(embed=create_error_embed("Amount must be greater than 0."))
            return
        
        user = await db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        if user[3] < amount:
            await ctx.send(embed=create_error_embed("Insufficient balance!"))
            return
        
        roll = random.randint(1, 6)
        won = False
        
        if number:
            if number < 1 or number > 6:
                await ctx.send(embed=create_error_embed("Number must be between 1 and 6."))
                return
            
            if roll == number:
                won = True
                multiplier = 6
            else:
                won = False
                multiplier = 0
        else:
            won = roll >= 4
            multiplier = 2 if won else 0
        
        if won:
            winnings = amount * multiplier
            await db.update_user_balance(ctx.author.id, winnings, "gambling", f"Dice roll won ({roll})")
            embed = create_success_embed(
                f"🎲 You rolled **{roll}**\n\nYou won **{format_number(winnings)}** coins!"
            )
        else:
            await db.update_user_balance(ctx.author.id, -amount, "gambling", f"Dice roll lost ({roll})")
            embed = create_error_embed(
                f"🎲 You rolled **{roll}**\n\nYou lost **{format_number(amount)}** coins!"
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="trivia", help="Play a trivia game")
    async def trivia(self, ctx, amount: int = 10):
        if amount <= 0:
            await ctx.send(embed=create_error_embed("Amount must be greater than 0."))
            return
        
        user = await db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        if user[3] < amount:
            await ctx.send(embed=create_error_embed("Insufficient balance!"))
            return
        
        questions = [
            {"q": "What is 2 + 2?", "a": ["4"]},
            {"q": "What color is the sky?", "a": ["blue", "sky blue"]},
            {"q": "How many legs does a spider have?", "a": ["8", "eight"]},
            {"q": "What is the capital of France?", "a": ["paris"]},
            {"q": "What is 5 x 5?", "a": ["25"]},
            {"q": "What is the largest planet?", "a": ["jupiter"]},
            {"q": "How many days in a leap year?", "a": ["366"]},
            {"q": "What is H2O?", "a": ["water"]},
            {"q": "What is the fastest land animal?", "a": ["cheetah"]},
            {"q": "How many continents are there?", "a": ["7", "seven"]}
        ]
        
        question = random.choice(questions)
        
        embed = create_embed(
            "❓ Trivia Question",
            f"**Question:** {question['q']}\n\nYou have 15 seconds to answer!\n\nReward: **{format_number(amount * 5)}** coins"
        )
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for("message", timeout=15.0, check=check)
            
            if msg.content.lower() in question["a"]:
                await db.update_user_balance(ctx.author.id, amount * 5, "trivia", "Correct answer")
                embed = create_success_embed(
                    f"✅ Correct!\n\nThe answer was **{question['a'][0]}**\nYou won **{format_number(amount * 5)}** coins!"
                )
            else:
                await db.update_user_balance(ctx.author.id, -amount, "trivia", "Wrong answer")
                embed = create_error_embed(
                    f"❌ Wrong!\n\nThe answer was **{question['a'][0]}**\nYou lost **{format_number(amount)}** coins!"
                )
            
            await ctx.send(embed=embed)
            
        except:
            await db.update_user_balance(ctx.author.id, -amount, "trivia", "Timeout")
            embed = create_error_embed(
                f"⏰ Time's up!\n\nYou lost **{format_number(amount)}** coins!"
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="rps", help="Rock Paper Scissors")
    async def rps(self, ctx, amount: int, choice: str):
        if amount <= 0:
            await ctx.send(embed=create_error_embed("Amount must be greater than 0."))
            return
        
        user = await db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        if user[3] < amount:
            await ctx.send(embed=create_error_embed("Insufficient balance!"))
            return
        
        choice = choice.lower()
        valid_choices = ["rock", "paper", "scissors"]
        
        if choice not in valid_choices:
            await ctx.send(embed=create_error_embed("Choose rock, paper, or scissors."))
            return
        
        # bot_choice MUST be defined BEFORE using it
        bot_choice = random.choice(valid_choices)
        
        win_conditions = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        
        if choice == bot_choice:
            await db.update_user_balance(ctx.author.id, 0, "rps", "Tie")
            embed = create_embed(
                "🤝 It's a Tie!",
                f"You: **{choice}**\nBot: **{bot_choice}**\n\nYour bet has been returned."
            )
        elif win_conditions[choice] == bot_choice:
            await db.update_user_balance(ctx.author.id, amount, "rps", f"Won against {bot_choice}")
            embed = create_success_embed(
                f"🎉 You Won!\n\nYou: **{choice}**\nBot: **{bot_choice}**\n\nYou won **{format_number(amount)}** coins!"
            )
        else:
            await db.update_user_balance(ctx.author.id, -amount, "rps", f"Lost against {bot_choice}")
            embed = create_error_embed(
                f"😢 You Lost!\n\nYou: **{choice}**\nBot: **{bot_choice}**\n\nYou lost **{format_number(amount)}** coins!"
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Games(bot))