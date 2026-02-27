import discord
from discord.ext import commands
from utils.utils import create_embed, create_error_embed, create_success_embed
from database.database import db
import asyncio
import time

class Antinuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raid_mode = {}
        self.protected_users = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Antinuke cog loaded")
    
    @commands.command(name="antinuke", help="Enable or disable antinuke protection")
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx, mode: str = None):
        if mode is None:
            if ctx.guild.id in self.raid_mode:
                status = "ENABLED" if self.raid_mode[ctx.guild.id] else "DISABLED"
                embed = create_embed("Antinuke Status", f"Antinuke is currently **{status}**")
            else:
                embed = create_embed("Antinuke Status", "Antinuke is currently **DISABLED**")
            await ctx.send(embed=embed)
            return
        
        mode = mode.lower()
        if mode == "on":
            self.raid_mode[ctx.guild.id] = True
            embed = create_success_embed("Antinuke protection is now **ENABLED**")
            await ctx.send(embed=embed)
        elif mode == "off":
            self.raid_mode[ctx.guild.id] = False
            embed = create_embed("Antinuke Status", "Antinuke protection is now **DISABLED**")
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=create_error_embed("Use `!antinuke on` or `!antinuke off`"))
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if guild.id not in self.raid_mode or not self.raid_mode[guild.id]:
            return
        
        # Get audit log to find who banned
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            if entry.target == user:
                moderator = entry.user
                
                # Check if moderator is not the owner or admin
                if moderator.id == guild.owner_id:
                    return
                
                if moderator.guild_permissions.administrator:
                    return
                
                # Ban the user who banned
                try:
                    await guild.ban(moderator, reason="Antinuke: Unauthorized ban")
                    embed = create_success_embed(
                        f"Antinuke triggered!\n\n**Banned:** {moderator}\n**Reason:** Unauthorized ban attempt"
                    )
                    
                    # Try to notify in a channel
                    for channel in guild.channels:
                        if isinstance(channel, discord.TextChannel) and channel.permissions_for(guild.me).send_messages:
                            await channel.send(embed=embed)
                            break
                except:
                    pass
    
    @commands.Cog.listener()
    async def on_member_kick(self, guild, user):
        if guild.id not in self.raid_mode or not self.raid_mode[guild.id]:
            return
        
        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
            if entry.target == user:
                moderator = entry.user
                
                if moderator.id == guild.owner_id:
                    return
                
                if moderator.guild_permissions.administrator:
                    return
                
                try:
                    await guild.ban(moderator, reason="Antinuke: Unauthorized kick")
                    embed = create_success_embed(
                        f"Antinuke triggered!\n\n**Kicked:** {moderator}\n**Reason:** Unauthorized kick attempt"
                    )
                    
                    for channel in guild.channels:
                        if isinstance(channel, discord.TextChannel) and channel.permissions_for(guild.me).send_messages:
                            await channel.send(embed=embed)
                            break
                except:
                    pass
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if channel.guild.id not in self.raid_mode or not self.raid_mode[channel.guild.id]:
            return
        
        async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=1):
            creator = entry.user
            
            if creator.id == channel.guild.owner_id:
                return
            
            if creator.guild_permissions.administrator:
                return
            
            try:
                await channel.delete()
                await channel.guild.ban(creator, reason="Antinuke: Unauthorized channel creation")
                embed = create_success_embed(
                    f"Antinuke triggered!\n\n**User:** {creator}\n**Reason:** Unauthorized channel creation"
                )
                
                for ch in channel.guild.channels:
                    if isinstance(ch, discord.TextChannel) and ch.permissions_for(channel.guild.me).send_messages:
                        await ch.send(embed=embed)
                        break
            except:
                pass
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if role.guild.id not in self.raid_mode or not self.raid_mode[role.guild.id]:
            return
        
        async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_create, limit=1):
            creator = entry.user
            
            if creator.id == role.guild.owner_id:
                return
            
            if creator.guild_permissions.administrator:
                return
            
            try:
                await role.delete()
                await role.guild.ban(creator, reason="Antinuke: Unauthorized role creation")
                embed = create_success_embed(
                    f"Antinuke triggered!\n\n**User:** {creator}\n**Reason:** Unauthorized role creation"
                )
                
                for channel in role.guild.channels:
                    if isinstance(channel, discord.TextChannel) and channel.permissions_for(role.guild.me).send_messages:
                        await channel.send(embed=embed)
                        break
            except:
                pass
    
    @commands.command(name="whitelist", help="Whitelist a user from antinuke")
    @commands.has_permissions(administrator=True)
    async def whitelist(self, ctx, member: discord.Member):
        if ctx.guild.id not in self.protected_users:
            self.protected_users[ctx.guild.id] = []
        
        if member.id not in self.protected_users[ctx.guild.id]:
            self.protected_users[ctx.guild.id].append(member.id)
            embed = create_success_embed(f"**{member}** is now whitelisted from antinuke")
        else:
            embed = create_embed("Whitelist", f"**{member}** is already whitelisted")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="unwhitelist", help="Remove user from whitelist")
    @commands.has_permissions(administrator=True)
    async def unwhitelist(self, ctx, member: discord.Member):
        if ctx.guild.id in self.protected_users and member.id in self.protected_users[ctx.guild.id]:
            self.protected_users[ctx.guild.id].remove(member.id)
            embed = create_success_embed(f"**{member}** is removed from whitelist")
        else:
            embed = create_error_embed(f"**{member}** is not in whitelist")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="antinukestatus", help="Check antinuke settings")
    @commands.has_permissions(administrator=True)
    async def antinuke_status(self, ctx):
        status = "ENABLED" if self.raid_mode.get(ctx.guild.id, False) else "DISABLED"
        
        embed = create_embed("Antinuke Settings", f"Status: **{status}**")
        
        whitelisted = self.protected_users.get(ctx.guild.id, [])
        if whitelisted:
            whitelisted_users = []
            for user_id in whitelisted:
                user = self.bot.get_user(user_id)
                if user:
                    whitelisted_users.append(str(user))
            embed.add_field(name="Whitelisted Users", value=", ".join(whitelisted_users) if whitelisted_users else "None")
        else:
            embed.add_field(name="Whitelisted Users", value="None")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Antinuke(bot))