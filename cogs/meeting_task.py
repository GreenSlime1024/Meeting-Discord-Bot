import discord
from discord.ext import commands
from utils.meeting import Meeting
from pymongo import MongoClient
from bot import MyBot
from bson.objectid import ObjectId
import asyncio

class Meeting_task(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.mongo_client:MongoClient  = bot.mongo_client
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingTask cog loaded.")
        self.meeting_coll  = self.mongo_client.meeting.meeting
        self.server_setting_coll = self.mongo_client.meeting.server_setting
        meeting_wait_load = []
        for meeting_doc in self.meeting_coll.find():
            _id = ObjectId(meeting_doc["_id"])
            guild_id = meeting_doc["guild_id"]
            guild = self.bot.get_guild(guild_id)
            title = meeting_doc["title"]
            start_time = meeting_doc["start_time"]
            day = start_time["day"]
            month = start_time["month"]
            year = start_time["year"]
            hour = start_time["hour"]
            minute = start_time["minute"]
            participate_role_id = meeting_doc["participate_role_id"]
            timezone = self.server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})["timezone"]
            meeting = Meeting(self.bot, guild, title, year, month, day, hour, minute, timezone, participate_role_id)
            meeting_wait_load.append(meeting.load_meeting(_id))
        await asyncio.gather(*meeting_wait_load)

async def setup(bot):
    await bot.add_cog(Meeting_task(bot))