import discord
from discord.ext import commands, tasks
from bot import MyBot


class ActivityCog(commands.Cog):
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog loaded.")
        
        self.activity_task.start()

    def __init__(self, bot: MyBot):
        self.bot = bot
        self.activitys = ["running on greenslime1024's good pi", "made by greenslime1024", "/create_meeting", "/set_server_settings"]
        self.index = 0

    @tasks.loop(seconds=15)
    async def activity_task(self):
        await self.bot.change_presence(activity=discord.Game(name=self.activitys[self.index]))
        self.index += 1
        if self.index == len(self.activitys):
            self.index = 0


async def setup(bot: MyBot):
    await bot.add_cog(ActivityCog(bot))
