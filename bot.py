import asyncio
import discord
import json
import os
from discord.ext import commands
import pymongo


def create_require_json():
    if os.path.exists("not_token.json"):
        print("not_token.json already exists.")
    else:
        data = {
            "TOKEN": "your token",
            "connection_string": "mongodb+srv://USERNAME:PASSWORD@dlh.ev44ah5.mongodb.net/?retryWrites=true&w=majority"
        }
        with open("not_token.json", "w") as jfile:
            json.dump(data, jfile, indent=4)
        print("Please fill the require data in not_token.json. Then run this file again.")


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="plz ", intents=discord.Intents.all(), owner_ids=set([1022080471506624545, 364976571192311808]))
        with open("not_token.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        connection_string = jdata["connection_string"]
        self.mongo_client = pymongo.MongoClient(connection_string)

    async def on_ready(self):
        print("Online.")

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")


bot = MyBot()

if __name__ == "__main__":
    create_require_json()
    with open("not_token.json", mode="r", encoding="utf8") as jfile:
        jdata = json.load(jfile)
    bot.run(jdata["TOKEN"])
