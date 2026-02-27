import discord
from discord.ext import commands
from utils.utils import create_embed, create_error_embed, create_success_embed, format_time
import yt_dlp
import asyncio
from collections import deque
import os

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.now_playing = {}
        
        self.ytdl_options = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "outtmpl": "downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s",
            "quiet": True,
        }
        
        self.ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -filter:a \"volume=0.5\""
        }
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Music cog loaded")
    
    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]
    
    @commands.command(name="play", help="Play a song")
    async def play(self, ctx, *, query):
        if not ctx.author.voice:
            await ctx.send(embed=create_error_embed("You must be in a voice channel!"))
            return
        
        if not ctx.guild.me.voice:
            try:
                await ctx.author.voice.channel.connect()
            except Exception as e:
                await ctx.send(embed=create_error_embed(f"Cannot join voice channel: {str(e)}"))
                return
        
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        
        await ctx.send(embed=create_embed("Searching", f"Searching for: **{query}**"))
        
        try:
            with yt_dlp.YoutubeDL(self.ytdl_options) as ytdl:
                info = ytdl.extract_info(query, download=False)
                
                if "entries" in info:
                    info = info[0]
                
                song_title = info["title"]
                song_url = info["url"]
                duration = info.get("duration", 0)
                thumbnail = info.get("thumbnail", None)
                
                song = {
                    "title": song_title,
                    "url": song_url,
                    "duration": duration,
                    "thumbnail": thumbnail,
                    "requester": ctx.author
                }
                
                queue = self.get_queue(ctx.guild.id)
                queue.append(song)
                
                if ctx.guild.id not in self.now_playing:
                    await self.play_next(ctx)
                else:
                    embed = create_embed(
                        "Added to Queue",
                        f"**{song_title}**\nDuration: {format_time(duration)}\nPosition: {len(queue)}"
                    )
                    if thumbnail:
                        embed.set_thumbnail(url=thumbnail)
                    await ctx.send(embed=embed)
                    
        except Exception as e:
            await ctx.send(embed=create_error_embed(f"Error: {str(e)}"))
    
    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        
        if not queue:
            self.now_playing.pop(ctx.guild.id, None)
            await ctx.send(embed=create_embed("Queue Empty", "No more songs in queue."))
            return
        
        song = queue.popleft()
        self.now_playing[ctx.guild.id] = song
        
        try:
            voice_client = ctx.guild.voice_client
            
            audio_source = discord.FFmpegOpusAudio(song["url"], **self.ffmpeg_options)
            
            def after_playing(error):
                if error:
                    print(f"Error in playback: {error}")
                asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
            
            voice_client.play(audio_source, after=after_playing)
            
            embed = create_embed(
                "Now Playing",
                f"**{song['title']}**\nDuration: {format_time(song['duration'])}\nRequested by: {song['requester'].mention}"
            )
            if song.get("thumbnail"):
                embed.set_thumbnail(url=song["thumbnail"])
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(embed=create_error_embed(f"Error playing song: {str(e)}"))
    
    @commands.command(name="skip", help="Skip current song")
    async def skip(self, ctx):
        if not ctx.guild.voice_client:
            await ctx.send(embed=create_error_embed("Not playing anything!"))
            return
        
        voice_client = ctx.guild.voice_client
        voice_client.stop()
        
        await ctx.send(embed=create_success_embed("Skipped current song!"))
    
    @commands.command(name="stop", help="Stop music and clear queue")
    async def stop(self, ctx):
        if ctx.guild.voice_client:
            ctx.guild.voice_client.stop()
            self.queues[ctx.guild.id] = deque()
            self.now_playing.pop(ctx.guild.id, None)
            await ctx.send(embed=create_success_embed("Music stopped and queue cleared!"))
        else:
            await ctx.send(embed=create_error_embed("Not playing anything!"))
    
    @commands.command(name="pause", help="Pause music")
    async def pause(self, ctx):
        if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.pause()
            await ctx.send(embed=create_embed("Paused", "Music has been paused."))
        else:
            await ctx.send(embed=create_error_embed("Nothing is playing!"))
    
    @commands.command(name="resume", help="Resume music")
    async def resume(self, ctx):
        if ctx.guild.voice_client and ctx.guild.voice_client.is_paused():
            ctx.guild.voice_client.resume()
            await ctx.send(embed=create_embed("Resumed", "Music has been resumed."))
        else:
            await ctx.send(embed=create_error_embed("Nothing is paused!"))
    
    @commands.command(name="queue", help="Show music queue")
    async def queue(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        now_playing = self.now_playing.get(ctx.guild.id)
        
        if not queue and not now_playing:
            await ctx.send(embed=create_embed("Queue", "Queue is empty!"))
            return
        
        embed = create_embed("Music Queue", "")
        
        if now_playing:
            embed.add_field(
                name="Now Playing",
                value=f"**{now_playing['title']}**\nDuration: {format_time(now_playing['duration'])}",
                inline=False
            )
        
        if queue:
            queue_list = []
            for i, song in enumerate(queue, 1):
                queue_list.append(f"{i}. {song['title']} ({format_time(song['duration'])})")
            
            queue_text = "\n".join(queue_list[:10])
            if len(queue) > 10:
                queue_text += f"\n... and {len(queue) - 10} more"
            
            embed.add_field(name="Up Next", value=queue_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="volume", help="Set volume (0-100)")
    async def volume(self, ctx, volume: int = 50):
        if volume < 0 or volume > 100:
            await ctx.send(embed=create_error_embed("Volume must be between 0 and 100!"))
            return
        
        if ctx.guild.voice_client:
            ctx.guild.voice_client.source.volume = volume / 100
            await ctx.send(embed=create_embed("Volume", f"Volume set to {volume}%"))
        else:
            await ctx.send(embed=create_error_embed("Not playing anything!"))
    
    @commands.command(name="np", help="Now playing")
    async def np(self, ctx):
        now_playing = self.now_playing.get(ctx.guild.id)
        
        if not now_playing:
            await ctx.send(embed=create_error_embed("Nothing is playing!"))
            return
        
        embed = create_embed(
            "Now Playing",
            f"**{now_playing['title']}**\nDuration: {format_time(now_playing['duration'])}\nRequested by: {now_playing['requester'].mention}"
        )
        if now_playing.get("thumbnail"):
            embed.set_thumbnail(url=now_playing["thumbnail"])
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))