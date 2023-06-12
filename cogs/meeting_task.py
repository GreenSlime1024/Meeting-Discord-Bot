from discord.ext import commands
from bot import MyBot

class Meeting_task(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingCommand cog loaded.")

async def setup(bot):
    await bot.add_cog(Meeting_task(bot))