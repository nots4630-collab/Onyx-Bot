import os
import asyncio
import logging
from datetime import datetime
import discord
from discord.ext import commands
from colorama import Fore, Style, init

init(autoreset=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get token from environment
BOT_TOKEN = os.environ.get('BOT_TOKEN', os.getenv('BOT_TOKEN'))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found!")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    logger.info(f'{Fore.GREEN}Bot is ready!{Style.RESET_ALL}')
    logger.info(f'Bot: {bot.user}')
    logger.info(f'Guilds: {len(bot.guilds)}')

# Load cogs
async def load_cogs():
    cogs = ['cogs.moderation', 'cogs.utility', 'cogs.economy', 'cogs.games', 'cogs.level', 'cogs.music', 'cogs.antinuke']
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f'Loaded {cog}')
        except Exception as e:
            logger.error(f'Failed to load {cog}: {e}')

async def main():
    await load_cogs()
    try:
        await bot.start(BOT_TOKEN)
    except Exception as e:
        logger.error(f'Error: {e}')

asyncio.run(main())