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
        tools_embed = discord.Embed(title="Tools Command", color=discord.Color.blue())
        tools_embed.add_field(name="ping", value="check ping", inline=False)
        tools_embed.add_field(name="author", value="check author's blog", inline=False)
        tools_embed.add_field(name="github-repo", value="check this bot's github repo", inline=False)
        tools_embed.add_field(name="support-server", value="check this bot's support server", inline=False)
        tools_embed.add_field(name="guild", value="check the guilds where I am in", inline=False)
        
        meeting_embed = discord.Embed(title="Meeting Command", color=discord.Color.blue())
        meeting_embed.add_field(name="</set_server_settings:1121308554448617602>", value="set server settings\nYou must do this before you </create_meeting:1101520045449957467>", inline=False)
        meeting_embed.add_field(name="</create_meeting:1101520045449957467>", value="create a meeting", inline=False)
        

        embeds = [tools_embed, meeting_embed]
        await interaction.response.send_message(embeds=embeds)
        

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
