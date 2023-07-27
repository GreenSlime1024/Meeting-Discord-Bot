import discord
from discord.ext import commands, tasks
import asyncio
from bot import MyBot


class Activity(commands.Cog):
    @commands.Cog.listener()
    async def on_ready(self):
        print("Activity cog loaded.")
        self.activity_task.start()

    def __init__(self, bot: MyBot):
        self.bot = bot
        self.activitys = ["運作平台: Eri24816 租的 server", "Made By GreenSlime1024", "核心功能已完成", "但還有細節和新功能待開發"]
        self.index = 0

    @tasks.loop(seconds=15)
    async def activity_task(self):
        await self.bot.change_presence(activity=discord.Game(name=self.activitys[self.index]))
        self.index += 1
        if self.index == len(self.activitys)-1:
            self.index = 0

async def setup(bot):
    await bot.add_cog(Activity(bot))