import discord
from discord.ext import commands
from discord import app_commands
from bot import MyBot


class Main(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Main cog loaded.")

    @app_commands.command(name="help", description="check help")
    async def help(self, interaction: discord.Interaction):
        embed_title = discord.Embed(title="How to create a meeting?", color=discord.Color.blue())

        embed_sever_settings = discord.Embed(title="1. Set Server Settings", color=discord.Color.blue())
        embed_sever_settings.add_field(name="[timezone]", value="timezone of your region", inline=False)
        embed_sever_settings.add_field(name="[meeting_admin_role]", value="choose the role that can control meeting", inline=False)

        embed_create_meeting = discord.Embed(title="2. Create a Meeting", color=discord.Color.blue())
        embed_create_meeting.add_field(name="[hour_local]", value="hour that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="[minute_local]", value="minute that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="(day_local)", value="day that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="(month_local)", value="month that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="(year_local)", value="year that meeting will starts at (24-hour)", inline=False)
        embed_create_meeting.add_field(name="(participate_role)", value="members of the role that are asked to join the meeting", inline=False)
        embed_create_meeting.add_field(name="(remind_time_ago)", value="time before the meeting that the bot will remind the members to join the meeting", inline=False)
        
        await interaction.response.send_message(embeds=[embed_title, embed_sever_settings, embed_create_meeting])
        
    @app_commands.command(name="ping", description="check ping")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"pong ({round(self.bot.latency*1000)}ms)")

    @app_commands.command(name="author", description="check author's blog")
    async def author(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://greenslime1024.github.io/")

    @app_commands.command(name="github-repo", description="check this bot's github repo")
    async def repo(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://github.com/GreenSlime1024/Distance-Learning-Discord-Bot")

    @app_commands.command(name="support-server", description="check this bot's support server")
    async def support_server(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://discord.gg/CVUjGJT94b")

    @app_commands.command(name="guild", description="check the guilds where I am in")
    async def guild(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Server List", color=discord.Color.blue())
        for guild in self.bot.guilds:
            embed.add_field(name=guild, value=guild.id, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Main(bot))
