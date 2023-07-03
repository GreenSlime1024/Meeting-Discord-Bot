import discord
from discord.ext import commands, tasks
from utils.meeting import Meeting
from pymongo import MongoClient
from bot import MyBot
from bson.objectid import ObjectId
import asyncio
import datetime
import pytz

class Meeting_task(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.mongo_client:MongoClient  = bot.mongo_client
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingTask cog loaded.")
        # load meeting from database
        self.meeting_coll  = self.mongo_client.meeting.meeting
        self.server_setting_coll = self.mongo_client.meeting.server_setting
        meeting_wait_load = []
        for meeting_doc in self.meeting_coll.find():
            _id = ObjectId(meeting_doc["_id"])
            guild_id = meeting_doc["guild_id"]
            guild = self.bot.get_guild(guild_id)
            participate_role_id = meeting_doc["participate_role_id"]
            title = meeting_doc["title"]
            timezone = self.server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})["timezone"]
            meeting_timestamp_UTC = meeting_doc["meeting_timestamp_UTC"]         
            meeting = Meeting(self.bot, guild, title, meeting_timestamp_UTC, timezone, participate_role_id)
            meeting_wait_load.append(meeting.load_meeting(_id))
        await asyncio.gather(*meeting_wait_load)
        
        # start meeting task
        @tasks.loop(seconds=1)
        async def start_meeting_task():
            now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)

        

async def setup(bot):
    await bot.add_cog(Meeting_task(bot))