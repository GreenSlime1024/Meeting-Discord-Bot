import discord
import json
import os
from discord.ext import commands
import pymongo


def create_require_json():
    if os.path.exists("not_token.json"):
        return True
    else:
        data = {
            "TOKEN": "your token",
            "connection_string": "mongodb+srv://USERNAME:PASSWORD@dlh.ev44ah5.mongodb.net/?retryWrites=true&w=majority"
        }
        with open("not_token.json", "w") as jfile:
            json.dump(data, jfile, indent=4)
        return False


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

if __name__ == "__main__":
    if create_require_json():
        print("not_token.json already exists.")
        bot = MyBot()
        with open("not_token.json", mode="r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
        bot.run(jdata["TOKEN"])
    else:
        print("Please fill the require data in not_token.json. Then run this file again.")
