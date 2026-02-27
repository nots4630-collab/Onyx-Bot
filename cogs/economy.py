import discord
from discord.ext import commands
from utils.utils import create_embed, create_error_embed, create_success_embed, format_number
from database.database import db
from config import INITIAL_BALANCE, DAILY_BONUS
import datetime

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Economy cog loaded")
    
    @commands.command(name="balance", help="Check your balance")
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = await db.get_user(member.id, member.name, member.discriminator)
        
        embed = create_embed(
            f"{member}'s Balance",
            f"Wallet: {format_number(user[3])} coins\nBank: {format_number(user[4])} coins"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="daily", help="Claim daily bonus")
    async def daily(self, ctx):
        user = await db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        if user[11] == today:
            embed = create_error_embed("You have already claimed your daily bonus today!")
            await ctx.send(embed=embed)
            return
        
        await db.update_user_balance(ctx.author.id, DAILY_BONUS, "daily", "Daily bonus")
        
        embed = create_success_embed(
            f"You received {format_number(DAILY_BONUS)} coins!\n\nCome back tomorrow for more!"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="pay", help="Transfer coins to another user")
    async def pay(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            await ctx.send(embed=create_error_embed("Amount must be greater than 0."))
            return
        
        sender = await db.get_user(ctx.author.id, ctx.author.name, ctx.author.discriminator)
        
        if sender[3] < amount:
            await ctx.send(embed=create_error_embed("Insufficient balance!"))
            return
        
        await db.update_user_balance(ctx.author.id, -amount, "transfer", f"Transfer to {member}")
        await db.update_user_balance(member.id, amount, "transfer", f"Transfer from {ctx.author}")
        
        embed = create_success_embed(
            f"You sent {format_number(amount)} coins to {member}"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="leaderboard", help="Show richest users")
    async def leaderboard(self, ctx):
        cursor = await db.db.execute(
            "SELECT * FROM users ORDER BY balance + bank DESC LIMIT 10"
        )
        users = await cursor.fetchall()
        
        embed = create_embed("Richest Users", "")
        
        for i, user in enumerate(users, 1):
            try:
                member = await self.bot.fetch_user(user[0])
                name = member.name if member else f"User {user[0]}"
            except:
                name = f"User {user[0]}"
            
            embed.add_field(
                name=f"#{i} {name}",
                value=f"Wallet: {format_number(user[3])} | Bank: {format_number(user[4])}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))