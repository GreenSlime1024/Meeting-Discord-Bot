import discord
from discord.ext import commands

from bot import MyBot


class Cog_Extension(commands.Cog):
    def __init__(self, bot:MyBot):
        self.bot = bot
