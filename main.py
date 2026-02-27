import os
import sys
import asyncio
import logging
from datetime import datetime
import discord
from discord.ext import commands
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=f'{Fore.CYAN}[{datetime.now().strftime("%H:%M:%S")}]{Style.RESET_ALL} %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from config import BOT_PREFIX
except ImportError:
    BOT_PREFIX = "!"

# Import utilities
from utils.utils import create_embed, create_error_embed

class UltimateBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
    
    async def setup_hook(self):
        """Load all cogs"""
        logger.info(f"{Fore.GREEN}Loading cogs...{Style.RESET_ALL}")
        
        cogs = [
            'cogs.moderation',
            'cogs.utility',
            'cogs.economy',
            'cogs.games',
            'cogs.level',
            'cogs.music',
            'cogs.antinuke'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"{Fore.GREEN}✓ Loaded {cog}{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"{Fore.RED}✗ Failed to load {cog}: {e}{Style.RESET_ALL}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}Bot Name: {self.user.name}{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}Bot ID: {self.user.id}{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}Guilds: {len(self.guilds)}{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}Latency: {round(self.latency * 1000)}ms{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
        logger.info(f"{Fore.YELLOW}Bot is ready! Prefix: {BOT_PREFIX}{Style.RESET_ALL}")

async def main():
    """Main function to run the bot"""
    from database.database import db
    
    # Connect to database
    logger.info(f"{Fore.YELLOW}Connecting to database...{Style.RESET_ALL}")
    try:
        await db.connect()
        logger.info(f"{Fore.GREEN}Database connected!{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"{Fore.RED}Database connection failed: {e}{Style.RESET_ALL}")
    
    # Get token from environment variable
    bot_token = os.environ.get('BOT_TOKEN', os.getenv('BOT_TOKEN', ''))
    
    if not bot_token or bot_token == '':
        logger.error(f"{Fore.RED}ERROR: BOT_TOKEN not found!{Style.RESET_ALL}")
        logger.error(f"{Fore.RED}Please set BOT_TOKEN environment variable.{Style.RESET_ALL}")
        sys.exit(1)
    
    logger.info(f"{Fore.YELLOW}Token found, logging in...{Style.RESET_ALL}")
    
    # Create bot instance
    bot = UltimateBot()
    
    # Run bot
    try:
        await bot.start(bot_token)
    except Exception as e:
        logger.error(f"{Fore.RED}Login failed: {e}{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")
    except Exception as e:
        print(f"Fatal error: {e}")