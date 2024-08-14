import discord
from discord.ext import commands
from discord import app_commands
from bot import MyBot


class Tools(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        embed_title = discord.Embed(title="How to create a meeting?", color=discord.Color.blue())

        embed_sever_settings = discord.Embed(title="1. Set Server Settings", description="</set_server_settings:1121308554448617602>", color=discord.Color.blue())
        embed_sever_settings.add_field(name="[timezone]", value="timezone of your region", inline=False)
        embed_sever_settings.add_field(name="[meeting_admin_role]", value="choose the role that can control meeting", inline=False)

        embed_create_meeting = discord.Embed(title="2. Create a Meeting", description="</create_meeting:1101520045449957467>", color=discord.Color.blue())
        embed_create_meeting.add_field(name="[hour_local]", value="hour that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="[minute_local]", value="minute that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="(day_local)", value="day that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="(month_local)", value="month that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="(year_local)", value="year that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="(participate_role)", value="members of the role that are asked to join the meeting", inline=False)
        embed_create_meeting.add_field(name="(remind_time_ago)", value="time before the meeting that the bot will remind the members to join the meeting", inline=False)

        self.embeds = [embed_title, embed_sever_settings, embed_create_meeting]
        print(f"{self.__class__.__name__} cog loaded.")

    @app_commands.command(name="help", description="check help")
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message(embeds=self.embeds)
        
    @app_commands.command(name="ping", description="check ping")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"pong ({round(self.bot.latency*1000)}ms)")

    @app_commands.command(name="about", description="check this bot's info")
    async def about(self, interaction: discord.Interaction):
        embed = discord.Embed(title="About This Bot", color=discord.Color.blue())
        embed.add_field(name="Author", value="GreenSlime1024", inline=False)
        embed.add_field(name="Github Repo", value="https://github.com/GreenSlime1024/Meeting-Discord-Bot", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: MyBot):
    await bot.add_cog(Tools(bot))
