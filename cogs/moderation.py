import discord
from discord.ext import commands
from database.database import db
from utils.utils import create_embed, create_error_embed, create_success_embed, can_execute_action, ConfirmView

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Moderation cog loaded")
    
    @commands.command(name="kick", help="Kick a user from the server")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        can_act, message = can_execute_action(ctx, member)
        if not can_act:
            await ctx.send(embed=create_error_embed(message))
            return
        
        view = ConfirmView(ctx.author.id)
        embed = create_embed(
            "Kick Confirmation",
            f"Are you sure you want to kick **{member}**?\n\nReason: {reason or 'No reason provided'}"
        )
        await ctx.send(embed=embed, view=view)
        await view.wait()
        
        if view.value:
            try:
                try:
                    dm_embed = create_embed(
                        "You have been kicked",
                        f"You have been kicked from **{ctx.guild.name}**.\n\nReason: {reason or 'No reason provided'}"
                    )
                    await member.send(embed=dm_embed)
                except:
                    pass
                
                await ctx.guild.kick(member, reason=f"{ctx.author}: {reason}")
                
                kick_embed = create_success_embed(
                    f"Successfully kicked **{member}**\nReason: {reason or 'No reason provided'}"
                )
                await ctx.send(embed=kick_embed)
                
            except discord.Forbidden:
                await ctx.send(embed=create_error_embed("I don't have permission to kick this user."))
    
    @commands.command(name="ban", help="Ban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, days: int = 0, *, reason=None):
        if days < 0 or days > 7:
            await ctx.send(embed=create_error_embed("Days must be between 0 and 7."))
            return
        
        can_act, message = can_execute_action(ctx, member)
        if not can_act:
            await ctx.send(embed=create_error_embed(message))
            return
        
        try:
            try:
                dm_embed = create_embed(
                    "You have been banned",
                    f"You have been banned from **{ctx.guild.name}**.\n\nReason: {reason or 'No reason provided'}"
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            await ctx.guild.ban(member, reason=f"{ctx.author}: {reason}", delete_message_days=days)
            
            ban_embed = create_success_embed(
                f"Successfully banned **{member}**\nReason: {reason or 'No reason provided'}\nMessage deletion: {days} days"
            )
            await ctx.send(embed=ban_embed)
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("I don't have permission to ban this user."))
    
    @commands.command(name="unban", help="Unban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            
            unban_embed = create_success_embed(f"Successfully unbanned **{user}**")
            await ctx.send(embed=unban_embed)
            
        except discord.NotFound:
            await ctx.send(embed=create_error_embed("User not found or not banned."))
    
    @commands.command(name="mute", help="Mute a user")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason=None):
        can_act, message = can_execute_action(ctx, member)
        if not can_act:
            await ctx.send(embed=create_error_embed(message))
            return
        
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            try:
                muted_role = await ctx.guild.create_role(name="Muted", reason="Creating muted role")
                for channel in ctx.guild.channels:
                    await channel.set_permissions(muted_role, send_messages=False, add_reactions=False)
            except:
                await ctx.send(embed=create_error_embed("Cannot create muted role."))
                return
        
        try:
            await member.add_roles(muted_role, reason=f"{ctx.author}: {reason}")
            
            duration_text = ""
            if duration:
                duration_text = f"\nDuration: {duration}"
            
            mute_embed = create_success_embed(
                f"Successfully muted **{member}**\nReason: {reason or 'No reason provided'}{duration_text}"
            )
            await ctx.send(embed=mute_embed)
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Cannot add muted role to user."))
    
    @commands.command(name="unmute", help="Unmute a user")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await ctx.send(embed=create_error_embed("Muted role not found."))
            return
        
        try:
            await member.remove_roles(muted_role)
            
            unmute_embed = create_success_embed(f"Successfully unmuted **{member}**")
            await ctx.send(embed=unmute_embed)
            
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Cannot remove muted role from user."))
    
    @commands.command(name="warn", help="Warn a user")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        can_act, message = can_execute_action(ctx, member)
        if not can_act:
            await ctx.send(embed=create_error_embed(message))
            return
        
        await db.add_warning(member.id, ctx.author.id, reason or "No reason", ctx.guild.id)
        
        warn_embed = create_success_embed(
            f"Successfully warned **{member}**\nReason: {reason or 'No reason provided'}"
        )
        await ctx.send(embed=warn_embed)
    
    @commands.command(name="warnings", help="Check user's warnings")
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        
        warnings = await db.get_warnings(member.id, ctx.guild.id)
        
        if not warnings:
            embed = create_embed(f"Warnings for {member}", "No warnings found!")
            await ctx.send(embed=embed)
            return
        
        embed = create_embed(f"Warnings for {member}", f"Total warnings: {len(warnings)}")
        for i, warning in enumerate(warnings[:10], 1):
            mod = await self.bot.fetch_user(warning[2]) if warning[2] else "Unknown"
            embed.add_field(
                name=f"Warning #{i}",
                value=f"Reason: {warning[3]}\nModerator: {mod}\nDate: {warning[5]}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="purge", help="Delete multiple messages")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10):
        if amount < 1:
            await ctx.send(embed=create_error_embed("Amount must be at least 1."))
            return
        
        if amount > 100:
            await ctx.send(embed=create_error_embed("Maximum amount is 100."))
            return
        
        # Delete the command message first
        try:
            await ctx.message.delete()
        except:
            pass
        
        # Purge messages
        deleted = await ctx.channel.purge(limit=amount)
        
        # Send confirmation
        embed = create_success_embed(f"Successfully deleted **{len(deleted)}** messages")
        confirmation = await ctx.send(embed=embed)
        
        # Delete confirmation after 3 seconds
        await confirmation.delete(delay=3)
    
    @commands.command(name="purgeuser", help="Delete messages from a specific user")
    @commands.has_permissions(manage_messages=True)
    async def purgeuser(self, ctx, member: discord.Member, amount: int = 10):
        if amount < 1:
            await ctx.send(embed=create_error_embed("Amount must be at least 1."))
            return
        
        if amount > 100:
            await ctx.send(embed=create_error_embed("Maximum amount is 100."))
            return
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        def check(m):
            return m.author == member
        
        deleted = await ctx.channel.purge(limit=amount, check=check)
        
        embed = create_success_embed(f"Deleted **{len(deleted)}** messages from **{member}**")
        confirmation = await ctx.send(embed=embed)
        await confirmation.delete(delay=3)
    
    @commands.command(name="purgebots", help="Delete all bot messages")
    @commands.has_permissions(manage_messages=True)
    async def purgebots(self, ctx, amount: int = 10):
        if amount < 1:
            await ctx.send(embed=create_error_embed("Amount must be at least 1."))
            return
        
        if amount > 100:
            await ctx.send(embed=create_error_embed("Maximum amount is 100."))
            return
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        def check(m):
            return m.author.bot
        
        deleted = await ctx.channel.purge(limit=amount, check=check)
        
        embed = create_success_embed(f"Deleted **{len(deleted)}** bot messages")
        confirmation = await ctx.send(embed=embed)
        await confirmation.delete(delay=3)

async def setup(bot):
    await bot.add_cog(Moderation(bot))