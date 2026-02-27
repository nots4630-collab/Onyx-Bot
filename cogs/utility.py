import discord
from discord.ext import commands
from utils.utils import create_embed, create_error_embed

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Utility cog loaded")
    
    @commands.command(name="ping", help="Check bot latency")
    async def ping(self, ctx):
        embed = create_embed(
            "Pong!",
            f"Bot Latency: {round(self.bot.latency * 1000)}ms"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="help", help="Show all commands")
    async def help(self, ctx):
        embed = create_embed("Help Menu", "Prefix: ~")
        
        categories = {
            "Moderation": ["kick", "ban", "unmute", "warn", "clear"],
            "Utility": ["ping", "help", "userinfo", "serverinfo", "avatar", "invite"],
            "Economy": ["balance", "daily", "pay"],
            "Games": ["flip", "dice", "trivia", "rps"],
            "Level": ["rank", "levelboard"],
            "Music": ["play", "skip", "pause", "resume", "queue", "stop"]
        }
        
        for category, commands in categories.items():
            embed.add_field(name=category, value=", ".join([f"`{c}`" for c in commands]), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="userinfo", help="Get user information")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        
        embed = create_embed(f"User Info: {member}", "")
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Created At", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="serverinfo", help="Get server information")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        
        embed = create_embed(f"Server Info: {guild.name}", "")
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="avatar", help="Get user's avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = create_embed(f"Avatar: {member}", "")
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(name="invite", help="Get bot invite link")
    async def invite(self, ctx):
        embed = create_embed(
            "Invite Link",
            f"[Click here to invite](https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot)"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))