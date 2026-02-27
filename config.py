import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_PREFIX = "!"
BOT_NAME = "Ultimate Bot"

# Database Configuration
DATABASE_PATH = "database/bot.db"

# API Keys (add your own)
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Feature Settings
ENABLE_MUSIC = True
ENABLE_ECONOMY = True
ENABLE_LEVELING = True
ENABLE_MODERATION = True

# Music Settings
MUSIC_VOLUME = 0.5
MAX_QUEUE_SIZE = 100
MAX_SONG_LENGTH = 600

# Economy Settings
INITIAL_BALANCE = 100
DAILY_BONUS = 50