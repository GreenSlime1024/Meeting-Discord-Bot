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
            while not self.bot.is_closed():
                activitys = ["運作平台: Eri24816 租的 server",
                             "Made By GreenSlime1024", "還沒做好"]
                for i in activitys:
                    await self.bot.change_presence(activity=discord.Game(i))
                    await asyncio.sleep(15)

        self.bg_task = self.bot.loop.create_task(activiy_task())


async def setup(bot):
    await bot.add_cog(Activity(bot))
