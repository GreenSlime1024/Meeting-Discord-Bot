import asyncio
import discord
import json
import os
from discord.ext import commands


def create_require_json():
    filenames = ["absent_members_temp.json", "meeting_info_count.json",
                 "meeting_info.json", "meeting_save.json", "guilds_info.json"]
    data = {}
    for filename in filenames:
        if os.path.exists(filename):
            pass
        else:
            with open(filename, "w") as jfile:
                json.dump(data, jfile)

    if os.path.exists("not_token.json"):
        pass
    else:
        TOKEN = input("paste your bot's token here: ")
        data = {
            "TOKEN": TOKEN
        }
        with open("not_token.json", "w") as jfile:
            json.dump(data, jfile)
    print("require jsons are created.")


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        owners = [1022080471506624545, 364976571192311808]
        super().__init__(command_prefix="plz ", intents=intents, owner_ids=set(owners))

    async def on_ready(self):
        print("Online.")

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")


bot = MyBot()
if __name__ == "__main__":
    create_require_json()
    with open("not_token.json", mode="r", encoding="utf8") as jfile:
        jdata = json.load(jfile)
    bot.run(jdata["TOKEN"])
