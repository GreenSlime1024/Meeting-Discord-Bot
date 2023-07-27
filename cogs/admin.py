import discord
from discord.ext import commands
from discord import app_commands
from bot import MyBot


class Admin(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin cog loaded.")

    @commands.is_owner()
    @commands.command()
    async def syncl(self, ctx: commands.Context):
        app_commands = await self.bot.tree.sync(guild=ctx.guild)
        await ctx.reply(f"synced {len(app_commands)} commands")

    @commands.is_owner()
    @commands.command()
    async def syncg(self, ctx: commands.Context):
        app_commands = await self.bot.tree.sync()
        await ctx.reply(f"synced {len(app_commands)} commands")

    @commands.is_owner()
    @app_commands.command(name="load",description="load extension")
    async def load(self, interaction: discord.Interaction, extension: str):
        await self.bot.load_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"`{extension}` loaded", ephemeral=False)

    @commands.is_owner()
    @app_commands.command(name="reload", description="reload extension")
    async def reload(self, interaction: discord.Interaction, extension: str):
        await self.bot.reload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"`{extension}` reloaded", ephemeral=False)

    @commands.is_owner()
    @app_commands.command(name="unload",description="unload extension")
    async def unload(self, interaction: discord.Interaction, extension: str):
        await self.bot.unload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"`{extension}` unloaded", ephemeral=False)


async def setup(bot):
    await bot.add_cog(Admin(bot))
