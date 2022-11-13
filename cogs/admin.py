import discord
from discord.ext import commands
from core.classes import Cog_Extension
from discord import app_commands
import os


class Admin(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        print('Admin cog loaded.')

    @commands.is_owner()
    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync()
        await ctx.reply(f'synced {len(fmt)} commands')

    @commands.is_owner()
    @app_commands.command()
    async def system(self, interaction: discord.Interaction, command: str):
        os.system(command)
        await interaction.response.send_message(f'`{command}` sended', ephemeral=False)

    @commands.is_owner()
    @app_commands.command()
    async def load(self, interaction: discord.Interaction, extension: str):
        await self.bot.load_extension(f'cogs.{extension}')
        await interaction.response.send_message(f'loaded `{extension}`', ephemeral=False)

    @commands.is_owner()
    @app_commands.command()
    async def reload(self, interaction: discord.Interaction, extension: str):
        await self.bot.reload_extension(f'cogs.{extension}')
        await interaction.response.send_message(f'reloaded `{extension}`', ephemeral=False)

    @commands.is_owner()
    @app_commands.command()
    async def unload(self, interaction: discord.Interaction, extension: str):
        await self.bot.unload_extension(f'cogs.{extension}')
        await interaction.response.send_message(f'unloaded `{extension}`', ephemeral=False)


async def setup(bot):
    await bot.add_cog(Admin(bot))
