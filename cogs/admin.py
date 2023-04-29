import discord
from discord.ext import commands
from discord import app_commands
import os


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin cog loaded.")

    @commands.is_owner()
    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync()
        await ctx.reply(f"synced {len(fmt)} commands")

    @commands.is_owner()
    @app_commands.command(name="load",description="load extension")
    async def load(self, interaction: discord.Interaction, extension: str):
        await self.bot.load_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"loaded `{extension}`", ephemeral=False)

    @commands.is_owner()
    @app_commands.command(name="reload", description="reload extension")
    async def reload(self, interaction: discord.Interaction, extension: str):
        await self.bot.reload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"reloaded `{extension}`", ephemeral=False)

    @commands.is_owner()
    @app_commands.command(name="unload",description="unload extension")
    async def unload(self, interaction: discord.Interaction, extension: str):
        await self.bot.unload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"unloaded `{extension}`", ephemeral=False)


async def setup(bot):
    await bot.add_cog(Admin(bot))
