import asyncio
import discord
import json
import os
from discord.ext import commands
from discord import app_commands

with open('not_token.json', mode='r', encoding='utf8') as jfile:
  jdata = json.load(jfile)

class MyBot(commands.Bot):
  def __init__(self):
    intents = discord.Intents.all()
    owners = [1022080471506624545, 364976571192311808]
    super().__init__(command_prefix='plz ', intents=intents, owner_ids = set(owners))

  async def on_ready(self):
    print('Online.')

  async def setup_hook(self):
    for filename in os.listdir('./cogs'):
      if filename.endswith('.py'):
        await bot.load_extension(f'cogs.{filename[:-3]}')

bot = MyBot()
if __name__ == "__main__":
  bot.run(jdata['TOKEN'])