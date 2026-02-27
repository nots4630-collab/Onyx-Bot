import discord
import datetime
import random
import string

def create_embed(title, description, color=0x2b2d31):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.datetime.utcnow()
    )
    return embed

def create_error_embed(description):
    return create_embed("Error", description, color=0xff0000)

def create_success_embed(description):
    return create_embed("Success", description, color=0x00ff00)

def format_number(num):
    return "{:,}".format(num)

def format_time(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"

def can_execute_action(ctx, target):
    if target == ctx.author:
        return False, "You cannot perform this action on yourself."
    if target == ctx.guild.owner:
        return False, "You cannot perform this action on the server owner."
    if ctx.author != ctx.guild.owner and ctx.author.top_role.position <= target.top_role.position:
        return False, "You cannot perform this action on someone with a higher or equal role."
    if ctx.guild.me.top_role.position <= target.top_role.position:
        return False, "I cannot perform this action on someone with a higher or equal role."
    return True, None

class ConfirmView(discord.ui.View):
    def __init__(self, author_id, timeout=30):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value = None