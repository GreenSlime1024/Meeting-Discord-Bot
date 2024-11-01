import discord
import json
import os
from discord.ext import commands
import motor.motor_asyncio as motor
from utils.mentionable_tree import MentionableTree
from pygit2 import Repository

with open("not_token.json", mode="r", encoding="utf8") as jfile:
    jdata = json.load(jfile)

branch = Repository('.').head.shorthand
CONNECTION_STRING = jdata["CONNECTION_STRING_"+branch]
TOKEN = jdata["TOKEN_"+branch]

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="plz ", intents=discord.Intents.all(), owner_ids=set([1022080471506624545, 364976571192311808]), tree_cls=MentionableTree)
        self.mongo_client = motor.AsyncIOMotorClient(CONNECTION_STRING)

    async def on_ready(self):
        print(f"Logged in as {self.user}")

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

    async def on_app_command_error(interaction:discord.Interaction, error:discord.app_commands.AppCommandError):
        embed = discord.Embed(
            title="❌ Error",
            description=f"```{error}```",
            color=discord.Color.red()
        )
        embed.add_field(name="Need help?", value="Join the [support server](https://discord.gg/4yGdjTdsYq)")

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)
    
    bot.tree.on_error = on_app_command_error

    bot.run(TOKEN)
