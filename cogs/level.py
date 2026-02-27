import discord
from discord.ext import commands
from utils.utils import create_embed, create_error_embed, create_success_embed, format_number
from database.database import db

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Level cog loaded")
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.bot:
            return
        
        if not ctx.guild:
            return
        
        level_up, new_level, new_xp = await db.add_xp(ctx.author.id, 5)
        
        if level_up:
            try:
                embed = create_success_embed(
                    f"{ctx.author.mention} leveled up to Level {new_level}!"
                )
                await ctx.channel.send(embed=embed)
            except:
                pass
    
    @commands.command(name="rank", help="Check your level and XP")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = await db.get_user(member.id, member.name, member.discriminator)
        
        level = user[7]
        xp = user[6]
        total_xp = user[5]
        
        next_level_xp = level * 100 * level
        current_level_xp = (level - 1) * 100 * (level - 1) if level > 1 else 0
        xp_in_level = xp
        xp_needed = next_level_xp - current_level_xp
        
        progress = (xp_in_level / xp_needed) * 100 if xp_needed > 0 else 100
        
        embed = create_embed(
            f"{member}'s Level",
            f"Level: {level}\nXP: {xp_in_level}/{xp_needed}\nTotal XP: {format_number(total_xp)}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        bar_length = 20
        filled = int(bar_length * progress / 100)
        bar = "#" * filled + "-" * (bar_length - filled)
        embed.add_field(name="Progress", value=f"`{bar}` {progress:.1f}%", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="level", help="Same as rank")
    async def level(self, ctx, member: discord.Member = None):
        await self.rank(ctx, member)
    
    @commands.command(name="levelboard", help="Show top users by level")
    async def levelboard(self, ctx):
        cursor = await db.db.execute(
            "SELECT * FROM users ORDER BY total_xp DESC LIMIT 10"
        )
        users = await cursor.fetchall()
        
        embed = create_embed("Level Leaderboard", "")
        
        for i, user in enumerate(users, 1):
            try:
                member = await self.bot.fetch_user(user[0])
                name = member.name if member else f"User {user[0]}"
            except:
                name = f"User {user[0]}"
            
            embed.add_field(
                name=f"#{i} {name}",
                value=f"Level: {user[7]} | XP: {format_number(user[5])}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Level(bot))