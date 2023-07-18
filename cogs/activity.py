import discord
from discord.ext import commands
import asyncio


class Activity(commands.Cog):
    @commands.Cog.listener()
    async def on_ready(self):
        print("Activity cog loaded.")

    def __init__(self, bot):
        self.bot = bot

        async def activiy_task():
            await self.bot.wait_until_ready()
            activitys = ["運作平台: Eri24816 租的 server", "Made By GreenSlime1024", "核心功能已完成", "但還有細節和新功能待開發"]
            for activity in activitys:
                await self.bot.change_presence(activity=discord.Game(activity))
                await asyncio.sleep(15)
                
        self.bot.loop.create_task(activiy_task())

async def setup(bot):
    await bot.add_cog(Activity(bot))