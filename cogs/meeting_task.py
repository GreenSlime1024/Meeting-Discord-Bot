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
    
    async def get_meeting_info(self, meeting_doc, server_setting_doc):
        _id = ObjectId(meeting_doc["_id"])
        guild_id = meeting_doc["guild_id"]
        guild = self.bot.get_guild(guild_id)
        participate_role_id = meeting_doc["participate_role_id"]
        title = meeting_doc["title"]
        timezone = server_setting_doc["timezone"]
        meeting_timestamp_UTC = meeting_doc["meeting_timestamp_UTC"]         
        meeting = Meeting(self.bot, _id, guild, title, meeting_timestamp_UTC, timezone, participate_role_id)
        return meeting
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("MeetingTask cog loaded.")
        # load or start meeting from database
        meeting_coll  = self.mongo_client.meeting.meeting
        server_setting_coll = self.mongo_client.meeting.server_setting
        meeting_wait_load_or_start = []

        for meeting_doc in meeting_coll.find():
            server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
            meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
            meeting_wait_load_or_start.append(meeting.load_meeting())

            meeting_timestamp_UTC = meeting_doc["meeting_timestamp_UTC"]
            now_timestamp_UTC = int(datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0).timestamp())
            if meeting_timestamp_UTC <= now_timestamp_UTC and meeting_doc["status"] == "pending":
                meeting_wait_load_or_start.append(meeting.start_meeting())
        await asyncio.gather(*meeting_wait_load_or_start)

        # call start check loop
        await self.StartCheck.start()
    
    # start check loop
    @tasks.loop(seconds=1)
    async def StartCheck(self):
        now_time_UTC = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        now_timestamp_UTC = now_time_UTC.timestamp()
        if now_time_UTC.second == 0:
            meeting_coll = self.mongo_client.meeting.meeting
            server_setting_coll = self.mongo_client.meeting.server_setting
            meeting_wait_start = []
            
            for meeting_doc in meeting_coll.find({"meeting_timestamp_UTC": int(now_timestamp_UTC), "status": "pending"}):
                server_setting_doc = server_setting_coll.find_one({"guild_id": meeting_doc["guild_id"]})
                meeting = await self.get_meeting_info(meeting_doc, server_setting_doc)
                meeting_wait_start.append(meeting.start_meeting())
            await asyncio.gather(*meeting_wait_start)

async def setup(bot):
    await bot.add_cog(Meeting_task(bot))