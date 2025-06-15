import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # Required for command reading

# Use '!' as the command prefix (e.g. !hello)
bot = commands.Bot(command_prefix='!', intents=intents)

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

bot.run(TOKEN)
