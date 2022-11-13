import discord
from discord.ext import commands
from core.classes import Cog_Extension
from discord import app_commands


class Main(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print('Main cog loaded.')

    @app_commands.command(name='ping', description='check ping')
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'pong ({round(self.bot.latency*1000)}ms)')

    @app_commands.command(name="avatar", description="check someone's avatar")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        if member == None:
            member = interaction.user
        userAvatarUrl = member.display_avatar
        await interaction.response.send_message(str(userAvatarUrl))

    @app_commands.command(name='author', description="check GreenSlime's blog")
    async def author(self, interaction: discord.Interaction):
        await interaction.response.send_message('https://greenslime1024.github.io/')

    @app_commands.command(name='github-repo', description="check ROW Bot's github repo")
    async def repo(self, interaction: discord.Interaction):
        await interaction.response.send_message('https://github.com/GreenSlime1024/Distance-Learning-Discord-Bot')

    @app_commands.command(name='guild', description='check guilds which i provide services')
    async def guild(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Server List", color=0x8280ff)
        for guild in self.bot.guilds:
            embed.add_field(name=guild, value=guild.id, inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Main(bot))
