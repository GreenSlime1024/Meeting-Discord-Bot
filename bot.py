import discord
import json
import os
from discord.ext import commands
import motor.motor_asyncio as motor


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="plz ", intents=discord.Intents.all(), owner_ids=set([1022080471506624545, 364976571192311808]))
        with open("not_token.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        connection_string = jdata["connection_string"]
        self.mongo_client = motor.AsyncIOMotorClient(connection_string)

    async def on_ready(self):
        print("Online.")

    async def setup_hook(self):
        from utils.meeting import Meeting_Buttons
        self.add_view(Meeting_Buttons())
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")

if __name__ == "__main__":
    bot = MyBot()
    with open("not_token.json", mode="r", encoding="utf8") as jfile:
        jdata = json.load(jfile)

    tree = bot.tree
    @tree.error
    async def on_app_command_error(interaction:discord.Interaction, error:discord.app_commands.AppCommandError):
        embed = discord.Embed(title="Error", color=discord.Color.red())
        embed.description = f"```{error}```"
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

    bot.run(jdata["discord_token"])
