import discord
from discord.ext import commands
from discord import app_commands
from bot import MyBot


class ToolsCog(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} loaded.")
        command_settings:app_commands.Group = self.bot.tree.get_command("settings")
        command_init:app_commands.Command = command_settings.get_command("init")
        command_meeting:app_commands.Group = self.bot.tree.get_command("meeting")
        command_create_meeting:app_commands.Command = command_meeting.get_command("create")
        command_init_mention = await self.bot.tree.find_mention_for(command_init)
        command_create_mention = await self.bot.tree.find_mention_for(command_create_meeting)
        
        embed_title = discord.Embed(title="How to create a meeting?", color=discord.Color.blue())

        embed_sever_settings = discord.Embed(title="1. Initialize the Settings", description=command_init_mention, color=discord.Color.blue())
        embed_sever_settings.add_field(name="[timezone]", value="timezone of the server", inline=False)
        embed_sever_settings.add_field(name="[meeting_admin_role]", value="role that can control meetings", inline=False)

        embed_create_meeting = discord.Embed(title="2. Create a Meeting", description=command_create_mention, color=discord.Color.blue())
        embed_create_meeting.add_field(name="[hour]", value="hour that meeting will starts at (use 24-hour clock)", inline=False)
        embed_create_meeting.add_field(name="[minute]", value="minute that meeting will starts at", inline=False)
        embed_create_meeting.add_field(name="(day)", value="day that meeting will starts at", inline=False)
        embed_create_meeting.add_field(name="(month)", value="month that meeting will starts at", inline=False)
        embed_create_meeting.add_field(name="(year)", value="year that meeting will starts at", inline=False)
        embed_create_meeting.add_field(name="(participate_role)", value="members who are asked to participate the meeting", inline=False)
        embed_create_meeting.add_field(name="(remind_time_ago)", value="when to remind the meeting", inline=False)

        self.embeds = [embed_title, embed_sever_settings, embed_create_meeting]

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
        embed.add_field(name="Support Server", value="https://discord.gg/4yGdjTdsYq", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: MyBot):
    await bot.add_cog(ToolsCog(bot))
