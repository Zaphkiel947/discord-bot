import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp
import asyncio

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # Required for command reading

# Use '!' as the command prefix (e.g. !hello)
bot = commands.Bot(command_prefix='!', intents=intents)

song_queues = {}


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Add a simple command: !hello
@bot.command()
async def hello(ctx):
    await ctx.send('Alola!')


@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

#for words and phrases 
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return 
    
    msg = message.content.lower()

    if any(phrase in msg for phrase in ["fuck you", "fk you", "fuk you"]):
        await message.channel.send("you are gay-_-")

    elif any(phrase in msg for phrase in ["alive"]):
        await message.channel.send("He is dead.") 

    
    # ✅ Handle "miku ..." custom keyword
    if msg.startswith("miku"):
        parts = message.content.split(" ", 1)
        
        if len(parts) == 1:
            await message.channel.send("Hi, I'm Miku! How can I help?")
            return

        command = parts[1].strip()

        # 🎵 Play music if it's a URL
        if command.startswith("play "):
            link = command[5:].strip()
            ctx = await bot.get_context(message)
            await play(ctx, link)
            return

        # 🔁 Built-in triggers
        elif command == "ping":
            await message.channel.send("pong!")
            return

        elif "how are you" in command:
            await message.channel.send("I'm doing great! ✨ What about you?")
            return

        else:
            await message.channel.send(f"🤖 Sorry, I didn't understand '{command}'")
            return

    await bot.process_commands(message)

#Music command (play)
@bot.command()
async def play(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("You're not connected to a voice channel.")
        return
    
    if "list=" in url:
        await ctx.send("❌ Playlist links are not supported. Use direct YouTube video links.")
        return
    
    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)

    vc = ctx.voice_client

#Stop any current playing audio
    if vc.is_playing():
        vc.stop()

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']

    ffmpeg_opts = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    source = await discord.FFmpegOpusAudio.from_probe(audio_url, **ffmpeg_opts)
    vc.play(source, after=lambda e: print(f'Finished palying: {e}' if e else 'Playback complete.'))

    await ctx.send(f"🎶 Now playing: **{info['title']}**")

#Leave voice channel
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel.")
    else:
        await ctx.send("Not in a voice channel.")

#Stop playing
@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_palying():
        ctx.voice_client.stop()
        await ctx.send("Playback stopped.")
    else:
        await ctx.send("Nothing is playing.")

@bot.command()
async def play_song(ctx, *, url):
    guild_id = ctx.guild.id

    if guild_id not in song_queues:
        song_queues[guild_id] = []

    song_queues[guild_id].append(url)

    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You're not in a voice channel.")
            return

    if not ctx.voice_client.is_playing():
        await play_next(ctx.guild.id)

#Play nexr helper
async def play_next(ctx):
    guild_id = ctx.guild.id

    if guild_id not in song_queues or not song_queues[guild_id]:
        await ctx.voice_client.disconnect()
        return

    url = song_queues[guild_id].pop(0)  # ✅ YOU MUST HAVE THIS LINE

    ydl_opts = {'format': 'bestaudio', 'quiet': True, 'noplaylist': True}
    ffmpeg_opts = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info.get("title", "Unknown Title")

        FFMPEG_PATH = "./ffmpeg.exe"
        source = await discord.FFmpegOpusAudio.from_probe(audio_url, executable=FFMPEG_PATH, **ffmpeg_opts)


        def after_playing(error):
            if error:
                print(f"[ERROR] {error}")
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

        ctx.voice_client.play(source, after=after_playing)
        await ctx.send(f"🎵 Now playing: **{title}**")

    except Exception as e:
        await ctx.send(f"❌ Could not play the song: {e}")

@bot.command(name="queue")
async def show_queue(ctx):
    guild_id = ctx.guild.id

    if guild_id not in song_queues or not song_queues[guild_id]:
        await ctx.send("🔇 The queue is empty.")
        return

    queue_list = song_queues[guild_id]
    msg = "**🎶 Upcoming Songs:**\n"
    for i, url in enumerate(queue_list, start=1):
        msg += f"{i}. {url}\n"

    await ctx.send(msg)



#Pause
@bot.command()
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ Paused.")

#Resume
@bot.command()
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶ Resumed.")

#Skip
@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()  # triggers `after` callback to play next
        await ctx.send("⏭ Skipped to next song.")


bot.run(TOKEN)
